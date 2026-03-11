"""Unified market data collector that orchestrates all sub-collectors."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_data import BondDaily, FundNav, StockDaily
from app.services.market_data.base import BaseCollector
from app.services.market_data.a_share import AShareCollector
from app.services.market_data.bond import BondCollector
from app.services.market_data.fund import FundCollector
from app.services.market_data.hk_stock import HKStockCollector
from app.services.market_data.us_stock import USStockCollector

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """Facade that delegates to market-specific collectors and writes to DB."""

    def __init__(self) -> None:
        self.a_share = AShareCollector()
        self.us_stock = USStockCollector()
        self.hk_stock = HKStockCollector()
        self.fund = FundCollector()
        self.bond = BondCollector()

    # --- Stock daily (A-share / US / HK) ---

    async def collect_stock_daily(
        self,
        db: AsyncSession,
        market: str,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:
        """Fetch and store daily stock data.

        Args:
            db: Database session.
            market: One of "a_share", "us_stock", "hk_stock".
            symbol: Stock code / ticker.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            Number of rows upserted.
        """
        collector = self._get_stock_collector(market)
        df = await collector.fetch_daily(symbol, start_date, end_date)
        if df.empty:
            return 0

        records = self._df_to_stock_records(df)
        count = await collector.bulk_upsert(db, StockDaily, records)
        await db.commit()
        logger.info("Upserted %d rows for %s:%s", count, market, symbol)
        return count

    async def collect_fund_nav(
        self,
        db: AsyncSession,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:
        """Fetch and store fund NAV data."""
        df = await self.fund.fetch_daily(symbol, start_date, end_date)
        if df.empty:
            return 0

        records = self._df_to_fund_records(df)
        count = await self.fund.bulk_upsert(db, FundNav, records)
        await db.commit()
        logger.info("Upserted %d fund NAV rows for %s", count, symbol)
        return count

    async def collect_bond_daily(
        self,
        db: AsyncSession,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> int:
        """Fetch and store bond daily data."""
        df = await self.bond.fetch_daily(symbol, start_date, end_date)
        if df.empty:
            return 0

        records = self._df_to_bond_records(df)
        count = await self.bond.bulk_upsert(db, BondDaily, records)
        await db.commit()
        logger.info("Upserted %d bond rows for %s", count, symbol)
        return count

    # --- Batch operations ---

    async def collect_stock_batch(
        self,
        db: AsyncSession,
        market: str,
        symbols: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, int]:
        """Collect daily data for multiple symbols. Returns {symbol: row_count}."""
        results: dict[str, int] = {}
        for symbol in symbols:
            try:
                count = await self.collect_stock_daily(db, market, symbol, start_date, end_date)
                results[symbol] = count
            except Exception:
                logger.exception("Failed to collect %s:%s", market, symbol)
                results[symbol] = 0
        return results

    # --- Internal helpers ---

    def _get_stock_collector(self, market: str) -> AShareCollector | USStockCollector | HKStockCollector:
        collectors: dict[str, AShareCollector | USStockCollector | HKStockCollector] = {
            "a_share": self.a_share,
            "us_stock": self.us_stock,
            "hk_stock": self.hk_stock,
        }
        collector = collectors.get(market)
        if collector is None:
            raise ValueError(f"Unknown market: {market}. Expected one of {list(collectors.keys())}")
        return collector

    @staticmethod
    def _df_to_stock_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert a standardised stock DataFrame to list of dicts for upsert."""
        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "time": BaseCollector._ensure_tz_aware(row["time"]),
                "symbol": str(row["symbol"]),
                "name": row.get("name"),
                "market": str(row["market"]),
                "open": BaseCollector._safe_float(row["open"]),
                "high": BaseCollector._safe_float(row["high"]),
                "low": BaseCollector._safe_float(row["low"]),
                "close": BaseCollector._safe_float(row["close"]),
                "volume": BaseCollector._safe_int(row["volume"]),
                "amount": BaseCollector._safe_float(row.get("amount")),
                "turnover": BaseCollector._safe_float(row.get("turnover")),
                "change_pct": BaseCollector._safe_float(row.get("change_pct")),
                "amplitude": BaseCollector._safe_float(row.get("amplitude")),
            })
        return records

    @staticmethod
    def _df_to_fund_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert a standardised fund DataFrame to list of dicts for upsert."""
        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "time": BaseCollector._ensure_tz_aware(row["time"]),
                "symbol": str(row["symbol"]),
                "name": row.get("name"),
                "nav": BaseCollector._safe_float(row["nav"]),
                "accumulated_nav": BaseCollector._safe_float(row.get("accumulated_nav")),
                "daily_return": BaseCollector._safe_float(row.get("daily_return")),
            })
        return records

    @staticmethod
    def _df_to_bond_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert a standardised bond DataFrame to list of dicts for upsert."""
        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            records.append({
                "time": BaseCollector._ensure_tz_aware(row["time"]),
                "symbol": str(row["symbol"]),
                "name": row.get("name"),
                "bond_type": row.get("bond_type"),
                "close": BaseCollector._safe_float(row["close"]),
                "volume": BaseCollector._safe_int(row.get("volume", 0)),
                "amount": BaseCollector._safe_float(row.get("amount")),
                "ytm": BaseCollector._safe_float(row.get("ytm")),
                "change_pct": BaseCollector._safe_float(row.get("change_pct")),
            })
        return records

"""Feature Engine — orchestrates technical + fundamental feature computation and storage."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature import StockFeature
from app.services.feature_engine.fundamental import FundamentalCollector
from app.services.feature_engine.technical import compute_technical_indicators

logger = logging.getLogger(__name__)

# Columns produced by the technical indicator module
TECHNICAL_COLS = [
    "ma5", "ma10", "ma20", "ma60", "ma120", "ma250",
    "ema12", "ema26",
    "macd", "macd_signal", "macd_hist",
    "rsi_14",
    "kdj_k", "kdj_d", "kdj_j",
    "boll_upper", "boll_mid", "boll_lower",
    "atr_14",
    "obv",
]

FUNDAMENTAL_COLS = [
    "pe_ttm", "pb", "ps_ttm", "total_mv", "circ_mv",
    "roe", "revenue_yoy", "profit_yoy",
]

ALL_FEATURE_COLS = TECHNICAL_COLS + FUNDAMENTAL_COLS


class FeatureEngine:
    """Compute and persist stock features."""

    def __init__(self) -> None:
        self.fundamental = FundamentalCollector()

    async def compute_for_symbol(
        self,
        db: AsyncSession,
        symbol: str,
        market: str,
        lookback_days: int = 300,
        store_days: int | None = None,
    ) -> int:
        """Compute features for a single symbol and upsert into stock_features.

        Args:
            db: Async database session.
            symbol: Stock symbol.
            market: Market identifier (a_share / us_stock / hk_stock).
            lookback_days: How many days of historical data to load for
                indicator calculation (need enough for MA250).
            store_days: How many of the most recent days to store.
                None = store all computed rows.

        Returns:
            Number of feature rows upserted.
        """
        # 1. Load OHLCV from stock_daily
        ohlcv = await self._load_ohlcv(db, symbol, market, lookback_days)
        if ohlcv.empty:
            logger.info("No OHLCV data for %s/%s, skipping", market, symbol)
            return 0

        # 2. Compute technical indicators
        featured = compute_technical_indicators(ohlcv)

        # 3. Fetch fundamental factors (latest snapshot, apply to all rows)
        fund_data = await self.fundamental.fetch(symbol, market)

        # 4. Merge fundamentals into the DataFrame
        for col in FUNDAMENTAL_COLS:
            featured[col] = fund_data.get(col)

        # 5. Trim to store_days (only store the most recent N rows)
        if store_days is not None:
            featured = featured.tail(store_days)

        # 6. Build records and upsert
        records = self._to_records(featured, symbol, market)
        if not records:
            return 0

        return await self._upsert(db, records)

    async def compute_batch(
        self,
        db: AsyncSession,
        symbols: list[tuple[str, str]],
        lookback_days: int = 300,
        store_days: int | None = 1,
    ) -> dict[str, int]:
        """Compute features for multiple (symbol, market) pairs.

        Returns a dict mapping symbol -> rows upserted.
        """
        results: dict[str, int] = {}
        for symbol, market in symbols:
            try:
                count = await self.compute_for_symbol(
                    db, symbol, market, lookback_days, store_days,
                )
                results[symbol] = count
                if count > 0:
                    logger.info("Computed %d feature rows for %s/%s", count, market, symbol)
            except Exception:
                logger.error("Failed to compute features for %s/%s", market, symbol, exc_info=True)
                results[symbol] = 0
        return results

    async def _load_ohlcv(
        self,
        db: AsyncSession,
        symbol: str,
        market: str,
        lookback_days: int,
    ) -> pd.DataFrame:
        """Load OHLCV data from stock_daily ordered by time asc."""
        query = text("""
            SELECT time, open, high, low, close, volume
            FROM stock_daily
            WHERE symbol = :symbol AND market = :market
              AND time >= NOW() - make_interval(days => :days)
            ORDER BY time ASC
        """)
        result = await db.execute(query, {"symbol": symbol, "market": market, "days": lookback_days})
        rows = result.fetchall()
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
        # Ensure numeric types
        for col in ("open", "high", "low", "close"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(int)
        return df

    @staticmethod
    def _to_records(df: pd.DataFrame, symbol: str, market: str) -> list[dict[str, Any]]:
        """Convert featured DataFrame rows to dicts for upsert."""
        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            rec: dict[str, Any] = {
                "time": _ensure_tz(row["time"]),
                "symbol": symbol,
                "market": market,
            }
            for col in ALL_FEATURE_COLS:
                val = row.get(col)
                if val is not None and pd.notna(val):
                    rec[col] = float(val)
                else:
                    rec[col] = None
            records.append(rec)
        return records

    @staticmethod
    async def _upsert(db: AsyncSession, records: list[dict[str, Any]]) -> int:
        """Bulk upsert feature records into stock_features."""
        if not records:
            return 0

        table: Any = StockFeature.__table__
        stmt = pg_insert(table).values(records)

        pk_cols = {c.name for c in table.primary_key.columns}
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in table.columns
            if c.name not in pk_cols
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=list(pk_cols),
            set_=update_cols,
        )
        await db.execute(stmt)
        return len(records)


def _ensure_tz(dt: Any) -> datetime:
    """Ensure datetime is timezone-aware."""
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
    if isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    result: datetime = dt
    return result

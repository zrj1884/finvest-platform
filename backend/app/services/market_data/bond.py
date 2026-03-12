"""Bond data collector using AKShare."""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from functools import partial

import pandas as pd

from app.services.market_data.base import BaseCollector

logger = logging.getLogger(__name__)


class BondCollector(BaseCollector):
    """Collector for bond data via AKShare."""

    async def fetch_daily(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Fetch convertible bond daily data from AKShare.

        Args:
            symbol: Bond code, e.g. "113050" (南银转债)
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        """
        import akshare as ak

        loop = asyncio.get_running_loop()
        raw: pd.DataFrame = await loop.run_in_executor(
            None,
            partial(
                ak.bond_zh_hs_cov_daily,
                symbol=symbol,
            ),
        )

        if raw.empty:
            logger.warning("No data returned for bond %s", symbol)
            return pd.DataFrame()

        name = await self._fetch_name(symbol)
        return self._standardise(raw, symbol, name, start_date, end_date)

    # Well-known bond names (fallback when API unavailable)
    _BOND_NAMES: dict[str, str] = {
        "113009": "广汽转债", "113050": "南银转债", "128108": "蓝晓转2",
        "123045": "中矿转债", "110074": "精测转债", "113014": "林洋转债",
        "110043": "无锡转债", "128053": "尚荣转债", "123060": "天路转债",
        "110038": "济川转债", "019733": "24国债09", "019732": "24国债08",
    }

    @staticmethod
    def _strip_exchange(symbol: str) -> str:
        """Strip exchange prefix: 'sh113009' → '113009', 'sz128108' → '128108'."""
        if len(symbol) > 2 and symbol[:2] in ("sh", "sz"):
            return symbol[2:]
        return symbol

    async def _fetch_name(self, symbol: str) -> str | None:
        """Try to fetch bond name via AKShare, then fallback to known names."""
        import akshare as ak

        pure = self._strip_exchange(symbol)
        try:
            loop = asyncio.get_running_loop()
            df = await loop.run_in_executor(None, ak.bond_zh_hs_cov_spot)
            if not df.empty:
                # Try matching with and without exchange prefix
                for code in (symbol, pure):
                    row = df[df["symbol"] == code]
                    if not row.empty:
                        return str(row.iloc[0].get("name", symbol))
        except Exception:
            logger.debug("Could not fetch name for bond %s", symbol)
        return self._BOND_NAMES.get(pure)

    async def fetch_treasury_yield(self) -> pd.DataFrame:
        """Fetch China treasury yield curve data."""
        import akshare as ak

        loop = asyncio.get_running_loop()
        raw: pd.DataFrame = await loop.run_in_executor(
            None,
            ak.bond_china_yield,
        )
        return raw

    def _standardise(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Standardise AKShare bond DataFrame to our schema."""
        col_map: dict[str, str] = {
            "date": "time",
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close",
            "volume": "volume",
        }
        df = df.rename(columns=col_map)

        result = pd.DataFrame()
        result["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Shanghai")
        result["symbol"] = symbol
        result["name"] = name
        result["bond_type"] = "可转债"
        result["close"] = pd.to_numeric(df["close"], errors="coerce")
        result["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0).astype(int)
        result["amount"] = None
        result["ytm"] = None
        result["change_pct"] = result["close"].pct_change() * 100

        # Filter by date range
        if start_date:
            result = result[result["time"] >= pd.Timestamp(start_date, tz="Asia/Shanghai")]
        if end_date:
            result = result[result["time"] <= pd.Timestamp(end_date, tz="Asia/Shanghai")]

        return result

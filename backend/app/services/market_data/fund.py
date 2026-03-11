"""Fund NAV data collector using AKShare."""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from functools import partial

import pandas as pd

from app.services.market_data.base import BaseCollector

logger = logging.getLogger(__name__)


class FundCollector(BaseCollector):
    """Collector for fund NAV data via AKShare."""

    async def fetch_daily(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Fetch fund NAV history from AKShare.

        Args:
            symbol: Fund code, e.g. "110011" (易方达中小盘)
        """
        import akshare as ak

        loop = asyncio.get_running_loop()
        raw: pd.DataFrame = await loop.run_in_executor(
            None,
            partial(ak.fund_open_fund_info_em, symbol=symbol, indicator="单位净值走势"),
        )

        if raw.empty:
            logger.warning("No data returned for fund %s", symbol)
            return pd.DataFrame()

        return self._standardise(raw, symbol, start_date, end_date)

    def _standardise(
        self,
        df: pd.DataFrame,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Standardise AKShare fund NAV DataFrame to our schema."""
        col_map: dict[str, str] = {
            "净值日期": "time",
            "单位净值": "nav",
            "累计净值": "accumulated_nav",
            "日增长率": "daily_return",
        }
        df = df.rename(columns=col_map)

        keep = [c for c in col_map.values() if c in df.columns]
        df = df[keep].copy()

        df["symbol"] = symbol
        df["name"] = None

        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Shanghai")

        # Filter by date range
        if start_date:
            df = df[df["time"] >= pd.Timestamp(start_date, tz="Asia/Shanghai")]
        if end_date:
            df = df[df["time"] <= pd.Timestamp(end_date, tz="Asia/Shanghai")]

        return df

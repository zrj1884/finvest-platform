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

        # Fetch unit NAV (单位净值走势) — contains: 净值日期, 单位净值, 日增长率
        raw: pd.DataFrame = await loop.run_in_executor(
            None,
            partial(ak.fund_open_fund_info_em, symbol=symbol, indicator="单位净值走势"),
        )

        if raw.empty:
            logger.warning("No data returned for fund %s", symbol)
            return pd.DataFrame()

        # Fetch accumulated NAV (累计净值走势) — contains: 净值日期, 累计净值
        try:
            acc_raw: pd.DataFrame = await loop.run_in_executor(
                None,
                partial(ak.fund_open_fund_info_em, symbol=symbol, indicator="累计净值走势"),
            )
            if not acc_raw.empty and "累计净值" in acc_raw.columns and "净值日期" in acc_raw.columns:
                acc_raw["净值日期"] = pd.to_datetime(acc_raw["净值日期"]).dt.strftime("%Y-%m-%d")
                raw["净值日期"] = pd.to_datetime(raw["净值日期"]).dt.strftime("%Y-%m-%d")
                raw = raw.merge(acc_raw[["净值日期", "累计净值"]], on="净值日期", how="left")
        except Exception:
            logger.debug("Could not fetch accumulated NAV for fund %s", symbol)

        name = await self._fetch_name(symbol)
        return self._standardise(raw, symbol, name, start_date, end_date)

    async def _fetch_name(self, symbol: str) -> str | None:
        """Fetch fund name via AKShare."""
        import akshare as ak

        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(
                None,
                partial(ak.fund_individual_basic_info_xq, symbol=symbol),
            )
            row = info[info["item"] == "基金名称"]
            if not row.empty:
                return str(row.iloc[0]["value"])
        except Exception:
            logger.debug("Could not fetch name for fund %s", symbol)
        return None

    def _standardise(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str | None = None,
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
        df["name"] = name

        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Shanghai")

        # Filter by date range
        if start_date:
            df = df[df["time"] >= pd.Timestamp(start_date, tz="Asia/Shanghai")]
        if end_date:
            df = df[df["time"] <= pd.Timestamp(end_date, tz="Asia/Shanghai")]

        return df

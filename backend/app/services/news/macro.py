"""Macro economic data collector using AKShare."""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class MacroDataCollector:
    """Collector for macroeconomic data via AKShare."""

    async def fetch_gdp_china(self) -> pd.DataFrame:
        """Fetch China GDP quarterly data."""
        import akshare as ak

        loop = asyncio.get_running_loop()
        df: pd.DataFrame = await loop.run_in_executor(None, ak.macro_china_gdp)
        return df

    async def fetch_cpi_china(self) -> pd.DataFrame:
        """Fetch China CPI monthly data."""
        import akshare as ak

        loop = asyncio.get_running_loop()
        df: pd.DataFrame = await loop.run_in_executor(None, ak.macro_china_cpi)
        return df

    async def fetch_pmi_china(self) -> pd.DataFrame:
        """Fetch China PMI monthly data."""
        import akshare as ak

        loop = asyncio.get_running_loop()
        df: pd.DataFrame = await loop.run_in_executor(None, ak.macro_china_pmi)
        return df

    async def fetch_money_supply(self) -> pd.DataFrame:
        """Fetch China money supply (M0/M1/M2) data."""
        import akshare as ak

        loop = asyncio.get_running_loop()
        df: pd.DataFrame = await loop.run_in_executor(None, ak.macro_china_money_supply)
        return df

    async def fetch_shibor(self) -> pd.DataFrame:
        """Fetch Shanghai Interbank Offered Rate data."""
        import akshare as ak

        loop = asyncio.get_running_loop()
        df: pd.DataFrame = await loop.run_in_executor(
            None,
            partial(ak.rate_interbank, market="上海银行间同业拆放利率(Shibor)", symbol="隔夜", indicator="利率"),
        )
        return df

    async def fetch_summary(self) -> dict[str, Any]:
        """Fetch a summary of key macro indicators.

        Returns a dict with the latest values for each indicator.
        """
        summary: dict[str, Any] = {}

        try:
            gdp = await self.fetch_gdp_china()
            if not gdp.empty:
                summary["gdp_latest"] = gdp.iloc[-1].to_dict()
        except Exception:
            logger.exception("Failed to fetch GDP data")

        try:
            cpi = await self.fetch_cpi_china()
            if not cpi.empty:
                summary["cpi_latest"] = cpi.iloc[-1].to_dict()
        except Exception:
            logger.exception("Failed to fetch CPI data")

        try:
            pmi = await self.fetch_pmi_china()
            if not pmi.empty:
                summary["pmi_latest"] = pmi.iloc[-1].to_dict()
        except Exception:
            logger.exception("Failed to fetch PMI data")

        return summary

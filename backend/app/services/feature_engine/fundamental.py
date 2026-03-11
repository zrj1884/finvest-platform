"""Fundamental factor collection via AKShare.

Fetches PE/PB/PS/market-cap/ROE/revenue-growth for A-share stocks.
US and HK stocks use a simplified approach (yfinance `.info`).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class FundamentalCollector:
    """Collect fundamental factors for different markets."""

    async def fetch_a_share(self, symbol: str) -> dict[str, Any]:
        """Fetch A-share fundamental data from AKShare.

        Uses ak.stock_individual_info_em for basic info (PE/PB/total_mv etc.)
        Returns a dict with keys: pe_ttm, pb, ps_ttm, total_mv, circ_mv, roe,
        revenue_yoy, profit_yoy.  Missing values are None.
        """
        loop = asyncio.get_running_loop()
        try:
            info = await loop.run_in_executor(None, self._fetch_a_share_info, symbol)
            return info
        except Exception:
            logger.warning("Failed to fetch A-share fundamentals for %s", symbol, exc_info=True)
            return {}

    @staticmethod
    def _fetch_a_share_info(symbol: str) -> dict[str, Any]:
        import akshare as ak

        result: dict[str, Any] = {}

        # stock_individual_info_em returns a 2-column DataFrame: item, value
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            if df is not None and not df.empty:
                info_map: dict[str, Any] = {}
                for _, row in df.iterrows():
                    info_map[str(row.iloc[0])] = row.iloc[1]

                result["total_mv"] = _safe_float(info_map.get("总市值"))
                result["circ_mv"] = _safe_float(info_map.get("流通市值"))

                # Convert to 亿
                if result["total_mv"] is not None:
                    result["total_mv"] = round(result["total_mv"] / 1e8, 2)
                if result["circ_mv"] is not None:
                    result["circ_mv"] = round(result["circ_mv"] / 1e8, 2)
        except Exception:
            logger.debug("stock_individual_info_em failed for %s", symbol, exc_info=True)

        # stock_individual_spot_xq for PE/PB (雪球实时数据)
        try:
            # xq requires SZ/SH prefix
            xq_symbol = f"SZ{symbol}" if symbol.startswith(("0", "3")) else f"SH{symbol}"
            df_xq = ak.stock_individual_spot_xq(symbol=xq_symbol)
            if df_xq is not None and not df_xq.empty:
                xq_map: dict[str, Any] = {}
                for _, xq_row in df_xq.iterrows():
                    xq_map[str(xq_row.iloc[0])] = xq_row.iloc[1]
                result["pe_ttm"] = _safe_float(xq_map.get("市盈率(动)"))
                # PB = price / 每股净资产
                bvps = _safe_float(xq_map.get("每股净资产"))
                price = _safe_float(xq_map.get("现价"))
                if bvps and price and bvps > 0:
                    result["pb"] = round(price / bvps, 4)
        except Exception:
            logger.debug("stock_individual_spot_xq failed for %s", symbol, exc_info=True)

        # stock_financial_analysis_indicator for ROE / growth
        try:
            df_fin = ak.stock_financial_analysis_indicator(symbol=symbol, start_year="2024")
            if df_fin is not None and not df_fin.empty:
                latest_fin = df_fin.iloc[0]  # most recent
                result["roe"] = _safe_float(latest_fin.get("净资产收益率(%)"))
                result["revenue_yoy"] = _safe_float(latest_fin.get("主营业务收入增长率(%)"))
                result["profit_yoy"] = _safe_float(latest_fin.get("净利润增长率(%)"))
        except Exception:
            logger.debug("stock_financial_analysis_indicator failed for %s", symbol, exc_info=True)

        return result

    async def fetch_us_stock(self, symbol: str) -> dict[str, Any]:
        """Fetch US stock fundamental data via yfinance."""
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, self._fetch_yf_info, symbol)
        except Exception:
            logger.warning("Failed to fetch US fundamentals for %s", symbol, exc_info=True)
            return {}

    @staticmethod
    def _fetch_yf_info(symbol: str) -> dict[str, Any]:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        return {
            "pe_ttm": _safe_float(info.get("trailingPE")),
            "pb": _safe_float(info.get("priceToBook")),
            "ps_ttm": _safe_float(info.get("priceToSalesTrailing12Months")),
            "total_mv": _round_to_yi(_safe_float(info.get("marketCap"))),
            "circ_mv": None,  # yfinance doesn't differentiate
            "roe": _pct_from_ratio(_safe_float(info.get("returnOnEquity"))),
            "revenue_yoy": _pct_from_ratio(_safe_float(info.get("revenueGrowth"))),
            "profit_yoy": _pct_from_ratio(_safe_float(info.get("earningsGrowth"))),
        }

    async def fetch_hk_stock(self, symbol: str) -> dict[str, Any]:
        """Fetch HK stock fundamentals — uses yfinance with .HK suffix."""
        yf_symbol = f"{symbol}.HK" if not symbol.endswith(".HK") else symbol
        return await self.fetch_us_stock(yf_symbol)

    async def fetch(self, symbol: str, market: str) -> dict[str, Any]:
        """Dispatch to the appropriate market collector."""
        if market == "a_share":
            return await self.fetch_a_share(symbol)
        elif market == "us_stock":
            return await self.fetch_us_stock(symbol)
        elif market == "hk_stock":
            return await self.fetch_hk_stock(symbol)
        return {}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
        if pd.isna(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _round_to_yi(value: float | None) -> float | None:
    """Convert a raw number to 亿 (1e8)."""
    if value is None:
        return None
    return round(value / 1e8, 2)


def _pct_from_ratio(value: float | None) -> float | None:
    """Convert a ratio (0.15) to percentage (15.0)."""
    if value is None:
        return None
    return round(value * 100, 4)

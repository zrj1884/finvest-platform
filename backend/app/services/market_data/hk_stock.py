"""Hong Kong stock market data collector using AKShare."""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from functools import partial

import pandas as pd

from app.services.market_data.base import BaseCollector

logger = logging.getLogger(__name__)


class HKStockCollector(BaseCollector):
    """Collector for HK stock data via AKShare."""

    MARKET = "hk_stock"

    async def fetch_daily(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Fetch HK stock daily OHLCV from AKShare.

        Args:
            symbol: HK stock code, e.g. "00700" (腾讯), "09988" (阿里巴巴)
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        """
        import akshare as ak

        start_str = start_date.strftime("%Y%m%d") if start_date else "19900101"
        end_str = end_date.strftime("%Y%m%d") if end_date else date.today().strftime("%Y%m%d")

        loop = asyncio.get_running_loop()
        raw: pd.DataFrame = await loop.run_in_executor(
            None,
            partial(
                ak.stock_hk_hist,
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq",
            ),
        )

        if raw.empty:
            logger.warning("No data returned for HK stock %s", symbol)
            return pd.DataFrame()

        name = await self._fetch_name(symbol)
        return self._standardise(raw, symbol, name)

    # Well-known HK stock names (fallback when API unavailable)
    _HK_NAMES: dict[str, str] = {
        "00700": "腾讯控股", "09988": "阿里巴巴-W", "01810": "小米集团-W",
        "09999": "网易-S", "03690": "美团-W", "00005": "汇丰控股",
        "02318": "中国平安", "00388": "香港交易所", "01024": "快手-W",
        "09618": "京东集团-SW", "09888": "百度集团-SW",
        "02020": "安踏体育", "01211": "比亚迪股份", "00941": "中国移动",
        "00883": "中国海洋石油",
    }

    async def _fetch_name(self, symbol: str) -> str | None:
        """Fetch HK stock name: try yfinance first, then fallback to known names."""
        try:
            import yfinance as yf

            loop = asyncio.get_running_loop()
            ticker = yf.Ticker(f"{symbol}.HK")
            info: dict[str, object] = await loop.run_in_executor(None, lambda: ticker.info)
            name = str(info.get("shortName") or info.get("longName") or "")
            if name:
                return name
        except Exception:
            logger.debug("yfinance lookup failed for HK %s, using fallback", symbol)
        return self._HK_NAMES.get(symbol)

    def _standardise(self, df: pd.DataFrame, symbol: str, name: str | None = None) -> pd.DataFrame:
        """Standardise AKShare HK stock DataFrame to our schema."""
        col_map: dict[str, str] = {
            "日期": "time",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
            "换手率": "turnover",
            "涨跌幅": "change_pct",
            "振幅": "amplitude",
        }
        df = df.rename(columns=col_map)

        keep = [c for c in col_map.values() if c in df.columns]
        df = df[keep].copy()

        df["symbol"] = symbol
        df["name"] = name
        df["market"] = self.MARKET

        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Hong_Kong")

        return df

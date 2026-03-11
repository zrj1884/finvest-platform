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

        return self._standardise(raw, symbol)

    def _standardise(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
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
        df["name"] = None
        df["market"] = self.MARKET

        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Hong_Kong")

        return df

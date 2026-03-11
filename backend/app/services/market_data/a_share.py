"""A-share (A股) market data collector using AKShare."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone
from functools import partial

import pandas as pd

from app.services.market_data.base import BaseCollector

logger = logging.getLogger(__name__)


class AShareCollector(BaseCollector):
    """Collector for A-share (沪深A股) data via AKShare."""

    MARKET = "a_share"

    async def fetch_daily(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Fetch A-share daily OHLCV from AKShare.

        Args:
            symbol: Stock code, e.g. "000001" (平安银行), "600519" (贵州茅台)
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
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust="qfq",  # 前复权
            ),
        )

        if raw.empty:
            logger.warning("No data returned for A-share %s", symbol)
            return pd.DataFrame()

        return self._standardise(raw, symbol)

    async def fetch_realtime(self, symbols: list[str] | None = None) -> pd.DataFrame:
        """Fetch realtime A-share quotes.

        Args:
            symbols: Optional list of stock codes to filter.
                     If None, returns all A-share realtime quotes.
        """
        import akshare as ak

        loop = asyncio.get_running_loop()
        raw: pd.DataFrame = await loop.run_in_executor(
            None,
            ak.stock_zh_a_spot_em,
        )

        if raw.empty:
            return pd.DataFrame()

        if symbols:
            raw = raw[raw["代码"].isin(symbols)]

        return self._standardise_realtime(raw)

    def _standardise(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Standardise AKShare A-share history DataFrame to our schema."""
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

        # Keep only mapped columns that exist
        keep = [c for c in col_map.values() if c in df.columns]
        df = df[keep].copy()

        df["symbol"] = symbol
        df["name"] = None  # name not in history API
        df["market"] = self.MARKET

        # Parse time
        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Shanghai")

        return df

    def _standardise_realtime(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardise AKShare A-share realtime DataFrame."""
        now = datetime.now(tz=timezone.utc)
        col_map: dict[str, str] = {
            "代码": "symbol",
            "名称": "name",
            "今开": "open",
            "最高": "high",
            "最低": "low",
            "最新价": "close",
            "成交量": "volume",
            "成交额": "amount",
            "换手率": "turnover",
            "涨跌幅": "change_pct",
            "振幅": "amplitude",
        }
        df = df.rename(columns=col_map)
        keep = [c for c in col_map.values() if c in df.columns]
        df = df[keep].copy()

        df["market"] = self.MARKET
        df["time"] = now

        return df

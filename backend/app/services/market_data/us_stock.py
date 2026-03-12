"""US stock market data collector using yfinance."""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from functools import partial

import pandas as pd

from app.services.market_data.base import BaseCollector

logger = logging.getLogger(__name__)


class USStockCollector(BaseCollector):
    """Collector for US stock data via yfinance."""

    MARKET = "us_stock"

    async def fetch_daily(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Fetch US stock daily OHLCV from yfinance.

        Args:
            symbol: Ticker symbol, e.g. "AAPL", "MSFT", "GOOGL"
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        """

        start_str = start_date.isoformat() if start_date else "2021-01-01"
        end_str = end_date.isoformat() if end_date else date.today().isoformat()

        loop = asyncio.get_running_loop()
        raw: pd.DataFrame = await loop.run_in_executor(
            None,
            partial(
                _download_yf,
                symbol=symbol,
                start=start_str,
                end=end_str,
            ),
        )

        if raw.empty:
            logger.warning("No data returned for US stock %s", symbol)
            return pd.DataFrame()

        name = await self._fetch_name(symbol)
        return self._standardise(raw, symbol, name)

    async def _fetch_name(self, symbol: str) -> str | None:
        """Fetch US stock name via yfinance."""
        try:
            import yfinance as yf

            loop = asyncio.get_running_loop()
            ticker = yf.Ticker(symbol)
            info: dict[str, object] = await loop.run_in_executor(None, lambda: ticker.info)
            return str(info.get("shortName") or info.get("longName") or symbol)
        except Exception:
            logger.debug("Could not fetch name for US stock %s", symbol)
        return None

    def _standardise(self, df: pd.DataFrame, symbol: str, name: str | None = None) -> pd.DataFrame:
        """Standardise yfinance DataFrame to our schema."""
        df = df.reset_index()

        col_map: dict[str, str] = {
            "Date": "time",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df = df.rename(columns=col_map)

        keep = [c for c in col_map.values() if c in df.columns]
        df = df[keep].copy()

        df["symbol"] = symbol
        df["name"] = name
        df["market"] = self.MARKET
        df["amount"] = None
        df["turnover"] = None
        df["amplitude"] = None

        # Calculate change_pct from close prices
        df["change_pct"] = df["close"].pct_change() * 100

        # Ensure timezone-aware
        df["time"] = pd.to_datetime(df["time"])
        if df["time"].dt.tz is None:
            df["time"] = df["time"].dt.tz_localize("America/New_York")
        else:
            df["time"] = df["time"].dt.tz_convert("America/New_York")

        return df


def _download_yf(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Synchronous yfinance download (run in executor)."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    df: pd.DataFrame = ticker.history(start=start, end=end, auto_adjust=True)
    return df

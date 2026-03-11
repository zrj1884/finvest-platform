"""Tests for market data collection services."""

from datetime import date, datetime, timezone
from unittest.mock import patch

import pandas as pd
import pytest

from app.services.market_data.a_share import AShareCollector
from app.services.market_data.base import BaseCollector
from app.services.market_data.bond import BondCollector
from app.services.market_data.collector import MarketDataCollector
from app.services.market_data.fund import FundCollector
from app.services.market_data.hk_stock import HKStockCollector
from app.services.market_data.us_stock import USStockCollector


# --- BaseCollector helper tests ---

class TestBaseCollectorHelpers:
    def test_safe_float_normal(self) -> None:
        assert BaseCollector._safe_float(3.14) == 3.14

    def test_safe_float_none(self) -> None:
        assert BaseCollector._safe_float(None) is None

    def test_safe_float_nan(self) -> None:
        assert BaseCollector._safe_float(float("nan")) is None

    def test_safe_float_string(self) -> None:
        assert BaseCollector._safe_float("abc") is None

    def test_safe_int_normal(self) -> None:
        assert BaseCollector._safe_int(42) == 42

    def test_safe_int_none(self) -> None:
        assert BaseCollector._safe_int(None) == 0

    def test_safe_int_nan(self) -> None:
        assert BaseCollector._safe_int(float("nan")) == 0

    def test_ensure_tz_aware_naive(self) -> None:
        naive = datetime(2025, 1, 1, 12, 0, 0)
        aware = BaseCollector._ensure_tz_aware(naive)
        assert aware.tzinfo is not None
        assert aware.tzinfo == timezone.utc

    def test_ensure_tz_aware_already_aware(self) -> None:
        aware = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = BaseCollector._ensure_tz_aware(aware)
        assert result.tzinfo == timezone.utc

    def test_ensure_tz_aware_pandas_timestamp(self) -> None:
        ts = pd.Timestamp("2025-01-01 12:00:00")
        result = BaseCollector._ensure_tz_aware(ts)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None


# --- A-share collector tests ---

class TestAShareCollector:
    @pytest.fixture()
    def collector(self) -> AShareCollector:
        return AShareCollector()

    def _make_raw_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "日期": ["2025-01-02", "2025-01-03"],
            "开盘": [10.0, 10.5],
            "最高": [10.8, 11.0],
            "最低": [9.9, 10.2],
            "收盘": [10.5, 10.8],
            "成交量": [100000, 120000],
            "成交额": [1050000, 1296000],
            "换手率": [1.5, 1.8],
            "涨跌幅": [2.0, 2.86],
            "振幅": [8.5, 7.5],
        })

    @pytest.mark.asyncio
    async def test_fetch_daily(self, collector: AShareCollector) -> None:
        raw = self._make_raw_df()
        with patch("akshare.stock_zh_a_hist", return_value=raw):
            df = await collector.fetch_daily("000001", date(2025, 1, 1), date(2025, 1, 31))

        assert len(df) == 2
        assert "time" in df.columns
        assert "symbol" in df.columns
        assert df["symbol"].iloc[0] == "000001"
        assert df["market"].iloc[0] == "a_share"
        assert df["close"].iloc[0] == 10.5

    @pytest.mark.asyncio
    async def test_fetch_daily_empty(self, collector: AShareCollector) -> None:
        with patch("akshare.stock_zh_a_hist", return_value=pd.DataFrame()):
            df = await collector.fetch_daily("000001")

        assert df.empty

    @pytest.mark.asyncio
    async def test_fetch_realtime(self, collector: AShareCollector) -> None:
        raw = pd.DataFrame({
            "代码": ["000001", "600519"],
            "名称": ["平安银行", "贵州茅台"],
            "今开": [10.0, 1800.0],
            "最高": [10.5, 1850.0],
            "最低": [9.8, 1790.0],
            "最新价": [10.3, 1820.0],
            "成交量": [500000, 30000],
            "成交额": [5150000.0, 54600000.0],
            "换手率": [2.5, 0.3],
            "涨跌幅": [3.0, 1.1],
            "振幅": [7.0, 3.3],
        })
        with patch("akshare.stock_zh_a_spot_em", return_value=raw):
            df = await collector.fetch_realtime(["000001"])

        assert len(df) == 1
        assert df["symbol"].iloc[0] == "000001"


# --- US stock collector tests ---

class TestUSStockCollector:
    @pytest.fixture()
    def collector(self) -> USStockCollector:
        return USStockCollector()

    @pytest.mark.asyncio
    async def test_fetch_daily(self, collector: USStockCollector) -> None:
        raw = pd.DataFrame({
            "Date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
            "Open": [150.0, 152.0],
            "High": [155.0, 156.0],
            "Low": [149.0, 151.0],
            "Close": [153.0, 154.5],
            "Volume": [1000000, 1100000],
        })
        raw = raw.set_index("Date")

        with patch("app.services.market_data.us_stock._download_yf", return_value=raw):
            df = await collector.fetch_daily("AAPL", date(2025, 1, 1), date(2025, 1, 31))

        assert len(df) == 2
        assert df["symbol"].iloc[0] == "AAPL"
        assert df["market"].iloc[0] == "us_stock"
        assert df["close"].iloc[0] == 153.0

    @pytest.mark.asyncio
    async def test_fetch_daily_empty(self, collector: USStockCollector) -> None:
        with patch("app.services.market_data.us_stock._download_yf", return_value=pd.DataFrame()):
            df = await collector.fetch_daily("INVALID")

        assert df.empty


# --- HK stock collector tests ---

class TestHKStockCollector:
    @pytest.fixture()
    def collector(self) -> HKStockCollector:
        return HKStockCollector()

    @pytest.mark.asyncio
    async def test_fetch_daily(self, collector: HKStockCollector) -> None:
        raw = pd.DataFrame({
            "日期": ["2025-01-02", "2025-01-03"],
            "开盘": [400.0, 405.0],
            "最高": [410.0, 412.0],
            "最低": [398.0, 402.0],
            "收盘": [408.0, 410.0],
            "成交量": [5000000, 5500000],
            "成交额": [2040000000.0, 2255000000.0],
            "换手率": [0.5, 0.55],
            "涨跌幅": [2.0, 0.49],
            "振幅": [3.0, 2.47],
        })
        with patch("akshare.stock_hk_hist", return_value=raw):
            df = await collector.fetch_daily("00700", date(2025, 1, 1), date(2025, 1, 31))

        assert len(df) == 2
        assert df["symbol"].iloc[0] == "00700"
        assert df["market"].iloc[0] == "hk_stock"


# --- Fund collector tests ---

class TestFundCollector:
    @pytest.fixture()
    def collector(self) -> FundCollector:
        return FundCollector()

    @pytest.mark.asyncio
    async def test_fetch_daily(self, collector: FundCollector) -> None:
        raw = pd.DataFrame({
            "净值日期": ["2025-01-02", "2025-01-03"],
            "单位净值": [1.5, 1.52],
            "累计净值": [3.2, 3.22],
            "日增长率": [0.5, 1.33],
        })
        with patch("akshare.fund_open_fund_info_em", return_value=raw):
            df = await collector.fetch_daily("110011")

        assert len(df) == 2
        assert df["symbol"].iloc[0] == "110011"
        assert "nav" in df.columns


# --- Bond collector tests ---

class TestBondCollector:
    @pytest.fixture()
    def collector(self) -> BondCollector:
        return BondCollector()

    @pytest.mark.asyncio
    async def test_fetch_daily(self, collector: BondCollector) -> None:
        raw = pd.DataFrame({
            "date": ["2025-01-02", "2025-01-03"],
            "open": [100.0, 101.0],
            "high": [101.5, 102.0],
            "low": [99.5, 100.5],
            "close": [101.0, 101.5],
            "volume": [10000, 12000],
        })
        with patch("akshare.bond_zh_hs_cov_daily", return_value=raw):
            df = await collector.fetch_daily("113050")

        assert len(df) == 2
        assert df["symbol"].iloc[0] == "113050"
        assert df["bond_type"].iloc[0] == "可转债"


# --- MarketDataCollector orchestrator tests ---

class TestMarketDataCollector:
    def test_get_stock_collector_a_share(self) -> None:
        mdc = MarketDataCollector()
        assert isinstance(mdc._get_stock_collector("a_share"), AShareCollector)

    def test_get_stock_collector_us_stock(self) -> None:
        mdc = MarketDataCollector()
        assert isinstance(mdc._get_stock_collector("us_stock"), USStockCollector)

    def test_get_stock_collector_hk_stock(self) -> None:
        mdc = MarketDataCollector()
        assert isinstance(mdc._get_stock_collector("hk_stock"), HKStockCollector)

    def test_get_stock_collector_invalid(self) -> None:
        mdc = MarketDataCollector()
        with pytest.raises(ValueError, match="Unknown market"):
            mdc._get_stock_collector("invalid")

    def test_df_to_stock_records(self) -> None:
        df = pd.DataFrame({
            "time": [datetime(2025, 1, 2, tzinfo=timezone.utc)],
            "symbol": ["000001"],
            "name": ["平安银行"],
            "market": ["a_share"],
            "open": [10.0],
            "high": [10.5],
            "low": [9.8],
            "close": [10.3],
            "volume": [100000],
            "amount": [1030000.0],
            "turnover": [1.5],
            "change_pct": [3.0],
            "amplitude": [7.0],
        })
        records = MarketDataCollector._df_to_stock_records(df)
        assert len(records) == 1
        assert records[0]["symbol"] == "000001"
        assert records[0]["close"] == 10.3

    def test_df_to_fund_records(self) -> None:
        df = pd.DataFrame({
            "time": [datetime(2025, 1, 2, tzinfo=timezone.utc)],
            "symbol": ["110011"],
            "name": [None],
            "nav": [1.5],
            "accumulated_nav": [3.2],
            "daily_return": [0.5],
        })
        records = MarketDataCollector._df_to_fund_records(df)
        assert len(records) == 1
        assert records[0]["nav"] == 1.5

    def test_df_to_bond_records(self) -> None:
        df = pd.DataFrame({
            "time": [datetime(2025, 1, 2, tzinfo=timezone.utc)],
            "symbol": ["113050"],
            "name": [None],
            "bond_type": ["可转债"],
            "close": [101.0],
            "volume": [10000],
            "amount": [None],
            "ytm": [None],
            "change_pct": [0.5],
        })
        records = MarketDataCollector._df_to_bond_records(df)
        assert len(records) == 1
        assert records[0]["bond_type"] == "可转债"

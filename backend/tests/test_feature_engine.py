"""Tests for feature engineering pipeline."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.feature_engine.technical import (
    compute_technical_indicators,
    compute_ma,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_kdj,
    compute_bollinger,
    compute_atr,
    compute_obv,
)
from app.services.feature_engine.fundamental import FundamentalCollector, _safe_float, _round_to_yi, _pct_from_ratio
from app.services.feature_engine.engine import FeatureEngine, _ensure_tz


def _make_ohlcv(n: int = 100) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_ = close + np.random.randn(n) * 0.5
    volume = np.random.randint(1000000, 10000000, size=n)
    return pd.DataFrame({
        "time": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


# ===== Technical Indicators =====

class TestMovingAverages:
    def test_ma_columns_exist(self) -> None:
        df = compute_ma(_make_ohlcv())
        for p in (5, 10, 20, 60, 120, 250):
            assert f"ma{p}" in df.columns

    def test_ma5_value(self) -> None:
        df = _make_ohlcv(10)
        df = compute_ma(df)
        expected = df["close"].iloc[:5].mean()
        assert abs(df["ma5"].iloc[4] - expected) < 0.0001

    def test_ma_nan_before_period(self) -> None:
        df = compute_ma(_make_ohlcv(10))
        assert pd.isna(df["ma10"].iloc[8])
        assert pd.notna(df["ma10"].iloc[9])


class TestEMA:
    def test_ema_columns(self) -> None:
        df = compute_ema(_make_ohlcv())
        assert "ema12" in df.columns
        assert "ema26" in df.columns

    def test_ema_not_nan(self) -> None:
        df = compute_ema(_make_ohlcv(30))
        assert pd.notna(df["ema12"].iloc[-1])
        assert pd.notna(df["ema26"].iloc[-1])


class TestMACD:
    def test_macd_columns(self) -> None:
        df = compute_macd(_make_ohlcv())
        assert "macd" in df.columns
        assert "macd_signal" in df.columns
        assert "macd_hist" in df.columns

    def test_macd_hist_equals_diff(self) -> None:
        df = compute_macd(_make_ohlcv())
        diff = df["macd"] - df["macd_signal"]
        np.testing.assert_array_almost_equal(df["macd_hist"].values, diff.values)


class TestRSI:
    def test_rsi_range(self) -> None:
        df = compute_rsi(_make_ohlcv())
        valid = df["rsi_14"].dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_rsi_column_exists(self) -> None:
        df = compute_rsi(_make_ohlcv())
        assert "rsi_14" in df.columns


class TestKDJ:
    def test_kdj_columns(self) -> None:
        df = compute_kdj(_make_ohlcv())
        assert "kdj_k" in df.columns
        assert "kdj_d" in df.columns
        assert "kdj_j" in df.columns

    def test_kdj_j_formula(self) -> None:
        df = compute_kdj(_make_ohlcv())
        valid = df.dropna(subset=["kdj_k", "kdj_d", "kdj_j"])
        expected_j = 3.0 * valid["kdj_k"] - 2.0 * valid["kdj_d"]
        np.testing.assert_array_almost_equal(valid["kdj_j"].values, expected_j.values)


class TestBollinger:
    def test_bollinger_columns(self) -> None:
        df = compute_bollinger(_make_ohlcv())
        assert "boll_upper" in df.columns
        assert "boll_mid" in df.columns
        assert "boll_lower" in df.columns

    def test_bollinger_symmetry(self) -> None:
        df = compute_bollinger(_make_ohlcv())
        valid = df.dropna(subset=["boll_upper", "boll_mid", "boll_lower"])
        upper_diff = valid["boll_upper"] - valid["boll_mid"]
        lower_diff = valid["boll_mid"] - valid["boll_lower"]
        np.testing.assert_array_almost_equal(upper_diff.values, lower_diff.values)


class TestATR:
    def test_atr_positive(self) -> None:
        df = compute_atr(_make_ohlcv())
        valid = df["atr_14"].dropna()
        assert (valid > 0).all()


class TestOBV:
    def test_obv_starts_at_zero(self) -> None:
        df = compute_obv(_make_ohlcv())
        # OBV at index 0: sign(diff) is 0, so cumsum starts at 0
        assert df["obv"].iloc[0] == 0.0


class TestAllIndicators:
    def test_compute_all(self) -> None:
        df = compute_technical_indicators(_make_ohlcv(300))
        expected_cols = [
            "ma5", "ma10", "ma20", "ma60", "ma120", "ma250",
            "ema12", "ema26", "macd", "macd_signal", "macd_hist",
            "rsi_14", "kdj_k", "kdj_d", "kdj_j",
            "boll_upper", "boll_mid", "boll_lower",
            "atr_14", "obv",
        ]
        for col in expected_cols:
            assert col in df.columns

    def test_empty_dataframe(self) -> None:
        df = compute_technical_indicators(pd.DataFrame())
        assert df.empty


# ===== Fundamental Helpers =====

class TestFundamentalHelpers:
    def test_safe_float(self) -> None:
        assert _safe_float(None) is None
        assert _safe_float(float("nan")) is None
        assert _safe_float("abc") is None
        assert _safe_float(3.14) == 3.14
        assert _safe_float("42") == 42.0

    def test_round_to_yi(self) -> None:
        assert _round_to_yi(None) is None
        assert _round_to_yi(1e10) == 100.0
        assert _round_to_yi(5e8) == 5.0

    def test_pct_from_ratio(self) -> None:
        assert _pct_from_ratio(None) is None
        assert _pct_from_ratio(0.15) == 15.0
        assert _pct_from_ratio(-0.05) == -5.0


class TestFundamentalCollector:
    @pytest.mark.asyncio
    async def test_fetch_a_share(self) -> None:
        collector = FundamentalCollector()
        mock_info_df = pd.DataFrame({"item": ["总市值", "流通市值"], "value": [1e12, 8e11]})
        mock_xq_df = pd.DataFrame({
            "item": ["市盈率(动)", "每股净资产", "现价"],
            "value": [15.5, 20.0, 30.0],
        })
        mock_fin_df = pd.DataFrame({
            "净资产收益率(%)": [12.5],
            "主营业务收入增长率(%)": [20.3],
            "净利润增长率(%)": [15.8],
        })

        with (
            patch("akshare.stock_individual_info_em", return_value=mock_info_df),
            patch("akshare.stock_individual_spot_xq", return_value=mock_xq_df),
            patch("akshare.stock_financial_analysis_indicator", return_value=mock_fin_df),
        ):
            result = await collector.fetch_a_share("000001")

        assert result["total_mv"] == 10000.0
        assert result["pe_ttm"] == 15.5
        assert result["pb"] == 1.5  # 30.0 / 20.0
        assert result["roe"] == 12.5

    @pytest.mark.asyncio
    async def test_fetch_us_stock(self) -> None:
        collector = FundamentalCollector()
        mock_info = {
            "trailingPE": 25.0,
            "priceToBook": 10.5,
            "priceToSalesTrailing12Months": 8.0,
            "marketCap": 3e12,
            "returnOnEquity": 0.30,
            "revenueGrowth": 0.10,
            "earningsGrowth": 0.15,
        }

        with patch("yfinance.Ticker") as MockTicker:
            instance = MagicMock()
            instance.info = mock_info
            MockTicker.return_value = instance
            result = await collector.fetch_us_stock("AAPL")

        assert result["pe_ttm"] == 25.0
        assert result["roe"] == 30.0
        assert result["total_mv"] == 30000.0

    @pytest.mark.asyncio
    async def test_fetch_dispatches(self) -> None:
        collector = FundamentalCollector()
        with patch.object(collector, "fetch_a_share", new_callable=AsyncMock, return_value={"pe_ttm": 10}) as mock:
            result = await collector.fetch("000001", "a_share")
            mock.assert_called_once_with("000001")
            assert result == {"pe_ttm": 10}

    @pytest.mark.asyncio
    async def test_fetch_unknown_market(self) -> None:
        collector = FundamentalCollector()
        result = await collector.fetch("XYZ", "unknown")
        assert result == {}


# ===== Engine =====

class TestEnsureTz:
    def test_naive_datetime(self) -> None:
        from datetime import datetime, timezone
        dt = _ensure_tz(datetime(2025, 1, 1))
        assert dt.tzinfo is not None
        assert dt.tzinfo == timezone.utc

    def test_pandas_timestamp(self) -> None:
        ts = pd.Timestamp("2025-01-01")
        result = _ensure_tz(ts)
        assert result.tzinfo is not None

    def test_date_object(self) -> None:
        from datetime import date
        result = _ensure_tz(date(2025, 1, 1))
        assert hasattr(result, "hour")  # it's a datetime now


class TestFeatureEngine:
    @pytest.mark.asyncio
    async def test_compute_for_symbol_no_data(self) -> None:
        engine = FeatureEngine()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        count = await engine.compute_for_symbol(mock_db, "000001", "a_share")
        assert count == 0

    @pytest.mark.asyncio
    async def test_compute_for_symbol_with_data(self) -> None:
        engine = FeatureEngine()
        ohlcv = _make_ohlcv(50)
        rows = [tuple(row) for row in ohlcv.values]

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = rows
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch.object(engine.fundamental, "fetch", new_callable=AsyncMock, return_value={"pe_ttm": 15.0}):
            count = await engine.compute_for_symbol(mock_db, "000001", "a_share", store_days=5)

        assert count == 5
        # Verify upsert was called (second execute call)
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_compute_batch(self) -> None:
        engine = FeatureEngine()

        async def mock_compute(db: object, sym: str, market: str, lookback: int = 300, store: int | None = None) -> int:
            return 1

        with patch.object(engine, "compute_for_symbol", side_effect=mock_compute):
            results = await engine.compute_batch(
                AsyncMock(),
                [("000001", "a_share"), ("AAPL", "us_stock")],
                store_days=1,
            )

        assert results == {"000001": 1, "AAPL": 1}

    @pytest.mark.asyncio
    async def test_compute_batch_error_handling(self) -> None:
        engine = FeatureEngine()

        async def mock_compute(db: object, sym: str, market: str, lookback: int = 300, store: int | None = None) -> int:
            if sym == "BAD":
                raise RuntimeError("test error")
            return 1

        with patch.object(engine, "compute_for_symbol", side_effect=mock_compute):
            results = await engine.compute_batch(
                AsyncMock(),
                [("GOOD", "a_share"), ("BAD", "us_stock")],
                store_days=1,
            )

        assert results["GOOD"] == 1
        assert results["BAD"] == 0

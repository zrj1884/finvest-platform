"""Technical indicator calculations from OHLCV data.

All functions accept a pandas DataFrame sorted by time (ascending) with
columns: time, open, high, low, close, volume.  They return the same
DataFrame with new indicator columns appended.

No external TA library required — pure pandas/numpy implementation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _sma(series: "pd.Series[float]", period: int) -> "pd.Series[float]":
    """Simple Moving Average."""
    return series.rolling(window=period, min_periods=period).mean()


def _ema(series: "pd.Series[float]", period: int) -> "pd.Series[float]":
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_ma(df: pd.DataFrame) -> pd.DataFrame:
    """Add MA5/10/20/60/120/250 columns."""
    for p in (5, 10, 20, 60, 120, 250):
        df[f"ma{p}"] = _sma(df["close"], p)
    return df


def compute_ema(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA12/26 columns."""
    df["ema12"] = _ema(df["close"], 12)
    df["ema26"] = _ema(df["close"], 26)
    return df


def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD = EMA(fast) - EMA(slow), Signal = EMA(MACD, signal), Hist = MACD - Signal."""
    if "ema12" not in df.columns:
        df = compute_ema(df)
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_signal"] = _ema(df["macd"], signal)
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI (Relative Strength Index) using Wilder's smoothing."""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))
    return df


def compute_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """KDJ indicator.

    RSV = (Close - Low_N) / (High_N - Low_N) * 100
    K = EMA(RSV, m1)  (using 1/m1 smoothing factor)
    D = EMA(K, m2)
    J = 3*K - 2*D
    """
    low_n = df["low"].rolling(window=n, min_periods=n).min()
    high_n = df["high"].rolling(window=n, min_periods=n).max()

    rsv = (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan) * 100.0

    df["kdj_k"] = rsv.ewm(alpha=1.0 / m1, adjust=False).mean()
    df["kdj_d"] = df["kdj_k"].ewm(alpha=1.0 / m2, adjust=False).mean()
    df["kdj_j"] = 3.0 * df["kdj_k"] - 2.0 * df["kdj_d"]
    return df


def compute_bollinger(df: pd.DataFrame, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands: mid = SMA(period), upper/lower = mid ± num_std * std."""
    df["boll_mid"] = _sma(df["close"], period)
    rolling_std = df["close"].rolling(window=period, min_periods=period).std()
    df["boll_upper"] = df["boll_mid"] + num_std * rolling_std
    df["boll_lower"] = df["boll_mid"] - num_std * rolling_std
    return df


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average True Range."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr_14"] = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return df


def compute_obv(df: pd.DataFrame) -> pd.DataFrame:
    """On-Balance Volume."""
    sign = np.sign(df["close"].diff())
    sign.iloc[0] = 0
    df["obv"] = (sign * df["volume"]).cumsum()
    return df


def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all technical indicators on the given OHLCV DataFrame.

    The input DataFrame must have columns: time, open, high, low, close, volume
    and be sorted by time ascending.

    Returns the DataFrame with all indicator columns added.
    """
    if df.empty:
        return df

    df = df.copy()
    df = compute_ma(df)
    df = compute_ema(df)
    df = compute_macd(df)
    df = compute_rsi(df)
    df = compute_kdj(df)
    df = compute_bollinger(df)
    df = compute_atr(df)
    df = compute_obv(df)
    return df

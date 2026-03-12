"""Dataset preparation for stock prediction models.

Converts raw OHLCV + feature data into sliding-window tensors suitable for
time-series forecasting with PyTorch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


# Default feature columns used for model input
DEFAULT_FEATURES = [
    "open", "high", "low", "close", "volume",
    "ma5", "ma10", "ma20", "ma60",
    "ema12", "ema26",
    "macd", "macd_signal", "macd_hist",
    "rsi_14",
    "kdj_k", "kdj_d", "kdj_j",
    "boll_upper", "boll_mid", "boll_lower",
    "atr_14",
]


@dataclass
class DataSplit:
    """Train / validation / test split."""

    X_train: torch.Tensor
    y_train: torch.Tensor
    X_val: torch.Tensor
    y_val: torch.Tensor
    X_test: torch.Tensor
    y_test: torch.Tensor
    feature_names: list[str]
    scaler_mean: Any
    scaler_std: Any


class StockDataset(Dataset):  # type: ignore[type-arg]
    """PyTorch dataset wrapping (X, y) tensors."""

    def __init__(self, X: torch.Tensor, y: torch.Tensor) -> None:
        self.X = X
        self.y = y

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


def prepare_dataset(
    df: pd.DataFrame,
    feature_cols: list[str] | None = None,
    target_col: str = "close",
    seq_len: int = 30,
    pred_len: int = 1,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> DataSplit:
    """Build sliding-window dataset from a DataFrame.

    Args:
        df: DataFrame with time-sorted rows. Must contain feature_cols + target_col.
        feature_cols: Input feature columns. Defaults to DEFAULT_FEATURES.
        target_col: Column to predict (next-day return by default computed from close).
        seq_len: Number of look-back time steps.
        pred_len: Number of future steps to predict.
        train_ratio: Fraction for training.
        val_ratio: Fraction for validation (rest goes to test).

    Returns:
        DataSplit with train/val/test tensors and scaler params.
    """
    if feature_cols is None:
        feature_cols = [c for c in DEFAULT_FEATURES if c in df.columns]

    # Drop rows with NaN in any feature column
    cols_needed = feature_cols + [target_col]
    df = df.dropna(subset=cols_needed).reset_index(drop=True)

    features = df[feature_cols].values.astype(np.float32)
    target = df[target_col].values.astype(np.float32)

    # Compute next-day return as prediction target: (close[t+1] - close[t]) / close[t]
    returns = np.zeros(len(target), dtype=np.float32)
    returns[:-1] = (target[1:] - target[:-1]) / np.where(target[:-1] == 0, 1, target[:-1])

    # Z-score normalisation (fit on training portion only)
    n_train = int(len(features) * train_ratio)
    scaler_mean = features[:n_train].mean(axis=0)
    scaler_std = features[:n_train].std(axis=0)
    scaler_std = np.where(scaler_std == 0, 1, scaler_std)

    features_norm = (features - scaler_mean) / scaler_std

    # Create sliding windows
    X_list: list[Any] = []
    y_list: list[float] = []

    for i in range(len(features_norm) - seq_len - pred_len + 1):
        X_list.append(features_norm[i : i + seq_len])
        # Target: average return over pred_len future days
        y_list.append(float(returns[i + seq_len : i + seq_len + pred_len].mean()))

    X_arr = np.array(X_list, dtype=np.float32)
    y_arr = np.array(y_list, dtype=np.float32)

    # Split
    n_total = len(X_arr)
    n_train_w = int(n_total * train_ratio)
    n_val_w = int(n_total * val_ratio)

    X_train = torch.from_numpy(X_arr[:n_train_w])
    y_train = torch.from_numpy(y_arr[:n_train_w])
    X_val = torch.from_numpy(X_arr[n_train_w : n_train_w + n_val_w])
    y_val = torch.from_numpy(y_arr[n_train_w : n_train_w + n_val_w])
    X_test = torch.from_numpy(X_arr[n_train_w + n_val_w :])
    y_test = torch.from_numpy(y_arr[n_train_w + n_val_w :])

    return DataSplit(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        feature_names=feature_cols,
        scaler_mean=scaler_mean,
        scaler_std=scaler_std,
    )

"""LSTM-based stock prediction model."""

from __future__ import annotations

import torch
import torch.nn as nn


class LSTMPredictor(nn.Module):
    """Multi-layer LSTM for time-series forecasting.

    Input:  (batch, seq_len, n_features)
    Output: (batch, 1) — predicted return
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (batch, seq_len, input_size)

        Returns:
            Predictions of shape (batch, 1).
        """
        # lstm_out: (batch, seq_len, hidden_size)
        lstm_out, _ = self.lstm(x)
        # Take the last time step
        last_hidden = lstm_out[:, -1, :]
        out = self.dropout(last_hidden)
        out = self.fc(out)
        result: torch.Tensor = out
        return result

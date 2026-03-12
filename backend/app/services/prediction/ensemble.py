"""Ensemble predictor combining multiple models."""

from __future__ import annotations

import torch
import torch.nn as nn


class EnsemblePredictor(nn.Module):
    """Weighted average ensemble of multiple prediction models.

    Combines predictions from LSTM and Transformer (or any nn.Module)
    using learnable weights via a softmax-normalised mixing layer.
    """

    def __init__(self, models: list[nn.Module]) -> None:
        super().__init__()
        self.models = nn.ModuleList(models)
        # Learnable weights (one per model)
        self.weights = nn.Parameter(torch.ones(len(models)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass: weighted average of model predictions.

        Args:
            x: (batch, seq_len, input_size)

        Returns:
            Ensemble prediction of shape (batch, 1).
        """
        w = torch.softmax(self.weights, dim=0)
        predictions = torch.stack([m(x) for m in self.models], dim=0)  # (n_models, batch, 1)
        # Weighted sum: (n_models,) @ (n_models, batch, 1) -> (batch, 1)
        weighted = (w.unsqueeze(-1).unsqueeze(-1) * predictions).sum(dim=0)
        return weighted

    def get_weights(self) -> list[float]:
        """Return normalised model weights."""
        w = torch.softmax(self.weights, dim=0)
        return w.detach().cpu().tolist()

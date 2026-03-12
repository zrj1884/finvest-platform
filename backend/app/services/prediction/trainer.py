"""Model training loop with MLflow tracking."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from app.services.prediction.dataset import DataSplit, StockDataset

logger = logging.getLogger(__name__)


@dataclass
class TrainResult:
    """Result of a training run."""

    train_losses: list[float]
    val_losses: list[float]
    best_val_loss: float
    best_epoch: int


class ModelTrainer:
    """Train and evaluate stock prediction models."""

    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 1e-3,
        batch_size: int = 64,
        device: str | None = None,
    ) -> None:
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.batch_size = batch_size
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        self.best_model_state: dict[str, Any] | None = None

    def train(
        self,
        data: DataSplit,
        epochs: int = 50,
        patience: int = 10,
        mlflow_run: bool = False,
    ) -> TrainResult:
        """Train the model with early stopping.

        Args:
            data: DataSplit with train/val/test tensors.
            epochs: Maximum number of training epochs.
            patience: Early stopping patience (epochs without improvement).
            mlflow_run: Whether to log to MLflow.

        Returns:
            TrainResult with loss history.
        """
        train_ds = StockDataset(data.X_train, data.y_train)
        val_ds = StockDataset(data.X_val, data.y_val)

        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        train_losses: list[float] = []
        val_losses: list[float] = []
        best_val_loss = float("inf")
        best_epoch = 0
        patience_counter = 0

        # Optional MLflow logging
        mlflow_client: Any = None
        if mlflow_run:
            try:
                import mlflow

                mlflow_client = mlflow
                mlflow.start_run()
                mlflow.log_params({
                    "model_type": self.model.__class__.__name__,
                    "learning_rate": self.optimizer.defaults["lr"],
                    "batch_size": self.batch_size,
                    "epochs": epochs,
                    "seq_len": data.X_train.shape[1],
                    "n_features": data.X_train.shape[2],
                    "train_size": len(data.X_train),
                    "val_size": len(data.X_val),
                    "test_size": len(data.X_test),
                })
            except ImportError:
                logger.warning("MLflow not available, skipping logging")

        try:
            for epoch in range(epochs):
                # Train
                train_loss = self._train_epoch(train_loader)
                train_losses.append(train_loss)

                # Validate
                val_loss = self._eval(val_loader)
                val_losses.append(val_loss)

                logger.info("Epoch %d/%d — train_loss: %.6f, val_loss: %.6f", epoch + 1, epochs, train_loss, val_loss)

                if mlflow_client:
                    mlflow_client.log_metrics({"train_loss": train_loss, "val_loss": val_loss}, step=epoch)

                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_epoch = epoch
                    patience_counter = 0
                    self.best_model_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info("Early stopping at epoch %d", epoch + 1)
                        break

            # Restore best model
            if self.best_model_state:
                self.model.load_state_dict(self.best_model_state)
                self.model.to(self.device)

        finally:
            if mlflow_client:
                try:
                    mlflow_client.log_metric("best_val_loss", best_val_loss)
                    mlflow_client.log_metric("best_epoch", best_epoch)
                    mlflow_client.end_run()
                except Exception:
                    pass

        return TrainResult(
            train_losses=train_losses,
            val_losses=val_losses,
            best_val_loss=best_val_loss,
            best_epoch=best_epoch,
        )

    def _train_epoch(self, loader: DataLoader) -> float:  # type: ignore[type-arg]
        """Run one training epoch."""
        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for X_batch, y_batch in loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device).unsqueeze(-1)

            self.optimizer.zero_grad()
            pred = self.model(X_batch)
            loss = self.criterion(pred, y_batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        return total_loss / max(n_batches, 1)

    def _eval(self, loader: DataLoader) -> float:  # type: ignore[type-arg]
        """Evaluate on a dataset, return average loss."""
        self.model.eval()
        total_loss = 0.0
        n_batches = 0

        with torch.no_grad():
            for X_batch, y_batch in loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device).unsqueeze(-1)

                pred = self.model(X_batch)
                loss = self.criterion(pred, y_batch)
                total_loss += loss.item()
                n_batches += 1

        return total_loss / max(n_batches, 1)

    def predict(self, X: torch.Tensor) -> torch.Tensor:
        """Generate predictions for input tensor.

        Args:
            X: (n_samples, seq_len, n_features)

        Returns:
            Predictions tensor of shape (n_samples, 1).
        """
        self.model.eval()
        with torch.no_grad():
            X = X.to(self.device)
            result: torch.Tensor = self.model(X).cpu()
            return result

    def save_model(self, path: str | Path) -> None:
        """Save model state dict to disk."""
        torch.save(self.model.state_dict(), path)
        logger.info("Model saved to %s", path)

    def load_model(self, path: str | Path) -> None:
        """Load model state dict from disk."""
        state = torch.load(path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state)
        logger.info("Model loaded from %s", path)

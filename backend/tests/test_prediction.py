"""Tests for stock prediction models and backtesting framework."""

import numpy as np
import pandas as pd
import torch

from app.services.prediction.dataset import StockDataset, prepare_dataset, DEFAULT_FEATURES
from app.services.prediction.lstm_model import LSTMPredictor
from app.services.prediction.transformer_model import TransformerPredictor
from app.services.prediction.ensemble import EnsemblePredictor
from app.services.prediction.trainer import ModelTrainer, TrainResult
from app.services.prediction.backtest import Backtester, BacktestResult, _compute_max_drawdown


def _make_featured_df(n: int = 300) -> pd.DataFrame:
    """Generate synthetic DataFrame with OHLCV + feature columns."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_ = close + np.random.randn(n) * 0.5
    volume = np.random.randint(1_000_000, 10_000_000, size=n).astype(float)

    df = pd.DataFrame({
        "time": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })

    # Add synthetic feature columns
    for col in DEFAULT_FEATURES:
        if col not in df.columns:
            df[col] = np.random.randn(n) * 10 + 50

    return df


# ===== Dataset =====

class TestStockDataset:
    def test_len(self) -> None:
        X = torch.randn(100, 30, 10)
        y = torch.randn(100)
        ds = StockDataset(X, y)
        assert len(ds) == 100

    def test_getitem(self) -> None:
        X = torch.randn(10, 5, 3)
        y = torch.randn(10)
        ds = StockDataset(X, y)
        xi, yi = ds[0]
        assert xi.shape == (5, 3)
        assert yi.shape == ()


class TestPrepareDataset:
    def test_shapes(self) -> None:
        df = _make_featured_df(200)
        split = prepare_dataset(df, seq_len=20, pred_len=1)
        assert split.X_train.ndim == 3
        assert split.y_train.ndim == 1
        assert split.X_train.shape[1] == 20  # seq_len
        assert split.X_train.shape[2] == len(split.feature_names)

    def test_split_ratios(self) -> None:
        df = _make_featured_df(200)
        split = prepare_dataset(df, seq_len=10, train_ratio=0.7, val_ratio=0.15)
        total = len(split.X_train) + len(split.X_val) + len(split.X_test)
        assert len(split.X_train) > len(split.X_val)
        assert len(split.X_val) > 0
        assert len(split.X_test) > 0
        assert total > 0

    def test_scaler_params(self) -> None:
        df = _make_featured_df(100)
        split = prepare_dataset(df, seq_len=10)
        assert split.scaler_mean.shape[0] == len(split.feature_names)
        assert split.scaler_std.shape[0] == len(split.feature_names)
        assert (split.scaler_std > 0).all()

    def test_custom_features(self) -> None:
        df = _make_featured_df(100)
        split = prepare_dataset(df, feature_cols=["open", "close", "volume"], seq_len=10)
        assert split.X_train.shape[2] == 3
        assert split.feature_names == ["open", "close", "volume"]


# ===== LSTM Model =====

class TestLSTMPredictor:
    def test_output_shape(self) -> None:
        model = LSTMPredictor(input_size=10, hidden_size=32, num_layers=2)
        x = torch.randn(8, 30, 10)  # batch=8, seq=30, features=10
        out = model(x)
        assert out.shape == (8, 1)

    def test_single_layer(self) -> None:
        model = LSTMPredictor(input_size=5, hidden_size=16, num_layers=1)
        x = torch.randn(4, 10, 5)
        out = model(x)
        assert out.shape == (4, 1)

    def test_gradient_flow(self) -> None:
        model = LSTMPredictor(input_size=5, hidden_size=16, num_layers=1)
        x = torch.randn(4, 10, 5)
        out = model(x)
        loss = out.sum()
        loss.backward()
        # Check that gradients exist
        for param in model.parameters():
            if param.requires_grad:
                assert param.grad is not None


# ===== Transformer Model =====

class TestTransformerPredictor:
    def test_output_shape(self) -> None:
        model = TransformerPredictor(input_size=10, d_model=32, nhead=4, num_layers=2)
        x = torch.randn(8, 30, 10)
        out = model(x)
        assert out.shape == (8, 1)

    def test_different_seq_len(self) -> None:
        model = TransformerPredictor(input_size=10, d_model=16, nhead=2)
        for seq_len in [5, 20, 50]:
            x = torch.randn(4, seq_len, 10)
            out = model(x)
            assert out.shape == (4, 1)

    def test_gradient_flow(self) -> None:
        model = TransformerPredictor(input_size=5, d_model=16, nhead=2, num_layers=1)
        x = torch.randn(4, 10, 5)
        out = model(x)
        loss = out.sum()
        loss.backward()
        for param in model.parameters():
            if param.requires_grad:
                assert param.grad is not None


# ===== Ensemble =====

class TestEnsemblePredictor:
    def test_output_shape(self) -> None:
        m1 = LSTMPredictor(input_size=10, hidden_size=16, num_layers=1)
        m2 = TransformerPredictor(input_size=10, d_model=16, nhead=2, num_layers=1)
        ensemble = EnsemblePredictor([m1, m2])
        x = torch.randn(4, 20, 10)
        out = ensemble(x)
        assert out.shape == (4, 1)

    def test_weights_sum_to_one(self) -> None:
        m1 = LSTMPredictor(input_size=5, hidden_size=8, num_layers=1)
        m2 = TransformerPredictor(input_size=5, d_model=8, nhead=2, num_layers=1)
        ensemble = EnsemblePredictor([m1, m2])
        weights = ensemble.get_weights()
        assert abs(sum(weights) - 1.0) < 1e-5

    def test_gradient_flow(self) -> None:
        m1 = LSTMPredictor(input_size=5, hidden_size=8, num_layers=1)
        m2 = TransformerPredictor(input_size=5, d_model=8, nhead=2, num_layers=1)
        ensemble = EnsemblePredictor([m1, m2])
        x = torch.randn(4, 10, 5)
        out = ensemble(x)
        loss = out.sum()
        loss.backward()
        assert ensemble.weights.grad is not None


# ===== Trainer =====

class TestModelTrainer:
    def test_train_basic(self) -> None:
        df = _make_featured_df(200)
        data = prepare_dataset(df, feature_cols=["open", "close", "volume"], seq_len=10)
        model = LSTMPredictor(input_size=3, hidden_size=16, num_layers=1)
        trainer = ModelTrainer(model, learning_rate=1e-3, batch_size=32, device="cpu")

        result = trainer.train(data, epochs=3, patience=10)
        assert isinstance(result, TrainResult)
        assert len(result.train_losses) == 3
        assert len(result.val_losses) == 3
        assert result.best_val_loss >= 0

    def test_predict(self) -> None:
        model = LSTMPredictor(input_size=3, hidden_size=8, num_layers=1)
        trainer = ModelTrainer(model, device="cpu")
        X = torch.randn(10, 5, 3)
        preds = trainer.predict(X)
        assert preds.shape == (10, 1)

    def test_save_load(self, tmp_path: object) -> None:
        import pathlib
        path = pathlib.Path(str(tmp_path)) / "model.pt"
        model = LSTMPredictor(input_size=3, hidden_size=8, num_layers=1)
        trainer = ModelTrainer(model, device="cpu")

        # Get initial prediction
        X = torch.randn(2, 5, 3)
        pred_before = trainer.predict(X)

        trainer.save_model(path)

        # Create new model, load weights
        model2 = LSTMPredictor(input_size=3, hidden_size=8, num_layers=1)
        trainer2 = ModelTrainer(model2, device="cpu")
        trainer2.load_model(path)
        pred_after = trainer2.predict(X)

        torch.testing.assert_close(pred_before, pred_after)


# ===== Backtest =====

class TestBacktester:
    def test_all_positive_predictions(self) -> None:
        preds = np.ones(100) * 0.01  # always predict positive
        actuals = np.random.randn(100) * 0.02  # random returns
        bt = Backtester(threshold=0.0, commission=0.001)
        result = bt.run(preds, actuals)
        assert isinstance(result, BacktestResult)
        assert result.total_trades == 100
        assert len(result.equity_curve) == 101

    def test_no_trades(self) -> None:
        preds = np.ones(50) * -0.01  # always predict negative
        actuals = np.random.randn(50) * 0.02
        bt = Backtester(threshold=0.0)
        result = bt.run(preds, actuals)
        assert result.total_trades == 0
        assert result.total_return == 0.0
        assert result.win_rate == 0.0

    def test_perfect_prediction(self) -> None:
        actuals = np.array([0.05, 0.03, -0.02, 0.01, -0.04])
        preds = actuals.copy()  # perfect foresight
        bt = Backtester(threshold=0.0, commission=0.0)
        result = bt.run(preds, actuals)
        assert result.total_trades == 3  # only positive predictions
        assert result.win_rate == 1.0
        assert result.total_return > 0

    def test_tensor_input(self) -> None:
        preds = torch.randn(30)
        actuals = torch.randn(30) * 0.02
        bt = Backtester()
        result = bt.run(preds, actuals)
        assert isinstance(result, BacktestResult)

    def test_summary(self) -> None:
        preds = np.ones(50) * 0.01
        actuals = np.ones(50) * 0.01
        bt = Backtester(commission=0.0)
        result = bt.run(preds, actuals)
        summary = result.summary()
        assert "total_return_pct" in summary
        assert "sharpe_ratio" in summary
        assert "max_drawdown_pct" in summary

    def test_max_drawdown(self) -> None:
        curve = [1.0, 1.1, 1.2, 0.9, 1.0, 0.8]
        dd = _compute_max_drawdown(curve)
        # Max drawdown: from 1.2 to 0.8 = 33.3%
        assert abs(dd - (1.2 - 0.8) / 1.2) < 1e-10

    def test_sharpe_ratio_sign(self) -> None:
        # Mostly positive returns with some variance should give positive Sharpe
        np.random.seed(42)
        preds = np.ones(252) * 0.01
        actuals = np.random.normal(0.005, 0.01, 252)  # positive mean, some variance
        bt = Backtester(commission=0.0, risk_free_rate=0.0)
        result = bt.run(preds, actuals)
        assert result.sharpe_ratio > 0

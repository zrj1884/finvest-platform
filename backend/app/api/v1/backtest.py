"""Backtesting API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


class BacktestRequest(BaseModel):
    symbol: str
    market: str
    model_type: str = "lstm"  # lstm / transformer / ensemble
    seq_len: int = 30
    train_epochs: int = 20
    lookback_days: int = 500


class BacktestResponse(BaseModel):
    symbol: str
    market: str
    model_type: str
    total_return_pct: float
    annualised_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    equity_curve: list[float]
    train_loss: float
    val_loss: float


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    req: BacktestRequest,
    db: AsyncSession = Depends(get_db),
) -> BacktestResponse:
    """Run a prediction model backtest on historical data."""
    import pandas as pd
    from sqlalchemy import text

    from app.services.feature_engine.technical import compute_technical_indicators
    from app.services.prediction.backtest import Backtester
    from app.services.prediction.dataset import prepare_dataset
    from app.services.prediction.ensemble import EnsemblePredictor
    from app.services.prediction.lstm_model import LSTMPredictor
    from app.services.prediction.trainer import ModelTrainer
    from app.services.prediction.transformer_model import TransformerPredictor

    # 1. Load OHLCV data
    query = text("""
        SELECT time, open, high, low, close, volume
        FROM stock_daily
        WHERE symbol = :symbol AND market = :market
          AND time >= NOW() - make_interval(days => :days)
        ORDER BY time ASC
    """)
    result = await db.execute(query, {
        "symbol": req.symbol, "market": req.market, "days": req.lookback_days,
    })
    rows = result.fetchall()

    if len(rows) < 100:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data: {len(rows)} rows (need at least 100)",
        )

    df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(int)

    # 2. Compute technical indicators
    df = compute_technical_indicators(df)

    # 3. Prepare dataset
    feature_cols = ["open", "close", "volume", "ma5", "ma10", "ma20", "rsi_14", "macd", "macd_signal"]
    feature_cols = [c for c in feature_cols if c in df.columns]
    data = prepare_dataset(df, feature_cols=feature_cols, seq_len=req.seq_len)

    n_features = data.X_train.shape[2]

    # 4. Create model
    import torch.nn as nn

    model: nn.Module
    if req.model_type == "lstm":
        model = LSTMPredictor(input_size=n_features, hidden_size=64, num_layers=2)
    elif req.model_type == "transformer":
        model = TransformerPredictor(input_size=n_features, d_model=32, nhead=4, num_layers=2)
    elif req.model_type == "ensemble":
        m1 = LSTMPredictor(input_size=n_features, hidden_size=64, num_layers=2)
        m2 = TransformerPredictor(input_size=n_features, d_model=32, nhead=4, num_layers=2)
        model = EnsemblePredictor([m1, m2])
    else:
        raise HTTPException(status_code=400, detail=f"Unknown model type: {req.model_type}")

    # 5. Train
    trainer = ModelTrainer(model, learning_rate=1e-3, batch_size=32, device="cpu")
    train_result = trainer.train(data, epochs=req.train_epochs, patience=10)

    # 6. Predict on test set
    predictions = trainer.predict(data.X_test)

    # 7. Backtest
    backtester = Backtester(threshold=0.0, commission=0.001)
    bt_result = backtester.run(predictions, data.y_test)
    summary = bt_result.summary()

    # Downsample equity curve to max 200 points
    curve = bt_result.equity_curve
    if len(curve) > 200:
        step = len(curve) // 200
        curve = curve[::step]

    return BacktestResponse(
        symbol=req.symbol,
        market=req.market,
        model_type=req.model_type,
        total_return_pct=summary["total_return_pct"],
        annualised_return_pct=summary["annualised_return_pct"],
        sharpe_ratio=summary["sharpe_ratio"],
        max_drawdown_pct=summary["max_drawdown_pct"],
        win_rate_pct=summary["win_rate_pct"],
        total_trades=int(summary["total_trades"]),
        equity_curve=curve,
        train_loss=train_result.train_losses[-1] if train_result.train_losses else 0.0,
        val_loss=train_result.best_val_loss,
    )

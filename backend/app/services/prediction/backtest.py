"""Backtesting framework for stock prediction strategies.

Evaluates prediction model performance with financial metrics:
annualised return, Sharpe ratio, max drawdown, win rate, etc.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest performance metrics."""

    total_return: float  # cumulative return %
    annualised_return: float  # %
    sharpe_ratio: float
    max_drawdown: float  # %
    win_rate: float  # % of positive-return trades
    total_trades: int
    avg_return_per_trade: float  # %
    equity_curve: list[float] = field(default_factory=list)  # daily portfolio values

    def summary(self) -> dict[str, float]:
        """Return a summary dict for logging / MLflow."""
        return {
            "total_return_pct": round(self.total_return * 100, 2),
            "annualised_return_pct": round(self.annualised_return * 100, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "max_drawdown_pct": round(self.max_drawdown * 100, 2),
            "win_rate_pct": round(self.win_rate * 100, 2),
            "total_trades": self.total_trades,
            "avg_return_per_trade_pct": round(self.avg_return_per_trade * 100, 4),
        }


class Backtester:
    """Simple long-only backtester driven by model predictions.

    Strategy: If predicted return > threshold, go long.
    Hold for 1 day, then re-evaluate.
    """

    def __init__(
        self,
        threshold: float = 0.0,
        commission: float = 0.001,
        risk_free_rate: float = 0.03,
        trading_days_per_year: int = 252,
    ) -> None:
        self.threshold = threshold
        self.commission = commission
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year

    def run(
        self,
        predictions: "torch.Tensor | np.ndarray[Any, Any]",
        actual_returns: "torch.Tensor | np.ndarray[Any, Any]",
    ) -> BacktestResult:
        """Run backtest simulation.

        Args:
            predictions: Model predicted returns, shape (n_days,) or (n_days, 1).
            actual_returns: Actual next-day returns, shape (n_days,) or (n_days, 1).

        Returns:
            BacktestResult with performance metrics.
        """
        if isinstance(predictions, torch.Tensor):
            predictions = predictions.detach().cpu().numpy()
        if isinstance(actual_returns, torch.Tensor):
            actual_returns = actual_returns.detach().cpu().numpy()

        preds = predictions.flatten().astype(np.float64)
        actuals = actual_returns.flatten().astype(np.float64)

        n_days = min(len(preds), len(actuals))
        preds = preds[:n_days]
        actuals = actuals[:n_days]

        # Simulate
        equity = 1.0
        equity_curve = [equity]
        daily_returns: list[float] = []
        trades = 0
        winning_trades = 0

        for i in range(n_days):
            if preds[i] > self.threshold:
                # Go long
                ret = actuals[i] - 2 * self.commission  # entry + exit commission
                equity *= (1.0 + ret)
                daily_returns.append(ret)
                trades += 1
                if ret > 0:
                    winning_trades += 1
            else:
                # Stay in cash
                daily_returns.append(0.0)

            equity_curve.append(equity)

        # Metrics
        total_return = equity - 1.0

        daily_ret_arr = np.array(daily_returns)
        n_years = n_days / self.trading_days_per_year
        annualised_return = (1.0 + total_return) ** (1.0 / max(n_years, 0.01)) - 1.0 if total_return > -1 else -1.0

        # Sharpe ratio (annualised)
        daily_rf = self.risk_free_rate / self.trading_days_per_year
        excess_returns = daily_ret_arr - daily_rf
        if len(excess_returns) > 1 and np.std(excess_returns) > 0:
            sharpe_ratio = float(
                np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(self.trading_days_per_year)
            )
        else:
            sharpe_ratio = 0.0

        # Max drawdown
        max_drawdown = _compute_max_drawdown(equity_curve)

        # Win rate
        win_rate = winning_trades / max(trades, 1)
        avg_ret = float(np.mean([r for r in daily_returns if r != 0.0])) if trades > 0 else 0.0

        return BacktestResult(
            total_return=total_return,
            annualised_return=annualised_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=trades,
            avg_return_per_trade=avg_ret,
            equity_curve=equity_curve,
        )


def _compute_max_drawdown(equity_curve: list[float]) -> float:
    """Compute maximum drawdown from an equity curve."""
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd

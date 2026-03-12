"""Abstract trading gateway interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.order import Order


class TradingGateway(ABC):
    """Base class for trading execution gateways.

    Concrete implementations:
      - SimulatedGateway: in-process matching engine for paper trading
      - AlpacaGateway: real US-stock execution via Alpaca API (future)
    """

    @abstractmethod
    async def submit_order(self, db: AsyncSession, order: Order, account: Account) -> Order:
        """Submit an order for execution.

        For sim: attempt immediate fill.
        For real: forward to broker and update status to SUBMITTED.
        """
        ...

    @abstractmethod
    async def cancel_order(self, db: AsyncSession, order: Order) -> Order:
        """Request cancellation of an open order."""
        ...


def get_gateway(*, is_simulated: bool, broker: str | None = None) -> TradingGateway:
    """Factory: return the appropriate gateway for an account."""
    if is_simulated:
        from app.services.trading.sim_gateway import SimulatedGateway

        return SimulatedGateway()

    if broker == "alpaca":
        raise NotImplementedError("Alpaca gateway not yet implemented")

    raise ValueError(f"No gateway available for broker: {broker}")

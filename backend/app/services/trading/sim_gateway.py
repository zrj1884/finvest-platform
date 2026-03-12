"""Simulated trading gateway — paper trading with in-process matching."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.order import Order, OrderStatus
from app.services.trading.gateway import TradingGateway
from app.services.trading.matching_engine import try_fill
from app.services.trading.order_state import validate_transition

from app.crud import order as order_crud


class SimulatedGateway(TradingGateway):
    """Paper trading gateway using the simulated matching engine."""

    async def submit_order(self, db: AsyncSession, order: Order, account: Account) -> Order:
        """Submit order to the simulated matching engine."""
        return await try_fill(db, order, account)

    async def cancel_order(self, db: AsyncSession, order: Order) -> Order:
        """Cancel a pending or submitted order."""
        validate_transition(order.status, OrderStatus.CANCELLED)
        from datetime import datetime, timezone

        return await order_crud.update(
            db,
            order,
            status=OrderStatus.CANCELLED,
            cancelled_at=datetime.now(tz=timezone.utc),
        )

"""Order CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus


async def get_by_id(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    return await db.get(Order, order_id)


async def list_by_account(
    db: AsyncSession,
    account_id: uuid.UUID,
    *,
    status: OrderStatus | None = None,
    symbol: str | None = None,
    limit: int = 100,
) -> list[Order]:
    stmt = select(Order).where(Order.account_id == account_id)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    if symbol is not None:
        stmt = stmt.where(Order.symbol == symbol)
    stmt = stmt.order_by(Order.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, **kwargs: Any) -> Order:
    order = Order(**kwargs)
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def update(db: AsyncSession, order: Order, **kwargs: Any) -> Order:
    for key, value in kwargs.items():
        setattr(order, key, value)
    await db.flush()
    await db.refresh(order)
    return order

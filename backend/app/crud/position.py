"""Position CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position


async def get_by_id(db: AsyncSession, position_id: uuid.UUID) -> Position | None:
    return await db.get(Position, position_id)


async def get_by_symbol(
    db: AsyncSession, account_id: uuid.UUID, symbol: str
) -> Position | None:
    result = await db.execute(
        select(Position).where(
            Position.account_id == account_id, Position.symbol == symbol
        )
    )
    return result.scalar_one_or_none()


async def list_by_account(db: AsyncSession, account_id: uuid.UUID) -> list[Position]:
    result = await db.execute(
        select(Position)
        .where(Position.account_id == account_id)
        .order_by(Position.symbol)
    )
    return list(result.scalars().all())


async def get_or_create(
    db: AsyncSession, account_id: uuid.UUID, symbol: str, **defaults: Any
) -> tuple[Position, bool]:
    """Get existing position or create a new one. Returns (position, created)."""
    pos = await get_by_symbol(db, account_id, symbol)
    if pos is not None:
        return pos, False
    pos = Position(account_id=account_id, symbol=symbol, **defaults)
    db.add(pos)
    await db.flush()
    await db.refresh(pos)
    return pos, True


async def update(db: AsyncSession, position: Position, **kwargs: Any) -> Position:
    for key, value in kwargs.items():
        setattr(position, key, value)
    await db.flush()
    await db.refresh(position)
    return position

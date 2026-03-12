"""Account CRUD operations."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


async def get_by_id(db: AsyncSession, account_id: uuid.UUID) -> Account | None:
    return await db.get(Account, account_id)


async def list_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[Account]:
    result = await db.execute(
        select(Account).where(Account.user_id == user_id).order_by(Account.created_at.desc())
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, **kwargs: Any) -> Account:
    account = Account(**kwargs)
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


async def update_balance(db: AsyncSession, account: Account, delta: Decimal) -> Account:
    """Adjust account balance by delta (positive = credit, negative = debit)."""
    account.balance = Decimal(str(account.balance)) + delta
    await db.flush()
    await db.refresh(account)
    return account


async def reset(db: AsyncSession, account: Account, balance: Decimal) -> Account:
    """Reset a simulated account: clear positions/orders, restore balance."""
    # Positions and orders are cascade-deleted via relationship
    from app.models.order import Order
    from app.models.position import Position

    await db.execute(
        select(Position).where(Position.account_id == account.id).execution_options(synchronize_session="fetch")
    )
    for pos in list(account.positions):
        await db.delete(pos)
    for order in list(account.orders):
        await db.delete(order)

    account.balance = balance
    await db.flush()
    await db.refresh(account)
    return account

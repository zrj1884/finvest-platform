"""Portfolio / position management — update positions and account balance on fills."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import account as account_crud
from app.crud import position as position_crud
from app.models.account import Account
from app.models.order import Order, OrderSide
from app.models.position import Position


async def apply_fill(
    db: AsyncSession,
    account: Account,
    order: Order,
    fill_quantity: int,
    fill_price: Decimal,
    commission: Decimal,
) -> Position:
    """Update position and account balance after an order fill.

    Args:
        db: Database session.
        account: The trading account.
        order: The filled (or partially filled) order.
        fill_quantity: Number of shares filled in this event.
        fill_price: Execution price per share.
        commission: Commission charged for this fill.

    Returns:
        The updated Position object.
    """
    pos, _created = await position_crud.get_or_create(
        db, account.id, order.symbol, name=order.name
    )

    qty = Decimal(str(pos.quantity))
    avg = Decimal(str(pos.avg_cost))
    fill_qty = Decimal(str(fill_quantity))
    realized = Decimal(str(pos.realized_pnl))

    if order.side == OrderSide.BUY:
        # Weighted average cost
        total_cost = avg * qty + fill_price * fill_qty
        new_qty = qty + fill_qty
        new_avg = total_cost / new_qty if new_qty > 0 else Decimal("0")

        await position_crud.update(
            db,
            pos,
            quantity=int(new_qty),
            available_quantity=pos.available_quantity + fill_quantity,
            avg_cost=float(new_avg.quantize(Decimal("0.0001"))),
            current_price=float(fill_price),
            market_value=float((new_qty * fill_price).quantize(Decimal("0.0001"))),
            unrealized_pnl=float(
                ((fill_price - new_avg) * new_qty).quantize(Decimal("0.0001"))
            ),
        )

        # Debit account: cost + commission
        cost = fill_price * fill_qty + commission
        await account_crud.update_balance(db, account, -cost)

    else:  # SELL
        pnl = (fill_price - avg) * fill_qty
        new_qty = qty - fill_qty
        new_realized = realized + pnl

        update_kwargs: dict[str, object] = {
            "quantity": int(new_qty),
            "available_quantity": pos.available_quantity - fill_quantity,
            "current_price": float(fill_price),
            "realized_pnl": float(new_realized.quantize(Decimal("0.0001"))),
        }

        if new_qty > 0:
            update_kwargs["market_value"] = float(
                (new_qty * fill_price).quantize(Decimal("0.0001"))
            )
            update_kwargs["unrealized_pnl"] = float(
                ((fill_price - avg) * new_qty).quantize(Decimal("0.0001"))
            )
        else:
            # Position closed
            update_kwargs["market_value"] = 0
            update_kwargs["unrealized_pnl"] = 0
            update_kwargs["avg_cost"] = 0

        await position_crud.update(db, pos, **update_kwargs)

        # Credit account: proceeds - commission
        proceeds = fill_price * fill_qty - commission
        await account_crud.update_balance(db, account, proceeds)

    return pos

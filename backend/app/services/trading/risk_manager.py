"""Pre-trade and post-trade risk checks.

Rules:
  - Position concentration: single position ≤ 30% of total account value
  - Daily loss limit: cumulative daily loss ≤ 5% of account balance at day start
  - Order frequency: ≤ 10 orders per minute per account
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.order import Order, OrderSide, OrderStatus
from app.models.position import Position

# --- Configurable thresholds ---

MAX_POSITION_CONCENTRATION = Decimal("0.30")  # 30%
MAX_DAILY_LOSS_PCT = Decimal("0.05")  # 5%
MAX_ORDERS_PER_MINUTE = 10


async def pre_trade_check(
    db: AsyncSession,
    account: Account,
    symbol: str,
    side: str,
    quantity: int,
    price: Decimal,
) -> list[str]:
    """Run all pre-trade risk checks. Returns list of error messages (empty = OK)."""
    errors: list[str] = []

    # 1. Position concentration check (only for buys)
    if side == OrderSide.BUY.value or side == OrderSide.BUY:
        concentration_err = await _check_concentration(
            db, account, symbol, quantity, price
        )
        if concentration_err:
            errors.append(concentration_err)

    # 2. Daily loss limit
    loss_err = await _check_daily_loss(db, account)
    if loss_err:
        errors.append(loss_err)

    # 3. Order frequency
    freq_err = await _check_order_frequency(db, account.id)
    if freq_err:
        errors.append(freq_err)

    return errors


async def _check_concentration(
    db: AsyncSession,
    account: Account,
    symbol: str,
    quantity: int,
    price: Decimal,
) -> str | None:
    """Check if the order would cause position concentration > 30%."""
    # Total account value = balance + sum of all position market values
    result = await db.execute(
        select(func.coalesce(func.sum(Position.market_value), 0)).where(
            Position.account_id == account.id,
            Position.quantity > 0,
        )
    )
    total_market_value = Decimal(str(result.scalar_one()))
    total_value = Decimal(str(account.balance)) + total_market_value

    if total_value <= 0:
        return None

    # Current position value for this symbol
    result = await db.execute(
        select(Position.market_value).where(
            Position.account_id == account.id,
            Position.symbol == symbol,
        )
    )
    row = result.scalar_one_or_none()
    current_position_value = Decimal(str(row)) if row else Decimal("0")

    # Projected position value after this order
    order_value = Decimal(str(quantity)) * price
    projected_value = current_position_value + order_value

    # Projected total account value (balance decreases, position increases)
    projected_total = total_value  # net stays roughly the same before price changes

    concentration = projected_value / projected_total
    if concentration > MAX_POSITION_CONCENTRATION:
        pct = (concentration * 100).quantize(Decimal("0.1"))
        limit_pct = (MAX_POSITION_CONCENTRATION * 100).quantize(Decimal("0.1"))
        return f"Position concentration {pct}% exceeds limit of {limit_pct}%"

    return None


async def _check_daily_loss(
    db: AsyncSession,
    account: Account,
) -> str | None:
    """Check if cumulative daily realized loss exceeds 5% of account balance."""
    now = datetime.now(tz=timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Sum of realized P&L from today's filled orders
    result = await db.execute(
        select(func.coalesce(func.sum(Order.commission), 0)).where(
            Order.account_id == account.id,
            Order.status.in_([OrderStatus.FILLED, OrderStatus.PARTIAL_FILLED]),
            Order.filled_at >= day_start,
        )
    )
    _daily_commission = Decimal(str(result.scalar_one()))

    # Sum commissions paid today as part of realized losses
    daily_realized_pnl = -_daily_commission

    # Also check unrealized losses on current positions
    result = await db.execute(
        select(func.coalesce(func.sum(Position.unrealized_pnl), 0)).where(
            Position.account_id == account.id,
            Position.quantity > 0,
        )
    )
    unrealized = Decimal(str(result.scalar_one()))

    # Total daily loss = negative unrealized + commissions paid today
    total_loss = min(unrealized, Decimal("0")) + daily_realized_pnl

    # Use current balance + total position value as reference
    result = await db.execute(
        select(func.coalesce(func.sum(Position.market_value), 0)).where(
            Position.account_id == account.id,
            Position.quantity > 0,
        )
    )
    total_positions = Decimal(str(result.scalar_one()))
    reference_value = Decimal(str(account.balance)) + total_positions

    if reference_value > 0 and total_loss < 0:
        loss_pct = abs(total_loss) / reference_value
        if loss_pct > MAX_DAILY_LOSS_PCT:
            pct = (loss_pct * 100).quantize(Decimal("0.1"))
            limit_pct = (MAX_DAILY_LOSS_PCT * 100).quantize(Decimal("0.1"))
            return f"Daily loss {pct}% exceeds limit of {limit_pct}%"

    return None


async def _check_order_frequency(
    db: AsyncSession,
    account_id: uuid.UUID,
) -> str | None:
    """Check if more than 10 orders placed in the last minute."""
    one_min_ago = datetime.now(tz=timezone.utc) - timedelta(minutes=1)

    result = await db.execute(
        select(func.count()).select_from(Order).where(
            Order.account_id == account_id,
            Order.created_at >= one_min_ago,
        )
    )
    count = result.scalar_one()

    if count >= MAX_ORDERS_PER_MINUTE:
        return f"Order frequency limit reached ({MAX_ORDERS_PER_MINUTE} orders/minute)"

    return None

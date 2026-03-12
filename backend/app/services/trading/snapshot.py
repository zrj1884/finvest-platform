"""Portfolio snapshot service — records daily portfolio values for performance curves."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.schemas.portfolio import PerformancePoint


async def record_snapshot(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Record a portfolio snapshot for the given user (call daily via scheduler)."""
    from sqlalchemy import select

    result = await db.execute(
        select(Account).where(Account.user_id == user_id)
    )
    accounts = list(result.scalars().all())

    total_balance = Decimal("0")
    total_market_value = Decimal("0")
    total_unrealized = Decimal("0")
    total_realized = Decimal("0")

    for acct in accounts:
        total_balance += Decimal(str(acct.balance))
        for pos in acct.positions:
            if pos.quantity > 0:
                total_market_value += Decimal(str(pos.market_value))
                total_unrealized += Decimal(str(pos.unrealized_pnl))
                total_realized += Decimal(str(pos.realized_pnl))

    total_value = total_balance + total_market_value
    now = datetime.now(tz=timezone.utc)

    await db.execute(
        text(
            "INSERT INTO portfolio_snapshots "
            "(time, user_id, total_value, total_balance, total_market_value, "
            " unrealized_pnl, realized_pnl) "
            "VALUES (:time, :user_id, :total_value, :total_balance, "
            " :total_market_value, :unrealized_pnl, :realized_pnl)"
        ),
        {
            "time": now,
            "user_id": user_id,
            "total_value": float(total_value),
            "total_balance": float(total_balance),
            "total_market_value": float(total_market_value),
            "unrealized_pnl": float(total_unrealized),
            "realized_pnl": float(total_realized),
        },
    )
    await db.flush()


async def get_performance_curve(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 90,
) -> list[PerformancePoint]:
    """Get daily portfolio value history for performance curve.

    Uses portfolio_snapshots table. If no snapshots exist, returns
    a single point with current portfolio value.
    """
    result = await db.execute(
        text(
            "SELECT time_bucket('1 day', time) AS day, "
            "  last(total_value, time) AS total_value "
            "FROM portfolio_snapshots "
            "WHERE user_id = :user_id "
            "  AND time >= NOW() - make_interval(days => :days) "
            "GROUP BY day "
            "ORDER BY day"
        ),
        {"user_id": user_id, "days": days},
    )
    rows = result.all()

    if not rows:
        # Fallback: calculate current value as single data point
        from app.services.trading.asset_tracker import get_overview

        overview = await get_overview(db, user_id)
        if overview.account_count > 0:
            return [
                PerformancePoint(
                    date=date.today(),
                    total_value=overview.total_value,
                )
            ]
        return []

    return [
        PerformancePoint(
            date=row.day.date() if hasattr(row.day, "date") else row.day,
            total_value=Decimal(str(row.total_value)).quantize(Decimal("0.01")),
        )
        for row in rows
    ]

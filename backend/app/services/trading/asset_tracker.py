"""Asset tracker — aggregates portfolio data across all user accounts."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.order import Order, OrderSide, OrderStatus
from app.schemas.portfolio import (
    AssetOverview,
    CashFlowItem,
    HoldingItem,
    MarketAllocation,
)


async def get_overview(db: AsyncSession, user_id: uuid.UUID) -> AssetOverview:
    """Calculate total asset overview across all accounts."""
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
    total_pnl = total_unrealized + total_realized

    # Calculate P&L percentage based on initial investment
    initial = total_value - total_pnl
    pnl_pct = (total_pnl / initial * 100) if initial > 0 else Decimal("0")

    return AssetOverview(
        total_value=total_value.quantize(Decimal("0.01")),
        total_balance=total_balance.quantize(Decimal("0.01")),
        total_market_value=total_market_value.quantize(Decimal("0.01")),
        total_unrealized_pnl=total_unrealized.quantize(Decimal("0.01")),
        total_realized_pnl=total_realized.quantize(Decimal("0.01")),
        total_pnl=total_pnl.quantize(Decimal("0.01")),
        total_pnl_pct=pnl_pct.quantize(Decimal("0.01")),
        account_count=len(accounts),
    )


async def get_allocation(db: AsyncSession, user_id: uuid.UUID) -> list[MarketAllocation]:
    """Get asset allocation breakdown by market."""
    result = await db.execute(
        select(Account).where(Account.user_id == user_id)
    )
    accounts = list(result.scalars().all())

    market_data: dict[str, dict[str, Decimal | int]] = {}
    for acct in accounts:
        market = acct.market.value if hasattr(acct.market, "value") else str(acct.market)
        if market not in market_data:
            market_data[market] = {
                "market_value": Decimal("0"),
                "balance": Decimal("0"),
                "account_count": 0,
            }
        market_data[market]["balance"] += Decimal(str(acct.balance))
        market_data[market]["account_count"] += 1
        for pos in acct.positions:
            if pos.quantity > 0:
                market_data[market]["market_value"] += Decimal(str(pos.market_value))

    grand_total = sum(
        (v["market_value"] + v["balance"]) for v in market_data.values()
    )

    allocations = []
    for market, data in market_data.items():
        total = data["market_value"] + data["balance"]
        pct = (total / grand_total * 100) if grand_total > 0 else Decimal("0")
        allocations.append(
            MarketAllocation(
                market=market,
                market_value=Decimal(str(data["market_value"])).quantize(Decimal("0.01")),
                balance=Decimal(str(data["balance"])).quantize(Decimal("0.01")),
                total_value=Decimal(str(total)).quantize(Decimal("0.01")),
                percentage=Decimal(str(pct)).quantize(Decimal("0.01")),
                account_count=int(data["account_count"]),
            )
        )

    return sorted(allocations, key=lambda a: a.total_value, reverse=True)


async def get_holdings(db: AsyncSession, user_id: uuid.UUID) -> list[HoldingItem]:
    """Get all holdings (positions with quantity > 0) across accounts."""
    result = await db.execute(
        select(Account).where(Account.user_id == user_id)
    )
    accounts = list(result.scalars().all())

    holdings = []
    for acct in accounts:
        market = acct.market.value if hasattr(acct.market, "value") else str(acct.market)
        for pos in acct.positions:
            if pos.quantity <= 0:
                continue
            avg = Decimal(str(pos.avg_cost))
            pnl_pct = (
                ((Decimal(str(pos.current_price)) - avg) / avg * 100)
                if avg > 0
                else Decimal("0")
            )
            holdings.append(
                HoldingItem(
                    symbol=pos.symbol,
                    name=pos.name,
                    market=market,
                    account_name=acct.name,
                    account_id=acct.id,
                    quantity=pos.quantity,
                    avg_cost=avg.quantize(Decimal("0.0001")),
                    current_price=Decimal(str(pos.current_price)).quantize(Decimal("0.0001")),
                    market_value=Decimal(str(pos.market_value)).quantize(Decimal("0.01")),
                    unrealized_pnl=Decimal(str(pos.unrealized_pnl)).quantize(Decimal("0.01")),
                    unrealized_pnl_pct=pnl_pct.quantize(Decimal("0.01")),
                    realized_pnl=Decimal(str(pos.realized_pnl)).quantize(Decimal("0.01")),
                )
            )

    return sorted(holdings, key=lambda h: h.market_value, reverse=True)


async def get_cash_flows(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[CashFlowItem]:
    """Get recent cash flow events (filled orders)."""
    # Get user's account IDs
    result = await db.execute(
        select(Account.id, Account.name).where(Account.user_id == user_id)
    )
    account_map = {row.id: row.name for row in result.all()}

    if not account_map:
        return []

    result = await db.execute(
        select(Order)
        .where(
            Order.account_id.in_(list(account_map.keys())),
            Order.status.in_([OrderStatus.FILLED, OrderStatus.PARTIAL_FILLED]),
            Order.filled_at.is_not(None),
        )
        .order_by(Order.filled_at.desc())
        .limit(limit)
    )
    orders = result.scalars().all()

    flows = []
    for o in orders:
        filled_price = Decimal(str(o.filled_price or 0))
        amount = filled_price * Decimal(str(o.filled_quantity))
        if o.side == OrderSide.BUY:
            amount = -(amount + Decimal(str(o.commission)))
        else:
            amount = amount - Decimal(str(o.commission))

        flows.append(
            CashFlowItem(
                id=o.id,
                account_name=account_map.get(o.account_id, "Unknown"),
                symbol=o.symbol,
                side=o.side.value if hasattr(o.side, "value") else str(o.side),
                quantity=o.filled_quantity,
                price=filled_price.quantize(Decimal("0.0001")),
                commission=Decimal(str(o.commission)).quantize(Decimal("0.0001")),
                amount=amount.quantize(Decimal("0.01")),
                filled_at=o.filled_at,
            )
        )

    return flows

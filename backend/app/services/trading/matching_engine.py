"""Simulated matching engine — fills orders against latest market prices."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import order as order_crud
from app.models.account import Account, Market
from app.models.order import Order, OrderSide, OrderStatus, OrderType
from app.services.trading.order_state import validate_transition
from app.services.trading.portfolio import apply_fill
from app.services.trading.rules.a_share import AShareRules
from app.services.trading.rules.base import MarketRules
from app.services.trading.rules.convertible_bond import ConvertibleBondRules
from app.services.trading.rules.us_stock import USStockRules

logger = logging.getLogger(__name__)

_RULES: dict[str, MarketRules] = {
    Market.A_SHARE.value: AShareRules(),
    Market.US_STOCK.value: USStockRules(),
    Market.HK_STOCK.value: USStockRules(),  # HK uses US-style rules for now
    Market.FUND.value: AShareRules(),  # Fund uses A-share-style rules
    Market.BOND.value: ConvertibleBondRules(),  # Convertible bond T+0 rules
}


def get_rules(market: str) -> MarketRules:
    """Return the MarketRules instance for a given market."""
    rules = _RULES.get(market)
    if rules is None:
        raise ValueError(f"No rules defined for market: {market}")
    return rules


async def get_latest_price(db: AsyncSession, symbol: str, market: str) -> Decimal | None:
    """Fetch the latest close price from the appropriate table."""
    from sqlalchemy import text

    if market in (Market.A_SHARE.value, Market.US_STOCK.value, Market.HK_STOCK.value):
        row = await db.execute(
            text(
                "SELECT close FROM stock_daily "
                "WHERE symbol = :symbol AND market = :market "
                "ORDER BY time DESC LIMIT 1"
            ),
            {"symbol": symbol, "market": market},
        )
    elif market == Market.FUND.value:
        row = await db.execute(
            text(
                "SELECT nav AS close FROM fund_nav "
                "WHERE symbol = :symbol "
                "ORDER BY time DESC LIMIT 1"
            ),
            {"symbol": symbol},
        )
    elif market == Market.BOND.value:
        row = await db.execute(
            text(
                "SELECT close FROM bond_daily "
                "WHERE symbol = :symbol "
                "ORDER BY time DESC LIMIT 1"
            ),
            {"symbol": symbol},
        )
    else:
        return None

    result = row.first()
    if result is None:
        return None
    return Decimal(str(result[0]))


async def try_fill(
    db: AsyncSession,
    order: Order,
    account: Account,
) -> Order:
    """Attempt to fill an order using simulated matching.

    Market orders: fill immediately at latest price ± slippage.
    Limit orders: fill if price condition is met, otherwise leave as SUBMITTED.
    """
    market = account.market.value if hasattr(account.market, "value") else str(account.market)
    rules = get_rules(market)

    latest_price = await get_latest_price(db, order.symbol, market)
    if latest_price is None:
        # No market data — reject
        validate_transition(order.status, OrderStatus.REJECTED)
        order = await order_crud.update(
            db, order, status=OrderStatus.REJECTED, remark="No market data available"
        )
        return order

    now = datetime.now(tz=timezone.utc)

    if order.order_type == OrderType.MARKET:
        fill_price = rules.apply_slippage(order.side, latest_price)
        return await _execute_fill(db, order, account, rules, fill_price, order.quantity, now)

    # Limit order
    limit_price = Decimal(str(order.price))
    should_fill = False
    if order.side == OrderSide.BUY and latest_price <= limit_price:
        should_fill = True
    elif order.side == OrderSide.SELL and latest_price >= limit_price:
        should_fill = True

    if should_fill:
        return await _execute_fill(db, order, account, rules, limit_price, order.quantity, now)

    # Not fillable yet — mark as submitted
    if order.status == OrderStatus.PENDING:
        validate_transition(order.status, OrderStatus.SUBMITTED)
        order = await order_crud.update(db, order, status=OrderStatus.SUBMITTED, submitted_at=now)

    return order


async def _execute_fill(
    db: AsyncSession,
    order: Order,
    account: Account,
    rules: MarketRules,
    fill_price: Decimal,
    fill_quantity: int,
    now: datetime,
) -> Order:
    """Execute a fill: update order status, position, and account balance."""
    commission = rules.calculate_commission(order.side, fill_quantity, fill_price)

    # Check sufficient balance for buy orders
    if order.side == OrderSide.BUY:
        total_cost = fill_price * fill_quantity + commission
        if total_cost > Decimal(str(account.balance)):
            validate_transition(order.status, OrderStatus.REJECTED)
            return await order_crud.update(
                db, order, status=OrderStatus.REJECTED, remark="Insufficient balance"
            )

    target_status = OrderStatus.FILLED
    validate_transition(order.status, target_status)

    order = await order_crud.update(
        db,
        order,
        status=target_status,
        filled_quantity=fill_quantity,
        filled_price=float(fill_price),
        commission=float(commission),
        filled_at=now,
        submitted_at=order.submitted_at or now,
    )

    await apply_fill(db, account, order, fill_quantity, fill_price, commission)
    logger.info(
        "Filled order %s: %s %d %s @ %s",
        order.id,
        order.side.value,
        fill_quantity,
        order.symbol,
        fill_price,
    )
    return order

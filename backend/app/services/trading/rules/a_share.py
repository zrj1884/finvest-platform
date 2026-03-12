"""A-share market rules — T+1, ±10%/20% price limits, lot size 100."""

from __future__ import annotations

from decimal import Decimal

from app.models.order import OrderSide, OrderType

from .base import MarketRules

# Commission: 0.025% (min ¥5)
COMMISSION_RATE = Decimal("0.00025")
MIN_COMMISSION = Decimal("5")
# Stamp duty: 0.1% on sells only
STAMP_DUTY_RATE = Decimal("0.001")
# Slippage for market orders
SLIPPAGE_PCT = Decimal("0.001")
# Standard lot size
LOT_SIZE = 100
# Price limit percentage (main board)
PRICE_LIMIT_PCT = Decimal("0.10")


class AShareRules(MarketRules):
    """A-share (沪深A股) trading rules."""

    def validate_order(
        self,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Decimal | None,
        current_price: Decimal,
        available_quantity: int = 0,
        *,
        is_t1: bool = False,
    ) -> list[str]:
        errors: list[str] = []

        if quantity <= 0:
            errors.append("Quantity must be positive")

        # Lot size check: buy must be multiples of 100; sell can be odd lot
        if side == OrderSide.BUY and quantity % LOT_SIZE != 0:
            errors.append(f"Buy quantity must be a multiple of {LOT_SIZE}")

        if order_type == OrderType.LIMIT and price is None:
            errors.append("Limit orders require a price")

        if order_type == OrderType.LIMIT and price is not None and price <= 0:
            errors.append("Limit price must be positive")

        # Price limit check for limit orders
        if order_type == OrderType.LIMIT and price is not None and current_price > 0:
            upper = current_price * (1 + PRICE_LIMIT_PCT)
            lower = current_price * (1 - PRICE_LIMIT_PCT)
            if price > upper or price < lower:
                errors.append(
                    f"Price {price} outside ±{PRICE_LIMIT_PCT * 100}% limit "
                    f"[{lower.quantize(Decimal('0.01'))}, {upper.quantize(Decimal('0.01'))}]"
                )

        # T+1: cannot sell shares bought today
        if side == OrderSide.SELL:
            if quantity > available_quantity:
                errors.append(
                    f"Insufficient available shares: available {available_quantity}, "
                    f"requested {quantity}"
                )

        return errors

    def calculate_commission(
        self,
        side: OrderSide,
        quantity: int,
        fill_price: Decimal,
    ) -> Decimal:
        turnover = fill_price * quantity
        commission = max(turnover * COMMISSION_RATE, MIN_COMMISSION)
        if side == OrderSide.SELL:
            commission += turnover * STAMP_DUTY_RATE
        return commission.quantize(Decimal("0.0001"))

    def apply_slippage(self, side: OrderSide, price: Decimal) -> Decimal:
        if side == OrderSide.BUY:
            return (price * (1 + SLIPPAGE_PCT)).quantize(Decimal("0.01"))
        return (price * (1 - SLIPPAGE_PCT)).quantize(Decimal("0.01"))

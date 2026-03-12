"""Convertible bond (可转债) market rules — T+0, no price limits, 10 lots."""

from __future__ import annotations

from decimal import Decimal

from app.models.order import OrderSide, OrderType

from .base import MarketRules

# Commission: 0.01% (min ¥1) — varies by broker, using typical online rate
COMMISSION_RATE = Decimal("0.0001")
MIN_COMMISSION = Decimal("1")
# No stamp duty for convertible bonds
# Standard lot size: 10 (1 lot = 10 bonds, par ¥100 each)
LOT_SIZE = 10
# Slippage for market orders
SLIPPAGE_PCT = Decimal("0.001")


class ConvertibleBondRules(MarketRules):
    """Convertible bond (可转债) trading rules.

    Key differences from A-shares:
    - T+0: can buy and sell on the same day
    - No price limits (since 2022 reform: ±20% first day, then ±30% after)
    - Lot size: 10 bonds (not 100 shares)
    - Lower commission than stocks
    """

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

        # Lot size check: buy must be multiples of 10
        if side == OrderSide.BUY and quantity % LOT_SIZE != 0:
            errors.append(f"Buy quantity must be a multiple of {LOT_SIZE}")

        if order_type == OrderType.LIMIT and price is None:
            errors.append("Limit orders require a price")

        if order_type == OrderType.LIMIT and price is not None and price <= 0:
            errors.append("Limit price must be positive")

        # T+0: sell validation only checks available quantity (no T+1 restriction)
        if side == OrderSide.SELL:
            if quantity > available_quantity:
                errors.append(
                    f"Insufficient available bonds: available {available_quantity}, "
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
        return commission.quantize(Decimal("0.0001"))

    def apply_slippage(self, side: OrderSide, price: Decimal) -> Decimal:
        if side == OrderSide.BUY:
            return (price * (1 + SLIPPAGE_PCT)).quantize(Decimal("0.01"))
        return (price * (1 - SLIPPAGE_PCT)).quantize(Decimal("0.01"))

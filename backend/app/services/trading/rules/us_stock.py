"""US stock market rules — T+0, no price limits, SEC/FINRA fees."""

from __future__ import annotations

from decimal import Decimal

from app.models.order import OrderSide, OrderType

from .base import MarketRules

# SEC fee: ~$8 per $1M of sale proceeds (as of 2024)
SEC_FEE_RATE = Decimal("0.000008")
# FINRA TAF: $0.000166 per share sold (max $8.30)
FINRA_TAF_RATE = Decimal("0.000166")
# Simulated broker commission: $0 (zero-commission like Alpaca)
BROKER_COMMISSION = Decimal("0")
# Slippage for market orders
SLIPPAGE_PCT = Decimal("0.001")  # 0.1%


class USStockRules(MarketRules):
    """US equity trading rules."""

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

        if order_type == OrderType.LIMIT and price is None:
            errors.append("Limit orders require a price")

        if order_type == OrderType.LIMIT and price is not None and price <= 0:
            errors.append("Limit price must be positive")

        if side == OrderSide.SELL and quantity > available_quantity:
            errors.append(
                f"Insufficient shares: available {available_quantity}, requested {quantity}"
            )

        # US stocks: no lot size restriction, fractional shares not supported here
        return errors

    def calculate_commission(
        self,
        side: OrderSide,
        quantity: int,
        fill_price: Decimal,
    ) -> Decimal:
        total = BROKER_COMMISSION
        if side == OrderSide.SELL:
            proceeds = fill_price * quantity
            total += proceeds * SEC_FEE_RATE
            taf = FINRA_TAF_RATE * quantity
            total += min(taf, Decimal("8.30"))
        return total.quantize(Decimal("0.0001"))

    def apply_slippage(self, side: OrderSide, price: Decimal) -> Decimal:
        if side == OrderSide.BUY:
            return (price * (1 + SLIPPAGE_PCT)).quantize(Decimal("0.0001"))
        return (price * (1 - SLIPPAGE_PCT)).quantize(Decimal("0.0001"))

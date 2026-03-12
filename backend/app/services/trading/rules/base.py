"""Abstract market rules — each market implements its own validation & commission logic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.models.order import Order, OrderSide, OrderType


class MarketRules(ABC):
    """Base class for market-specific trading rules."""

    @abstractmethod
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
        """Return a list of validation error messages (empty = valid)."""
        ...

    @abstractmethod
    def calculate_commission(
        self,
        side: OrderSide,
        quantity: int,
        fill_price: Decimal,
    ) -> Decimal:
        """Calculate commission/fees for a filled trade."""
        ...

    @abstractmethod
    def apply_slippage(
        self, side: OrderSide, price: Decimal
    ) -> Decimal:
        """Apply slippage to a market-order fill price."""
        ...

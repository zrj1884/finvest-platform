"""Tests for convertible bond market rules."""

from decimal import Decimal

import pytest

from app.models.order import OrderSide, OrderType
from app.services.trading.rules.convertible_bond import (
    COMMISSION_RATE,
    MIN_COMMISSION,
    ConvertibleBondRules,
)


@pytest.fixture
def rules() -> ConvertibleBondRules:
    return ConvertibleBondRules()


class TestValidation:
    def test_valid_buy(self, rules: ConvertibleBondRules) -> None:
        errors = rules.validate_order(
            OrderSide.BUY, OrderType.MARKET, 10, None, Decimal("120")
        )
        assert errors == []

    def test_buy_odd_lot_invalid(self, rules: ConvertibleBondRules) -> None:
        errors = rules.validate_order(
            OrderSide.BUY, OrderType.MARKET, 15, None, Decimal("120")
        )
        assert any("multiple of 10" in e for e in errors)

    def test_sell_odd_lot_ok(self, rules: ConvertibleBondRules) -> None:
        """Selling odd lots is allowed (liquidation)."""
        errors = rules.validate_order(
            OrderSide.SELL, OrderType.MARKET, 5, None, Decimal("120"),
            available_quantity=5,
        )
        assert errors == []

    def test_sell_insufficient(self, rules: ConvertibleBondRules) -> None:
        errors = rules.validate_order(
            OrderSide.SELL, OrderType.MARKET, 20, None, Decimal("120"),
            available_quantity=10,
        )
        assert any("Insufficient" in e for e in errors)

    def test_t0_same_day_sell(self, rules: ConvertibleBondRules) -> None:
        """T+0: can sell bonds bought today (no T+1 restriction)."""
        errors = rules.validate_order(
            OrderSide.SELL, OrderType.MARKET, 10, None, Decimal("120"),
            available_quantity=10,
        )
        assert errors == []

    def test_limit_requires_price(self, rules: ConvertibleBondRules) -> None:
        errors = rules.validate_order(
            OrderSide.BUY, OrderType.LIMIT, 10, None, Decimal("120")
        )
        assert any("price" in e.lower() for e in errors)

    def test_zero_quantity(self, rules: ConvertibleBondRules) -> None:
        errors = rules.validate_order(
            OrderSide.BUY, OrderType.MARKET, 0, None, Decimal("120")
        )
        assert any("positive" in e.lower() for e in errors)


class TestCommission:
    def test_commission_above_minimum(self, rules: ConvertibleBondRules) -> None:
        # 100 bonds at ¥120 = ¥12,000 × 0.01% = ¥1.20 > ¥1 min
        commission = rules.calculate_commission(OrderSide.BUY, 100, Decimal("120"))
        expected = (Decimal("12000") * COMMISSION_RATE).quantize(Decimal("0.0001"))
        assert commission == expected

    def test_commission_minimum(self, rules: ConvertibleBondRules) -> None:
        # 10 bonds at ¥100 = ¥1,000 × 0.01% = ¥0.10 < ¥1 min
        commission = rules.calculate_commission(OrderSide.BUY, 10, Decimal("100"))
        assert commission == MIN_COMMISSION

    def test_no_stamp_duty_on_sell(self, rules: ConvertibleBondRules) -> None:
        """Unlike A-shares, convertible bonds have no stamp duty."""
        buy_comm = rules.calculate_commission(OrderSide.BUY, 100, Decimal("120"))
        sell_comm = rules.calculate_commission(OrderSide.SELL, 100, Decimal("120"))
        assert buy_comm == sell_comm


class TestSlippage:
    def test_buy_higher(self, rules: ConvertibleBondRules) -> None:
        slipped = rules.apply_slippage(OrderSide.BUY, Decimal("100"))
        assert slipped > Decimal("100")

    def test_sell_lower(self, rules: ConvertibleBondRules) -> None:
        slipped = rules.apply_slippage(OrderSide.SELL, Decimal("100"))
        assert slipped < Decimal("100")

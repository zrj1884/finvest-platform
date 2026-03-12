"""Tests for market-specific trading rules."""

from decimal import Decimal

import pytest

from app.models.order import OrderSide, OrderType
from app.services.trading.rules.a_share import AShareRules
from app.services.trading.rules.us_stock import USStockRules


class TestUSStockRules:
    rules = USStockRules()

    def test_valid_market_buy(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.MARKET, 10, None, Decimal("150.00")
        )
        assert errors == []

    def test_valid_limit_buy(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.LIMIT, 10, Decimal("148.00"), Decimal("150.00")
        )
        assert errors == []

    def test_limit_order_requires_price(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.LIMIT, 10, None, Decimal("150.00")
        )
        assert any("require" in e.lower() for e in errors)

    def test_sell_insufficient_shares(self):
        errors = self.rules.validate_order(
            OrderSide.SELL, OrderType.MARKET, 100, None, Decimal("150.00"),
            available_quantity=50,
        )
        assert any("insufficient" in e.lower() for e in errors)

    def test_sell_sufficient_shares(self):
        errors = self.rules.validate_order(
            OrderSide.SELL, OrderType.MARKET, 50, None, Decimal("150.00"),
            available_quantity=50,
        )
        assert errors == []

    def test_zero_quantity_invalid(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.MARKET, 0, None, Decimal("150.00")
        )
        assert any("positive" in e.lower() for e in errors)

    def test_commission_buy(self):
        commission = self.rules.calculate_commission(
            OrderSide.BUY, 100, Decimal("150.00")
        )
        assert commission == Decimal("0")  # Zero-commission broker

    def test_commission_sell_includes_sec_fee(self):
        commission = self.rules.calculate_commission(
            OrderSide.SELL, 100, Decimal("150.00")
        )
        assert commission > 0

    def test_slippage_buy_higher(self):
        price = Decimal("100.00")
        slipped = self.rules.apply_slippage(OrderSide.BUY, price)
        assert slipped > price

    def test_slippage_sell_lower(self):
        price = Decimal("100.00")
        slipped = self.rules.apply_slippage(OrderSide.SELL, price)
        assert slipped < price


class TestAShareRules:
    rules = AShareRules()

    def test_valid_buy_lot_100(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.MARKET, 100, None, Decimal("10.00")
        )
        assert errors == []

    def test_buy_odd_lot_invalid(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.MARKET, 50, None, Decimal("10.00")
        )
        assert any("multiple" in e.lower() for e in errors)

    def test_sell_odd_lot_ok(self):
        """Selling odd lots is allowed in A-share market."""
        errors = self.rules.validate_order(
            OrderSide.SELL, OrderType.MARKET, 50, None, Decimal("10.00"),
            available_quantity=50,
        )
        assert errors == []

    def test_price_limit_within_range(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.LIMIT, 100, Decimal("10.50"), Decimal("10.00")
        )
        assert errors == []

    def test_price_limit_exceeded(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.LIMIT, 100, Decimal("12.00"), Decimal("10.00")
        )
        assert any("limit" in e.lower() for e in errors)

    def test_price_limit_below_floor(self):
        errors = self.rules.validate_order(
            OrderSide.BUY, OrderType.LIMIT, 100, Decimal("8.00"), Decimal("10.00")
        )
        assert any("limit" in e.lower() for e in errors)

    def test_commission_buy(self):
        commission = self.rules.calculate_commission(
            OrderSide.BUY, 100, Decimal("10.00")
        )
        # Min commission is ¥5
        assert commission >= Decimal("5")

    def test_commission_sell_includes_stamp_duty(self):
        commission_buy = self.rules.calculate_commission(
            OrderSide.BUY, 1000, Decimal("10.00")
        )
        commission_sell = self.rules.calculate_commission(
            OrderSide.SELL, 1000, Decimal("10.00")
        )
        # Sell commission includes stamp duty, so should be higher
        assert commission_sell > commission_buy

    def test_slippage(self):
        price = Decimal("10.00")
        buy_price = self.rules.apply_slippage(OrderSide.BUY, price)
        sell_price = self.rules.apply_slippage(OrderSide.SELL, price)
        assert buy_price > price
        assert sell_price < price

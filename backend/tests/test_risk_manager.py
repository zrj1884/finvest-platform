"""Tests for pre-trade risk checks."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.trading.risk_manager import (
    MAX_DAILY_LOSS_PCT,
    MAX_ORDERS_PER_MINUTE,
    MAX_POSITION_CONCENTRATION,
    _check_concentration,
    _check_daily_loss,
    _check_order_frequency,
    pre_trade_check,
)


def _make_account(balance: float = 1_000_000.0) -> MagicMock:
    acct = MagicMock()
    acct.id = uuid.uuid4()
    acct.balance = balance
    return acct


def _scalar_one(val: object) -> MagicMock:
    """Create a mock result whose scalar_one() returns val."""
    result = MagicMock()
    result.scalar_one.return_value = val
    result.scalar_one_or_none.return_value = val
    result.scalars.return_value.all.return_value = []
    return result


class TestConcentration:
    @pytest.mark.asyncio
    async def test_within_limit(self) -> None:
        db = AsyncMock()
        # total_market_value = 0, current_position = None
        db.execute = AsyncMock(side_effect=[_scalar_one(0), _scalar_one(None)])
        acct = _make_account(1_000_000)

        # Buying 100 shares at $100 = $10,000 / $1,000,000 = 1% → OK
        err = await _check_concentration(db, acct, "AAPL", 100, Decimal("100"))
        assert err is None

    @pytest.mark.asyncio
    async def test_exceeds_limit(self) -> None:
        db = AsyncMock()
        # total_market_value = 0, current_position = 200000
        db.execute = AsyncMock(side_effect=[_scalar_one(0), _scalar_one(200000)])
        acct = _make_account(1_000_000)

        # Existing $200k + buying $200k = $400k / $1M = 40% > 30%
        err = await _check_concentration(db, acct, "AAPL", 2000, Decimal("100"))
        assert err is not None
        assert "concentration" in err.lower()

    @pytest.mark.asyncio
    async def test_zero_total_value(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[_scalar_one(0)])
        acct = _make_account(0)

        err = await _check_concentration(db, acct, "AAPL", 100, Decimal("100"))
        assert err is None


class TestDailyLoss:
    @pytest.mark.asyncio
    async def test_no_loss(self) -> None:
        db = AsyncMock()
        # daily_commission = 0, unrealized = 0, total_positions = 0
        db.execute = AsyncMock(
            side_effect=[_scalar_one(0), _scalar_one(0), _scalar_one(0)]
        )
        acct = _make_account(1_000_000)

        err = await _check_daily_loss(db, acct)
        assert err is None

    @pytest.mark.asyncio
    async def test_within_limit(self) -> None:
        db = AsyncMock()
        # daily_commission = 100, unrealized = -30000 (3%), total_positions = 500000
        db.execute = AsyncMock(
            side_effect=[_scalar_one(100), _scalar_one(-30000), _scalar_one(500000)]
        )
        acct = _make_account(1_000_000)

        # loss = -30000 - 100 = -30100 / 1500000 ≈ 2% < 5%
        err = await _check_daily_loss(db, acct)
        assert err is None

    @pytest.mark.asyncio
    async def test_exceeds_limit(self) -> None:
        db = AsyncMock()
        # daily_commission = 0, unrealized = -100000, total_positions = 500000
        db.execute = AsyncMock(
            side_effect=[_scalar_one(0), _scalar_one(-100000), _scalar_one(500000)]
        )
        acct = _make_account(1_000_000)

        # loss = -100000 / 1500000 ≈ 6.7% > 5%
        err = await _check_daily_loss(db, acct)
        assert err is not None
        assert "daily loss" in err.lower()


class TestOrderFrequency:
    @pytest.mark.asyncio
    async def test_within_limit(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_one(5))

        err = await _check_order_frequency(db, uuid.uuid4())
        assert err is None

    @pytest.mark.asyncio
    async def test_exceeds_limit(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_one(MAX_ORDERS_PER_MINUTE))

        err = await _check_order_frequency(db, uuid.uuid4())
        assert err is not None
        assert "frequency" in err.lower()


class TestPreTradeCheck:
    @pytest.mark.asyncio
    async def test_all_pass(self) -> None:
        with (
            patch(
                "app.services.trading.risk_manager._check_concentration",
                return_value=None,
            ) as _,
            patch(
                "app.services.trading.risk_manager._check_daily_loss",
                return_value=None,
            ) as _,
            patch(
                "app.services.trading.risk_manager._check_order_frequency",
                return_value=None,
            ) as _,
        ):
            db = AsyncMock()
            acct = _make_account()
            errors = await pre_trade_check(db, acct, "AAPL", "buy", 100, Decimal("150"))
            assert errors == []

    @pytest.mark.asyncio
    async def test_multiple_failures(self) -> None:
        with (
            patch(
                "app.services.trading.risk_manager._check_concentration",
                return_value="Concentration too high",
            ) as _,
            patch(
                "app.services.trading.risk_manager._check_daily_loss",
                return_value="Daily loss exceeded",
            ) as _,
            patch(
                "app.services.trading.risk_manager._check_order_frequency",
                return_value="Too many orders",
            ) as _,
        ):
            db = AsyncMock()
            acct = _make_account()
            errors = await pre_trade_check(db, acct, "AAPL", "buy", 100, Decimal("150"))
            assert len(errors) == 3

    @pytest.mark.asyncio
    async def test_sell_skips_concentration(self) -> None:
        with (
            patch(
                "app.services.trading.risk_manager._check_concentration",
            ) as mock_conc,
            patch(
                "app.services.trading.risk_manager._check_daily_loss",
                return_value=None,
            ) as _,
            patch(
                "app.services.trading.risk_manager._check_order_frequency",
                return_value=None,
            ) as _,
        ):
            db = AsyncMock()
            acct = _make_account()
            errors = await pre_trade_check(db, acct, "AAPL", "sell", 100, Decimal("150"))
            assert errors == []
            mock_conc.assert_not_called()


class TestThresholds:
    def test_concentration_is_30_pct(self) -> None:
        assert MAX_POSITION_CONCENTRATION == Decimal("0.30")

    def test_daily_loss_is_5_pct(self) -> None:
        assert MAX_DAILY_LOSS_PCT == Decimal("0.05")

    def test_frequency_is_10_per_min(self) -> None:
        assert MAX_ORDERS_PER_MINUTE == 10

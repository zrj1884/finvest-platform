"""Tests for order state machine."""

import pytest

from app.models.order import OrderStatus
from app.services.trading.order_state import (
    TERMINAL_STATES,
    can_transition,
    is_terminal,
    validate_transition,
)


class TestCanTransition:
    def test_pending_to_submitted(self):
        assert can_transition(OrderStatus.PENDING, OrderStatus.SUBMITTED) is True

    def test_pending_to_rejected(self):
        assert can_transition(OrderStatus.PENDING, OrderStatus.REJECTED) is True

    def test_pending_to_filled_invalid(self):
        assert can_transition(OrderStatus.PENDING, OrderStatus.FILLED) is False

    def test_submitted_to_filled(self):
        assert can_transition(OrderStatus.SUBMITTED, OrderStatus.FILLED) is True

    def test_submitted_to_partial(self):
        assert can_transition(OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED) is True

    def test_submitted_to_cancelled(self):
        assert can_transition(OrderStatus.SUBMITTED, OrderStatus.CANCELLED) is True

    def test_partial_to_filled(self):
        assert can_transition(OrderStatus.PARTIAL_FILLED, OrderStatus.FILLED) is True

    def test_partial_to_cancelled(self):
        assert can_transition(OrderStatus.PARTIAL_FILLED, OrderStatus.CANCELLED) is True

    def test_partial_to_submitted_invalid(self):
        assert can_transition(OrderStatus.PARTIAL_FILLED, OrderStatus.SUBMITTED) is False

    def test_filled_is_terminal(self):
        assert can_transition(OrderStatus.FILLED, OrderStatus.CANCELLED) is False
        assert can_transition(OrderStatus.FILLED, OrderStatus.PENDING) is False

    def test_cancelled_is_terminal(self):
        assert can_transition(OrderStatus.CANCELLED, OrderStatus.FILLED) is False

    def test_rejected_is_terminal(self):
        assert can_transition(OrderStatus.REJECTED, OrderStatus.SUBMITTED) is False


class TestValidateTransition:
    def test_valid_transition_no_error(self):
        validate_transition(OrderStatus.PENDING, OrderStatus.SUBMITTED)

    def test_invalid_transition_raises(self):
        with pytest.raises(ValueError, match="Invalid order status transition"):
            validate_transition(OrderStatus.FILLED, OrderStatus.CANCELLED)


class TestIsTerminal:
    def test_terminal_states(self):
        for s in TERMINAL_STATES:
            assert is_terminal(s) is True

    def test_non_terminal_states(self):
        for s in (OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED):
            assert is_terminal(s) is False

"""Order state machine — validates and applies status transitions."""

from __future__ import annotations

from app.models.order import OrderStatus

# Allowed state transitions: from_status -> set of valid target statuses
VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.SUBMITTED, OrderStatus.FILLED, OrderStatus.REJECTED},
    OrderStatus.SUBMITTED: {
        OrderStatus.PARTIAL_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
    },
    OrderStatus.PARTIAL_FILLED: {
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
    },
    # Terminal states — no further transitions
    OrderStatus.FILLED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.REJECTED: set(),
}

TERMINAL_STATES = {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    """Check whether a transition from *current* to *target* is valid."""
    return target in VALID_TRANSITIONS.get(current, set())


def validate_transition(current: OrderStatus, target: OrderStatus) -> None:
    """Raise ValueError if the transition is invalid."""
    if not can_transition(current, target):
        raise ValueError(
            f"Invalid order status transition: {current.value} -> {target.value}"
        )


def is_terminal(status: OrderStatus) -> bool:
    """Return True if the status is a terminal (final) state."""
    return status in TERMINAL_STATES

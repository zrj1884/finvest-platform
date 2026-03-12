"""Portfolio / asset dashboard schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class AssetOverview(BaseModel):
    """Aggregated asset summary across all accounts."""

    total_value: Decimal
    total_balance: Decimal
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    account_count: int


class MarketAllocation(BaseModel):
    """Allocation breakdown by market."""

    market: str
    market_value: Decimal
    balance: Decimal
    total_value: Decimal
    percentage: Decimal
    account_count: int


class HoldingItem(BaseModel):
    """Single holding across accounts."""

    symbol: str
    name: str | None
    market: str
    account_name: str
    account_id: uuid.UUID
    quantity: int
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    realized_pnl: Decimal


class PerformancePoint(BaseModel):
    """Single data point on the performance curve."""

    date: date
    total_value: Decimal


class CashFlowItem(BaseModel):
    """A single cash flow event (order fill)."""

    id: uuid.UUID
    account_name: str
    symbol: str
    side: str
    quantity: int
    price: Decimal
    commission: Decimal
    amount: Decimal
    filled_at: datetime

    model_config = {"from_attributes": True}

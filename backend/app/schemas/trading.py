"""Trading request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# --- Account ---


class AccountCreate(BaseModel):
    name: str = Field(max_length=100)
    market: str  # a_share, us_stock, hk_stock, fund, bond
    is_simulated: bool = True
    balance: Decimal | None = None  # None → use default sim balance


class AccountRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    market: str
    broker: str | None
    account_no: str | None
    balance: Decimal
    is_simulated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AccountWithPositions(AccountRead):
    positions: list[PositionRead] = []


# --- Position ---


class PositionRead(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    symbol: str
    name: str | None
    quantity: int
    available_quantity: int
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Order ---


class OrderCreate(BaseModel):
    account_id: uuid.UUID
    symbol: str = Field(max_length=20)
    side: str  # buy, sell
    order_type: str  # market, limit
    quantity: int = Field(gt=0)
    price: Decimal | None = None  # required for limit orders
    remark: str | None = Field(None, max_length=500)


class OrderRead(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    symbol: str
    name: str | None
    side: str
    order_type: str
    status: str
    quantity: int
    filled_quantity: int
    price: Decimal | None
    filled_price: Decimal | None
    commission: Decimal
    submitted_at: datetime | None
    filled_at: datetime | None
    cancelled_at: datetime | None
    broker_order_id: str | None
    remark: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Performance ---


class PerformanceStats(BaseModel):
    total_value: Decimal
    total_cost: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    win_count: int
    loss_count: int
    win_rate: Decimal | None


# Forward ref update
AccountWithPositions.model_rebuild()

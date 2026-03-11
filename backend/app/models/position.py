"""Position (持仓) model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.account import Account


class Position(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "positions"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 证券代码
    name: Mapped[str | None] = mapped_column(String(100))  # 证券名称
    quantity: Mapped[int] = mapped_column(Integer, default=0)  # 持仓数量
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)  # 可卖数量
    avg_cost: Mapped[float] = mapped_column(Numeric(20, 4), default=0)  # 平均成本价
    current_price: Mapped[float] = mapped_column(Numeric(20, 4), default=0)  # 最新价
    market_value: Mapped[float] = mapped_column(Numeric(20, 4), default=0)  # 市值
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(20, 4), default=0)  # 未实现盈亏
    realized_pnl: Mapped[float] = mapped_column(Numeric(20, 4), default=0)  # 已实现盈亏

    # Relationships
    account: Mapped[Account] = relationship("Account", back_populates="positions")

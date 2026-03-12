"""Order (订单) model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.account import Account


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"  # 市价单
    LIMIT = "limit"  # 限价单


class OrderStatus(str, enum.Enum):
    PENDING = "pending"  # 待提交
    SUBMITTED = "submitted"  # 已提交
    PARTIAL_FILLED = "partial_filled"  # 部分成交
    FILLED = "filled"  # 全部成交
    CANCELLED = "cancelled"  # 已撤销
    REJECTED = "rejected"  # 已拒绝


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(100))
    side: Mapped[OrderSide] = mapped_column(
        Enum(OrderSide, values_callable=lambda e: [m.value for m in e], name="order_side_enum", create_type=False),
        nullable=False,
    )
    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, values_callable=lambda e: [m.value for m in e], name="order_type_enum", create_type=False),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, values_callable=lambda e: [m.value for m in e], name="order_status_enum", create_type=False),
        default=OrderStatus.PENDING,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # 委托数量
    filled_quantity: Mapped[int] = mapped_column(Integer, default=0)  # 成交数量
    price: Mapped[float | None] = mapped_column(Numeric(20, 4))  # 委托价格（限价单）
    filled_price: Mapped[float | None] = mapped_column(Numeric(20, 4))  # 成交均价
    commission: Mapped[float] = mapped_column(Numeric(20, 4), default=0)  # 手续费
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    broker_order_id: Mapped[str | None] = mapped_column(String(100))  # 券商订单号
    remark: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    account: Mapped[Account] = relationship("Account", back_populates="orders")

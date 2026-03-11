"""Trading account model."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.position import Position
    from app.models.user import User


class Market(str, enum.Enum):
    """Supported markets."""

    A_SHARE = "a_share"  # 沪深A股
    US_STOCK = "us_stock"  # 美股
    HK_STOCK = "hk_stock"  # 港股
    FUND = "fund"  # 基金
    BOND = "bond"  # 债券


class Account(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[Market] = mapped_column(Enum(Market), nullable=False)
    broker: Mapped[str | None] = mapped_column(String(100))  # 券商名称
    account_no: Mapped[str | None] = mapped_column(String(100))  # 券商账号
    balance: Mapped[float] = mapped_column(Numeric(20, 4), default=0)  # 可用资金
    is_simulated: Mapped[bool] = mapped_column(default=True)  # 是否模拟盘

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="accounts")
    positions: Mapped[list[Position]] = relationship("Position", back_populates="account", lazy="selectin")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="account", lazy="selectin")

"""A-share real trading gateway — broker abstraction layer.

Supports future integration with broker APIs (easytrader, 同花顺 OpenAPI, etc.).
Currently provides:
  - Abstract BrokerAdapter interface
  - EasyTraderAdapter (requires Windows + 同花顺/华泰 client)
  - Gateway implementation that maps TradingGateway operations to broker calls
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import order as order_crud
from app.models.account import Account
from app.models.order import Order, OrderStatus
from app.services.trading.gateway import TradingGateway
from app.services.trading.order_state import validate_transition

logger = logging.getLogger(__name__)


class BrokerAdapter(ABC):
    """Abstract broker adapter — wraps broker-specific API calls."""

    @abstractmethod
    async def connect(self, account_no: str, password: str) -> None:
        """Establish connection to broker client/API."""
        ...

    @abstractmethod
    async def buy(
        self, symbol: str, price: Decimal, quantity: int
    ) -> str:
        """Place a buy order. Returns broker order ID."""
        ...

    @abstractmethod
    async def sell(
        self, symbol: str, price: Decimal, quantity: int
    ) -> str:
        """Place a sell order. Returns broker order ID."""
        ...

    @abstractmethod
    async def cancel(self, broker_order_id: str) -> bool:
        """Cancel an order. Returns True if successful."""
        ...

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> dict[str, object]:
        """Query order status from broker.

        Returns dict with keys: status, filled_quantity, filled_price, etc.
        """
        ...

    @abstractmethod
    async def get_balance(self) -> Decimal:
        """Query available balance from broker."""
        ...

    @abstractmethod
    async def get_positions(self) -> list[dict[str, object]]:
        """Query current positions from broker.

        Returns list of dicts with: symbol, quantity, available_quantity, avg_cost, etc.
        """
        ...


class EasyTraderAdapter(BrokerAdapter):
    """EasyTrader adapter — controls desktop trading clients via pywinauto.

    Requirements:
      - Windows OS
      - 同花顺 or 华泰 trading client installed
      - pip install easytrader

    This adapter is provided as a reference implementation. Due to its
    dependency on Windows desktop automation, it is NOT recommended for
    production use. Consider using broker OpenAPI when available.
    """

    def __init__(self, broker: str = "ths") -> None:
        self._broker = broker
        self._client: object = None

    async def connect(self, account_no: str, password: str) -> None:
        try:
            import easytrader  # type: ignore[import-not-found]
        except ImportError:
            raise RuntimeError(
                "easytrader is not installed. Install with: pip install easytrader\n"
                "Note: easytrader requires Windows + 同花顺/华泰 desktop client."
            )

        self._client = easytrader.use(self._broker)
        self._client.connect(account_no)  # type: ignore[union-attr]
        logger.info("Connected to %s broker account %s", self._broker, account_no)

    async def buy(self, symbol: str, price: Decimal, quantity: int) -> str:
        if self._client is None:
            raise RuntimeError("Broker not connected")
        result = self._client.buy(symbol, float(price), quantity)  # type: ignore[union-attr]
        return str(result.get("entrust_no", ""))

    async def sell(self, symbol: str, price: Decimal, quantity: int) -> str:
        if self._client is None:
            raise RuntimeError("Broker not connected")
        result = self._client.sell(symbol, float(price), quantity)  # type: ignore[union-attr]
        return str(result.get("entrust_no", ""))

    async def cancel(self, broker_order_id: str) -> bool:
        if self._client is None:
            raise RuntimeError("Broker not connected")
        try:
            self._client.cancel_entrust(broker_order_id)  # type: ignore[union-attr]
            return True
        except Exception:
            logger.exception("Failed to cancel order %s", broker_order_id)
            return False

    async def get_order_status(self, broker_order_id: str) -> dict[str, object]:
        if self._client is None:
            raise RuntimeError("Broker not connected")
        today_orders = self._client.today_entrusts  # type: ignore[union-attr]
        for order in today_orders:
            if str(order.get("entrust_no")) == broker_order_id:
                return order  # type: ignore[return-value]
        return {}

    async def get_balance(self) -> Decimal:
        if self._client is None:
            raise RuntimeError("Broker not connected")
        balance_info = self._client.balance  # type: ignore[union-attr]
        return Decimal(str(balance_info.get("可用金额", 0)))

    async def get_positions(self) -> list[dict[str, object]]:
        if self._client is None:
            raise RuntimeError("Broker not connected")
        return self._client.position  # type: ignore[union-attr, return-value]


class AShareGateway(TradingGateway):
    """A-share real trading gateway using a broker adapter.

    This gateway forwards orders to a real broker via the BrokerAdapter
    interface. Order status is tracked asynchronously — after submission,
    a background sync task should poll the broker for status updates.
    """

    def __init__(self, adapter: BrokerAdapter) -> None:
        self._adapter = adapter

    async def submit_order(self, db: AsyncSession, order: Order, account: Account) -> Order:
        """Forward order to broker for execution."""
        now = datetime.now(tz=timezone.utc)

        try:
            price = Decimal(str(order.price)) if order.price else Decimal("0")
            if order.side.value == "buy":
                broker_id = await self._adapter.buy(order.symbol, price, order.quantity)
            else:
                broker_id = await self._adapter.sell(order.symbol, price, order.quantity)

            validate_transition(order.status, OrderStatus.SUBMITTED)
            order = await order_crud.update(
                db,
                order,
                status=OrderStatus.SUBMITTED,
                broker_order_id=broker_id,
                submitted_at=now,
            )
            logger.info("Submitted order %s to broker, broker_id=%s", order.id, broker_id)

        except Exception as e:
            validate_transition(order.status, OrderStatus.REJECTED)
            order = await order_crud.update(
                db,
                order,
                status=OrderStatus.REJECTED,
                remark=f"Broker error: {e}",
            )
            logger.error("Order %s rejected by broker: %s", order.id, e)

        return order

    async def cancel_order(self, db: AsyncSession, order: Order) -> Order:
        """Request cancellation from broker."""
        if not order.broker_order_id:
            validate_transition(order.status, OrderStatus.CANCELLED)
            return await order_crud.update(
                db,
                order,
                status=OrderStatus.CANCELLED,
                cancelled_at=datetime.now(tz=timezone.utc),
            )

        success = await self._adapter.cancel(order.broker_order_id)
        if success:
            validate_transition(order.status, OrderStatus.CANCELLED)
            return await order_crud.update(
                db,
                order,
                status=OrderStatus.CANCELLED,
                cancelled_at=datetime.now(tz=timezone.utc),
            )

        raise ValueError(f"Broker failed to cancel order {order.broker_order_id}")

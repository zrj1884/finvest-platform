"""Tests for A-share gateway and broker adapter."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.order import OrderStatus
from app.services.trading.ashare_gateway import (
    AShareGateway,
    BrokerAdapter,
    EasyTraderAdapter,
)


class MockBrokerAdapter(BrokerAdapter):
    """Test broker adapter."""

    def __init__(self) -> None:
        self.connected = False
        self.orders: dict[str, dict[str, object]] = {}
        self._next_id = 1000

    async def connect(self, account_no: str, password: str) -> None:
        self.connected = True

    async def buy(self, symbol: str, price: Decimal, quantity: int) -> str:
        oid = str(self._next_id)
        self._next_id += 1
        self.orders[oid] = {"symbol": symbol, "price": price, "quantity": quantity, "side": "buy"}
        return oid

    async def sell(self, symbol: str, price: Decimal, quantity: int) -> str:
        oid = str(self._next_id)
        self._next_id += 1
        self.orders[oid] = {"symbol": symbol, "price": price, "quantity": quantity, "side": "sell"}
        return oid

    async def cancel(self, broker_order_id: str) -> bool:
        return broker_order_id in self.orders

    async def get_order_status(self, broker_order_id: str) -> dict[str, object]:
        return self.orders.get(broker_order_id, {})

    async def get_balance(self) -> Decimal:
        return Decimal("500000")

    async def get_positions(self) -> list[dict[str, object]]:
        return []


def _make_order(side: str = "buy", price: float = 10.0) -> MagicMock:
    order = MagicMock()
    order.id = uuid.uuid4()
    order.symbol = "600000"
    order.side = MagicMock()
    order.side.value = side
    order.price = price
    order.quantity = 100
    order.status = OrderStatus.PENDING
    order.broker_order_id = None
    return order


def _make_account() -> MagicMock:
    account = MagicMock()
    account.id = uuid.uuid4()
    account.is_simulated = False
    account.broker = "ths"
    return account


class TestMockBrokerAdapter:
    @pytest.mark.asyncio
    async def test_buy_returns_order_id(self) -> None:
        adapter = MockBrokerAdapter()
        oid = await adapter.buy("600000", Decimal("10"), 100)
        assert oid == "1000"
        assert "600000" in str(adapter.orders["1000"])

    @pytest.mark.asyncio
    async def test_sell_returns_order_id(self) -> None:
        adapter = MockBrokerAdapter()
        oid = await adapter.sell("600000", Decimal("10"), 100)
        assert oid is not None

    @pytest.mark.asyncio
    async def test_cancel_known_order(self) -> None:
        adapter = MockBrokerAdapter()
        oid = await adapter.buy("600000", Decimal("10"), 100)
        assert await adapter.cancel(oid) is True

    @pytest.mark.asyncio
    async def test_cancel_unknown_order(self) -> None:
        adapter = MockBrokerAdapter()
        assert await adapter.cancel("unknown") is False


class TestAShareGateway:
    @pytest.mark.asyncio
    async def test_submit_buy_order(self) -> None:
        adapter = MockBrokerAdapter()
        gateway = AShareGateway(adapter)
        db = AsyncMock()
        order = _make_order("buy")
        account = _make_account()

        with patch("app.services.trading.ashare_gateway.order_crud") as mock_crud:
            mock_crud.update = AsyncMock(return_value=order)
            await gateway.submit_order(db, order, account)
            mock_crud.update.assert_called_once()
            call_kwargs = mock_crud.update.call_args
            assert call_kwargs[1]["status"] == OrderStatus.SUBMITTED
            assert call_kwargs[1]["broker_order_id"] is not None

    @pytest.mark.asyncio
    async def test_submit_sell_order(self) -> None:
        adapter = MockBrokerAdapter()
        gateway = AShareGateway(adapter)
        db = AsyncMock()
        order = _make_order("sell")
        account = _make_account()

        with patch("app.services.trading.ashare_gateway.order_crud") as mock_crud:
            mock_crud.update = AsyncMock(return_value=order)
            await gateway.submit_order(db, order, account)
            call_kwargs = mock_crud.update.call_args
            assert call_kwargs[1]["status"] == OrderStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_broker_error_rejects_order(self) -> None:
        adapter = MockBrokerAdapter()
        # Make buy raise an error
        adapter.buy = AsyncMock(side_effect=RuntimeError("Connection lost"))  # type: ignore[method-assign]
        gateway = AShareGateway(adapter)
        db = AsyncMock()
        order = _make_order("buy")
        account = _make_account()

        with patch("app.services.trading.ashare_gateway.order_crud") as mock_crud:
            mock_crud.update = AsyncMock(return_value=order)
            await gateway.submit_order(db, order, account)
            call_kwargs = mock_crud.update.call_args
            assert call_kwargs[1]["status"] == OrderStatus.REJECTED
            assert "Connection lost" in call_kwargs[1]["remark"]

    @pytest.mark.asyncio
    async def test_cancel_with_broker_id(self) -> None:
        adapter = MockBrokerAdapter()
        # Pre-create an order in adapter
        oid = await adapter.buy("600000", Decimal("10"), 100)
        gateway = AShareGateway(adapter)
        db = AsyncMock()
        order = _make_order()
        order.broker_order_id = oid
        order.status = OrderStatus.SUBMITTED

        with patch("app.services.trading.ashare_gateway.order_crud") as mock_crud:
            mock_crud.update = AsyncMock(return_value=order)
            await gateway.cancel_order(db, order)
            call_kwargs = mock_crud.update.call_args
            assert call_kwargs[1]["status"] == OrderStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_without_broker_id(self) -> None:
        adapter = MockBrokerAdapter()
        gateway = AShareGateway(adapter)
        db = AsyncMock()
        order = _make_order()
        order.broker_order_id = None
        order.status = OrderStatus.SUBMITTED

        with patch("app.services.trading.ashare_gateway.order_crud") as mock_crud:
            mock_crud.update = AsyncMock(return_value=order)
            await gateway.cancel_order(db, order)
            call_kwargs = mock_crud.update.call_args
            assert call_kwargs[1]["status"] == OrderStatus.CANCELLED


class TestEasyTraderAdapter:
    def test_init(self) -> None:
        adapter = EasyTraderAdapter(broker="ths")
        assert adapter._broker == "ths"
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_connect_without_easytrader_raises(self) -> None:
        adapter = EasyTraderAdapter()
        with pytest.raises(RuntimeError, match="easytrader is not installed"):
            await adapter.connect("account", "password")

    @pytest.mark.asyncio
    async def test_buy_without_connect_raises(self) -> None:
        adapter = EasyTraderAdapter()
        with pytest.raises(RuntimeError, match="Broker not connected"):
            await adapter.buy("600000", Decimal("10"), 100)

    @pytest.mark.asyncio
    async def test_sell_without_connect_raises(self) -> None:
        adapter = EasyTraderAdapter()
        with pytest.raises(RuntimeError, match="Broker not connected"):
            await adapter.sell("600000", Decimal("10"), 100)

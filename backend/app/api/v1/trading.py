"""Trading (order management) API endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud import account as account_crud
from app.crud import order as order_crud
from app.crud import position as position_crud
from app.db.session import get_db
from app.models.order import OrderSide, OrderStatus, OrderType
from app.models.user import User
from app.schemas.trading import OrderCreate, OrderRead
from app.services.trading.gateway import get_gateway
from app.services.trading.matching_engine import get_latest_price, get_rules

router = APIRouter(prefix="/trading", tags=["trading"])


@router.post("/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def place_order(
    body: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """Place a new order."""
    # Load and verify account ownership
    account = await account_crud.get_by_id(db, body.account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    # Validate enums
    try:
        side = OrderSide(body.side)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid side: {body.side}")
    try:
        order_type = OrderType(body.order_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid order_type: {body.order_type}")

    # Limit order requires price
    if order_type == OrderType.LIMIT and body.price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limit orders require a price")

    # Validate via market rules
    market = account.market.value if hasattr(account.market, "value") else str(account.market)
    rules = get_rules(market)

    # Get available quantity for sell validation
    available_qty = 0
    if side == OrderSide.SELL:
        pos = await position_crud.get_by_symbol(db, account.id, body.symbol)
        available_qty = pos.available_quantity if pos else 0

    current_price = await get_latest_price(db, body.symbol, market)
    if current_price is None:
        current_price = body.price or Decimal("0")

    errors = rules.validate_order(
        side=side,
        order_type=order_type,
        quantity=body.quantity,
        price=body.price,
        current_price=current_price,
        available_quantity=available_qty,
    )
    if errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(errors))

    # Create order record
    order = await order_crud.create(
        db,
        account_id=account.id,
        symbol=body.symbol,
        side=side,
        order_type=order_type,
        quantity=body.quantity,
        price=float(body.price) if body.price is not None else None,
        remark=body.remark,
    )

    # Submit to gateway
    gateway = get_gateway(is_simulated=account.is_simulated, broker=account.broker)
    order = await gateway.submit_order(db, order)

    return OrderRead.model_validate(order)


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(
    account_id: uuid.UUID = Query(...),
    order_status: str | None = Query(None, alias="status"),
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OrderRead]:
    """List orders for an account."""
    account = await account_crud.get_by_id(db, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    status_filter = None
    if order_status is not None:
        try:
            status_filter = OrderStatus(order_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {order_status}",
            )

    orders = await order_crud.list_by_account(
        db, account_id, status=status_filter, symbol=symbol, limit=limit
    )
    return [OrderRead.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """Get a single order."""
    order = await order_crud.get_by_id(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Verify ownership
    account = await account_crud.get_by_id(db, order.account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return OrderRead.model_validate(order)


@router.delete("/orders/{order_id}", response_model=OrderRead)
async def cancel_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """Cancel an open order."""
    order = await order_crud.get_by_id(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Verify ownership
    account = await account_crud.get_by_id(db, order.account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in {order.status.value} status",
        )

    gateway = get_gateway(is_simulated=account.is_simulated, broker=account.broker)
    order = await gateway.cancel_order(db, order)

    return OrderRead.model_validate(order)

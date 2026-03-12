"""Account management API endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.crud import account as account_crud
from app.crud import position as position_crud
from app.db.session import get_db
from app.models.account import Market
from app.models.user import User
from app.schemas.trading import AccountCreate, AccountRead, AccountWithPositions, PositionRead

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    body: AccountCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountRead:
    """Create a new trading account (simulated or real)."""
    # Validate market enum
    try:
        Market(body.market)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid market: {body.market}. Must be one of: {[m.value for m in Market]}",
        )

    balance = body.balance if body.balance is not None else Decimal(str(settings.SIM_DEFAULT_BALANCE))

    account = await account_crud.create(
        db,
        user_id=user.id,
        name=body.name,
        market=body.market,
        is_simulated=body.is_simulated,
        balance=float(balance),
    )
    return AccountRead.model_validate(account)


@router.get("", response_model=list[AccountRead])
async def list_accounts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AccountRead]:
    """List all accounts for the current user."""
    accounts = await account_crud.list_by_user(db, user.id)
    return [AccountRead.model_validate(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountWithPositions)
async def get_account(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountWithPositions:
    """Get account detail with positions."""
    account = await account_crud.get_by_id(db, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return AccountWithPositions.model_validate(account)


@router.get("/{account_id}/positions", response_model=list[PositionRead])
async def list_positions(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PositionRead]:
    """List positions for an account."""
    account = await account_crud.get_by_id(db, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    positions = await position_crud.list_by_account(db, account_id)
    return [PositionRead.model_validate(p) for p in positions]


@router.post("/{account_id}/reset", response_model=AccountRead)
async def reset_account(
    account_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountRead:
    """Reset a simulated account — clear positions/orders and restore balance."""
    account = await account_crud.get_by_id(db, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if not account.is_simulated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset a real trading account",
        )

    balance = Decimal(str(settings.SIM_DEFAULT_BALANCE))
    account = await account_crud.reset(db, account, balance)
    return AccountRead.model_validate(account)

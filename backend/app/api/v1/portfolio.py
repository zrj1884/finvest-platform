"""Portfolio / asset dashboard API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.portfolio import (
    AssetOverview,
    CashFlowItem,
    HoldingItem,
    MarketAllocation,
    PerformancePoint,
)
from app.services.trading import asset_tracker
from app.services.trading.snapshot import get_performance_curve

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/overview", response_model=AssetOverview)
async def get_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AssetOverview:
    """Get total asset overview across all accounts."""
    return await asset_tracker.get_overview(db, user.id)


@router.get("/allocation", response_model=list[MarketAllocation])
async def get_allocation(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MarketAllocation]:
    """Get asset allocation breakdown by market."""
    return await asset_tracker.get_allocation(db, user.id)


@router.get("/holdings", response_model=list[HoldingItem])
async def get_holdings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HoldingItem]:
    """Get all holdings across accounts."""
    return await asset_tracker.get_holdings(db, user.id)


@router.get("/performance", response_model=list[PerformancePoint])
async def get_performance(
    days: int = Query(90, ge=7, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PerformancePoint]:
    """Get daily portfolio value curve."""
    return await get_performance_curve(db, user.id, days=days)


@router.get("/cash-flows", response_model=list[CashFlowItem])
async def get_cash_flows(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CashFlowItem]:
    """Get recent cash flow events."""
    return await asset_tracker.get_cash_flows(db, user.id, limit=limit)

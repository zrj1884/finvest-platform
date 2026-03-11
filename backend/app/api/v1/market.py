"""Market data query API endpoints."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_db
from app.models.market_data import BondDaily, FundNav, NewsArticle, StockDaily

router = APIRouter(prefix="/market", tags=["market"])

# Cache TTL in seconds
CACHE_TTL_SNAPSHOT = 60  # 1 min for realtime-ish data
CACHE_TTL_HISTORY = 3600  # 1 hour for historical data
CACHE_TTL_NEWS = 300  # 5 min for news


# --- Stock endpoints ---


@router.get("/stocks/{symbol}/daily")
async def get_stock_daily(
    symbol: str,
    market: str = Query("a_share", description="Market: a_share, us_stock, hk_stock"),
    start_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get daily OHLCV data for a stock symbol."""
    cache_key = f"stock:daily:{market}:{symbol}:{start_date}:{end_date}:{limit}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    stmt = (
        select(StockDaily)
        .where(StockDaily.symbol == symbol, StockDaily.market == market)
        .order_by(StockDaily.time.desc())
        .limit(limit)
    )
    if start_date:
        stmt = stmt.where(StockDaily.time >= start_date)
    if end_date:
        stmt = stmt.where(StockDaily.time <= end_date)

    result = await db.execute(stmt)
    rows = result.scalars().all()
    data = [_stock_to_dict(r) for r in rows]

    await _set_cache(cache_key, data, CACHE_TTL_HISTORY)
    return data


@router.get("/stocks/{symbol}/kline")
async def get_stock_kline(
    symbol: str,
    market: str = Query("a_share"),
    period: str = Query("daily", description="Period: daily, weekly, monthly"),
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(200, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
) -> list[list[Any]]:
    """Get K-line (candlestick) data in [time, open, close, low, high, volume] format.

    Suitable for ECharts candlestick chart.
    """
    cache_key = f"stock:kline:{market}:{symbol}:{period}:{start_date}:{end_date}:{limit}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    if period == "daily":
        stmt = (
            select(StockDaily)
            .where(StockDaily.symbol == symbol, StockDaily.market == market)
            .order_by(StockDaily.time.asc())
            .limit(limit)
        )
        if start_date:
            stmt = stmt.where(StockDaily.time >= start_date)
        if end_date:
            stmt = stmt.where(StockDaily.time <= end_date)

        result = await db.execute(stmt)
        rows = result.scalars().all()
        data: list[list[Any]] = [
            [r.time.isoformat(), float(r.open), float(r.close), float(r.low), float(r.high), r.volume]
            for r in rows
        ]
    elif period in ("weekly", "monthly"):
        view = "stock_weekly" if period == "weekly" else "stock_monthly"
        query = text(f"""
            SELECT bucket, open, close, low, high, volume
            FROM {view}
            WHERE symbol = :symbol
            ORDER BY bucket ASC
            LIMIT :limit
        """)
        result = await db.execute(query, {"symbol": symbol, "limit": limit})
        data = [
            [row.bucket.isoformat(), float(row.open), float(row.close), float(row.low), float(row.high), int(row.volume)]
            for row in result.fetchall()
        ]
    else:
        data = []

    await _set_cache(cache_key, data, CACHE_TTL_HISTORY)
    return data


# --- Fund endpoints ---


@router.get("/funds/{symbol}/nav")
async def get_fund_nav(
    symbol: str,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get fund NAV history."""
    cache_key = f"fund:nav:{symbol}:{start_date}:{end_date}:{limit}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    stmt = (
        select(FundNav)
        .where(FundNav.symbol == symbol)
        .order_by(FundNav.time.desc())
        .limit(limit)
    )
    if start_date:
        stmt = stmt.where(FundNav.time >= start_date)
    if end_date:
        stmt = stmt.where(FundNav.time <= end_date)

    result = await db.execute(stmt)
    rows = result.scalars().all()
    data = [_fund_to_dict(r) for r in rows]

    await _set_cache(cache_key, data, CACHE_TTL_HISTORY)
    return data


# --- Bond endpoints ---


@router.get("/bonds/{symbol}/daily")
async def get_bond_daily(
    symbol: str,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get bond daily data."""
    cache_key = f"bond:daily:{symbol}:{start_date}:{end_date}:{limit}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    stmt = (
        select(BondDaily)
        .where(BondDaily.symbol == symbol)
        .order_by(BondDaily.time.desc())
        .limit(limit)
    )
    if start_date:
        stmt = stmt.where(BondDaily.time >= start_date)
    if end_date:
        stmt = stmt.where(BondDaily.time <= end_date)

    result = await db.execute(stmt)
    rows = result.scalars().all()
    data = [_bond_to_dict(r) for r in rows]

    await _set_cache(cache_key, data, CACHE_TTL_HISTORY)
    return data


# --- News endpoints ---


@router.get("/news")
async def get_news(
    source: str | None = Query(None, description="Filter by source"),
    symbol: str | None = Query(None, description="Filter by related symbol"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get latest financial news."""
    cache_key = f"news:{source}:{symbol}:{limit}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    stmt = select(NewsArticle).order_by(NewsArticle.time.desc()).limit(limit)
    if source:
        stmt = stmt.where(NewsArticle.source == source)
    if symbol:
        stmt = stmt.where(NewsArticle.symbols.contains(symbol))

    result = await db.execute(stmt)
    rows = result.scalars().all()
    data = [_news_to_dict(r) for r in rows]

    await _set_cache(cache_key, data, CACHE_TTL_NEWS)
    return data


# --- Helpers ---


def _stock_to_dict(r: StockDaily) -> dict[str, Any]:
    return {
        "time": r.time.isoformat(),
        "symbol": r.symbol,
        "name": r.name,
        "market": r.market,
        "open": float(r.open),
        "high": float(r.high),
        "low": float(r.low),
        "close": float(r.close),
        "volume": r.volume,
        "amount": float(r.amount) if r.amount else None,
        "turnover": float(r.turnover) if r.turnover else None,
        "change_pct": float(r.change_pct) if r.change_pct else None,
        "amplitude": float(r.amplitude) if r.amplitude else None,
    }


def _fund_to_dict(r: FundNav) -> dict[str, Any]:
    return {
        "time": r.time.isoformat(),
        "symbol": r.symbol,
        "name": r.name,
        "nav": float(r.nav),
        "accumulated_nav": float(r.accumulated_nav) if r.accumulated_nav else None,
        "daily_return": float(r.daily_return) if r.daily_return else None,
    }


def _bond_to_dict(r: BondDaily) -> dict[str, Any]:
    return {
        "time": r.time.isoformat(),
        "symbol": r.symbol,
        "name": r.name,
        "bond_type": r.bond_type,
        "close": float(r.close),
        "volume": r.volume,
        "amount": float(r.amount) if r.amount else None,
        "ytm": float(r.ytm) if r.ytm else None,
        "change_pct": float(r.change_pct) if r.change_pct else None,
    }


def _news_to_dict(r: NewsArticle) -> dict[str, Any]:
    return {
        "time": r.time.isoformat(),
        "source": r.source,
        "url": r.url,
        "title": r.title,
        "content": r.content,
        "symbols": r.symbols,
        "sentiment_score": float(r.sentiment_score) if r.sentiment_score else None,
    }


async def _get_cache(key: str) -> Any:
    """Get value from Redis cache."""
    try:
        redis = await get_redis()
        data = await redis.get(f"cache:{key}")
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


async def _set_cache(key: str, value: Any, ttl: int) -> None:
    """Set value in Redis cache with TTL."""
    try:
        redis = await get_redis()
        await redis.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
    except Exception:
        pass

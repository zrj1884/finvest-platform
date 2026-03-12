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


# --- Symbol search (autocomplete) ---


@router.get("/symbols/search")
async def search_symbols(
    q: str = Query(..., min_length=1, max_length=20, description="Search query"),
    market: str = Query("a_share", description="Market: a_share, us_stock, hk_stock, fund, bond"),
    limit: int = Query(10, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, str]]:
    """Search symbols by code or name prefix for autocomplete."""
    pattern = f"%{q}%"
    if market in ("a_share", "us_stock", "hk_stock"):
        stmt = text("""
            SELECT DISTINCT ON (symbol) symbol, name
            FROM stock_daily
            WHERE market = :market AND (symbol ILIKE :pattern OR name ILIKE :pattern)
            ORDER BY symbol, date DESC
            LIMIT :lim
        """)
    elif market == "fund":
        stmt = text("""
            SELECT DISTINCT ON (symbol) symbol, name
            FROM fund_nav
            WHERE symbol ILIKE :pattern OR name ILIKE :pattern
            ORDER BY symbol, date DESC
            LIMIT :lim
        """)
    elif market == "bond":
        stmt = text("""
            SELECT DISTINCT ON (symbol) symbol, name
            FROM bond_daily
            WHERE symbol ILIKE :pattern OR name ILIKE :pattern
            ORDER BY symbol, date DESC
            LIMIT :lim
        """)
    else:
        return []
    result = await db.execute(stmt, {"market": market, "pattern": pattern, "lim": limit})
    return [{"symbol": row[0], "name": row[1] or ""} for row in result.fetchall()]


# --- Stock list (snapshot) ---


@router.get("/stocks/snapshot")
async def list_stock_snapshot(
    market: str = Query("a_share", description="Market: a_share, us_stock, hk_stock"),
    search: str | None = Query(None, description="Search by symbol or name"),
    sort_by: str = Query("symbol", description="Sort field: symbol, name, close, change_pct, volume, time"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get the latest snapshot for each symbol in the market, with pagination and sorting."""
    cache_key = f"stock:snapshot:{market}:{search}:{sort_by}:{sort_order}:{page}:{page_size}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    # Use DISTINCT ON to get the latest row per symbol
    allowed_sort = {"symbol", "name", "close", "change_pct", "volume", "time"}
    col = sort_by if sort_by in allowed_sort else "symbol"
    order = "DESC" if sort_order == "desc" else "ASC"
    # Null handling for change_pct
    null_pos = "NULLS LAST" if order == "ASC" else "NULLS FIRST"

    search_clause = ""
    params: dict[str, Any] = {"market": market, "limit": page_size, "offset": (page - 1) * page_size}
    if search:
        search_clause = "AND (s.symbol ILIKE :search OR s.name ILIKE :search)"
        params["search"] = f"%{search}%"

    query = text(f"""
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol
                    ORDER BY (CASE WHEN change_pct IS NOT NULL THEN 0 ELSE 1 END), time DESC
                ) AS rn
            FROM stock_daily
            WHERE market = :market AND name IS NOT NULL AND name <> ''
        ),
        latest AS (
            SELECT * FROM ranked WHERE rn = 1
        )
        SELECT *, COUNT(*) OVER() AS total_count
        FROM latest s
        WHERE 1=1 {search_clause}
        ORDER BY {col} {order} {null_pos}
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    total = rows[0].total_count if rows else 0
    items = []
    for r in rows:
        items.append({
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
        })

    data = {"items": items, "total": total, "page": page, "page_size": page_size}
    await _set_cache(cache_key, data, CACHE_TTL_SNAPSHOT)
    return data


# --- Stock detail endpoints ---


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
        # Subquery: pick most recent `limit` rows, then return in ASC order for charting
        stmt = (
            select(StockDaily)
            .where(StockDaily.symbol == symbol, StockDaily.market == market)
        )
        if start_date:
            stmt = stmt.where(StockDaily.time >= start_date)
        if end_date:
            stmt = stmt.where(StockDaily.time <= end_date)
        stmt = stmt.order_by(StockDaily.time.desc()).limit(limit)

        result = await db.execute(stmt)
        rows = list(reversed(result.scalars().all()))
        data: list[list[Any]] = [
            [r.time.isoformat(), float(r.open), float(r.close), float(r.low), float(r.high), r.volume]
            for r in rows
        ]
    elif period in ("weekly", "monthly"):
        view = "stock_weekly" if period == "weekly" else "stock_monthly"
        query = text(f"""
            SELECT time, open, close, low, high, volume
            FROM {view}
            WHERE symbol = :symbol AND market = :market
            ORDER BY time DESC
            LIMIT :limit
        """)
        result = await db.execute(query, {"symbol": symbol, "market": market, "limit": limit})
        raw_rows = list(reversed(result.fetchall()))
        data = [
            [row.time.isoformat(), float(row.open), float(row.close), float(row.low), float(row.high), int(row.volume)]
            for row in raw_rows
        ]
    else:
        data = []

    await _set_cache(cache_key, data, CACHE_TTL_HISTORY)
    return data


# --- Fund list (snapshot) ---


@router.get("/funds/snapshot")
async def list_fund_snapshot(
    search: str | None = Query(None, description="Search by symbol or name"),
    sort_by: str = Query("symbol", description="Sort field: symbol, name, nav, accumulated_nav, daily_return, time"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get the latest snapshot for each fund, with pagination and sorting."""
    cache_key = f"fund:snapshot:{search}:{sort_by}:{sort_order}:{page}:{page_size}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    allowed_sort = {"symbol", "name", "nav", "accumulated_nav", "daily_return", "time"}
    col = sort_by if sort_by in allowed_sort else "symbol"
    order = "DESC" if sort_order == "desc" else "ASC"
    null_pos = "NULLS LAST" if order == "ASC" else "NULLS FIRST"

    search_clause = ""
    params: dict[str, Any] = {"limit": page_size, "offset": (page - 1) * page_size}
    if search:
        search_clause = "AND (s.symbol ILIKE :search OR s.name ILIKE :search)"
        params["search"] = f"%{search}%"

    query = text(f"""
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol
                    ORDER BY (CASE WHEN daily_return IS NOT NULL THEN 0 ELSE 1 END), time DESC
                ) AS rn
            FROM fund_nav
            WHERE name IS NOT NULL AND name <> ''
        ),
        latest AS (
            SELECT * FROM ranked WHERE rn = 1
        )
        SELECT *, COUNT(*) OVER() AS total_count
        FROM latest s
        WHERE 1=1 {search_clause}
        ORDER BY {col} {order} {null_pos}
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    total = rows[0].total_count if rows else 0
    items = []
    for r in rows:
        items.append({
            "time": r.time.isoformat(),
            "symbol": r.symbol,
            "name": r.name,
            "nav": float(r.nav),
            "accumulated_nav": float(r.accumulated_nav) if r.accumulated_nav else None,
            "daily_return": float(r.daily_return) if r.daily_return else None,
        })

    data = {"items": items, "total": total, "page": page, "page_size": page_size}
    await _set_cache(cache_key, data, CACHE_TTL_SNAPSHOT)
    return data


# --- Fund detail endpoints ---


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


# --- Bond list (snapshot) ---


@router.get("/bonds/snapshot")
async def list_bond_snapshot(
    search: str | None = Query(None, description="Search by symbol or name"),
    sort_by: str = Query("symbol", description="Sort field: symbol, name, close, change_pct, volume, time"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get the latest snapshot for each bond, with pagination and sorting."""
    cache_key = f"bond:snapshot:{search}:{sort_by}:{sort_order}:{page}:{page_size}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    allowed_sort = {"symbol", "name", "close", "change_pct", "volume", "time"}
    col = sort_by if sort_by in allowed_sort else "symbol"
    order = "DESC" if sort_order == "desc" else "ASC"
    null_pos = "NULLS LAST" if order == "ASC" else "NULLS FIRST"

    search_clause = ""
    params: dict[str, Any] = {"limit": page_size, "offset": (page - 1) * page_size}
    if search:
        search_clause = "AND (s.symbol ILIKE :search OR s.name ILIKE :search)"
        params["search"] = f"%{search}%"

    query = text(f"""
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol
                    ORDER BY (CASE WHEN change_pct IS NOT NULL THEN 0 ELSE 1 END), time DESC
                ) AS rn
            FROM bond_daily
        ),
        latest AS (
            SELECT * FROM ranked WHERE rn = 1
        )
        SELECT *, COUNT(*) OVER() AS total_count
        FROM latest s
        WHERE 1=1 {search_clause}
        ORDER BY {col} {order} {null_pos}
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    total = rows[0].total_count if rows else 0
    items = []
    for r in rows:
        items.append({
            "time": r.time.isoformat(),
            "symbol": r.symbol,
            "name": r.name,
            "bond_type": r.bond_type,
            "close": float(r.close),
            "volume": r.volume,
            "amount": float(r.amount) if r.amount else None,
            "ytm": float(r.ytm) if r.ytm else None,
            "change_pct": float(r.change_pct) if r.change_pct else None,
        })

    data = {"items": items, "total": total, "page": page, "page_size": page_size}
    await _set_cache(cache_key, data, CACHE_TTL_SNAPSHOT)
    return data


# --- Bond detail endpoints ---


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
    keyword: str | None = Query(None, description="Fuzzy search in title and content"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get latest financial news."""
    cache_key = f"news:{source}:{symbol}:{keyword}:{limit}"
    cached = await _get_cache(cache_key)
    if cached is not None:
        return cached  # type: ignore[no-any-return]

    stmt = select(NewsArticle).order_by(NewsArticle.time.desc()).limit(limit)
    if source:
        stmt = stmt.where(NewsArticle.source == source)
    if symbol:
        stmt = stmt.where(NewsArticle.symbols.contains(symbol))
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            NewsArticle.title.ilike(pattern) | NewsArticle.content.ilike(pattern)
        )

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

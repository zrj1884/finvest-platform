"""Base collector interface for market data sources."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for market data collectors.

    Each collector fetches data from a specific source (AKShare, yfinance, etc.)
    and returns standardised pandas DataFrames that map to our TimescaleDB models.
    """

    @abstractmethod
    async def fetch_daily(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Fetch daily OHLCV data for a symbol.

        Returns a DataFrame with columns matching the target model:
            time, symbol, name, market, open, high, low, close,
            volume, amount, turnover, change_pct, amplitude
        """
        ...

    @staticmethod
    def _ensure_tz_aware(dt: datetime | pd.Timestamp) -> datetime:
        """Ensure a datetime is timezone-aware (UTC if naive)."""
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """Convert a value to float, returning None for NaN/None."""
        if value is None:
            return None
        try:
            f = float(value)
            if pd.isna(f):
                return None
            return f
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        """Convert a value to int, returning 0 for NaN/None."""
        if value is None:
            return 0
        try:
            f = float(value)
            if pd.isna(f):
                return 0
            return int(f)
        except (TypeError, ValueError):
            return 0

    async def bulk_upsert(
        self,
        db: AsyncSession,
        model: Any,
        records: list[dict[str, Any]],
    ) -> int:
        """Bulk upsert records into a TimescaleDB hypertable.

        Uses PostgreSQL ON CONFLICT DO UPDATE for idempotent writes.
        Returns the number of rows upserted.
        """
        if not records:
            return 0

        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(model).values(records)

        # Build the SET clause for ON CONFLICT (all columns except PKs)
        pk_cols = {c.name for c in model.__table__.primary_key.columns}
        update_cols = {c.name: stmt.excluded[c.name] for c in model.__table__.columns if c.name not in pk_cols}

        stmt = stmt.on_conflict_do_update(
            index_elements=list(pk_cols),
            set_=update_cols,
        )
        await db.execute(stmt)
        return len(records)

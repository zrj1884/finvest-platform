"""News collector orchestrator — fetches, deduplicates, and stores news."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_data import NewsArticle
from app.services.news.base import BaseScraper, NewsItem
from app.services.news.eastmoney import EastMoneyScraper
from app.services.news.sina_finance import SinaFinanceScraper
from app.services.news.xueqiu import XueqiuScraper

logger = logging.getLogger(__name__)


class NewsCollector:
    """Orchestrates news collection from multiple sources."""

    def __init__(self) -> None:
        self.scrapers: list[BaseScraper] = [
            SinaFinanceScraper(),
            EastMoneyScraper(),
            XueqiuScraper(),
        ]

    async def collect_all(self, db: AsyncSession, limit_per_source: int = 50) -> dict[str, int]:
        """Fetch news from all sources, deduplicate, and store.

        Returns:
            Dict mapping source name to number of articles stored.
        """
        results: dict[str, int] = {}

        for scraper in self.scrapers:
            try:
                items = await scraper.fetch_latest(limit=limit_per_source)
                if not items:
                    results[scraper.source_name] = 0
                    continue

                # Deduplicate within batch by URL
                seen: set[str] = set()
                unique_items: list[NewsItem] = []
                for item in items:
                    if item.dedup_key not in seen:
                        seen.add(item.dedup_key)
                        unique_items.append(item)

                count = await self._store(db, unique_items)
                results[scraper.source_name] = count
                logger.info("Stored %d articles from %s", count, scraper.source_name)

            except Exception:
                logger.exception("Failed to collect from %s", scraper.source_name)
                results[scraper.source_name] = 0

        return results

    async def collect_source(
        self, db: AsyncSession, source_name: str, limit: int = 50
    ) -> int:
        """Collect news from a specific source.

        Args:
            db: Database session.
            source_name: Source identifier (e.g. "sina_finance").
            limit: Maximum articles to fetch.

        Returns:
            Number of articles stored.
        """
        scraper = next((s for s in self.scrapers if s.source_name == source_name), None)
        if scraper is None:
            raise ValueError(f"Unknown source: {source_name}")

        items = await scraper.fetch_latest(limit=limit)
        if not items:
            return 0

        return await self._store(db, items)

    async def _store(self, db: AsyncSession, items: list[NewsItem]) -> int:
        """Upsert news items into the database.

        TimescaleDB requires the partitioning column (time) in every unique
        index, so we cannot create a unique constraint on (source, url) alone.
        Instead we delete existing rows that share the same (source, url) as
        the incoming batch, then insert fresh rows.
        """
        if not items:
            return 0

        records: list[dict[str, Any]] = [item.to_dict() for item in items]

        # Delete old rows with matching (source, url) to prevent duplicates
        url_pairs = [(r["source"], r["url"]) for r in records]
        del_stmt = delete(NewsArticle).where(
            tuple_(NewsArticle.source, NewsArticle.url).in_(url_pairs)
        )
        await db.execute(del_stmt)

        # Insert new rows
        stmt = pg_insert(NewsArticle).values(records)
        # If two items in the same batch happen to share (time, source, url),
        # do nothing on conflict with the existing PK.
        stmt = stmt.on_conflict_do_nothing()
        await db.execute(stmt)
        await db.commit()
        return len(records)

"""Sina Finance (新浪财经) news scraper."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.services.news.base import BaseScraper, NewsItem

logger = logging.getLogger(__name__)

# Sina Finance RSS-like API endpoints
SINA_FINANCE_API = "https://feed.mix.sina.com.cn/api/roll/get"


class SinaFinanceScraper(BaseScraper):
    """Scraper for Sina Finance news."""

    source_name = "sina_finance"

    async def fetch_latest(self, limit: int = 50) -> list[NewsItem]:
        """Fetch latest financial news from Sina Finance API."""
        items: list[NewsItem] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    SINA_FINANCE_API,
                    params={
                        "pageid": "153",  # 财经频道
                        "lid": "2516",    # 全部财经
                        "num": str(limit),
                        "versionNumber": "1.2.4",
                    },
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                data = resp.json()

            result = data.get("result", {})
            articles = result.get("data", [])

            for article in articles:
                title = article.get("title", "").strip()
                url = article.get("url", "").strip()
                if not title or not url:
                    continue

                # Parse timestamp
                ctime = article.get("ctime", "")
                try:
                    time = datetime.strptime(ctime, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    time = datetime.now(tz=timezone.utc)

                content = self.clean_html(article.get("summary", "") or article.get("intro", "") or "")

                items.append(NewsItem(
                    title=title,
                    url=url,
                    source=self.source_name,
                    time=time,
                    content=self.truncate(content) if content else None,
                ))

        except Exception:
            logger.exception("Failed to fetch Sina Finance news")

        return items

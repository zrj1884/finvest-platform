"""East Money (东方财富) news scraper."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.services.news.base import BaseScraper, NewsItem

logger = logging.getLogger(__name__)

# East Money news API
EASTMONEY_API = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"


class EastMoneyScraper(BaseScraper):
    """Scraper for East Money financial news."""

    source_name = "eastmoney"

    async def fetch_latest(self, limit: int = 50) -> list[NewsItem]:
        """Fetch latest financial news from East Money."""
        items: list[NewsItem] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    EASTMONEY_API,
                    params={
                        "client": "web",
                        "biz": "web_home_channel",
                        "column": "重大事件",
                        "order": "1",
                        "needInteractData": "0",
                        "page_index": "1",
                        "page_size": str(limit),
                    },
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                data = resp.json()

            articles = data.get("data", {}).get("list", [])

            for article in articles:
                title = article.get("title", "").strip()
                url = article.get("url", "").strip()
                if not title or not url:
                    continue

                # Parse timestamp
                showtime = article.get("showtime", "")
                try:
                    time = datetime.strptime(showtime, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    time = datetime.now(tz=timezone.utc)

                content = article.get("digest", "")

                items.append(NewsItem(
                    title=title,
                    url=url,
                    source=self.source_name,
                    time=time,
                    content=self.truncate(content) if content else None,
                ))

        except Exception:
            logger.exception("Failed to fetch East Money news")

        return items

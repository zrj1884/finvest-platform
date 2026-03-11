"""Xueqiu (雪球) sentiment data scraper."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.services.news.base import BaseScraper, NewsItem

logger = logging.getLogger(__name__)

# Xueqiu hot articles API
XUEQIU_API = "https://xueqiu.com/statuses/hot/listV2.json"


class XueqiuScraper(BaseScraper):
    """Scraper for Xueqiu sentiment / hot discussions."""

    source_name = "xueqiu"

    async def fetch_latest(self, limit: int = 50) -> list[NewsItem]:
        """Fetch latest hot discussions from Xueqiu."""
        items: list[NewsItem] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Xueqiu requires a cookie to access API
                # First visit the homepage to get cookie
                await client.get(
                    "https://xueqiu.com/",
                    headers={"User-Agent": "Mozilla/5.0"},
                )

                resp = await client.get(
                    XUEQIU_API,
                    params={
                        "since_id": "-1",
                        "max_id": "-1",
                        "size": str(limit),
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://xueqiu.com/",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            articles = data.get("items", [])

            for item in articles:
                article = item.get("original_status", {}) or item
                title = article.get("title", "") or article.get("description", "")
                title = self.clean_html(title)[:200] if title else ""
                if not title:
                    continue

                article_id = article.get("id", "")
                user_id = article.get("user_id", article.get("user", {}).get("id", ""))
                url = f"https://xueqiu.com/{user_id}/{article_id}" if article_id else ""
                if not url:
                    continue

                # Parse timestamp (milliseconds)
                created_at = article.get("created_at", 0)
                if created_at:
                    time = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
                else:
                    time = datetime.now(tz=timezone.utc)

                content = self.clean_html(article.get("text", "") or "")

                # Extract mentioned stock symbols
                symbols_list: list[str] = []
                for tag in article.get("stock_tags", []) or []:
                    code = tag.get("code", "")
                    if code:
                        symbols_list.append(code)

                items.append(NewsItem(
                    title=title,
                    url=url,
                    source=self.source_name,
                    time=time,
                    content=self.truncate(content) if content else None,
                    symbols=",".join(symbols_list) if symbols_list else None,
                ))

        except Exception:
            logger.exception("Failed to fetch Xueqiu data")

        return items

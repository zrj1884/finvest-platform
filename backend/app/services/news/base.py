"""Base scraper interface for news sources."""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class NewsItem:
    """Standardised news article data."""

    __slots__ = ("title", "url", "source", "time", "content", "symbols", "sentiment_score")

    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        time: datetime,
        content: str | None = None,
        symbols: str | None = None,
        sentiment_score: float | None = None,
    ) -> None:
        self.title = title
        self.url = url
        self.source = source
        self.time = time
        self.content = content
        self.symbols = symbols
        self.sentiment_score = sentiment_score

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "time": self.time,
            "content": self.content,
            "symbols": self.symbols,
            "sentiment_score": self.sentiment_score,
        }

    @property
    def dedup_key(self) -> str:
        """Generate a deduplication key from URL."""
        return hashlib.md5(self.url.encode()).hexdigest()


class BaseScraper(ABC):
    """Abstract base class for news scrapers."""

    source_name: str = ""

    @abstractmethod
    async def fetch_latest(self, limit: int = 50) -> list[NewsItem]:
        """Fetch latest news articles from this source.

        Args:
            limit: Maximum number of articles to return.

        Returns:
            List of NewsItem objects.
        """
        ...

    @staticmethod
    def clean_html(html: str) -> str:
        """Strip HTML tags from content."""
        return re.sub(r"<[^>]+>", "", html).strip()

    @staticmethod
    def truncate(text: str, max_length: int = 5000) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

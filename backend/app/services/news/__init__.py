"""News and sentiment collection services."""

from app.services.news.base import BaseScraper
from app.services.news.collector import NewsCollector

__all__ = ["BaseScraper", "NewsCollector"]

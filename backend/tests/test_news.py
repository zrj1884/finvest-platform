"""Tests for news and sentiment collection services."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.news.base import BaseScraper, NewsItem
from app.services.news.collector import NewsCollector
from app.services.news.eastmoney import EastMoneyScraper
from app.services.news.sina_finance import SinaFinanceScraper
from app.services.news.xueqiu import XueqiuScraper


# --- NewsItem tests ---

class TestNewsItem:
    def test_to_dict(self) -> None:
        item = NewsItem(
            title="Test",
            url="https://example.com/1",
            source="test",
            time=datetime(2025, 1, 1, tzinfo=timezone.utc),
            content="Hello",
        )
        d = item.to_dict()
        assert d["title"] == "Test"
        assert d["source"] == "test"

    def test_dedup_key(self) -> None:
        item1 = NewsItem(title="A", url="https://example.com/1", source="test", time=datetime.now(tz=timezone.utc))
        item2 = NewsItem(title="B", url="https://example.com/1", source="test", time=datetime.now(tz=timezone.utc))
        item3 = NewsItem(title="A", url="https://example.com/2", source="test", time=datetime.now(tz=timezone.utc))

        # Same URL -> same dedup key
        assert item1.dedup_key == item2.dedup_key
        # Different URL -> different dedup key
        assert item1.dedup_key != item3.dedup_key


class TestBaseScraperHelpers:
    def test_clean_html(self) -> None:
        assert BaseScraper.clean_html("<p>Hello <b>world</b></p>") == "Hello world"
        assert BaseScraper.clean_html("no tags") == "no tags"

    def test_truncate(self) -> None:
        assert BaseScraper.truncate("short", 100) == "short"
        assert BaseScraper.truncate("abcdef", 3) == "abc..."


# --- SinaFinanceScraper tests ---

class TestSinaFinanceScraper:
    @pytest.mark.asyncio
    async def test_fetch_latest(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "data": [
                    {
                        "title": "A股市场大涨",
                        "url": "https://finance.sina.com.cn/1",
                        "ctime": "2025-01-02 10:00:00",
                        "summary": "<p>市场利好消息</p>",
                    },
                    {
                        "title": "央行降息",
                        "url": "https://finance.sina.com.cn/2",
                        "ctime": "2025-01-02 11:00:00",
                        "intro": "降息50个基点",
                    },
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.news.sina_finance.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            scraper = SinaFinanceScraper()
            items = await scraper.fetch_latest(limit=10)

        assert len(items) == 2
        assert items[0].title == "A股市场大涨"
        assert items[0].source == "sina_finance"
        assert items[0].content == "市场利好消息"  # HTML stripped

    @pytest.mark.asyncio
    async def test_fetch_latest_error(self) -> None:
        with patch("app.services.news.sina_finance.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            scraper = SinaFinanceScraper()
            items = await scraper.fetch_latest()

        assert items == []


# --- EastMoneyScraper tests ---

class TestEastMoneyScraper:
    @pytest.mark.asyncio
    async def test_fetch_latest(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "list": [
                    {
                        "title": "重要经济数据发布",
                        "url": "https://finance.eastmoney.com/1",
                        "showtime": "2025-01-02 09:00:00",
                        "digest": "GDP 增长 5.2%",
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.news.eastmoney.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            scraper = EastMoneyScraper()
            items = await scraper.fetch_latest(limit=10)

        assert len(items) == 1
        assert items[0].source == "eastmoney"


# --- XueqiuScraper tests ---

class TestXueqiuScraper:
    @pytest.mark.asyncio
    async def test_fetch_latest(self) -> None:
        homepage_response = MagicMock()
        homepage_response.raise_for_status = MagicMock()

        api_response = MagicMock()
        api_response.json.return_value = {
            "items": [
                {
                    "original_status": {
                        "id": 123456,
                        "user_id": 789,
                        "title": "茅台投资分析",
                        "text": "<p>看好白酒板块</p>",
                        "created_at": 1735776000000,  # 2025-01-02 00:00:00 UTC
                        "stock_tags": [{"code": "SH600519"}],
                    }
                }
            ]
        }
        api_response.raise_for_status = MagicMock()

        with patch("app.services.news.xueqiu.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[homepage_response, api_response])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            scraper = XueqiuScraper()
            items = await scraper.fetch_latest(limit=10)

        assert len(items) == 1
        assert items[0].source == "xueqiu"
        assert items[0].symbols == "SH600519"
        assert "看好白酒板块" in (items[0].content or "")


# --- NewsCollector orchestrator tests ---

class TestNewsCollector:
    def test_init_has_all_scrapers(self) -> None:
        collector = NewsCollector()
        source_names = [s.source_name for s in collector.scrapers]
        assert "sina_finance" in source_names
        assert "eastmoney" in source_names
        assert "xueqiu" in source_names

    @pytest.mark.asyncio
    async def test_collect_source_invalid(self) -> None:
        collector = NewsCollector()
        mock_db = AsyncMock()
        with pytest.raises(ValueError, match="Unknown source"):
            await collector.collect_source(mock_db, "nonexistent")


# --- Scheduler tests ---

class TestScheduler:
    def test_setup_scheduler(self) -> None:
        from app.services.scheduler import setup_scheduler

        sched = setup_scheduler()
        job_ids = [job.id for job in sched.get_jobs()]
        assert "collect_news" in job_ids
        assert "collect_a_share_daily" in job_ids
        assert "collect_us_stock_daily" in job_ids

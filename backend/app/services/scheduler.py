"""Task scheduler for periodic data collection jobs."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def _collect_news() -> None:
    """Scheduled job: collect news from all sources."""
    from app.services.news.collector import NewsCollector

    collector = NewsCollector()
    async with async_session_factory() as db:
        results = await collector.collect_all(db)
        total = sum(results.values())
        logger.info("Scheduled news collection complete: %d articles from %s", total, results)


async def _collect_a_share_daily() -> None:
    """Scheduled job: collect A-share daily data for tracked symbols."""
    from app.services.market_data.collector import MarketDataCollector

    # Default watchlist — in production this would come from user portfolios/config
    symbols = ["000001", "600519", "000858", "601318", "600036"]
    collector = MarketDataCollector()
    async with async_session_factory() as db:
        results = await collector.collect_stock_batch(db, "a_share", symbols)
        logger.info("Scheduled A-share collection: %s", results)


async def _collect_us_stock_daily() -> None:
    """Scheduled job: collect US stock daily data for tracked symbols."""
    from app.services.market_data.collector import MarketDataCollector

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    collector = MarketDataCollector()
    async with async_session_factory() as db:
        results = await collector.collect_stock_batch(db, "us_stock", symbols)
        logger.info("Scheduled US stock collection: %s", results)


async def _compute_features() -> None:
    """Scheduled job: compute technical + fundamental features for tracked stocks."""
    from app.services.feature_engine.engine import FeatureEngine

    engine = FeatureEngine()
    symbols: list[tuple[str, str]] = [
        # A-share
        ("000001", "a_share"), ("600519", "a_share"), ("000858", "a_share"),
        ("601318", "a_share"), ("600036", "a_share"),
        # US stock
        ("AAPL", "us_stock"), ("MSFT", "us_stock"), ("GOOGL", "us_stock"),
        ("AMZN", "us_stock"), ("TSLA", "us_stock"),
        # HK stock
        ("00700", "hk_stock"), ("09988", "hk_stock"), ("01810", "hk_stock"),
    ]
    async with async_session_factory() as db:
        results = await engine.compute_batch(db, symbols, store_days=1)
        total = sum(results.values())
        logger.info("Scheduled feature computation: %d rows for %d symbols", total, len(results))


async def _analyze_sentiment() -> None:
    """Scheduled job: analyze sentiment for recent unscored news articles."""
    from app.services.llm.sentiment import SentimentAnalyzer

    analyzer = SentimentAnalyzer()
    async with async_session_factory() as db:
        try:
            result = await analyzer.analyze_and_store(db, limit=20)
            logger.info("Scheduled sentiment analysis: %s", result)
        except Exception:
            logger.error("Scheduled sentiment analysis failed", exc_info=True)


def setup_scheduler() -> AsyncIOScheduler:
    """Configure and return the scheduler with all jobs.

    Call scheduler.start() in the app lifespan to activate.
    """
    # News collection: every 30 minutes during market hours
    scheduler.add_job(
        _collect_news,
        trigger=IntervalTrigger(minutes=30),
        id="collect_news",
        name="Collect financial news",
        replace_existing=True,
    )

    # A-share daily: Mon-Fri at 16:00 CST (after market close)
    scheduler.add_job(
        _collect_a_share_daily,
        trigger=CronTrigger(day_of_week="mon-fri", hour=16, minute=0, timezone="Asia/Shanghai"),
        id="collect_a_share_daily",
        name="Collect A-share daily data",
        replace_existing=True,
    )

    # US stock daily: Mon-Fri at 17:00 EST (after market close)
    scheduler.add_job(
        _collect_us_stock_daily,
        trigger=CronTrigger(day_of_week="mon-fri", hour=17, minute=0, timezone="America/New_York"),
        id="collect_us_stock_daily",
        name="Collect US stock daily data",
        replace_existing=True,
    )

    # Feature computation: Mon-Fri at 18:00 CST (after all market data collected)
    scheduler.add_job(
        _compute_features,
        trigger=CronTrigger(day_of_week="mon-fri", hour=18, minute=0, timezone="Asia/Shanghai"),
        id="compute_features",
        name="Compute stock features",
        replace_existing=True,
    )

    # Sentiment analysis: every hour (only processes articles without scores)
    scheduler.add_job(
        _analyze_sentiment,
        trigger=IntervalTrigger(hours=1),
        id="analyze_sentiment",
        name="Analyze news sentiment",
        replace_existing=True,
    )

    return scheduler

"""Seed database with sample market data for local development.

Usage:
    cd backend && poetry run python -m scripts.seed_data
    OR
    cd backend && poetry run python ../scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def seed() -> None:
    from app.db.session import async_session_factory
    from app.services.market_data.collector import MarketDataCollector
    from app.services.news.collector import NewsCollector

    collector = MarketDataCollector()
    news_collector = NewsCollector()

    async with async_session_factory() as db:
        # --- A-share stocks ---
        a_symbols = ["000001", "600519", "000858", "601318", "600036"]
        logger.info("Collecting A-share daily data for %s ...", a_symbols)
        a_results = await collector.collect_stock_batch(db, "a_share", a_symbols)
        logger.info("A-share results: %s", a_results)

        # --- US stocks ---
        us_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        logger.info("Collecting US stock daily data for %s ...", us_symbols)
        us_results = await collector.collect_stock_batch(db, "us_stock", us_symbols)
        logger.info("US stock results: %s", us_results)

        # --- HK stocks ---
        hk_symbols = ["00700", "09988", "01810"]
        logger.info("Collecting HK stock daily data for %s ...", hk_symbols)
        hk_results = await collector.collect_stock_batch(db, "hk_stock", hk_symbols)
        logger.info("HK stock results: %s", hk_results)

        # --- Fund NAV ---
        fund_symbols = ["110011", "519300"]
        logger.info("Collecting fund NAV data for %s ...", fund_symbols)
        for fsym in fund_symbols:
            try:
                count = await collector.collect_fund_nav(db, fsym)
                logger.info("Fund %s: %d rows", fsym, count)
            except Exception:
                logger.exception("Failed to collect fund %s", fsym)

        # --- Bond ---
        bond_symbols = ["sh019733", "sh019732"]
        logger.info("Collecting bond data for %s ...", bond_symbols)
        for bsym in bond_symbols:
            try:
                count = await collector.collect_bond_daily(db, bsym)
                logger.info("Bond %s: %d rows", bsym, count)
            except Exception:
                logger.exception("Failed to collect bond %s", bsym)

        # --- News ---
        logger.info("Collecting news from all sources ...")
        try:
            news_results = await news_collector.collect_all(db)
            logger.info("News results: %s", news_results)
        except Exception:
            logger.exception("Failed to collect news")

        # --- Refresh continuous aggregates for weekly/monthly views ---
        logger.info("Refreshing continuous aggregates ...")
        from sqlalchemy import text

        for view in ("stock_weekly", "stock_monthly"):
            await db.execute(text(f"CALL refresh_continuous_aggregate('{view}', NULL, NULL)"))
            logger.info("Refreshed %s", view)

    logger.info("=== Seed complete ===")


if __name__ == "__main__":
    asyncio.run(seed())

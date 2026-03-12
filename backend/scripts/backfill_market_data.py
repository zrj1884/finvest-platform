"""One-time script to backfill market data for all tracked symbols.

Usage:
    cd backend && poetry run python scripts/backfill_market_data.py
"""

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")


async def collect_one_stock(market: str, symbol: str) -> int:
    """Collect one stock with its own session to isolate errors."""
    from app.db.session import async_session_factory
    from app.services.market_data.collector import MarketDataCollector

    collector = MarketDataCollector()
    try:
        async with async_session_factory() as db:
            count = await collector.collect_stock_daily(db, market, symbol)
            logger.info("  %s:%s → %d rows", market, symbol, count)
            return count
    except Exception:
        logger.exception("  FAILED %s:%s", market, symbol)
        return 0


async def collect_one_fund(symbol: str) -> int:
    from app.db.session import async_session_factory
    from app.services.market_data.collector import MarketDataCollector

    collector = MarketDataCollector()
    try:
        async with async_session_factory() as db:
            count = await collector.collect_fund_nav(db, symbol)
            logger.info("  fund:%s → %d rows", symbol, count)
            return count
    except Exception:
        logger.exception("  FAILED fund:%s", symbol)
        return 0


async def collect_one_bond(symbol: str) -> int:
    from app.db.session import async_session_factory
    from app.services.market_data.collector import MarketDataCollector

    collector = MarketDataCollector()
    try:
        async with async_session_factory() as db:
            count = await collector.collect_bond_daily(db, symbol)
            logger.info("  bond:%s → %d rows", symbol, count)
            return count
    except Exception:
        logger.exception("  FAILED bond:%s", symbol)
        return 0


async def main() -> None:
    from app.services.scheduler import (
        A_SHARE_SYMBOLS, US_STOCK_SYMBOLS, HK_STOCK_SYMBOLS,
        FUND_SYMBOLS, BOND_SYMBOLS,
    )

    logger.info("=== A-share (%d) ===", len(A_SHARE_SYMBOLS))
    for s in A_SHARE_SYMBOLS:
        await collect_one_stock("a_share", s)

    logger.info("=== US stocks (%d) ===", len(US_STOCK_SYMBOLS))
    for s in US_STOCK_SYMBOLS:
        await collect_one_stock("us_stock", s)

    logger.info("=== HK stocks (%d) ===", len(HK_STOCK_SYMBOLS))
    for s in HK_STOCK_SYMBOLS:
        await collect_one_stock("hk_stock", s)

    logger.info("=== Funds (%d) ===", len(FUND_SYMBOLS))
    for s in FUND_SYMBOLS:
        await collect_one_fund(s)

    logger.info("=== Bonds (%d) ===", len(BOND_SYMBOLS))
    for s in BOND_SYMBOLS:
        await collect_one_bond(s)

    logger.info("=== Backfill complete ===")


if __name__ == "__main__":
    asyncio.run(main())

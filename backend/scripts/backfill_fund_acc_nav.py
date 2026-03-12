"""One-time script to backfill fund accumulated_nav and bond names.

Usage:
    cd backend && poetry run python scripts/backfill_fund_acc_nav.py
"""

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")


async def backfill_fund_acc_nav() -> None:
    """Re-collect fund data to populate accumulated_nav."""
    from app.db.session import async_session_factory
    from app.services.market_data.collector import MarketDataCollector
    from app.services.scheduler import FUND_SYMBOLS

    collector = MarketDataCollector()

    logger.info("=== Backfilling fund accumulated_nav (%d funds) ===", len(FUND_SYMBOLS))
    for symbol in FUND_SYMBOLS:
        try:
            async with async_session_factory() as db:
                count = await collector.collect_fund_nav(db, symbol)
                logger.info("  fund:%s → %d rows", symbol, count)
        except Exception:
            logger.exception("  FAILED fund:%s", symbol)


async def backfill_bond_names() -> None:
    """Re-collect bond data to populate missing names."""
    from app.db.session import async_session_factory
    from app.services.market_data.collector import MarketDataCollector
    from app.services.scheduler import BOND_SYMBOLS

    collector = MarketDataCollector()

    logger.info("=== Backfilling bond names (%d bonds) ===", len(BOND_SYMBOLS))
    for symbol in BOND_SYMBOLS:
        try:
            async with async_session_factory() as db:
                count = await collector.collect_bond_daily(db, symbol)
                logger.info("  bond:%s → %d rows", symbol, count)
        except Exception:
            logger.exception("  FAILED bond:%s", symbol)


async def main() -> None:
    await backfill_fund_acc_nav()
    await backfill_bond_names()
    logger.info("=== Backfill complete ===")


if __name__ == "__main__":
    asyncio.run(main())

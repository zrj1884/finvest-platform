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

# ── Tracked symbol lists ──────────────────────────────────────────────
A_SHARE_SYMBOLS = [
    # 上证50成分 / 沪深300权重
    "000001", "600519", "000858", "601318", "600036",  # 平安银行 茅台 五粮液 中国平安 招商银行
    "600000", "601166", "600276", "601888", "600900",  # 浦发银行 兴业银行 恒瑞医药 中国中免 长江电力
    "000333", "000651", "002594", "300750", "600030",  # 美的集团 格力电器 比亚迪 宁德时代 中信证券
    "601398", "601288", "600887", "000568", "002415",  # 工商银行 农业银行 伊利股份 泸州老窖 海康威视
]

US_STOCK_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",   # Apple Microsoft Google Amazon Tesla
    "NVDA", "META", "BRK-B", "JPM", "V",        # Nvidia Meta Berkshire JPMorgan Visa
    "JNJ", "WMT", "PG", "MA", "UNH",            # J&J Walmart P&G Mastercard UnitedHealth
    "HD", "DIS", "NFLX", "COST", "CRM",          # HomeDepot Disney Netflix Costco Salesforce
]

HK_STOCK_SYMBOLS = [
    "00700", "09988", "01810", "09999", "03690",  # 腾讯 阿里 小米 网易 美团
    "00005", "02318", "00388", "01024", "09618",  # 汇丰 中国平安 港交所 快手 京东
    "09888", "02020", "01211", "00941", "00883",  # 百度 安踏 比亚迪 中国移动 中海油
]

FUND_SYMBOLS = [
    "110011", "519300", "000961", "161725", "005827",  # 易方达精选 大成沪深300 天弘沪深300ETF 招商中证白酒 易方达蓝筹
    "003834", "007119", "001156", "519674", "001632",  # 华夏能源革新 景顺长城绩优成长 工银瑞信前沿医疗 银河创新成长 天弘中证食品
    "519778", "002190", "260108", "001938",             # 交银成长30 农银汇理新能源 景顺鼎益 中欧时代先锋
]

BOND_SYMBOLS = [
    "sh113009", "sh113050", "sz128108", "sz123045", "sh110074",  # 广汽转债 南银转债 蓝晓转2 中矿转债 精测转债
    "sh113014", "sh110043", "sz128053", "sz123060", "sh110038",  # 林洋转债 无锡转债 尚荣转债 天路转债 济川转债
]


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

    collector = MarketDataCollector()
    async with async_session_factory() as db:
        results = await collector.collect_stock_batch(db, "a_share", A_SHARE_SYMBOLS)
        logger.info("Scheduled A-share collection: %s", results)


async def _collect_us_stock_daily() -> None:
    """Scheduled job: collect US stock daily data for tracked symbols."""
    from app.services.market_data.collector import MarketDataCollector

    collector = MarketDataCollector()
    async with async_session_factory() as db:
        results = await collector.collect_stock_batch(db, "us_stock", US_STOCK_SYMBOLS)
        logger.info("Scheduled US stock collection: %s", results)


async def _collect_hk_stock_daily() -> None:
    """Scheduled job: collect HK stock daily data for tracked symbols."""
    from app.services.market_data.collector import MarketDataCollector

    collector = MarketDataCollector()
    async with async_session_factory() as db:
        results = await collector.collect_stock_batch(db, "hk_stock", HK_STOCK_SYMBOLS)
        logger.info("Scheduled HK stock collection: %s", results)


async def _collect_fund_nav() -> None:
    """Scheduled job: collect fund NAV data for tracked funds."""
    from app.services.market_data.collector import MarketDataCollector

    collector = MarketDataCollector()
    async with async_session_factory() as db:
        for symbol in FUND_SYMBOLS:
            try:
                count = await collector.collect_fund_nav(db, symbol)
                logger.info("Fund %s: %d rows", symbol, count)
            except Exception:
                logger.exception("Failed to collect fund %s", symbol)


async def _collect_bond_daily() -> None:
    """Scheduled job: collect bond daily data for tracked bonds."""
    from app.services.market_data.collector import MarketDataCollector

    collector = MarketDataCollector()
    async with async_session_factory() as db:
        for symbol in BOND_SYMBOLS:
            try:
                count = await collector.collect_bond_daily(db, symbol)
                logger.info("Bond %s: %d rows", symbol, count)
            except Exception:
                logger.exception("Failed to collect bond %s", symbol)


async def _compute_features() -> None:
    """Scheduled job: compute technical + fundamental features for tracked stocks."""
    from app.services.feature_engine.engine import FeatureEngine

    engine = FeatureEngine()
    symbols: list[tuple[str, str]] = (
        [(s, "a_share") for s in A_SHARE_SYMBOLS]
        + [(s, "us_stock") for s in US_STOCK_SYMBOLS]
        + [(s, "hk_stock") for s in HK_STOCK_SYMBOLS]
    )
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

    # HK stock daily: Mon-Fri at 16:30 HKT (after market close)
    scheduler.add_job(
        _collect_hk_stock_daily,
        trigger=CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone="Asia/Hong_Kong"),
        id="collect_hk_stock_daily",
        name="Collect HK stock daily data",
        replace_existing=True,
    )

    # Fund NAV: Mon-Fri at 20:00 CST (NAV published after market)
    scheduler.add_job(
        _collect_fund_nav,
        trigger=CronTrigger(day_of_week="mon-fri", hour=20, minute=0, timezone="Asia/Shanghai"),
        id="collect_fund_nav",
        name="Collect fund NAV data",
        replace_existing=True,
    )

    # Bond daily: Mon-Fri at 16:30 CST (after market close)
    scheduler.add_job(
        _collect_bond_daily,
        trigger=CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone="Asia/Shanghai"),
        id="collect_bond_daily",
        name="Collect bond daily data",
        replace_existing=True,
    )

    # Feature computation: Mon-Fri at 21:00 CST (after all market data collected)
    scheduler.add_job(
        _compute_features,
        trigger=CronTrigger(day_of_week="mon-fri", hour=21, minute=0, timezone="Asia/Shanghai"),
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

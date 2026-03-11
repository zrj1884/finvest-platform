"""Market data (行情) models - TimescaleDB hypertables."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StockDaily(Base):
    """日线行情数据 - TimescaleDB hypertable, 按 time 分区."""

    __tablename__ = "stock_daily"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100))
    market: Mapped[str] = mapped_column(String(20), nullable=False)  # a_share / us_stock / hk_stock
    open: Mapped[float] = mapped_column(Numeric(20, 4))
    high: Mapped[float] = mapped_column(Numeric(20, 4))
    low: Mapped[float] = mapped_column(Numeric(20, 4))
    close: Mapped[float] = mapped_column(Numeric(20, 4))
    volume: Mapped[int] = mapped_column(BigInteger, default=0)
    amount: Mapped[float | None] = mapped_column(Numeric(20, 4))  # 成交额
    turnover: Mapped[float | None] = mapped_column(Numeric(10, 4))  # 换手率
    change_pct: Mapped[float | None] = mapped_column(Numeric(10, 4))  # 涨跌幅 %
    amplitude: Mapped[float | None] = mapped_column(Numeric(10, 4))  # 振幅 %

    __table_args__ = (
        Index("ix_stock_daily_symbol_time", "symbol", "time"),
        Index("ix_stock_daily_market_time", "market", "time"),
    )


class FundNav(Base):
    """基金净值数据 - TimescaleDB hypertable."""

    __tablename__ = "fund_nav"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100))
    nav: Mapped[float] = mapped_column(Numeric(20, 4))  # 单位净值
    accumulated_nav: Mapped[float | None] = mapped_column(Numeric(20, 4))  # 累计净值
    daily_return: Mapped[float | None] = mapped_column(Numeric(10, 4))  # 日涨跌幅 %

    __table_args__ = (Index("ix_fund_nav_symbol_time", "symbol", "time"),)


class BondDaily(Base):
    """债券日线数据 - TimescaleDB hypertable."""

    __tablename__ = "bond_daily"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(100))
    bond_type: Mapped[str | None] = mapped_column(String(50))  # 国债/企业债/可转债
    close: Mapped[float] = mapped_column(Numeric(20, 4))
    volume: Mapped[int] = mapped_column(BigInteger, default=0)
    amount: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ytm: Mapped[float | None] = mapped_column(Numeric(10, 4))  # 到期收益率 %
    change_pct: Mapped[float | None] = mapped_column(Numeric(10, 4))

    __table_args__ = (Index("ix_bond_daily_symbol_time", "symbol", "time"),)


class NewsArticle(Base):
    """财经新闻/资讯."""

    __tablename__ = "news_articles"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    source: Mapped[str] = mapped_column(String(50), primary_key=True)  # 来源
    url: Mapped[str] = mapped_column(String(500), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    symbols: Mapped[str | None] = mapped_column(String(500))  # 关联证券代码，逗号分隔
    sentiment_score: Mapped[float | None] = mapped_column(Numeric(5, 2))  # 情感得分 -1 ~ 1

    __table_args__ = (
        Index("ix_news_time", "time"),
        Index("ix_news_source_time", "source", "time"),
    )

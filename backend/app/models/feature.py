"""Feature Store models - TimescaleDB hypertables for computed features."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StockFeature(Base):
    """Stock technical & fundamental features - TimescaleDB hypertable.

    Computed from stock_daily OHLCV data and external fundamental sources.
    Primary key: (time, symbol) to align with stock_daily granularity.
    """

    __tablename__ = "stock_features"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    market: Mapped[str] = mapped_column(String(20), nullable=False)

    # --- Moving Averages ---
    ma5: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ma10: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ma20: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ma60: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ma120: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ma250: Mapped[float | None] = mapped_column(Numeric(20, 4))

    # --- EMA ---
    ema12: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ema26: Mapped[float | None] = mapped_column(Numeric(20, 4))

    # --- MACD ---
    macd: Mapped[float | None] = mapped_column(Numeric(20, 4))
    macd_signal: Mapped[float | None] = mapped_column(Numeric(20, 4))
    macd_hist: Mapped[float | None] = mapped_column(Numeric(20, 4))

    # --- RSI ---
    rsi_14: Mapped[float | None] = mapped_column(Numeric(10, 4))

    # --- KDJ ---
    kdj_k: Mapped[float | None] = mapped_column(Numeric(10, 4))
    kdj_d: Mapped[float | None] = mapped_column(Numeric(10, 4))
    kdj_j: Mapped[float | None] = mapped_column(Numeric(10, 4))

    # --- Bollinger Bands ---
    boll_upper: Mapped[float | None] = mapped_column(Numeric(20, 4))
    boll_mid: Mapped[float | None] = mapped_column(Numeric(20, 4))
    boll_lower: Mapped[float | None] = mapped_column(Numeric(20, 4))

    # --- ATR ---
    atr_14: Mapped[float | None] = mapped_column(Numeric(20, 4))

    # --- OBV ---
    obv: Mapped[float | None] = mapped_column(Numeric(20, 2))

    # --- Fundamental Factors ---
    pe_ttm: Mapped[float | None] = mapped_column(Numeric(20, 4))
    pb: Mapped[float | None] = mapped_column(Numeric(20, 4))
    ps_ttm: Mapped[float | None] = mapped_column(Numeric(20, 4))
    total_mv: Mapped[float | None] = mapped_column(Numeric(20, 2))  # 总市值(亿)
    circ_mv: Mapped[float | None] = mapped_column(Numeric(20, 2))  # 流通市值(亿)
    roe: Mapped[float | None] = mapped_column(Numeric(10, 4))  # %
    revenue_yoy: Mapped[float | None] = mapped_column(Numeric(10, 4))  # 营收同比增长 %
    profit_yoy: Mapped[float | None] = mapped_column(Numeric(10, 4))  # 净利润同比增长 %

    __table_args__ = (
        Index("ix_stock_features_symbol_time", "symbol", "time"),
        Index("ix_stock_features_market_time", "market", "time"),
    )

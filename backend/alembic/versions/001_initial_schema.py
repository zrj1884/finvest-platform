"""Initial schema - core tables + TimescaleDB hypertables.

Revision ID: 001
Revises: None
Create Date: 2026-03-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enable TimescaleDB extension ---
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    # === Business Tables ===

    # Users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Accounts
    op.create_table(
        "accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("market", sa.Enum("a_share", "us_stock", "hk_stock", "fund", "bond", name="market_enum"), nullable=False),
        sa.Column("broker", sa.String(100)),
        sa.Column("account_no", sa.String(100)),
        sa.Column("balance", sa.Numeric(20, 4), default=0),
        sa.Column("is_simulated", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Positions
    op.create_table(
        "positions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("symbol", sa.String(20), nullable=False, index=True),
        sa.Column("name", sa.String(100)),
        sa.Column("quantity", sa.Integer(), default=0),
        sa.Column("available_quantity", sa.Integer(), default=0),
        sa.Column("avg_cost", sa.Numeric(20, 4), default=0),
        sa.Column("current_price", sa.Numeric(20, 4), default=0),
        sa.Column("market_value", sa.Numeric(20, 4), default=0),
        sa.Column("unrealized_pnl", sa.Numeric(20, 4), default=0),
        sa.Column("realized_pnl", sa.Numeric(20, 4), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Orders
    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("symbol", sa.String(20), nullable=False, index=True),
        sa.Column("name", sa.String(100)),
        sa.Column("side", sa.Enum("buy", "sell", name="order_side_enum"), nullable=False),
        sa.Column("order_type", sa.Enum("market", "limit", name="order_type_enum"), nullable=False),
        sa.Column("status", sa.Enum("pending", "submitted", "partial_filled", "filled", "cancelled", "rejected", name="order_status_enum"), default="pending", index=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("filled_quantity", sa.Integer(), default=0),
        sa.Column("price", sa.Numeric(20, 4)),
        sa.Column("filled_price", sa.Numeric(20, 4)),
        sa.Column("commission", sa.Numeric(20, 4), default=0),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("filled_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("broker_order_id", sa.String(100)),
        sa.Column("remark", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # === Time-Series Tables (TimescaleDB Hypertables) ===

    # Stock Daily
    op.create_table(
        "stock_daily",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("market", sa.String(20), nullable=False),
        sa.Column("open", sa.Numeric(20, 4)),
        sa.Column("high", sa.Numeric(20, 4)),
        sa.Column("low", sa.Numeric(20, 4)),
        sa.Column("close", sa.Numeric(20, 4)),
        sa.Column("volume", sa.BigInteger(), default=0),
        sa.Column("amount", sa.Numeric(20, 4)),
        sa.Column("turnover", sa.Numeric(10, 4)),
        sa.Column("change_pct", sa.Numeric(10, 4)),
        sa.Column("amplitude", sa.Numeric(10, 4)),
        sa.PrimaryKeyConstraint("time", "symbol"),
    )
    op.create_index("ix_stock_daily_symbol_time", "stock_daily", ["symbol", "time"])
    op.create_index("ix_stock_daily_market_time", "stock_daily", ["market", "time"])

    # Fund NAV
    op.create_table(
        "fund_nav",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("nav", sa.Numeric(20, 4)),
        sa.Column("accumulated_nav", sa.Numeric(20, 4)),
        sa.Column("daily_return", sa.Numeric(10, 4)),
        sa.PrimaryKeyConstraint("time", "symbol"),
    )
    op.create_index("ix_fund_nav_symbol_time", "fund_nav", ["symbol", "time"])

    # Bond Daily
    op.create_table(
        "bond_daily",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("bond_type", sa.String(50)),
        sa.Column("close", sa.Numeric(20, 4)),
        sa.Column("volume", sa.BigInteger(), default=0),
        sa.Column("amount", sa.Numeric(20, 4)),
        sa.Column("ytm", sa.Numeric(10, 4)),
        sa.Column("change_pct", sa.Numeric(10, 4)),
        sa.PrimaryKeyConstraint("time", "symbol"),
    )
    op.create_index("ix_bond_daily_symbol_time", "bond_daily", ["symbol", "time"])

    # News Articles
    op.create_table(
        "news_articles",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("symbols", sa.String(500)),
        sa.Column("sentiment_score", sa.Numeric(5, 2)),
        sa.PrimaryKeyConstraint("time", "source", "url"),
    )
    op.create_index("ix_news_time", "news_articles", ["time"])
    op.create_index("ix_news_source_time", "news_articles", ["source", "time"])

    # === Convert to TimescaleDB Hypertables ===
    # chunk_time_interval: 按月分区（行情数据）/ 按周分区（新闻）

    # 股票日线 - 按月分区
    op.execute("""
        SELECT create_hypertable('stock_daily', 'time',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        )
    """)

    # 基金净值 - 按月分区
    op.execute("""
        SELECT create_hypertable('fund_nav', 'time',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        )
    """)

    # 债券日线 - 按月分区
    op.execute("""
        SELECT create_hypertable('bond_daily', 'time',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        )
    """)

    # 新闻资讯 - 按周分区（数据量大，查询时间范围短）
    op.execute("""
        SELECT create_hypertable('news_articles', 'time',
            chunk_time_interval => INTERVAL '1 week',
            if_not_exists => TRUE
        )
    """)

    # === Continuous Aggregates (连续聚合视图) ===
    # 股票周线聚合
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS stock_weekly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 week', time) AS time,
            symbol,
            market,
            first(open, time) AS open,
            max(high) AS high,
            min(low) AS low,
            last(close, time) AS close,
            sum(volume) AS volume,
            sum(amount) AS amount
        FROM stock_daily
        GROUP BY time_bucket('1 week', time), symbol, market
        WITH NO DATA
    """)

    # 股票月线聚合
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS stock_monthly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 month', time) AS time,
            symbol,
            market,
            first(open, time) AS open,
            max(high) AS high,
            min(low) AS low,
            last(close, time) AS close,
            sum(volume) AS volume,
            sum(amount) AS amount
        FROM stock_daily
        GROUP BY time_bucket('1 month', time), symbol, market
        WITH NO DATA
    """)

    # === Continuous Aggregate Policies (自动刷新策略) ===
    op.execute("""
        SELECT add_continuous_aggregate_policy('stock_weekly',
            start_offset => INTERVAL '1 month',
            end_offset => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        )
    """)

    op.execute("""
        SELECT add_continuous_aggregate_policy('stock_monthly',
            start_offset => INTERVAL '3 months',
            end_offset => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        )
    """)

    # === Data Retention Policy (数据保留策略) ===
    # 新闻数据保留 1 年
    op.execute("""
        SELECT add_retention_policy('news_articles',
            drop_after => INTERVAL '1 year',
            if_not_exists => TRUE
        )
    """)


def downgrade() -> None:
    # Drop continuous aggregates first
    op.execute("DROP MATERIALIZED VIEW IF EXISTS stock_monthly CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS stock_weekly CASCADE")

    # Drop time-series tables
    op.drop_table("news_articles")
    op.drop_table("bond_daily")
    op.drop_table("fund_nav")
    op.drop_table("stock_daily")

    # Drop business tables
    op.drop_table("orders")
    op.drop_table("positions")
    op.drop_table("accounts")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS market_enum")
    op.execute("DROP TYPE IF EXISTS order_side_enum")
    op.execute("DROP TYPE IF EXISTS order_type_enum")
    op.execute("DROP TYPE IF EXISTS order_status_enum")

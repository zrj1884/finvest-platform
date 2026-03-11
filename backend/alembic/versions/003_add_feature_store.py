"""Add stock_features table (Feature Store).

Revision ID: 003
Revises: 002
Create Date: 2026-03-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stock_features",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("market", sa.String(20), nullable=False),
        # Moving Averages
        sa.Column("ma5", sa.Numeric(20, 4)),
        sa.Column("ma10", sa.Numeric(20, 4)),
        sa.Column("ma20", sa.Numeric(20, 4)),
        sa.Column("ma60", sa.Numeric(20, 4)),
        sa.Column("ma120", sa.Numeric(20, 4)),
        sa.Column("ma250", sa.Numeric(20, 4)),
        # EMA
        sa.Column("ema12", sa.Numeric(20, 4)),
        sa.Column("ema26", sa.Numeric(20, 4)),
        # MACD
        sa.Column("macd", sa.Numeric(20, 4)),
        sa.Column("macd_signal", sa.Numeric(20, 4)),
        sa.Column("macd_hist", sa.Numeric(20, 4)),
        # RSI
        sa.Column("rsi_14", sa.Numeric(10, 4)),
        # KDJ
        sa.Column("kdj_k", sa.Numeric(10, 4)),
        sa.Column("kdj_d", sa.Numeric(10, 4)),
        sa.Column("kdj_j", sa.Numeric(10, 4)),
        # Bollinger Bands
        sa.Column("boll_upper", sa.Numeric(20, 4)),
        sa.Column("boll_mid", sa.Numeric(20, 4)),
        sa.Column("boll_lower", sa.Numeric(20, 4)),
        # ATR
        sa.Column("atr_14", sa.Numeric(20, 4)),
        # OBV
        sa.Column("obv", sa.Numeric(20, 2)),
        # Fundamental Factors
        sa.Column("pe_ttm", sa.Numeric(20, 4)),
        sa.Column("pb", sa.Numeric(20, 4)),
        sa.Column("ps_ttm", sa.Numeric(20, 4)),
        sa.Column("total_mv", sa.Numeric(20, 2)),
        sa.Column("circ_mv", sa.Numeric(20, 2)),
        sa.Column("roe", sa.Numeric(10, 4)),
        sa.Column("revenue_yoy", sa.Numeric(10, 4)),
        sa.Column("profit_yoy", sa.Numeric(10, 4)),
        sa.PrimaryKeyConstraint("time", "symbol"),
    )

    # Indexes
    op.create_index("ix_stock_features_symbol_time", "stock_features", ["symbol", "time"])
    op.create_index("ix_stock_features_market_time", "stock_features", ["market", "time"])

    # Convert to TimescaleDB hypertable (monthly partitions)
    op.execute("SELECT create_hypertable('stock_features', 'time', chunk_time_interval => INTERVAL '1 month')")


def downgrade() -> None:
    op.drop_index("ix_stock_features_market_time", table_name="stock_features")
    op.drop_index("ix_stock_features_symbol_time", table_name="stock_features")
    op.drop_table("stock_features")

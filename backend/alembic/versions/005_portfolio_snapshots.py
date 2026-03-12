"""Add portfolio_snapshots hypertable for daily portfolio value tracking.

Revision ID: 005
Revises: 004
Create Date: 2026-03-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_snapshots",
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("total_value", sa.Numeric(20, 4), nullable=False),
        sa.Column("total_balance", sa.Numeric(20, 4), nullable=False),
        sa.Column("total_market_value", sa.Numeric(20, 4), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(20, 4), server_default="0"),
        sa.Column("realized_pnl", sa.Numeric(20, 4), server_default="0"),
    )

    # Convert to TimescaleDB hypertable (monthly chunks)
    op.execute(
        "SELECT create_hypertable('portfolio_snapshots', 'time', "
        "chunk_time_interval => INTERVAL '1 month', "
        "if_not_exists => TRUE)"
    )

    # Index for querying by user
    op.create_index(
        "ix_portfolio_snapshots_user_time",
        "portfolio_snapshots",
        ["user_id", sa.text("time DESC")],
    )


def downgrade() -> None:
    op.drop_table("portfolio_snapshots")

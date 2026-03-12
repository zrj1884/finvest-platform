"""Clean up duplicate news articles (same source+url, different time).

Revision ID: 004
Revises: 003
Create Date: 2026-03-12

TimescaleDB requires the partitioning column (time) in all unique indexes,
so we cannot add a unique constraint on (source, url) alone. Instead, we
clean up existing duplicates and rely on application-level deduplication.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove duplicate rows keeping only the latest per (source, url)
    op.execute("""
        DELETE FROM news_articles a
        USING news_articles b
        WHERE a.source = b.source
          AND a.url = b.url
          AND a.time < b.time
    """)


def downgrade() -> None:
    pass  # Cannot re-insert deleted duplicates

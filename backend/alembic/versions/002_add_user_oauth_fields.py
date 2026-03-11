"""Add OAuth fields to users table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make hashed_password nullable (OAuth users may not have a password)
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=True)

    # Add OAuth columns
    op.add_column("users", sa.Column("oauth_provider", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("oauth_id", sa.String(255), nullable=True))

    # Index for OAuth lookups
    op.create_index("ix_users_oauth", "users", ["oauth_provider", "oauth_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_oauth", table_name="users")
    op.drop_column("users", "oauth_id")
    op.drop_column("users", "oauth_provider")
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=False)

"""add pair_created_at to tokens

Revision ID: b3c8f2a1d4e5
Revises: 2498f6dcb3be
Create Date: 2026-07-15 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c8f2a1d4e5"
down_revision: str | Sequence[str] | None = "2498f6dcb3be"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tokens",
        sa.Column("pair_created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_tokens_pair_created_at"),
        "tokens",
        ["pair_created_at"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tokens_pair_created_at"), table_name="tokens")
    op.drop_column("tokens", "pair_created_at")

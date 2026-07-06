"""Add import_batches table and batch_id FK on transactions.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("file_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("file_name", sa.String(256), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "transactions",
        sa.Column("batch_id", sa.Integer, sa.ForeignKey("import_batches.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transactions", "batch_id")
    op.drop_table("import_batches")

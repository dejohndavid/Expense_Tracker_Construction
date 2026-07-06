"""Initial schema: transactions and classification_rules tables.

Revision ID: 0001
Revises:
Create Date: 2026-07-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("transaction_date", sa.String(10), nullable=False),
        sa.Column("value_date", sa.String(10), nullable=False),
        sa.Column("narration", sa.Text, nullable=False),
        sa.Column("debit_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("credit_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("reference_number", sa.String(64), nullable=False),
        sa.Column("closing_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("payee_name", sa.String(256), nullable=True),
        sa.Column("upi_id", sa.String(128), nullable=True),
        sa.Column("purpose", sa.String(256), nullable=True),
        sa.Column("matched_keyword", sa.String(256), nullable=True),
        sa.Column("suggested_vendor", sa.String(256), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("subcategory", sa.String(64), nullable=True),
        sa.Column("stage", sa.String(64), nullable=True),
        sa.Column("payment_mode", sa.String(32), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 2), nullable=False),
        sa.Column("import_status", sa.String(16), nullable=False),
        sa.Column("review_reason", sa.Text, nullable=False),
        sa.Column("manual_notes", sa.Text, nullable=False, server_default=""),
    )
    op.create_table(
        "classification_rules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("keyword_groups_raw", sa.Text, nullable=False),
        sa.Column("vendor", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("subcategory", sa.String(64), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("payment_mode", sa.String(32), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_table("classification_rules")
    op.drop_table("transactions")

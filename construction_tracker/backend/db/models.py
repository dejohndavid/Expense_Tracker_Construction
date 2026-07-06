from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[str] = mapped_column(String(32))
    row_count: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"<ImportBatch id={self.id} file={self.file_name!r} hash={self.file_hash[:8]}>"


class TransactionRecord(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), nullable=True)
    transaction_date: Mapped[str] = mapped_column(String(10))
    value_date: Mapped[str] = mapped_column(String(10))
    narration: Mapped[str] = mapped_column(Text)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    reference_number: Mapped[str] = mapped_column(String(64))
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    direction: Mapped[str] = mapped_column(String(8))
    channel: Mapped[str] = mapped_column(String(16))
    payee_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    upi_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(256), nullable=True)
    matched_keyword: Mapped[str | None] = mapped_column(String(256), nullable=True)
    suggested_vendor: Mapped[str | None] = mapped_column(String(256), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    import_status: Mapped[str] = mapped_column(String(16))
    review_reason: Mapped[str] = mapped_column(Text)
    manual_notes: Mapped[str] = mapped_column(Text, default="")

    def __repr__(self) -> str:
        return f"<TransactionRecord id={self.id} date={self.transaction_date} status={self.import_status}>"


class ClassificationRuleRecord(Base):
    __tablename__ = "classification_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    # Keyword groups serialised as newline-separated groups; keywords within a group separated by "|"
    # e.g. "MADESH|JCB\nJCB"
    keyword_groups_raw: Mapped[str] = mapped_column(Text)
    vendor: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64))
    subcategory: Mapped[str] = mapped_column(String(64))
    stage: Mapped[str] = mapped_column(String(64))
    payment_mode: Mapped[str] = mapped_column(String(32))
    priority: Mapped[int] = mapped_column(default=100)
    enabled: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<ClassificationRuleRecord id={self.id} name={self.name!r}>"

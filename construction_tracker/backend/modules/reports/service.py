from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.models import TransactionRecord


@dataclass(frozen=True)
class CategorySummary:
    category: str
    subcategory: str
    stage: str
    transaction_count: int
    total_debit: Decimal


@dataclass(frozen=True)
class SpendSummary:
    total_transactions: int
    ready_count: int
    review_count: int
    ignored_count: int
    total_debit: Decimal
    ready_debit: Decimal
    by_category: list[CategorySummary]
    by_stage: list[CategorySummary]


def get_spend_summary(db: Session) -> SpendSummary:
    counts: dict[str, int] = {}
    debits: dict[str, Decimal] = {}

    for status, count, total in (
        db.query(
            TransactionRecord.import_status,
            func.count(TransactionRecord.id),
            func.sum(TransactionRecord.debit_amount),
        )
        .group_by(TransactionRecord.import_status)
        .all()
    ):
        counts[status] = int(count)
        debits[status] = Decimal(str(total or 0))

    total_transactions = sum(counts.values())
    total_debit = sum(debits.values(), Decimal("0"))
    ready_debit = debits.get("Ready", Decimal("0"))

    by_category = _aggregate(db, group_by="category")
    by_stage = _aggregate(db, group_by="stage")

    return SpendSummary(
        total_transactions=total_transactions,
        ready_count=counts.get("Ready", 0),
        review_count=counts.get("Review", 0),
        ignored_count=counts.get("Ignore", 0),
        total_debit=total_debit,
        ready_debit=ready_debit,
        by_category=by_category,
        by_stage=by_stage,
    )


def _aggregate(db: Session, *, group_by: str) -> list[CategorySummary]:
    category_col = TransactionRecord.category
    subcategory_col = TransactionRecord.subcategory
    stage_col = TransactionRecord.stage

    rows = (
        db.query(
            category_col,
            subcategory_col,
            stage_col,
            func.count(TransactionRecord.id),
            func.sum(TransactionRecord.debit_amount),
        )
        .filter(TransactionRecord.import_status == "Ready")
        .filter(TransactionRecord.debit_amount > 0)
        .group_by(category_col, subcategory_col, stage_col)
        .order_by(func.sum(TransactionRecord.debit_amount).desc())
        .all()
    )

    return [
        CategorySummary(
            category=cat or "",
            subcategory=sub or "",
            stage=stage or "",
            transaction_count=int(cnt),
            total_debit=Decimal(str(total or 0)),
        )
        for cat, sub, stage, cnt, total in rows
    ]

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.modules.reports.service import CategorySummary, SpendSummary, get_spend_summary

router = APIRouter(prefix="/reports", tags=["reports"])


class CategorySummaryOut(BaseModel):
    category: str
    subcategory: str
    stage: str
    transaction_count: int
    total_debit: str


class SpendSummaryOut(BaseModel):
    total_transactions: int
    ready_count: int
    review_count: int
    ignored_count: int
    total_debit: str
    ready_debit: str
    by_category: list[CategorySummaryOut]
    by_stage: list[CategorySummaryOut]


def _category_out(s: CategorySummary) -> CategorySummaryOut:
    return CategorySummaryOut(
        category=s.category,
        subcategory=s.subcategory,
        stage=s.stage,
        transaction_count=s.transaction_count,
        total_debit=f"{s.total_debit:.2f}",
    )


def _fmt(value: Decimal) -> str:
    return f"{value:.2f}"


@router.get("/spend")
def spend_summary(db: Annotated[Session, Depends(get_db)]) -> SpendSummaryOut:
    summary: SpendSummary = get_spend_summary(db)
    return SpendSummaryOut(
        total_transactions=summary.total_transactions,
        ready_count=summary.ready_count,
        review_count=summary.review_count,
        ignored_count=summary.ignored_count,
        total_debit=_fmt(summary.total_debit),
        ready_debit=_fmt(summary.ready_debit),
        by_category=[_category_out(c) for c in summary.by_category],
        by_stage=[_category_out(c) for c in summary.by_stage],
    )

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.base import Base
import backend.db.models  # noqa: F401
from backend.modules.imports.hdfc_parser import parse_hdfc_text_statement
from backend.modules.imports.review import build_review_rows
from backend.modules.reports.service import get_spend_summary
from backend.modules.transactions.service import save_review_rows

SAMPLE_STATEMENT = "\n".join(
    [
        "Date,Narration,Value Dat,Debit Amount,Credit Amount,Chq/Ref Number,Closing Balance",
        (
            "26/11/25,"
            "UPI-MADESH NAIK-MADESHNAIK460-1@OKHDFCBANK-SBIN0040029-"
            "569690930707-JCB DIESEL,"
            "26/11/25,10000.00,0.00,0000569690930707,312345.67"
        ),
        (
            "25/11/25,"
            "UPI-SRI CEMENT STORE-CEMENT@YBL-SBIN0001234-123456789-CEMENT BILL,"
            "25/11/25,5000.00,0.00,0000123456789,302345.67"
        ),
        (
            "06/11/25,"
            "NEFT CR-CITI0000004-MUSARUBRA SOFTWARE INDIA PVT LTD-SALARY,"
            "06/11/25,0.00,7000.00,CITIN52025110651403386,309686.12"
        ),
    ]
)


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def _seed_transactions(db: Session) -> None:
    rows = build_review_rows(parse_hdfc_text_statement(SAMPLE_STATEMENT))
    save_review_rows(db, rows)


def test_summary_counts(db: Session) -> None:
    summary = get_spend_summary(db)
    assert summary.total_transactions == 3
    assert summary.ready_count == 2
    assert summary.ignored_count == 1
    assert summary.review_count == 0


def test_summary_ready_debit(db: Session) -> None:
    summary = get_spend_summary(db)
    assert summary.ready_debit == Decimal("15000.00")


def test_summary_by_category_includes_machinery(db: Session) -> None:
    summary = get_spend_summary(db)
    categories = [row.category for row in summary.by_category]
    assert "Machinery" in categories


def test_summary_by_category_sorted_by_debit_desc(db: Session) -> None:
    summary = get_spend_summary(db)
    debits = [row.total_debit for row in summary.by_category]
    assert debits == sorted(debits, reverse=True)


def test_empty_db_returns_zero_summary() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    summary = get_spend_summary(session)
    session.close()
    assert summary.total_transactions == 0
    assert summary.ready_debit == Decimal("0")
    assert summary.by_category == []

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.base import Base
import backend.db.models  # noqa: F401
from backend.modules.imports.hdfc_parser import parse_hdfc_text_statement
from backend.modules.imports.review import build_review_rows
from backend.modules.transactions.service import list_transactions, save_review_rows

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


@pytest.fixture()
def review_rows() -> list:
    return build_review_rows(parse_hdfc_text_statement(SAMPLE_STATEMENT))


def test_save_review_rows_persists_all(db: Session, review_rows: list) -> None:
    records = save_review_rows(db, review_rows)
    assert len(records) == 2
    assert all(r.id is not None for r in records)


def test_list_transactions_returns_all(db: Session, review_rows: list) -> None:
    save_review_rows(db, review_rows)
    results = list_transactions(db)
    assert len(results) == 2


def test_list_transactions_filters_by_status(db: Session, review_rows: list) -> None:
    save_review_rows(db, review_rows)
    ready = list_transactions(db, status="Ready")
    ignored = list_transactions(db, status="Ignore")
    assert len(ready) == 1
    assert ready[0].suggested_vendor == "Madesh"
    assert len(ignored) == 1


def test_list_transactions_respects_limit(db: Session, review_rows: list) -> None:
    save_review_rows(db, review_rows)
    results = list_transactions(db, limit=1)
    assert len(results) == 1


def test_save_review_rows_stores_correct_values(db: Session, review_rows: list) -> None:
    records = save_review_rows(db, review_rows)
    jcb = next(r for r in records if r.import_status == "Ready")
    assert jcb.category == "Machinery"
    assert jcb.subcategory == "JCB"
    assert float(jcb.debit_amount) == 10000.0

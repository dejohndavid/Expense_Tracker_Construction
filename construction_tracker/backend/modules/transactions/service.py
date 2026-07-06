from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from backend.db.models import TransactionRecord
from backend.modules.imports.review import ReviewRow


def save_review_rows(db: Session, rows: list[ReviewRow]) -> list[TransactionRecord]:
    """Persist a batch of reviewed rows and return the saved records."""
    records: list[TransactionRecord] = []
    for row in rows:
        record = TransactionRecord(
            transaction_date=row["transaction_date"],
            value_date=row["value_date"],
            narration=row["narration"],
            debit_amount=Decimal(row["debit_amount"]),
            credit_amount=Decimal(row["credit_amount"]),
            reference_number=row["reference_number"],
            closing_balance=Decimal(row["closing_balance"]),
            direction=row["direction"],
            channel=row["channel"],
            payee_name=row["payee_name"] or None,
            upi_id=row["upi_id"] or None,
            purpose=row["purpose"] or None,
            matched_keyword=row["matched_keyword"] or None,
            suggested_vendor=row["suggested_vendor"] or None,
            category=row["category"] or None,
            subcategory=row["subcategory"] or None,
            stage=row["stage"] or None,
            payment_mode=row["payment_mode"] or None,
            confidence=Decimal(row["confidence"]),
            import_status=row["import_status"],
            review_reason=row["review_reason"],
            manual_notes=row["manual_notes"],
        )
        db.add(record)
        records.append(record)
    db.commit()
    for record in records:
        db.refresh(record)
    return records


def list_transactions(
    db: Session,
    *,
    status: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[TransactionRecord]:
    query = db.query(TransactionRecord)
    if status:
        query = query.filter(TransactionRecord.import_status == status)
    return query.order_by(TransactionRecord.id.desc()).offset(offset).limit(limit).all()

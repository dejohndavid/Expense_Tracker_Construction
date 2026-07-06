from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.db.models import ImportBatch, TransactionRecord
from backend.modules.imports.review import ReviewRow


@dataclass(frozen=True)
class SaveResult:
    saved: int
    skipped: int


def hash_statement(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def find_batch_by_hash(db: Session, file_hash: str) -> ImportBatch | None:
    return db.query(ImportBatch).filter(ImportBatch.file_hash == file_hash).first()


def load_batch_review_rows(db: Session, batch_id: int) -> list[ReviewRow]:
    records = (
        db.query(TransactionRecord)
        .filter(TransactionRecord.batch_id == batch_id)
        .order_by(TransactionRecord.id)
        .all()
    )
    return [_record_to_review_row(r) for r in records]


def save_review_rows(
    db: Session,
    rows: list[ReviewRow],
    *,
    file_hash: str | None = None,
    file_name: str | None = None,
) -> SaveResult:
    # Collect non-empty reference numbers from the incoming rows
    incoming_refs = {
        row["reference_number"]
        for row in rows
        if row["reference_number"].strip()
    }

    # Find which of those already exist in the DB
    existing_refs: set[str] = set()
    if incoming_refs:
        existing_refs = {
            r
            for (r,) in db.query(TransactionRecord.reference_number)
            .filter(TransactionRecord.reference_number.in_(incoming_refs))
            .all()
        }

    new_rows = [
        row for row in rows
        if not row["reference_number"].strip()
        or row["reference_number"] not in existing_refs
    ]
    skipped = len(rows) - len(new_rows)

    if not new_rows:
        return SaveResult(saved=0, skipped=skipped)

    batch: ImportBatch | None = None
    if file_hash:
        batch = ImportBatch(
            file_hash=file_hash,
            file_name=file_name or "unknown",
            created_at=datetime.now(timezone.utc).isoformat(),
            row_count=len(new_rows),
        )
        db.add(batch)
        db.flush()

    for row in new_rows:
        db.add(TransactionRecord(
            batch_id=batch.id if batch else None,
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
        ))

    db.commit()
    return SaveResult(saved=len(new_rows), skipped=skipped)


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


def _record_to_review_row(r: TransactionRecord) -> ReviewRow:
    return {
        "transaction_date": r.transaction_date,
        "value_date": r.value_date,
        "narration": r.narration,
        "debit_amount": str(r.debit_amount),
        "credit_amount": str(r.credit_amount),
        "reference_number": r.reference_number,
        "closing_balance": str(r.closing_balance),
        "direction": r.direction,
        "channel": r.channel,
        "payee_name": r.payee_name or "",
        "upi_id": r.upi_id or "",
        "purpose": r.purpose or "",
        "matched_keyword": r.matched_keyword or "",
        "suggested_vendor": r.suggested_vendor or "",
        "category": r.category or "",
        "subcategory": r.subcategory or "",
        "stage": r.stage or "",
        "payment_mode": r.payment_mode or "",
        "confidence": str(r.confidence),
        "import_status": r.import_status,
        "review_reason": r.review_reason,
        "manual_notes": r.manual_notes,
    }

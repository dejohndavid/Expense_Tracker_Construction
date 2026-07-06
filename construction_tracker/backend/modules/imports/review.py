from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from decimal import Decimal
from io import StringIO
from typing import TypedDict

from backend.modules.imports.hdfc_parser import HdfcTransaction
from backend.modules.vendors.rule_engine import MatchStatus, classify_transaction


class ReviewRow(TypedDict):
    transaction_date: str
    value_date: str
    narration: str
    debit_amount: str
    credit_amount: str
    reference_number: str
    closing_balance: str
    direction: str
    channel: str
    payee_name: str
    upi_id: str
    purpose: str
    matched_keyword: str
    suggested_vendor: str
    category: str
    subcategory: str
    stage: str
    payment_mode: str
    confidence: str
    import_status: str
    review_reason: str
    manual_notes: str


def build_review_rows(transactions: Sequence[HdfcTransaction]) -> list[ReviewRow]:
    rows: list[ReviewRow] = []
    for transaction in transactions:
        match = classify_transaction(transaction)
        metadata = transaction.metadata
        rows.append(
            {
                "transaction_date": transaction.transaction_date.isoformat(),
                "value_date": transaction.value_date.isoformat(),
                "narration": transaction.narration,
                "debit_amount": _format_decimal(transaction.debit_amount),
                "credit_amount": _format_decimal(transaction.credit_amount),
                "reference_number": transaction.reference_number,
                "closing_balance": _format_decimal(transaction.closing_balance),
                "direction": str(transaction.direction),
                "channel": str(metadata.channel),
                "payee_name": metadata.payee_name or "",
                "upi_id": metadata.upi_id or "",
                "purpose": metadata.purpose or "",
                "matched_keyword": match.matched_keyword or "",
                "suggested_vendor": match.suggested_vendor or "",
                "category": match.category or "",
                "subcategory": match.subcategory or "",
                "stage": match.stage or "",
                "payment_mode": match.payment_mode or "",
                "confidence": f"{match.confidence:.2f}",
                "import_status": str(match.status),
                "review_reason": match.reason,
                "manual_notes": "",
            }
        )
    return rows


def ready_ledger_rows(rows: Iterable[ReviewRow]) -> list[dict[str, str]]:
    return [
        {
            "transaction_date": row["transaction_date"],
            "narration": row["narration"],
            "debit_amount": row["debit_amount"],
            "suggested_vendor": row["suggested_vendor"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "stage": row["stage"],
            "payment_mode": row["payment_mode"],
            "reference_number": row["reference_number"],
            "manual_notes": row["manual_notes"],
        }
        for row in rows
        if row["import_status"] == MatchStatus.READY
    ]


def rows_to_csv(rows: Iterable[dict[str, str] | ReviewRow]) -> str:
    materialized_rows = list(rows)
    if not materialized_rows:
        return ""

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(materialized_rows[0].keys()))
    writer.writeheader()
    writer.writerows(materialized_rows)
    return output.getvalue()


def sum_debits(rows: Iterable[ReviewRow]) -> Decimal:
    return sum((Decimal(row["debit_amount"]) for row in rows), Decimal("0"))


def _format_decimal(value: Decimal) -> str:
    return f"{value:.2f}"

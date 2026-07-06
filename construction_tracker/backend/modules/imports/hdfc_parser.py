from __future__ import annotations

import csv
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum


class TransactionDirection(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"
    ZERO = "zero"


class TransferChannel(StrEnum):
    UPI = "UPI"
    NEFT = "NEFT"
    ACH = "ACH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TransactionMetadata:
    channel: TransferChannel
    payee_name: str | None = None
    upi_id: str | None = None
    bank_code: str | None = None
    bank_reference: str | None = None
    purpose: str | None = None


@dataclass(frozen=True)
class HdfcTransaction:
    transaction_date: date
    narration: str
    value_date: date
    debit_amount: Decimal
    credit_amount: Decimal
    reference_number: str
    closing_balance: Decimal
    direction: TransactionDirection
    metadata: TransactionMetadata


HEADER_ALIASES = {
    "date": "date",
    "narration": "narration",
    "value dat": "value_date",
    "value date": "value_date",
    "debit amount": "debit_amount",
    "credit amount": "credit_amount",
    "chq/ref number": "reference_number",
    "closing balance": "closing_balance",
}

UPI_ID_PATTERN = re.compile(r"^[A-Z0-9._-]+@[A-Z0-9._-]+$", re.IGNORECASE)
NUMERIC_REF_PATTERN = re.compile(r"^\d{8,}$")


class HdfcParseError(ValueError):
    """Raised when an HDFC statement cannot be parsed."""


def parse_hdfc_text_statement(statement_text: str) -> list[HdfcTransaction]:
    lines = [line for line in statement_text.replace("\r\n", "\n").split("\n") if line.strip()]
    header_index = _find_header_index(lines)
    header = _normalize_header(next(csv.reader([lines[header_index]])))

    missing_columns = {
        "date",
        "narration",
        "value_date",
        "debit_amount",
        "credit_amount",
        "reference_number",
        "closing_balance",
    } - set(header)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise HdfcParseError(f"HDFC statement is missing required columns: {missing}")

    transactions: list[HdfcTransaction] = []
    statement_rows = csv.reader(lines[header_index + 1 :])
    for line_number, row in enumerate(statement_rows, start=header_index + 2):
        if not row or not any(cell.strip() for cell in row):
            continue

        values = _row_to_dict(header, row)
        try:
            transactions.append(_parse_transaction(values))
        except (InvalidOperation, ValueError) as exc:
            raise HdfcParseError(f"Invalid transaction row at line {line_number}: {exc}") from exc

    return transactions


def parse_hdfc_text_file(path: str) -> list[HdfcTransaction]:
    with open(path, encoding="utf-8") as statement_file:
        return parse_hdfc_text_statement(statement_file.read())


def _find_header_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        normalized = line.lower()
        if "narration" in normalized and "debit amount" in normalized:
            return index
    raise HdfcParseError("Could not find HDFC statement header row.")


def _normalize_header(raw_header: list[str]) -> list[str]:
    normalized: list[str] = []
    for column in raw_header:
        key = " ".join(column.strip().lower().split())
        normalized.append(HEADER_ALIASES.get(key, key.replace(" ", "_")))
    return normalized


def _row_to_dict(header: list[str], row: list[str]) -> dict[str, str]:
    if len(row) > len(header) and len(header) == 7:
        row = [row[0], ",".join(row[1:-5]), *row[-5:]]

    padded_row = [*row, *[""] * max(0, len(header) - len(row))]
    return {
        column: padded_row[index].strip()
        for index, column in enumerate(header)
        if index < len(padded_row)
    }


def _parse_transaction(values: dict[str, str]) -> HdfcTransaction:
    debit_amount = _parse_decimal(values["debit_amount"])
    credit_amount = _parse_decimal(values["credit_amount"])
    narration = _normalize_spaces(values["narration"])
    return HdfcTransaction(
        transaction_date=_parse_hdfc_date(values["date"]),
        narration=narration,
        value_date=_parse_hdfc_date(values["value_date"]),
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        reference_number=values["reference_number"].strip(),
        closing_balance=_parse_decimal(values["closing_balance"]),
        direction=_direction_for(debit_amount, credit_amount),
        metadata=extract_transaction_metadata(narration),
    )


def extract_transaction_metadata(narration: str) -> TransactionMetadata:
    normalized = _normalize_spaces(narration)
    upper_narration = normalized.upper()

    if upper_narration.startswith("UPI-"):
        return _extract_upi_metadata(normalized)
    if upper_narration.startswith("NEFT"):
        return _extract_neft_metadata(normalized)
    if upper_narration.startswith("ACH"):
        return _extract_ach_metadata(normalized)

    return TransactionMetadata(channel=TransferChannel.UNKNOWN)


def _extract_upi_metadata(narration: str) -> TransactionMetadata:
    parts = [part.strip() for part in narration.split("-") if part.strip()]
    if len(parts) < 2:
        return TransactionMetadata(channel=TransferChannel.UPI)

    upi_index = _first_index(parts, lambda part: bool(UPI_ID_PATTERN.match(part)))
    if upi_index is None:
        return TransactionMetadata(
            channel=TransferChannel.UPI,
            payee_name=parts[1] if len(parts) > 1 else None,
            bank_reference=_first_matching(parts, NUMERIC_REF_PATTERN),
            purpose=_last_meaningful_upi_token(parts),
        )

    upi_id = parts[upi_index]
    payee_end_index = upi_index
    if upi_index > 2 and _looks_like_upi_id_prefix(parts[upi_index - 1]):
        upi_id = f"{parts[upi_index - 1]}-{upi_id}"
        payee_end_index = upi_index - 1

    reference_index = _first_index(
        parts[upi_index + 1 :], lambda part: bool(NUMERIC_REF_PATTERN.match(part))
    )
    absolute_reference_index = (
        upi_index + 1 + reference_index if reference_index is not None else None
    )

    payee_name = " ".join(parts[1:payee_end_index]).strip() or None
    bank_code = parts[upi_index + 1] if len(parts) > upi_index + 1 else None
    bank_reference = (
        parts[absolute_reference_index] if absolute_reference_index is not None else None
    )
    purpose = None
    if absolute_reference_index is not None and len(parts) > absolute_reference_index + 1:
        purpose = " ".join(parts[absolute_reference_index + 1 :]).strip() or None

    return TransactionMetadata(
        channel=TransferChannel.UPI,
        payee_name=payee_name,
        upi_id=upi_id,
        bank_code=bank_code,
        bank_reference=bank_reference,
        purpose=purpose,
    )


def _extract_neft_metadata(narration: str) -> TransactionMetadata:
    parts = [part.strip() for part in narration.split("-") if part.strip()]
    return TransactionMetadata(
        channel=TransferChannel.NEFT,
        bank_code=parts[1] if len(parts) > 1 else None,
        payee_name=parts[2] if len(parts) > 2 else None,
        purpose=parts[3] if len(parts) > 3 else None,
        bank_reference=parts[-1] if len(parts) > 1 else None,
    )


def _extract_ach_metadata(narration: str) -> TransactionMetadata:
    parts = [part.strip() for part in narration.split("-") if part.strip()]
    return TransactionMetadata(
        channel=TransferChannel.ACH,
        payee_name=parts[1] if len(parts) > 1 else None,
        bank_reference=parts[2] if len(parts) > 2 else None,
    )


def _parse_hdfc_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%d/%m/%y").date()


def _parse_decimal(value: str) -> Decimal:
    cleaned = value.replace(",", "").strip()
    return Decimal(cleaned or "0")


def _direction_for(debit_amount: Decimal, credit_amount: Decimal) -> TransactionDirection:
    if debit_amount > 0:
        return TransactionDirection.DEBIT
    if credit_amount > 0:
        return TransactionDirection.CREDIT
    return TransactionDirection.ZERO


def _normalize_spaces(value: str) -> str:
    return " ".join(value.strip().split())


def _looks_like_upi_id_prefix(value: str) -> bool:
    return bool(
        value and " " not in value and "@" not in value and not NUMERIC_REF_PATTERN.match(value)
    )


def _first_index(parts: list[str], predicate: Callable[[str], bool]) -> int | None:
    for index, part in enumerate(parts):
        if predicate(part):
            return index
    return None


def _first_matching(parts: list[str], pattern: re.Pattern[str]) -> str | None:
    for part in parts:
        if pattern.match(part):
            return part
    return None


def _last_meaningful_upi_token(parts: list[str]) -> str | None:
    if len(parts) <= 2:
        return None
    last_token = parts[-1]
    return None if last_token.upper() == "UPI" else last_token

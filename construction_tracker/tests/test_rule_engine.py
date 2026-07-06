from datetime import date
from decimal import Decimal

from backend.modules.imports.hdfc_parser import (
    HdfcTransaction,
    TransactionDirection,
    TransactionMetadata,
    TransferChannel,
)
from backend.modules.vendors.rule_engine import MatchStatus, classify_transaction


def test_ramesh_payment_is_ready_for_wall_construction() -> None:
    result = classify_transaction(
        _transaction("UPI-RAMESH-RAMESH@OKHDFCBANK-HDFC0000001-569690930701-WALL CONSTRUCTION")
    )

    assert result.status == MatchStatus.READY
    assert result.suggested_vendor == "Ramesh"
    assert result.category == "Labour"
    assert result.subcategory == "Mason"
    assert result.stage == "Wall Construction"


def test_madesh_jcb_payment_is_ready_for_machinery() -> None:
    result = classify_transaction(
        _transaction(
            "UPI-MADESH NAIK-MADESHNAIK460-1@OKHDFCBANK-SBIN0040029-569690930707-JCB DIESEL",
            payee_name="MADESH NAIK",
            purpose="JCB DIESEL",
        )
    )

    assert result.status == MatchStatus.READY
    assert result.suggested_vendor == "Madesh"
    assert result.category == "Machinery"
    assert result.subcategory == "JCB"
    assert result.matched_keyword == "MADESH + JCB"


def test_cement_payment_is_ready_for_materials() -> None:
    result = classify_transaction(_transaction("UPI-SRI CEMENT STORE-CEMENT BILL"))

    assert result.status == MatchStatus.READY
    assert result.category == "Material"
    assert result.subcategory == "Cement"


def test_sand_rule_does_not_match_anand() -> None:
    result = classify_transaction(_transaction("UPI-ANAND SWEETS-ANAND@YBL-UPI"))

    assert result.status == MatchStatus.REVIEW
    assert result.category is None


def test_credit_transaction_is_ignored() -> None:
    result = classify_transaction(
        _transaction(
            "NEFT CR-CITI0000004-MUSARUBRA SOFTWARE INDIA PVT LTD-SALARY",
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("7000.00"),
            direction=TransactionDirection.CREDIT,
        )
    )

    assert result.status == MatchStatus.IGNORE
    assert result.reason == "Credit transaction"


def test_unknown_debit_requires_review() -> None:
    result = classify_transaction(_transaction("UPI-UNKNOWN SHOP-UNKNOWN@YBL-UPI"))

    assert result.status == MatchStatus.REVIEW
    assert result.reason == "No construction rule matched"


def _transaction(
    narration: str,
    *,
    debit_amount: Decimal = Decimal("1000.00"),
    credit_amount: Decimal = Decimal("0.00"),
    direction: TransactionDirection = TransactionDirection.DEBIT,
    payee_name: str | None = None,
    purpose: str | None = None,
) -> HdfcTransaction:
    return HdfcTransaction(
        transaction_date=date(2025, 11, 26),
        narration=narration,
        value_date=date(2025, 11, 26),
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        reference_number="0000569690930707",
        closing_balance=Decimal("312345.67"),
        direction=direction,
        metadata=TransactionMetadata(
            channel=TransferChannel.UPI,
            payee_name=payee_name,
            upi_id=None,
            bank_code=None,
            bank_reference="569690930707",
            purpose=purpose,
        ),
    )

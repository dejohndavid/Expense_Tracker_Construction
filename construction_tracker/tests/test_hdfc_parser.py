from datetime import date
from decimal import Decimal

import pytest

from backend.modules.imports.hdfc_parser import (
    HdfcParseError,
    TransactionDirection,
    TransferChannel,
    extract_transaction_metadata,
    parse_hdfc_text_statement,
)

SAMPLE_STATEMENT = "\n".join(
    [
        "Date,Narration,Value Dat,Debit Amount,Credit Amount,Chq/Ref Number,Closing Balance",
        (
            "26/11/25,"
            "UPI-MADESH NAIK M SO LA-MADESHNAIK460-1@OKHDFCBANK-SBIN0040029-"
            "569690930707-JCB DIESEL,"
            "26/11/25,10000.00,0.00,0000569690930707,312345.67"
        ),
        (
            "06/11/25,"
            "NEFT CR-CITI0000004-MUSARUBRA SOFTWARE INDIA PVT LTD-DEJOHN DAVID N-"
            "CITIN52025110651403386,"
            "06/11/25,0.00,7000.00,CITIN52025110651403386,309686.12"
        ),
        (
            "10/11/25,"
            "ACH D- CANFINHOMESLTD-200226000588,"
            "10/11/25,50988.00,0.00,0000002434389314,204833.58"
        ),
    ]
)


def test_parse_hdfc_text_statement_returns_typed_transactions() -> None:
    transactions = parse_hdfc_text_statement(SAMPLE_STATEMENT)

    assert len(transactions) == 3

    first = transactions[0]
    assert first.transaction_date == date(2025, 11, 26)
    assert first.value_date == date(2025, 11, 26)
    assert first.debit_amount == Decimal("10000.00")
    assert first.credit_amount == Decimal("0.00")
    assert first.reference_number == "0000569690930707"
    assert first.closing_balance == Decimal("312345.67")
    assert first.direction == TransactionDirection.DEBIT


def test_parse_hdfc_text_statement_handles_unquoted_commas_in_narration() -> None:
    statement = "\n".join(
        [
            "Date,Narration,Value Dat,Debit Amount,Credit Amount,Chq/Ref Number,Closing Balance",
            (
                "21/12/25,"
                "NEFT DR-UBIN0911747-MKSA PETROLEUM SERVICE-NETBANK, MUM-"
                "HDFCH00686468673-NB4VHVRMABP5RBY2,"
                "21/12/25,149000.00,0.00,HDFCH00686468673,808451.44"
            ),
        ]
    )

    transaction = parse_hdfc_text_statement(statement)[0]

    assert transaction.narration == (
        "NEFT DR-UBIN0911747-MKSA PETROLEUM SERVICE-NETBANK, MUM-"
        "HDFCH00686468673-NB4VHVRMABP5RBY2"
    )
    assert transaction.debit_amount == Decimal("149000.00")
    assert transaction.reference_number == "HDFCH00686468673"


def test_extract_upi_metadata_with_hyphenated_upi_id() -> None:
    metadata = extract_transaction_metadata(
        "UPI-MADESH NAIK M SO LA-MADESHNAIK460-1@OKHDFCBANK-SBIN0040029-569690930707-JCB DIESEL"
    )

    assert metadata.channel == TransferChannel.UPI
    assert metadata.payee_name == "MADESH NAIK M SO LA"
    assert metadata.upi_id == "MADESHNAIK460-1@OKHDFCBANK"
    assert metadata.bank_code == "SBIN0040029"
    assert metadata.bank_reference == "569690930707"
    assert metadata.purpose == "JCB DIESEL"


def test_extract_upi_metadata_with_simple_upi_id() -> None:
    metadata = extract_transaction_metadata(
        "UPI-ZEPTO-ZEPTOONLINE@YBL-YESB0YBLUPI-530584260921-UPI"
    )

    assert metadata.channel == TransferChannel.UPI
    assert metadata.payee_name == "ZEPTO"
    assert metadata.upi_id == "ZEPTOONLINE@YBL"
    assert metadata.bank_code == "YESB0YBLUPI"
    assert metadata.bank_reference == "530584260921"
    assert metadata.purpose == "UPI"


def test_extract_neft_credit_metadata() -> None:
    transaction = parse_hdfc_text_statement(SAMPLE_STATEMENT)[1]

    assert transaction.direction == TransactionDirection.CREDIT
    assert transaction.metadata.channel == TransferChannel.NEFT
    assert transaction.metadata.bank_code == "CITI0000004"
    assert transaction.metadata.payee_name == "MUSARUBRA SOFTWARE INDIA PVT LTD"
    assert transaction.metadata.purpose == "DEJOHN DAVID N"
    assert transaction.metadata.bank_reference == "CITIN52025110651403386"


def test_extract_ach_debit_metadata() -> None:
    transaction = parse_hdfc_text_statement(SAMPLE_STATEMENT)[2]

    assert transaction.direction == TransactionDirection.DEBIT
    assert transaction.metadata.channel == TransferChannel.ACH
    assert transaction.metadata.payee_name == "CANFINHOMESLTD"
    assert transaction.metadata.bank_reference == "200226000588"


def test_parse_hdfc_text_statement_rejects_missing_header() -> None:
    with pytest.raises(HdfcParseError, match="header row"):
        parse_hdfc_text_statement("not,a,valid,statement")

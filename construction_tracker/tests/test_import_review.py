from backend.modules.imports.hdfc_parser import parse_hdfc_text_statement
from backend.modules.imports.review import (
    build_review_rows,
    ready_ledger_rows,
    rows_to_csv,
    sum_debits,
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
    ]
)


def test_build_review_rows_adds_classification_fields() -> None:
    rows = build_review_rows(parse_hdfc_text_statement(SAMPLE_STATEMENT))

    assert rows[0]["import_status"] == "Ready"
    assert rows[0]["suggested_vendor"] == "Madesh"
    assert rows[0]["category"] == "Machinery"
    assert rows[0]["subcategory"] == "JCB"
    assert rows[1]["import_status"] == "Ignore"


def test_ready_ledger_rows_keeps_only_ready_transactions() -> None:
    rows = build_review_rows(parse_hdfc_text_statement(SAMPLE_STATEMENT))
    ledger_rows = ready_ledger_rows(rows)

    assert len(ledger_rows) == 1
    assert ledger_rows[0]["suggested_vendor"] == "Madesh"
    assert "credit_amount" not in ledger_rows[0]


def test_review_rows_can_be_exported_to_csv() -> None:
    rows = build_review_rows(parse_hdfc_text_statement(SAMPLE_STATEMENT))

    csv_text = rows_to_csv(rows)

    assert "transaction_date" in csv_text
    assert "narration" in csv_text
    assert "Madesh" in csv_text


def test_sum_debits_totals_review_rows() -> None:
    rows = build_review_rows(parse_hdfc_text_statement(SAMPLE_STATEMENT))

    assert sum_debits(rows) == 10000

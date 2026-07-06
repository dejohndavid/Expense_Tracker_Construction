from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

import streamlit as st

from backend.config.settings import get_settings
from backend.db.session import create_all_tables, get_db
from backend.modules.imports.hdfc_parser import HdfcParseError, parse_hdfc_text_statement
from backend.modules.imports.review import (
    ReviewRow,
    build_review_rows,
    ready_ledger_rows,
    rows_to_csv,
    sum_debits,
)
from backend.modules.reports.service import get_spend_summary
from backend.modules.transactions.service import save_review_rows
from backend.modules.vendors.rule_engine import DEFAULT_RULES, MatchStatus
from backend.modules.vendors.rule_loader import seed_default_rules

settings = get_settings()

# Ensure tables exist and rules are seeded on first run
create_all_tables()
_db_init = next(get_db())
seed_default_rules(_db_init)
_db_init.close()

st.set_page_config(page_title=settings.app_name, page_icon="₹", layout="wide")


def _format_currency(value: Decimal) -> str:
    return f"₹{value:,.2f}"


def _rule_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in DEFAULT_RULES:
        rows.append(
            {
                "rule": rule.name,
                "keywords": _format_keyword_groups(rule.keyword_groups),
                "vendor": rule.vendor,
                "category": rule.category,
                "subcategory": rule.subcategory,
                "stage": rule.stage,
                "payment_mode": rule.payment_mode,
                "priority": rule.priority,
            }
        )
    return rows


def _format_keyword_groups(keyword_groups: Iterable[tuple[str, ...]]) -> str:
    return " | ".join(" + ".join(group) for group in keyword_groups)


st.title(settings.app_name)
st.caption(f"Version {settings.app_version}")

uploaded_file = st.file_uploader(
    "Import HDFC statement",
    type=["txt"],
    help="Use the Text export from HDFC NetBanking.",
)

if uploaded_file is None:
    st.info("Upload the HDFC Text statement to parse transactions and review construction matches.")
    st.stop()

try:
    statement_text = uploaded_file.getvalue().decode("utf-8", errors="replace")
    transactions = parse_hdfc_text_statement(statement_text)
except HdfcParseError as exc:
    st.error(f"Could not parse this HDFC statement: {exc}")
    st.stop()

review_rows = build_review_rows(transactions)

total_debits = sum_debits(review_rows)
ready_rows = [row for row in review_rows if row["import_status"] == MatchStatus.READY]
review_needed_rows = [row for row in review_rows if row["import_status"] == MatchStatus.REVIEW]
ignored_rows = [row for row in review_rows if row["import_status"] == MatchStatus.IGNORE]
ready_debits = sum_debits(ready_rows)

metric_columns = st.columns(5)
metric_columns[0].metric("Transactions", len(review_rows))
metric_columns[1].metric("Ready", len(ready_rows))
metric_columns[2].metric("Needs review", len(review_needed_rows))
metric_columns[3].metric("Ignored", len(ignored_rows))
metric_columns[4].metric("Ready debit", _format_currency(ready_debits))

st.caption(f"Total debit imported: {_format_currency(total_debits)}")

review_tab, ledger_tab, reports_tab, rules_tab = st.tabs(
    ["Import Review", "Ready Ledger", "Reports", "Rules"]
)

with review_tab:
    st.subheader("Review transactions")
    edited_rows: list[ReviewRow] = st.data_editor(
        review_rows,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        disabled=[
            "transaction_date",
            "value_date",
            "narration",
            "debit_amount",
            "credit_amount",
            "reference_number",
            "closing_balance",
            "direction",
            "channel",
            "upi_id",
            "matched_keyword",
            "confidence",
            "review_reason",
        ],
        column_config={
            "import_status": st.column_config.SelectboxColumn(
                "Import Status",
                options=[status.value for status in MatchStatus],
                required=True,
            )
        },
    )

    col_csv, col_save = st.columns([3, 1])
    with col_csv:
        st.download_button(
            "Download reviewed CSV",
            rows_to_csv(edited_rows),
            file_name="hdfc_import_review.csv",
            mime="text/csv",
        )
    with col_save:
        if st.button("Save to database", type="primary"):
            db_gen = get_db()
            db = next(db_gen)
            try:
                saved = save_review_rows(db, edited_rows)
                st.success(f"Saved {len(saved)} transactions to the database.")
            except Exception as exc:
                st.error(f"Could not save: {exc}")
            finally:
                db.close()

with ledger_tab:
    st.subheader("Ledger export")
    ledger_rows = ready_ledger_rows(edited_rows)
    if ledger_rows:
        st.dataframe(ledger_rows, width="stretch", hide_index=True)
    else:
        st.warning("No transactions are marked Ready yet.")

    st.download_button(
        "Download ready ledger CSV",
        rows_to_csv(ledger_rows),
        file_name="construction_ready_ledger.csv",
        mime="text/csv",
        disabled=not ledger_rows,
    )

with reports_tab:
    st.subheader("Spend reports")
    db_gen = get_db()
    db = next(db_gen)
    try:
        summary = get_spend_summary(db)
    finally:
        db.close()

    if summary.total_transactions == 0:
        st.info("No transactions in the database yet. Save an import to see reports.")
    else:
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total transactions", summary.total_transactions)
        r2.metric("Ready", summary.ready_count)
        r3.metric("Needs review", summary.review_count)
        r4.metric("Ready spend", _format_currency(summary.ready_debit))

        if summary.by_category:
            st.subheader("Spend by category")
            st.dataframe(
                [
                    {
                        "category": row.category,
                        "subcategory": row.subcategory,
                        "transactions": row.transaction_count,
                        "total_debit": _format_currency(row.total_debit),
                    }
                    for row in summary.by_category
                ],
                hide_index=True,
                width="stretch",
            )

        if summary.by_stage:
            st.subheader("Spend by stage")
            st.dataframe(
                [
                    {
                        "stage": row.stage,
                        "transactions": row.transaction_count,
                        "total_debit": _format_currency(row.total_debit),
                    }
                    for row in summary.by_stage
                ],
                hide_index=True,
                width="stretch",
            )

with rules_tab:
    st.subheader("Classification rules")
    st.dataframe(_rule_rows(), width="stretch", hide_index=True)

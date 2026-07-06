# ruff: noqa: E402
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import get_settings  # noqa: E402
from backend.db.base import Base  # noqa: E402
from backend.db.models import ClassificationRuleRecord  # noqa: E402
from backend.db.session import _engine  # noqa: E402
from backend.modules.imports.hdfc_parser import (  # noqa: E402
    HdfcParseError,
    parse_hdfc_text_statement,
)
from backend.modules.imports.review import (  # noqa: E402
    ReviewRow,
    build_review_rows,
    ready_ledger_rows,
    rows_to_csv,
    sum_debits,
)
from backend.modules.reports.service import get_spend_summary  # noqa: E402
from backend.modules.transactions.service import save_review_rows  # noqa: E402
from backend.modules.vendors.rule_engine import MatchStatus  # noqa: E402
from backend.modules.vendors.rule_loader import (  # noqa: E402
    add_rule,
    delete_rule,
    keyword_text_to_raw,
    list_all_rules,
    load_rules,
    raw_to_keyword_text,
    seed_default_rules,
    toggle_rule,
)
from sqlalchemy.orm import sessionmaker  # noqa: E402

settings = get_settings()

# Ensure tables and default rules exist
Base.metadata.create_all(bind=_engine())
_SessionFactory = sessionmaker(bind=_engine())


def _db():  # type: ignore[no-untyped-def]
    return _SessionFactory()


@st.cache_resource
def _seed() -> None:
    db = _db()
    try:
        seed_default_rules(db)
    finally:
        db.close()


_seed()

st.set_page_config(page_title=settings.app_name, page_icon="₹", layout="wide")


def _format_currency(value: Decimal) -> str:
    return f"₹{value:,.2f}"


def _rule_table_rows(records: list[ClassificationRuleRecord]) -> list[dict[str, Any]]:
    return [
        {
            "id": r.id,
            "name": r.name,
            "keywords": raw_to_keyword_text(r.keyword_groups_raw).replace("\n", " | "),
            "vendor": r.vendor,
            "category": r.category,
            "subcategory": r.subcategory,
            "stage": r.stage,
            "payment_mode": r.payment_mode,
            "priority": r.priority,
            "enabled": r.enabled,
        }
        for r in records
    ]


st.title(settings.app_name)
st.caption(f"Version {settings.app_version}")

uploaded_file = st.file_uploader(
    "Import HDFC statement",
    type=["txt"],
    help="Use the Text export from HDFC NetBanking.",
)

# Load DB rules once per rerun — used for both classification and the Rules tab
_rules_db = _db()
try:
    active_rules = load_rules(_rules_db)
finally:
    _rules_db.close()

if uploaded_file is None:
    st.info("Upload the HDFC Text statement to parse transactions and review construction matches.")
    st.divider()
    _manage_rules_placeholder = st.container()
else:
    _manage_rules_placeholder = None

if uploaded_file is not None:
    try:
        statement_text = uploaded_file.getvalue().decode("utf-8", errors="replace")
        transactions = parse_hdfc_text_statement(statement_text)
    except HdfcParseError as exc:
        st.error(f"Could not parse this HDFC statement: {exc}")
        st.stop()

    review_rows = build_review_rows(transactions, active_rules)

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
                db = _db()
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
        db = _db()
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
        _render_rules_tab = rules_tab
else:
    _render_rules_tab = _manage_rules_placeholder  # type: ignore[assignment]

# Rules management — rendered in either the tab or the placeholder below the upload prompt
with _render_rules_tab:  # type: ignore[attr-defined]
    st.subheader("Classification rules")

    db = _db()
    try:
        all_records = list_all_rules(db)
    finally:
        db.close()

    st.dataframe(
        _rule_table_rows(all_records),
        hide_index=True,
        width="stretch",
        column_config={
            "enabled": st.column_config.CheckboxColumn("Enabled"),
            "priority": st.column_config.NumberColumn("Priority"),
        },
    )

    enabled_ids = [r.id for r in all_records if r.enabled]
    disabled_ids = [r.id for r in all_records if not r.enabled]

    toggle_col, delete_col = st.columns(2)

    with toggle_col:
        with st.expander("Enable / disable a rule"):
            if disabled_ids:
                enable_id = st.selectbox(
                    "Enable rule",
                    options=disabled_ids,
                    format_func=lambda i: next(r.name for r in all_records if r.id == i),
                    key="enable_select",
                )
                if st.button("Enable", key="btn_enable"):
                    db = _db()
                    try:
                        toggle_rule(db, enable_id, enabled=True)
                    finally:
                        db.close()
                    st.success("Rule enabled.")
                    st.rerun()
            else:
                st.caption("All rules are currently enabled.")

            if enabled_ids:
                disable_id = st.selectbox(
                    "Disable rule",
                    options=enabled_ids,
                    format_func=lambda i: next(r.name for r in all_records if r.id == i),
                    key="disable_select",
                )
                if st.button("Disable", key="btn_disable"):
                    db = _db()
                    try:
                        toggle_rule(db, disable_id, enabled=False)
                    finally:
                        db.close()
                    st.success("Rule disabled.")
                    st.rerun()

    with delete_col:
        with st.expander("Delete a rule"):
            if all_records:
                del_id = st.selectbox(
                    "Rule to delete",
                    options=[r.id for r in all_records],
                    format_func=lambda i: next(r.name for r in all_records if r.id == i),
                    key="delete_select",
                )
                if st.button("Delete", type="primary", key="btn_delete"):
                    db = _db()
                    try:
                        delete_rule(db, del_id)
                    finally:
                        db.close()
                    st.success("Rule deleted.")
                    st.rerun()
            else:
                st.caption("No rules to delete.")

    st.divider()
    st.subheader("Add new rule")
    with st.form("add_rule_form", clear_on_submit=True):
        st.caption(
            "Each line in **Keywords** is one keyword group. "
            "Multiple keywords in a group are comma-separated. "
            "ALL keywords in a group must appear for the rule to match. "
            "Any group matching is enough.\n\n"
            "Example — match MADESH + JCB together, or JCB alone:\n```\nMADESH, JCB\nJCB\n```"
        )
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            f_name = st.text_input("Rule name *", placeholder="Plumbing work")
            f_vendor = st.text_input("Vendor *", placeholder="Plumbing Contractor")
            f_category = st.text_input("Category *", placeholder="Civil")
            f_subcategory = st.text_input("Subcategory", placeholder="Plumbing")
        with f_col2:
            f_keywords = st.text_area(
                "Keywords * (one group per line, comma-separated within group)",
                placeholder="PLUMBING\nPIPE, FITTING",
                height=120,
            )
            f_stage = st.text_input("Stage", placeholder="Plumbing")
            f_payment_mode = st.selectbox(
                "Payment mode", options=["UPI", "Bank Transfer", "NEFT", "Cash", "Other"]
            )
            f_priority = st.number_input("Priority", min_value=1, max_value=999, value=100)

        submitted = st.form_submit_button("Add rule", type="primary")

    if submitted:
        errors = []
        if not f_name.strip():
            errors.append("Rule name is required.")
        if not f_vendor.strip():
            errors.append("Vendor is required.")
        if not f_category.strip():
            errors.append("Category is required.")
        if not f_keywords.strip():
            errors.append("At least one keyword is required.")
        elif not keyword_text_to_raw(f_keywords):
            errors.append("Keywords could not be parsed — check the format.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            db = _db()
            try:
                add_rule(
                    db,
                    name=f_name.strip(),
                    keyword_groups_raw=keyword_text_to_raw(f_keywords),
                    vendor=f_vendor.strip(),
                    category=f_category.strip(),
                    subcategory=f_subcategory.strip(),
                    stage=f_stage.strip(),
                    payment_mode=f_payment_mode,
                    priority=int(f_priority),
                )
            except Exception as exc:
                st.error(f"Could not save rule: {exc}")
            else:
                st.success(f"Rule '{f_name.strip()}' added. Re-upload your statement to apply it.")
                st.rerun()
            finally:
                db.close()

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from backend.modules.imports.hdfc_parser import HdfcTransaction, TransactionDirection


class MatchStatus(StrEnum):
    READY = "Ready"
    REVIEW = "Review"
    IGNORE = "Ignore"


@dataclass(frozen=True)
class ClassificationRule:
    name: str
    keyword_groups: tuple[tuple[str, ...], ...]
    vendor: str
    category: str
    subcategory: str
    stage: str
    payment_mode: str
    priority: int = 100


@dataclass(frozen=True)
class MatchResult:
    status: MatchStatus
    matched_keyword: str | None
    suggested_vendor: str | None
    category: str | None
    subcategory: str | None
    stage: str | None
    payment_mode: str | None
    confidence: float
    reason: str


DEFAULT_RULES: tuple[ClassificationRule, ...] = (
    ClassificationRule(
        name="Ramesh masonry labour",
        keyword_groups=(("RAMESH",), ("WALL CONSTRUCTION",)),
        vendor="Ramesh",
        category="Labour",
        subcategory="Mason",
        stage="Wall Construction",
        payment_mode="UPI",
        priority=300,
    ),
    ClassificationRule(
        name="JCB work",
        keyword_groups=(("MADESH", "JCB"), ("JCB",)),
        vendor="Madesh",
        category="Machinery",
        subcategory="JCB",
        stage="Excavation",
        payment_mode="UPI",
        priority=280,
    ),
    ClassificationRule(
        name="Tractor work",
        keyword_groups=(("MADESH", "TRACTOR"), ("TRACTOR",)),
        vendor="Madesh",
        category="Machinery",
        subcategory="Tractor",
        stage="Excavation",
        payment_mode="UPI",
        priority=270,
    ),
    ClassificationRule(
        name="Borewell work",
        keyword_groups=(("BOREWELL",),),
        vendor="Borewell Vendor",
        category="Civil",
        subcategory="Borewell",
        stage="Site Clearing",
        payment_mode="Bank Transfer",
        priority=260,
    ),
    ClassificationRule(
        name="Cement material",
        keyword_groups=(("CEMENT",),),
        vendor="Material Vendor",
        category="Material",
        subcategory="Cement",
        stage="Foundation",
        payment_mode="UPI",
        priority=220,
    ),
    ClassificationRule(
        name="Sand material",
        keyword_groups=(("M SAND",), ("M-SAND",), ("MSAND",), ("SAND",)),
        vendor="Material Vendor",
        category="Material",
        subcategory="M-Sand",
        stage="Foundation",
        payment_mode="UPI",
        priority=210,
    ),
    ClassificationRule(
        name="Steel material",
        keyword_groups=(("STEEL",),),
        vendor="Material Vendor",
        category="Material",
        subcategory="Steel",
        stage="Foundation",
        payment_mode="Bank Transfer",
        priority=205,
    ),
    ClassificationRule(
        name="Electrical work",
        keyword_groups=(("KAVERI ELECTRICAL",), ("NOVATEUR ELECTRICAL",), ("ELECTRICAL",)),
        vendor="Electrical Vendor",
        category="Electrical",
        subcategory="Electrical",
        stage="Electrical",
        payment_mode="UPI",
        priority=200,
    ),
)


def classify_transaction(
    transaction: HdfcTransaction,
    rules: Sequence[ClassificationRule] = DEFAULT_RULES,
) -> MatchResult:
    if transaction.direction == TransactionDirection.CREDIT:
        return MatchResult(
            status=MatchStatus.IGNORE,
            matched_keyword=None,
            suggested_vendor=None,
            category=None,
            subcategory=None,
            stage=None,
            payment_mode=None,
            confidence=1.0,
            reason="Credit transaction",
        )

    if transaction.direction != TransactionDirection.DEBIT:
        return MatchResult(
            status=MatchStatus.REVIEW,
            matched_keyword=None,
            suggested_vendor=None,
            category=None,
            subcategory=None,
            stage=None,
            payment_mode=None,
            confidence=0.0,
            reason="Transaction has no debit amount",
        )

    search_text = _transaction_search_text(transaction)
    best_match = _best_rule_match(search_text, rules)
    if best_match is None:
        return MatchResult(
            status=MatchStatus.REVIEW,
            matched_keyword=None,
            suggested_vendor=transaction.metadata.payee_name,
            category=None,
            subcategory=None,
            stage=None,
            payment_mode=str(transaction.metadata.channel),
            confidence=0.2,
            reason="No construction rule matched",
        )

    rule, keyword_group = best_match
    return MatchResult(
        status=MatchStatus.READY,
        matched_keyword=" + ".join(keyword_group),
        suggested_vendor=rule.vendor,
        category=rule.category,
        subcategory=rule.subcategory,
        stage=rule.stage,
        payment_mode=rule.payment_mode,
        confidence=_confidence_for(keyword_group),
        reason=f"Matched rule: {rule.name}",
    )


def _best_rule_match(
    search_text: str,
    rules: Sequence[ClassificationRule],
) -> tuple[ClassificationRule, tuple[str, ...]] | None:
    matches: list[tuple[int, int, ClassificationRule, tuple[str, ...]]] = []
    for rule in rules:
        for keyword_group in rule.keyword_groups:
            if all(_contains_phrase(search_text, keyword) for keyword in keyword_group):
                matches.append((rule.priority, len(keyword_group), rule, keyword_group))

    if not matches:
        return None

    _priority, _keyword_count, rule, keyword_group = max(
        matches,
        key=lambda match: (match[0], match[1], len(" ".join(match[3]))),
    )
    return rule, keyword_group


def _transaction_search_text(transaction: HdfcTransaction) -> str:
    fields = [
        transaction.narration,
        transaction.metadata.payee_name,
        transaction.metadata.upi_id,
        transaction.metadata.purpose,
        transaction.reference_number,
    ]
    return _normalize_for_match(" ".join(field for field in fields if field))


def _contains_phrase(search_text: str, phrase: str) -> bool:
    normalized_phrase = _normalize_for_match(phrase)
    return f" {normalized_phrase} " in f" {search_text} "


def _normalize_for_match(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", " ", value.upper())
    return " ".join(normalized.split())


def _confidence_for(keyword_group: tuple[str, ...]) -> float:
    return min(0.95, 0.80 + (len(keyword_group) * 0.05))

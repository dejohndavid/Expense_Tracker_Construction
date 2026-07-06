from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.models import ClassificationRuleRecord
from backend.modules.vendors.rule_engine import ClassificationRule, DEFAULT_RULES


def _encode_keyword_groups(keyword_groups: tuple[tuple[str, ...], ...]) -> str:
    return "\n".join("|".join(group) for group in keyword_groups)


def _decode_keyword_groups(raw: str) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(group.split("|")) for group in raw.strip().splitlines() if group.strip())


def seed_default_rules(db: Session) -> None:
    """Insert DEFAULT_RULES into the DB if the table is empty."""
    if db.query(ClassificationRuleRecord).count() > 0:
        return
    for rule in DEFAULT_RULES:
        db.add(
            ClassificationRuleRecord(
                name=rule.name,
                keyword_groups_raw=_encode_keyword_groups(rule.keyword_groups),
                vendor=rule.vendor,
                category=rule.category,
                subcategory=rule.subcategory,
                stage=rule.stage,
                payment_mode=rule.payment_mode,
                priority=rule.priority,
                enabled=True,
            )
        )
    db.commit()


def load_rules(db: Session) -> tuple[ClassificationRule, ...]:
    """Return all enabled rules ordered by priority descending."""
    records = (
        db.query(ClassificationRuleRecord)
        .filter(ClassificationRuleRecord.enabled.is_(True))
        .order_by(ClassificationRuleRecord.priority.desc())
        .all()
    )
    return tuple(
        ClassificationRule(
            name=r.name,
            keyword_groups=_decode_keyword_groups(r.keyword_groups_raw),
            vendor=r.vendor,
            category=r.category,
            subcategory=r.subcategory,
            stage=r.stage,
            payment_mode=r.payment_mode,
            priority=r.priority,
        )
        for r in records
    )

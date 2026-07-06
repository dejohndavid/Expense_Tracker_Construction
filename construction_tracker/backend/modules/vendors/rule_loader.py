from __future__ import annotations

from sqlalchemy.orm import Session

from backend.db.models import ClassificationRuleRecord
from backend.modules.vendors.rule_engine import ClassificationRule, DEFAULT_RULES


def _encode_keyword_groups(keyword_groups: tuple[tuple[str, ...], ...]) -> str:
    return "\n".join("|".join(group) for group in keyword_groups)


def _decode_keyword_groups(raw: str) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(group.split("|")) for group in raw.strip().splitlines() if group.strip())


def keyword_text_to_raw(text: str) -> str:
    """Convert user-entered keyword text to stored format.

    Each line is one keyword group; keywords within a group are comma-separated.
    Example input:  "MADESH, JCB\\nJCB"
    Stored as:      "MADESH|JCB\\nJCB"
    """
    groups = []
    for line in text.strip().splitlines():
        keywords = [k.strip().upper() for k in line.split(",") if k.strip()]
        if keywords:
            groups.append("|".join(keywords))
    return "\n".join(groups)


def raw_to_keyword_text(raw: str) -> str:
    """Convert stored format back to user-friendly text."""
    groups = []
    for line in raw.strip().splitlines():
        keywords = [k.strip() for k in line.split("|") if k.strip()]
        if keywords:
            groups.append(", ".join(keywords))
    return "\n".join(groups)


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


def list_all_rules(db: Session) -> list[ClassificationRuleRecord]:
    """Return all rules (enabled and disabled) ordered by priority descending."""
    return (
        db.query(ClassificationRuleRecord)
        .order_by(ClassificationRuleRecord.priority.desc(), ClassificationRuleRecord.id)
        .all()
    )


def add_rule(
    db: Session,
    *,
    name: str,
    keyword_groups_raw: str,
    vendor: str,
    category: str,
    subcategory: str,
    stage: str,
    payment_mode: str,
    priority: int = 100,
) -> ClassificationRuleRecord:
    record = ClassificationRuleRecord(
        name=name,
        keyword_groups_raw=keyword_groups_raw,
        vendor=vendor,
        category=category,
        subcategory=subcategory,
        stage=stage,
        payment_mode=payment_mode,
        priority=priority,
        enabled=True,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_rule(db: Session, rule_id: int) -> bool:
    record = db.get(ClassificationRuleRecord, rule_id)
    if record is None:
        return False
    db.delete(record)
    db.commit()
    return True


def toggle_rule(db: Session, rule_id: int, *, enabled: bool) -> bool:
    record = db.get(ClassificationRuleRecord, rule_id)
    if record is None:
        return False
    record.enabled = enabled  # type: ignore[assignment]
    db.commit()
    return True

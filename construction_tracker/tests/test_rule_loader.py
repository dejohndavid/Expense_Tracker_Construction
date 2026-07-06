from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.base import Base
import backend.db.models  # noqa: F401
from backend.modules.vendors.rule_engine import DEFAULT_RULES
from backend.modules.vendors.rule_loader import (
    _decode_keyword_groups,
    _encode_keyword_groups,
    load_rules,
    seed_default_rules,
)


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    yield session
    session.close()


def test_encode_decode_roundtrip() -> None:
    groups: tuple[tuple[str, ...], ...] = (("MADESH", "JCB"), ("JCB",))
    assert _decode_keyword_groups(_encode_keyword_groups(groups)) == groups


def test_seed_inserts_default_rules(db: Session) -> None:
    seed_default_rules(db)
    rules = load_rules(db)
    assert len(rules) == len(DEFAULT_RULES)


def test_seed_is_idempotent(db: Session) -> None:
    seed_default_rules(db)
    seed_default_rules(db)
    rules = load_rules(db)
    assert len(rules) == len(DEFAULT_RULES)


def test_load_rules_preserves_keyword_groups(db: Session) -> None:
    seed_default_rules(db)
    rules = load_rules(db)
    jcb_rule = next(r for r in rules if r.name == "JCB work")
    assert ("MADESH", "JCB") in jcb_rule.keyword_groups


def test_load_rules_ordered_by_priority_descending(db: Session) -> None:
    seed_default_rules(db)
    rules = load_rules(db)
    priorities = [r.priority for r in rules]
    assert priorities == sorted(priorities, reverse=True)

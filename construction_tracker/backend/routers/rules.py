from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.modules.vendors.rule_loader import load_rules

router = APIRouter(prefix="/rules", tags=["rules"])


class RuleOut(BaseModel):
    name: str
    keywords: str
    vendor: str
    category: str
    subcategory: str
    stage: str
    payment_mode: str
    priority: int


@router.get("/")
def get_rules(db: Annotated[Session, Depends(get_db)]) -> list[RuleOut]:
    rules = load_rules(db)
    return [
        RuleOut(
            name=r.name,
            keywords=" | ".join(" + ".join(g) for g in r.keyword_groups),
            vendor=r.vendor,
            category=r.category,
            subcategory=r.subcategory,
            stage=r.stage,
            payment_mode=r.payment_mode,
            priority=r.priority,
        )
        for r in rules
    ]

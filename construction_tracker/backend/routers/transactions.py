from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.modules.imports.review import ReviewRow
from backend.modules.transactions.service import list_transactions, save_review_rows

router = APIRouter(prefix="/transactions", tags=["transactions"])


class SaveRequest(BaseModel):
    rows: list[ReviewRow]


class TransactionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    transaction_date: str
    value_date: str
    narration: str
    debit_amount: str
    credit_amount: str
    reference_number: str
    direction: str
    channel: str
    payee_name: str | None
    suggested_vendor: str | None
    category: str | None
    subcategory: str | None
    stage: str | None
    import_status: str
    manual_notes: str


@router.post("/", status_code=201)
def save_transactions(
    body: SaveRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int]:
    if not body.rows:
        raise HTTPException(status_code=422, detail="rows must not be empty")
    records = save_review_rows(db, body.rows)
    return {"saved": len(records)}


@router.get("/")
def get_transactions(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TransactionOut]:
    records = list_transactions(db, status=status, limit=limit, offset=offset)
    return [TransactionOut.model_validate(r) for r in records]

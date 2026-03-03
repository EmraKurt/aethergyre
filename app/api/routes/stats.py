from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.schemas.schemas import SetsResponse
from app.db.models.card import Expansion

from app.api.deps import get_db

router = APIRouter(prefix="/stats", tags=["stats"])

# TODO: GET /stats/cards/popular  — most-cubed cards (queries CardStats view)
# TODO: GET /stats/cards/{oracle_id} — cube count for a specific card
# NOTE: CardStats is a materialized view — call the refresh task before querying.
#       See app/tasks/bk_refreash.py

@router.get("/sets", response_model=List[SetsResponse])
def get_sets(
    type: str | None = Query(None, description=" expansion | core | promo | draft_innovation"),
    db: Session = Depends(get_db)):

    conditions = []
    if type:
        conditions.append(Expansion.set_type == type)

    return db.execute(select(Expansion).where(*conditions)).scalars().all()
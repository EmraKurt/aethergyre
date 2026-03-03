from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.card import Card, OracleCard, Expansion
from app.schemas.schemas import CardHistoryResponse, CardSearchPage, SetsResponse

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/search", response_model=CardSearchPage)
def search_cards(
    name: str | None = None,
    # Color filters use Scryfall single-letter codes: W U B R G
    # contains() maps to Postgres @> — card must include ALL listed colors
    colors: list[str] | None = Query(None, description="Card colors, e.g. ?colors=W&colors=U"),
    color_identity: list[str] | None = Query(None, description="Commander color identity"),
    type_line: str | None = Query(None, description="Substring match, e.g. 'Creature — Dragon'"),
    cmc_min: float | None = Query(None, description="Minimum mana value (inclusive)"),
    cmc_max: float | None = Query(None, description="Maximum mana value (inclusive)"),
    rarity: str | None = Query(None, description="common | uncommon | rare | mythic"),
    # keywords uses @> too — card must have ALL listed keywords
    keywords: list[str] | None = Query(None, description="e.g. ?keywords=Flying&keywords=Haste"),
    set_code: str | None = Query(None, description="Expansion code, e.g. MH3"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Search cards with optional filters.
    Returns the **latest printing** of each matching oracle card
    (one result per unique card identity, newest set first).
    """
    # Build filter conditions separately so the same list can be reused
    # for both the count query and the results query.
    conditions = []

    if name:
        conditions.append(OracleCard.name.ilike(f"%{name}%"))
    if colors:
        conditions.append(OracleCard.color.contains(colors))
    if color_identity:
        conditions.append(OracleCard.color_identity.contains(color_identity))
    if type_line:
        conditions.append(OracleCard.type_line.ilike(f"%{type_line}%"))
    if cmc_min is not None:
        conditions.append(OracleCard.cmc >= cmc_min)
    if cmc_max is not None:
        conditions.append(OracleCard.cmc <= cmc_max)
    if rarity:
        conditions.append(Card.rarity == rarity)
    if keywords:
        conditions.append(OracleCard.keywords.contains(keywords))
    if set_code:
        conditions.append(Expansion.code == set_code.upper())

    # Shared joins
    def base():
        return (
            select(Card)
            .join(OracleCard, Card.oracle_id == OracleCard.oracle_id)
            .join(Expansion, Card.set_id == Expansion.id)
            .where(*conditions)
        )

    # Count distinct oracle cards (not raw rows) for accurate pagination
    total = db.execute(
        select(func.count(Card.oracle_id.distinct()))
        .join(OracleCard, Card.oracle_id == OracleCard.oracle_id)
        .join(Expansion, Card.set_id == Expansion.id)
        .where(*conditions)
    ).scalar_one()

    # DISTINCT ON (oracle_id): one row per card identity, newest printing first.
    # ORDER BY must lead with the DISTINCT ON column.
    results = db.execute(
        base()
        .order_by(OracleCard.oracle_id, desc(Card.release_date))
        .distinct(OracleCard.oracle_id)
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    return {"total": total, "limit": limit, "offset": offset, "results": results}


@router.get("/{oracle_id}", response_model=CardHistoryResponse)
def get_card_versions(oracle_id: UUID, db: Session = Depends(get_db)):
    """
    Returns oracle data + every printing of that card.
    Use this to power a 'choose your favourite art' modal.
    """
    card = db.execute(
        select(OracleCard).where(OracleCard.oracle_id == oracle_id)
    ).scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return card


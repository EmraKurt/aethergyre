from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List
from app.db.session import get_db
from app.db.models.card import Card, OracleCard
from app.schemas.schemas import CardSearchResponse, CardHistoryResponse

router = APIRouter(prefix="/cards")

@router.get("/search", response_model=List[CardSearchResponse])
def search_cards(name: str, db: Session = Depends(get_db)):
    """
    Returns the LATEST printing of cards matching the name.
    Useful for 'Add to Deck' features where you just want the newest version.
    """
    # This query finds distinct Oracle IDs but picks the one with the newest release_date
    stmt = (
        select(Card)
        .join(OracleCard)
        .where(OracleCard.name.ilike(f"%{name}%"))
        .order_by(OracleCard.name, desc(Card.release_date))
        .distinct(OracleCard.name)
    )
    return db.execute(stmt).scalars().all()

@router.get("/{oracle_id}/all-versions", response_model=CardHistoryResponse)
def get_card_versions(oracle_id: UUID, db: Session = Depends(get_db)):
    """
    Returns the Oracle data and EVERY printing of that card.
    Perfect for a 'Choose your favorite art' modal.
    """
    stmt = select(OracleCard).where(OracleCard.oracle_id == oracle_id)
    oracle_card = db.execute(stmt).scalar_one_or_none()
    
    if not oracle_card:
        raise HTTPException(status_code=404, detail="Card not found")
    return oracle_card
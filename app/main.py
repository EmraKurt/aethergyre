from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import engine
from app.db.models.card import OracleCard
from app.schemas.card import OracleCardSchema
from app.db.base import Base
from app.api.deps import get_db

app = FastAPI()

# Optional: create tables if they don’t exist
Base.metadata.create_all(bind=engine)

@app.get("/cards/{name}", response_model=OracleCardSchema)
def get_card_by_name(name: str, db: Session = Depends(get_db)):
    
    stmt = select(OracleCard).where(OracleCard.name == name)
    result = db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return card

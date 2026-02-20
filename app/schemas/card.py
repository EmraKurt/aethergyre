from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class CardImageSchema(BaseModel):
    size: str
    path: str

    class Config:
        from_attributes = True


class CardSchema(BaseModel):
    id: UUID
    collection_number: str
    rarity: Optional[str]
    release_date: datetime
    layout: Optional[str]
    artist: Optional[str]
    images: List[CardImageSchema] = []

    class Config:
        from_attributes = True


class OracleCardSchema(BaseModel):
    oracle_id: UUID
    name: str
    oracle_text: Optional[str]
    type_line: Optional[str]
    power: Optional[str]
    toughness: Optional[str]

    cards: List[CardSchema] = []

    class Config:
        from_attributes = True

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict

# Base for shared attributes
class CardImageSchema(BaseModel):
    size: str
    path: str
    model_config = ConfigDict(from_attributes=True)

class OracleBase(BaseModel):
    oracle_id: UUID
    name: str
    oracle_text: Optional[str] = None
    type_line: Optional[str] = None
    mana_cost: Optional[str] = None
    cmc: float
    colors: Optional[List[str]] = Field(None, alias="color")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# 1. The "Default Search" Result (A specific printing + its oracle data)
class CardSearchResponse(BaseModel):
    id: UUID  # The specific Card Print ID
    collection_number: str
    rarity: Optional[str] = None
    set_code: str = Field(..., validation_alias="set.code") # Accesses Expansion.code
    release_date: datetime
    image_map: Dict[str, str] # Uses your @property from the model
    
    # Nested Oracle Data
    oracle_data: OracleBase = Field(..., alias="oracle_card")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# 2. The "All Versions" Result (The Oracle card + a list of all prints)
class CardHistoryResponse(OracleBase):
    prints: List[CardSearchResponse] = Field(..., alias="cards")
    
    model_config = ConfigDict(from_attributes=True)
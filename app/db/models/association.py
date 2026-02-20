from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

# 1. THE ASSOCIATION MODEL
class CubeCard(Base):
    __tablename__ = 'cube_cards'
    
    # These two foreign keys link the Cube and the Card
    cube_id = Column(Integer, ForeignKey('cubes.id'), primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.id'), primary_key=True)
    
    # Metadata specific to THIS card in THIS cube
    quantity = Column(Integer, default=1)
    is_foil = Column(Boolean, default=False)
    
    # Link to the actual card data (read-only)
    card = relationship("Card")
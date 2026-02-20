from sqlalchemy import Column, Integer, String, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase
from app.db.models import Base

class CardStats(Base):
    """
    This class represents the Materialized View.
    It looks and acts like a normal Model for querying, 
    but it is backed by a view, not a table.
    """
    __tablename__ = "card_stats"
    
    # We define the columns so SQLAlchemy knows how to map them
    # Ensure 'card_id' is marked as primary_key so the ORM is happy
    card_id = Column(Integer, ForeignKey("cards.id"), primary_key=True)
    card_name = Column(String)
    appearance_count = Column(Integer)

    # We tell SQLAlchemy this is not a real table to prevent it 
    # from trying to 'CREATE TABLE' during migrations.
    __table_args__ = {"info": {"is_view": True}}

# THE RAW SQL FOR THE VIEW
# You would run this in a migration file (like Alembic)
CREATE_VIEW_SQL = """
CREATE MATERIALIZED VIEW card_stats AS
SELECT 
    cc.card_id, 
    c.name as card_name, 
    COUNT(cc.cube_id) as appearance_count
FROM cube_cards cc
JOIN cards c ON cc.card_id = c.id
GROUP BY cc.card_id, c.name;
"""

REFRESH_VIEW_SQL = "REFRESH MATERIALIZED VIEW card_stats;"
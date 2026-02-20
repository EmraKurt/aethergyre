from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, Float, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
from app.db.base import Base

class OracleCard(Base):
    __tablename__ = "oracle_cards"
    __table_args__ = (
    UniqueConstraint("oracle_id"),
    )

    oracle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    oracle_text: Mapped[str | None] = mapped_column(Text)
    type_line: Mapped[str | None] = mapped_column(String)
    power: Mapped[str | None] = mapped_column(String)
    toughness: Mapped[str | None] = mapped_column(String)

    color: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    cmc: Mapped[float | None] = mapped_column(Float)
    mana_cost: Mapped[str | None] = mapped_column(String)

    produced_mana: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    
    color_identity: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    loyalty: Mapped[str | None] = mapped_column(String)

    cards: Mapped[list["Card"]] = relationship(back_populates="oracle_card")


class Expansion(Base):
    __tablename__ = "sets"

    __table_args__ = (
    UniqueConstraint("name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    card_count: Mapped[int | None] = mapped_column(Integer)
    released_at: Mapped[datetime | None] = mapped_column(DateTime)
    set_type: Mapped[str | None] = mapped_column(String(40))
    icon: Mapped[str | None] = mapped_column(String)

    cards: Mapped[list["Card"]] = relationship(back_populates="set")


class Card(Base):
    __tablename__ = "cards"

    __table_args__ = (
    UniqueConstraint("collection_number", "set_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    oracle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("oracle_cards.oracle_id"),
        nullable=False,

    )

    collection_number: Mapped[str] = mapped_column(String)
    rarity: Mapped[str | None] = mapped_column(String)
    flavor_text: Mapped[str | None] = mapped_column(Text)

    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sets.id"),
        nullable=False,
    )

    artist: Mapped[str | None] = mapped_column(String)
    card_back_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    release_date: Mapped[datetime] = mapped_column(DateTime)
    
    layout: Mapped[str | None] = mapped_column(String)

    oracle_card: Mapped["OracleCard"] = relationship(back_populates="cards")
    set: Mapped["Expansion"] = relationship(back_populates="cards")
    images: Mapped[list["CardImage"]] = relationship(
    back_populates="card",
    cascade="all, delete-orphan",
    )
    


    @property
    def image_map(self) -> dict[str, str]:
        return {img.size: img.path for img in self.images}


class CardImage(Base):
    __tablename__ = "card_images"

    id: Mapped[int] = mapped_column(primary_key=True)

    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    size: Mapped[str] = mapped_column(
        String(20),  # "small", "normal", "large"
        nullable=False,
    )

    path: Mapped[str] = mapped_column(String, nullable=False)

    card: Mapped["Card"] = relationship(back_populates="images")

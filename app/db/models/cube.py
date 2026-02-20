from __future__ import annotations
from datetime import UTC, datetime

from sqlalchemy import String, Text, Integer, Date, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
from app.db.base import Base


class Cube(Base):
    __tablename__ = "cubes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cubename: Mapped[str] = mapped_column(String(100), nullable=False)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    create_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    user: Mapped["User"] = relationship(back_populates="cubes")

    cube_cards: Mapped[list["CubeCard"]] = relationship(
        back_populates="cube",
        cascade="all, delete-orphan",
    )


class CubeCard(Base):
    __tablename__ = "cube_cards"

    cube_id: Mapped[int] = mapped_column(
        ForeignKey("cubes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        primary_key=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    cube: Mapped["Cube"] = relationship(back_populates="cube_cards")
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.token import Token


class AlphaScore(Base):
    """Current explainable alpha score for a token. One row per token
    (unique on token_id) -- upserted on each ranking pass, same pattern
    as `tokens` itself. History isn't stored here; it's regenerable at
    any time from tokens + token_snapshots, so a separate history table
    would just be redundant storage for V1."""

    __tablename__ = "alpha_scores"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("tokens.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    factor_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    token: Mapped[Token] = relationship(back_populates="alpha_score")

    def __repr__(self) -> str:
        return f"<AlphaScore token_id={self.token_id} score={self.score}>"

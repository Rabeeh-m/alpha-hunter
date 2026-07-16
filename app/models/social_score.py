from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SocialScore(Base):
    """Current explainable social signal. Same current-state-upserted
    pattern as AlphaScore/ContractSecurity. NOT wired into the Alpha
    Score composite this milestone -- that connective step is deliberately
    separate, same as M14 was its own milestone after M13's core landed."""

    __tablename__ = "social_scores"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tokens.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    score: Mapped[int] = mapped_column(nullable=False)
    factor_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    possible_inorganic_growth: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SocialScore token_id={self.token_id} score={self.score}>"
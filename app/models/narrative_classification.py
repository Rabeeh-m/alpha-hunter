from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Narrative(StrEnum):
    AI = "ai"
    DEFI = "defi"
    GAMING = "gaming"
    RWA = "rwa"
    INFRASTRUCTURE = "infrastructure"
    ZK = "zk"
    PRIVACY = "privacy"
    DEPIN = "depin"
    MEME = "meme"
    LAYER2 = "layer2"
    BITCOIN_ECOSYSTEM = "bitcoin_ecosystem"
    OTHER = "other"  # includes "insufficient signal to classify confidently"


class NarrativeClassification(Base):
    """Current classification. One row per token, upserted -- but unlike
    every other current-state table so far (AlphaScore, ContractSecurity,
    SocialScore), this is NOT expected to be re-upserted repeatedly. Once
    classified, a token stays classified; the scheduled job only ever
    targets NEVER-classified tokens (see scheduler job below), so in
    practice this table fills once per token and stays put."""

    __tablename__ = "narrative_classifications"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    primary_narrative: Mapped[Narrative] = mapped_column(
        SAEnum(Narrative, name="narrative_enum"), nullable=False, index=True
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reasoning: Mapped[str] = mapped_column(String(280), nullable=False)

    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<NarrativeClassification token_id={self.token_id} narrative={self.primary_narrative}>"
        )

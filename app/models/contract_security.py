from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContractSecurity(Base):
    """Current contract security assessment. One row per token
    (upserted) -- same current-state pattern as alpha_scores (M8) and
    wallet_holdings (M11). Re-scanning replaces, doesn't append; a
    history-of-security-changes table (e.g. "ownership was renounced on
    this date") is plausible future work but not built here."""

    __tablename__ = "contract_securities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tokens.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    safety_score: Mapped[int] = mapped_column(nullable=False)
    flags: Mapped[list] = mapped_column(JSON, nullable=False)
    is_honeypot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_mintable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_open_source: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    buy_tax: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    sell_tax: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    owner_address: Mapped[str | None] = mapped_column(nullable=True)

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ContractSecurity token_id={self.token_id} safety_score={self.safety_score}>"
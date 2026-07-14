from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WalletHolding(Base):
    """CURRENT approximate balance of one wallet in one token, as of the
    last scan. Upserted per (token_id, wallet_id) -- like alpha_scores,
    this is current-state, not history; a holdings-over-time table is
    future work once scan volume justifies it.

    ACCURACY CAVEAT (see WalletDiscoveryService docstring): balance is
    reconstructed from a bounded transfer-log window, not full on-chain
    history. Treat as directional/approximate, not authoritative.
    """

    __tablename__ = "wallet_holdings"
    __table_args__ = (UniqueConstraint("token_id", "wallet_id", name="uq_holding_token_wallet"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    approximate_balance: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    rank: Mapped[int] = mapped_column(nullable=False)  # 1 = largest holder in this scan

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
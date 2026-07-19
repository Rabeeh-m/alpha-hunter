from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.token import Token
    from app.models.wallet import Wallet


class WhaleEventType(StrEnum):
    NEW_POSITION = "new_position"
    INCREASED = "increased"
    DECREASED = "decreased"
    # EXIT deliberately not modeled yet -- detecting a wallet fully
    # dropping out of top holders needs diffing the complete previous
    # top-N set, not a per-wallet balance comparison. Future work.


class WhaleEvent(Base):
    """A DETECTED, DISCRETE occurrence -- not current-state. Unlike
    AlphaScore/ContractSecurity/WalletHolding (all upserted, one row per
    entity), every whale event is its own row; the history IS the point.
    Never upserted, never overwritten."""

    __tablename__ = "whale_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    wallet_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[WhaleEventType] = mapped_column(
        SAEnum(WhaleEventType, name="whale_event_type_enum"), nullable=False
    )
    previous_balance: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    new_balance: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    change_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 2), nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # lazy="joined" -- the whale feed ALWAYS needs token+wallet info
    # alongside the event itself (see WhaleEventRead.from_event); this
    # is the "N+1 vs. one extra join" trade-off from M8, same call here.
    token: Mapped[Token] = relationship(lazy="joined")
    wallet: Mapped[Wallet] = relationship(lazy="joined")

    def __repr__(self) -> str:
        return f"<WhaleEvent {self.event_type} token={self.token_id} wallet={self.wallet_id}>"

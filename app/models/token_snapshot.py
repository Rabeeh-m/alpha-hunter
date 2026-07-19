from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TokenSnapshot(Base):
    """A point-in-time reading of a token's market data, captured once per
    ingestion cycle. This is what powers historical charts -- the `tokens`
    table itself only ever holds the CURRENT state (upserted in place),
    so without this table there would be no way to show "liquidity over
    the last 24h" at all.

    No retention policy yet -- this table grows unboundedly. Revisit with
    partitioning by captured_at once there's enough volume to matter
    (see docs/ARCHITECTURE.md Performance Considerations).
    """

    __tablename__ = "token_snapshots"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False, index=True
    )

    price_usd: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    liquidity_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    volume_24h_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    market_cap_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    fdv_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<TokenSnapshot token_id={self.token_id} @ {self.captured_at}>"

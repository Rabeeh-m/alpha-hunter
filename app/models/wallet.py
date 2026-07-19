from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.chain import Chain


class WalletType(StrEnum):
    UNKNOWN = "unknown"
    WHALE = "whale"
    SMART_MONEY = "smart_money"  # not classified yet -- needs pattern
    VC = "vc"  # detection across multiple tokens
    EXCHANGE = "exchange"  # (repeated winners, etc.) -- future
    INFLUENCER = "influencer"  # milestone. See Step 137.
    EARLY_ADOPTER = "early_adopter"


class Wallet(Base):
    """A blockchain address, tagged with a best-effort classification.

    unique on (chain, address) -- the same address string could
    theoretically collide across chains (extremely unlikely for real
    addresses, but not structurally impossible), so chain is part of
    the identity, matching the pattern already used for Token.
    """

    __tablename__ = "wallets"
    __table_args__ = (UniqueConstraint("chain", "address", name="uq_wallet_chain_address"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chain: Mapped[Chain] = mapped_column(
        SAEnum(Chain, name="chain_enum", create_type=False), nullable=False, index=True
    )
    address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    wallet_type: Mapped[WalletType] = mapped_column(
        SAEnum(WalletType, name="wallet_type_enum", create_type=False),
        default=WalletType.UNKNOWN,
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Confidence in the wallet_type tag, 0-100. NULL for UNKNOWN wallets
    # that have never been scanned into any ranking -- distinct from a
    # low-confidence 0, which would mean "we looked and found nothing
    # notable," not "we haven't looked."
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Wallet {self.address[:10]}... ({self.chain}) type={self.wallet_type}>"

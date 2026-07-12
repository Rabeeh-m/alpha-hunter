from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.models.chain import Chain


class Token(Base, TimestampMixin):
    """
    A discovered token on a given chain.

    Design note: (chain, contract_address) is the natural unique key — the
    same contract address can exist on two different chains as unrelated
    tokens, so `contract_address` alone cannot be unique.
    """

    __tablename__ = "tokens"
    __table_args__ = (UniqueConstraint("chain", "contract_address", name="uq_token_chain_address"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    chain: Mapped[Chain] = mapped_column(
        SAEnum(Chain, name="chain_enum"), nullable=False, index=True
    )
    contract_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pair_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    decimals: Mapped[int] = mapped_column(default=18, nullable=False)

    dex: Mapped[str | None] = mapped_column(String(64), nullable=True)
    liquidity_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    market_cap_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    fdv_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    volume_24h_usd: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    price_usd: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    holder_count: Mapped[int | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<Token {self.symbol} ({self.chain}:{self.contract_address[:10]}...)>"

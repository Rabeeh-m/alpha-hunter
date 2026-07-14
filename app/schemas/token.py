from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.chain import Chain
from app.models.token import Token


class TokenPage(BaseModel):
    items: list["TokenRead"]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = {"from_attributes": True}

class TokenCreate(BaseModel):
    chain: Chain
    contract_address: str
    pair_address: str | None = None
    name: str
    symbol: str
    dex: str | None = None
    liquidity_usd: Decimal | None = None
    market_cap_usd: Decimal | None = None
    fdv_usd: Decimal | None = None
    volume_24h_usd: Decimal | None = None
    price_usd: Decimal | None = None
    pair_created_at: datetime | None = None

class TokenRead(BaseModel):
    id: UUID
    chain: Chain
    contract_address: str
    pair_address: str | None
    name: str
    symbol: str
    dex: str | None
    liquidity_usd: Decimal | None
    market_cap_usd: Decimal | None
    fdv_usd: Decimal | None
    volume_24h_usd: Decimal | None
    price_usd: Decimal | None
    holder_count: int | None
    created_at: datetime
    pair_created_at: datetime | None = None

    model_config = {"from_attributes": True}

    alpha_score: Decimal | None = None
    alpha_score_breakdown: dict | None = None

    @classmethod
    def from_token(cls, token: Token) -> "TokenRead":
        """Plain model_validate(token) can't flatten this -- token.alpha_score
        is a related AlphaScore object, not the Decimal this schema expects."""
        data = {c.name: getattr(token, c.name) for c in Token.__table__.columns}
        data["alpha_score"] = token.alpha_score.score if token.alpha_score else None
        data["alpha_score_breakdown"] = token.alpha_score.factor_breakdown if token.alpha_score else None
        return cls(**data)

class TokenSnapshotRead(BaseModel):
    captured_at: datetime
    price_usd: Decimal | None
    liquidity_usd: Decimal | None
    volume_24h_usd: Decimal | None
    market_cap_usd: Decimal | None
    fdv_usd: Decimal | None

    model_config = {"from_attributes": True}

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from app.models.chain import Chain


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
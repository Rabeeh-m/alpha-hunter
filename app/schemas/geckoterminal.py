from __future__ import annotations

from pydantic import BaseModel


class GeckoTerminalAttributes(BaseModel):
    name: str | None = None
    base_token_price_usd: str | None = None
    reserve_in_usd: str | None = None
    fdv_usd: str | None = None
    market_cap_usd: str | None = None
    volume_usd: dict[str, str] | None = None
    pool_created_at: str | None = None


class GeckoTerminalTokenRef(BaseModel):
    id: str  # e.g. "eth_0xabc123..." — network prefix + address
    type: str = "token"


class GeckoTerminalRelationshipData(BaseModel):
    data: GeckoTerminalTokenRef


class GeckoTerminalRelationships(BaseModel):
    base_token: GeckoTerminalRelationshipData
    dex: GeckoTerminalRelationshipData | None = None


class GeckoTerminalPool(BaseModel):
    id: str
    attributes: GeckoTerminalAttributes
    relationships: GeckoTerminalRelationships

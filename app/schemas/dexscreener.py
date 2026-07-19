from __future__ import annotations

from pydantic import BaseModel, Field


class DexScreenerLiquidity(BaseModel):
    usd: float | None = None


class DexScreenerToken(BaseModel):
    address: str
    name: str | None = None
    symbol: str | None = None


class DexScreenerPair(BaseModel):
    """One entry from GET /latest/dex/tokens/{address}."""

    chain_id: str = Field(alias="chainId")
    dex_id: str | None = Field(default=None, alias="dexId")
    pair_address: str | None = Field(default=None, alias="pairAddress")
    base_token: DexScreenerToken = Field(alias="baseToken")
    price_usd: str | None = Field(default=None, alias="priceUsd")
    liquidity: DexScreenerLiquidity | None = None
    fdv: float | None = None
    market_cap: float | None = Field(default=None, alias="marketCap")
    volume: dict[str, float] | None = None
    pair_created_at: int | None = Field(default=None, alias="pairCreatedAt")

    model_config = {"populate_by_name": True}


class DexScreenerLink(BaseModel):
    type: str | None = None
    url: str | None = None


class DexScreenerTokenProfile(BaseModel):
    chain_id: str = Field(alias="chainId")
    token_address: str = Field(alias="tokenAddress")
    links: list[DexScreenerLink] = Field(default_factory=list)

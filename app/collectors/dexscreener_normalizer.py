from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.models.chain import Chain
from app.schemas.dexscreener import DexScreenerPair
from app.schemas.token import TokenCreate

# DexScreener's chainId strings -> our internal Chain enum
_CHAIN_MAP: dict[str, Chain] = {
    "ethereum": Chain.ETHEREUM,
    "base": Chain.BASE,
    "solana": Chain.SOLANA,
    "bsc": Chain.BNB_CHAIN,
    "arbitrum": Chain.ARBITRUM,
    "polygon": Chain.POLYGON,
    "avalanche": Chain.AVALANCHE,
    "optimism": Chain.OPTIMISM,
}


def _to_decimal(value: float | str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def normalize_pair(pair: DexScreenerPair) -> TokenCreate | None:
    """Convert a raw DexScreener pair into our internal TokenCreate schema.
    Returns None for chains we don't support, so the caller can skip them."""

    chain = _CHAIN_MAP.get(pair.chain_id)
    if chain is None:
        return None

    return TokenCreate(
        chain=chain,
        contract_address=pair.base_token.address,
        pair_address=pair.pair_address,
        name=pair.base_token.name or "Unknown",
        symbol=pair.base_token.symbol or "UNKNOWN",
        dex=pair.dex_id,
        liquidity_usd=_to_decimal(pair.liquidity.usd if pair.liquidity else None),
        market_cap_usd=_to_decimal(pair.market_cap),
        fdv_usd=_to_decimal(pair.fdv),
        volume_24h_usd=_to_decimal((pair.volume or {}).get("h24")),
        price_usd=_to_decimal(pair.price_usd),
    )
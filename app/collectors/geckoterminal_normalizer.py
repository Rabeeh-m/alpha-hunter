from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.models.chain import Chain
from app.schemas.geckoterminal import GeckoTerminalPool
from app.schemas.token import TokenCreate

# GeckoTerminal network slug -> our internal Chain enum
_CHAIN_MAP: dict[str, Chain] = {
    "eth": Chain.ETHEREUM,
    "base": Chain.BASE,
    "solana": Chain.SOLANA,
    "bsc": Chain.BNB_CHAIN,
    "arbitrum": Chain.ARBITRUM,
    "polygon_pos": Chain.POLYGON,
    "avax": Chain.AVALANCHE,
    "optimism": Chain.OPTIMISM,
}


def _to_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def normalize_pool(pool: GeckoTerminalPool, network: str) -> TokenCreate | None:
    """Convert a raw GeckoTerminal pool into our internal TokenCreate schema.
    Returns None for unsupported networks so the caller can skip them."""

    chain = _CHAIN_MAP.get(network)
    if chain is None:
        return None

    # base_token id looks like "eth_0xabc123..." — strip the network prefix
    token_ref_id = pool.relationships.base_token.data.id
    contract_address = token_ref_id.split("_", 1)[-1]

    attrs = pool.attributes
    name = attrs.name or "Unknown"
    # GeckoTerminal's pool "name" is often "TOKEN / WETH" — take the symbol-looking part
    symbol = name.split("/")[0].strip() if "/" in name else name
    # Truncate to fit the Symbol column (String(32)) to avoid truncation errors
    symbol = symbol[:32]

    return TokenCreate(
        chain=chain,
        contract_address=contract_address,
        name=name,
        symbol=symbol,
        liquidity_usd=_to_decimal(attrs.reserve_in_usd),
        market_cap_usd=_to_decimal(attrs.market_cap_usd),
        fdv_usd=_to_decimal(attrs.fdv_usd),
        volume_24h_usd=_to_decimal((attrs.volume_usd or {}).get("h24")),
        price_usd=_to_decimal(attrs.base_token_price_usd),
    )
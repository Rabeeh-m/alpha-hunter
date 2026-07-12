from __future__ import annotations

from enum import StrEnum


class Chain(StrEnum):
    """Supported blockchains. Plain Python enum — used as a column type, not a table,
    since the set of chains changes rarely and doesn't need FK relationships."""

    ETHEREUM = "ethereum"
    BASE = "base"
    SOLANA = "solana"
    BNB_CHAIN = "bnb_chain"
    ARBITRUM = "arbitrum"
    POLYGON = "polygon"
    AVALANCHE = "avalanche"
    OPTIMISM = "optimism"

from __future__ import annotations

from app.models.chain import Chain

# Etherscan's V2 API unifies most EVM chains under one API key via
# ?chainid=. Solana isn't EVM and has no chainid here -- it needs an
# entirely separate data source, deferred to a future milestone.
ETHERSCAN_CHAIN_IDS: dict[Chain, int] = {
    Chain.ETHEREUM: 1,
    Chain.BASE: 8453,
    Chain.BNB_CHAIN: 56,
    Chain.ARBITRUM: 42161,
    Chain.POLYGON: 137,
    Chain.AVALANCHE: 43114,
    Chain.OPTIMISM: 10,
}


def is_wallet_scan_supported(chain: Chain) -> bool:
    return chain in ETHERSCAN_CHAIN_IDS
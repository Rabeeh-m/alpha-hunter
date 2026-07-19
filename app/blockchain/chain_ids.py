from __future__ import annotations

from app.models.chain import Chain

# EIP-155 chain IDs -- a shared EVM standard, not specific to any one
# provider. The same dict works for Etherscan, GoPlus, or any future
# multichain EVM API. Solana isn't EVM and has no chain ID here.
EVM_CHAIN_IDS: dict[Chain, int] = {
    Chain.ETHEREUM: 1,
    Chain.BASE: 8453,
    Chain.BNB_CHAIN: 56,
    Chain.ARBITRUM: 42161,
    Chain.POLYGON: 137,
    Chain.AVALANCHE: 43114,
    Chain.OPTIMISM: 10,
}

# Kept as an alias -- existing M11 code imports this name.
ETHERSCAN_CHAIN_IDS = EVM_CHAIN_IDS


def is_evm_chain(chain: Chain) -> bool:
    return chain in EVM_CHAIN_IDS


# Kept as an alias -- existing M11 code imports this name.
is_wallet_scan_supported = is_evm_chain

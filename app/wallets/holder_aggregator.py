from __future__ import annotations

from decimal import Decimal

from app.schemas.etherscan import EtherscanTransfer

# Addresses whose "balance" from transfer aggregation is meaningless --
# mint (0x0) and common burn addresses. Without this exclusion, 0x0 would
# show up as a top "holder" simply by virtue of being the sender on every
# mint transaction, which is a data artifact, not a real wallet.
_EXCLUDED_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
}


def aggregate_net_balances(transfers: list[EtherscanTransfer]) -> dict[str, Decimal]:
    """Reconstructs approximate current balances from a transfer window.

    ACCURACY CAVEAT: this only reflects transfers WITHIN the fetched
    window (see EtherscanClient.get_recent_transfers limit). A wallet
    that acquired its balance before the window and hasn't transacted
    since will be UNDER-represented or missing entirely. This is a
    directional approximation for surfacing likely-large holders, not
    an authoritative balance -- do not present it to users as exact.
    """
    balances: dict[str, Decimal] = {}

    for transfer in transfers:
        decimals = int(transfer.token_decimal) if transfer.token_decimal else 18
        amount = Decimal(transfer.value) / (Decimal(10) ** decimals)

        from_addr = transfer.from_address.lower()
        to_addr = transfer.to_address.lower()

        if from_addr not in _EXCLUDED_ADDRESSES:
            balances[from_addr] = balances.get(from_addr, Decimal(0)) - amount
        if to_addr not in _EXCLUDED_ADDRESSES:
            balances[to_addr] = balances.get(to_addr, Decimal(0)) + amount

    # Drop non-positive balances -- a wallet whose net activity in the
    # window is <= 0 either fully exited or is a pass-through (e.g. a
    # router contract), neither of which belongs in a "top holders" list.
    return {addr: bal for addr, bal in balances.items() if bal > 0}


def rank_top_holders(balances: dict[str, Decimal], top_n: int = 20) -> list[tuple[str, Decimal, int]]:
    """Returns (address, balance, rank) sorted descending, rank 1-indexed."""
    ranked = sorted(balances.items(), key=lambda item: item[1], reverse=True)[:top_n]
    return [(addr, bal, i + 1) for i, (addr, bal) in enumerate(ranked)]
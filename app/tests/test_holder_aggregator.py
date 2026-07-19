from __future__ import annotations

from decimal import Decimal

from app.schemas.etherscan import EtherscanTransfer
from app.wallets.holder_aggregator import aggregate_net_balances, rank_top_holders


def _transfer(from_addr: str, to_addr: str, value: str, decimals: str = "18") -> EtherscanTransfer:
    return EtherscanTransfer(
        **{"from": from_addr, "to": to_addr, "value": value, "tokenDecimal": decimals}
    )


def test_aggregate_nets_incoming_and_outgoing():
    transfers = [
        _transfer("0xmint", "0xalice", "1000000000000000000000"),  # +1000 to alice
        _transfer("0xalice", "0xbob", "400000000000000000000"),  # -400 alice, +400 bob
    ]
    balances = aggregate_net_balances(transfers)
    assert balances["0xalice"] == Decimal("600")
    assert balances["0xbob"] == Decimal("400")


def test_aggregate_excludes_mint_and_burn_addresses():
    transfers = [
        _transfer("0x0000000000000000000000000000000000000000", "0xalice", "500000000000000000000")
    ]
    balances = aggregate_net_balances(transfers)
    assert "0x0000000000000000000000000000000000000000" not in balances
    assert balances["0xalice"] == Decimal("500")


def test_aggregate_drops_nonpositive_balances():
    transfers = [
        _transfer("0xmint", "0xalice", "100000000000000000000"),
        _transfer("0xalice", "0xbob", "100000000000000000000"),  # alice nets to 0
    ]
    balances = aggregate_net_balances(transfers)
    assert "0xalice" not in balances
    assert balances["0xbob"] == Decimal("100")


def test_rank_top_holders_sorts_descending_with_1indexed_rank():
    balances = {"0xa": Decimal("100"), "0xb": Decimal("500"), "0xc": Decimal("300")}
    ranked = rank_top_holders(balances, top_n=2)
    assert ranked == [("0xb", Decimal("500"), 1), ("0xc", Decimal("300"), 2)]

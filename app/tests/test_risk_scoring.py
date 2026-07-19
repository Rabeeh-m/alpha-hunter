from __future__ import annotations

from app.contracts.risk_scoring import compute_contract_risk
from app.schemas.goplus import GoPlusTokenSecurity


def _security(**overrides) -> GoPlusTokenSecurity:
    base = {"is_open_source": "1"}
    return GoPlusTokenSecurity(**{**base, **overrides})


def test_no_data_returns_neutral_score():
    result = compute_contract_risk(None)
    assert result.safety_score == 50


def test_clean_contract_scores_high():
    result = compute_contract_risk(_security())
    assert result.safety_score == 100
    assert "No significant risk flags" in result.flags[0]


def test_honeypot_crashes_score_near_zero():
    result = compute_contract_risk(_security(is_honeypot="1"))
    assert result.safety_score <= 10
    assert result.is_honeypot is True


def test_mintable_with_renounced_owner_not_penalized_as_hard():
    result = compute_contract_risk(
        _security(is_mintable="1", owner_address="0x0000000000000000000000000000000000000000")
    )
    assert result.safety_score == 100  # renounced -- mintable alone isn't penalized
    assert result.is_mintable is True


def test_mintable_without_renounced_owner_is_penalized():
    result = compute_contract_risk(_security(is_mintable="1", owner_address="0xrealowner"))
    assert result.safety_score < 100


def test_very_high_tax_penalized_more_than_high_tax():
    high = compute_contract_risk(_security(buy_tax="0.15", sell_tax="0.15"))
    very_high = compute_contract_risk(_security(buy_tax="0.30", sell_tax="0.30"))
    assert very_high.safety_score < high.safety_score


def test_unverified_source_penalized():
    result = compute_contract_risk(_security(is_open_source="0"))
    assert result.safety_score < 100
    assert result.is_open_source is False


def test_score_never_goes_below_zero():
    result = compute_contract_risk(
        _security(
            is_honeypot="1",
            can_take_back_ownership="1",
            hidden_owner="1",
            selfdestruct="1",
            transfer_pausable="1",
            is_blacklisted="1",
            is_open_source="0",
            buy_tax="0.5",
            sell_tax="0.5",
        )
    )
    assert result.safety_score == 0

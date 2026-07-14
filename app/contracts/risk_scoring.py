from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.schemas.goplus import GoPlusTokenSecurity

# Deductions from a 100-point baseline. Weighted by how likely the flag
# is to represent an actual loss-of-funds risk vs. a milder concern.
# is_honeypot alone drops the score to ~0 -- "you cannot sell this
# token" is categorically different from every other flag here, which
# is why it's not just "a big deduction" but effectively a floor.
_DEDUCTIONS: dict[str, int] = {
    "is_honeypot": 95,
    "can_take_back_ownership": 25,
    "hidden_owner": 20,
    "is_mintable_unrenounced": 25,   # composite flag, see below
    "selfdestruct": 15,
    "transfer_pausable": 12,
    "is_blacklisted": 10,             # contract HAS a blacklist function (not that this token IS blacklisted)
    "not_open_source": 20,
    "high_tax": 15,                    # buy or sell tax > 10%
    "very_high_tax": 30,                # buy or sell tax > 25% (replaces high_tax, not additive)
}

TAX_HIGH_THRESHOLD = Decimal("0.10")
TAX_VERY_HIGH_THRESHOLD = Decimal("0.25")


def _is_true(value: str | None) -> bool:
    return value == "1"


def _parse_tax(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value)
    except (ValueError, ArithmeticError):
        return None


@dataclass
class ContractRiskResult:
    safety_score: int  # 0-100, 100 = safest. NOT a guarantee -- see module docstring.
    flags: list[str] = field(default_factory=list)  # human-readable reasons, for explainability
    buy_tax: Decimal | None = None
    sell_tax: Decimal | None = None
    is_honeypot: bool = False
    is_mintable: bool = False
    is_open_source: bool = True
    owner_address: str | None = None


def compute_contract_risk(security: GoPlusTokenSecurity | None) -> ContractRiskResult:
    """Computes an explainable safety score from GoPlus's raw flags.

    IMPORTANT CAVEAT: this is a heuristic over automated static/dynamic
    analysis, not a guarantee. False positives/negatives happen,
    especially on very recently deployed contracts GoPlus hasn't fully
    indexed yet. Treat as "worth investigating further," not "verified
    safe" or "verified malicious."

    `security=None` (GoPlus has no data for this contract yet, e.g. too
    new) returns a neutral 50, not 0 or 100 -- absence of data is not
    evidence of either safety or danger.
    """
    if security is None:
        return ContractRiskResult(safety_score=50, flags=["No security data available yet from GoPlus"])

    score = 100
    flags: list[str] = []

    is_honeypot = _is_true(security.is_honeypot)
    if is_honeypot:
        score -= _DEDUCTIONS["is_honeypot"]
        flags.append("HONEYPOT: token may not be sellable")

    if _is_true(security.can_take_back_ownership):
        score -= _DEDUCTIONS["can_take_back_ownership"]
        flags.append("Ownership can be reclaimed after renouncement")

    if _is_true(security.hidden_owner):
        score -= _DEDUCTIONS["hidden_owner"]
        flags.append("Hidden owner detected")

    is_mintable = _is_true(security.is_mintable)
    owner_renounced = security.owner_address in (
        "0x0000000000000000000000000000000000000000", None,
    )
    if is_mintable and not owner_renounced:
        score -= _DEDUCTIONS["is_mintable_unrenounced"]
        flags.append("Mintable by a non-renounced owner")
    elif is_mintable:
        flags.append("Mintable, but ownership appears renounced")

    if _is_true(security.selfdestruct):
        score -= _DEDUCTIONS["selfdestruct"]
        flags.append("Contract contains a self-destruct function")

    if _is_true(security.transfer_pausable):
        score -= _DEDUCTIONS["transfer_pausable"]
        flags.append("Transfers can be paused by the contract owner")

    if _is_true(security.is_blacklisted):
        score -= _DEDUCTIONS["is_blacklisted"]
        flags.append("Contract has blacklist functionality")

    is_open_source = _is_true(security.is_open_source) if security.is_open_source is not None else True
    if not is_open_source:
        score -= _DEDUCTIONS["not_open_source"]
        flags.append("Contract source is not verified/open source")

    buy_tax = _parse_tax(security.buy_tax)
    sell_tax = _parse_tax(security.sell_tax)
    max_tax = max((t for t in (buy_tax, sell_tax) if t is not None), default=None)
    if max_tax is not None:
        if max_tax >= TAX_VERY_HIGH_THRESHOLD:
            score -= _DEDUCTIONS["very_high_tax"]
            flags.append(f"Very high tax detected ({max_tax:.0%})")
        elif max_tax >= TAX_HIGH_THRESHOLD:
            score -= _DEDUCTIONS["high_tax"]
            flags.append(f"Elevated tax detected ({max_tax:.0%})")

    if not flags:
        flags.append("No significant risk flags detected")

    return ContractRiskResult(
        safety_score=max(0, score), flags=flags, buy_tax=buy_tax, sell_tax=sell_tax,
        is_honeypot=is_honeypot, is_mintable=is_mintable, is_open_source=is_open_source,
        owner_address=security.owner_address,
    )
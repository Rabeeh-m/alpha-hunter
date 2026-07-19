from __future__ import annotations

import math
from datetime import UTC, datetime
from dataclasses import dataclass
from decimal import Decimal

# Weights sum to 1.0. Liquidity and liquidity-growth are weighted highest
# (0.25 each) because for an EARLY-STAGE discovery tool, "is there real,
# growing tradeable depth" is a stronger signal than raw size metrics --
# a token can have a large market cap and still be untradeable if
# liquidity is thin. This is a hand-tuned V1 baseline; V8/V9 (ML) will
# eventually learn weights from real historical outcomes instead of
# these best-guess constants.
WEIGHTS: dict[str, float] = {
    "liquidity": 0.16,
    "volume": 0.12,
    "market_cap": 0.08,
    "age": 0.08,
    "liquidity_growth": 0.16,
    "contract_safety": 0.21,
    "social_signal": 0.09,
    "developer_activity": 0.10,
}


def _log_scale_score(value: Decimal | float | None, floor: float, ceiling: float) -> float:
    """Maps a USD value to 0-100 on a log10 scale between floor/ceiling.
    Log, not linear, because the difference between $1k and $10k liquidity
    is meaningful signal; the difference between $5M and $6M isn't."""
    if value is None or value <= 0:
        return 0.0
    normalized = (math.log10(float(value)) - math.log10(floor)) / (math.log10(ceiling) - math.log10(floor))
    return max(0.0, min(100.0, normalized * 100))


def liquidity_score(liquidity_usd: Decimal | None) -> float:
    """$1k -> 0, $1M -> 100."""
    return _log_scale_score(liquidity_usd, floor=1_000, ceiling=1_000_000)


def volume_score(volume_24h_usd: Decimal | None) -> float:
    """$1k -> 0, $1M -> 100."""
    return _log_scale_score(volume_24h_usd, floor=1_000, ceiling=1_000_000)


def market_cap_score(market_cap_usd: Decimal | None) -> float:
    """$10k -> 0, $50M -> 100.

    V1 SIMPLIFICATION, flagged deliberately: this treats bigger market
    cap as monotonically better, which isn't quite right for an
    early-stage tool -- a $40M cap token has less room to run than a
    $500k one. A bell-curve 'sweet spot' function is the more correct
    model; deferred until V8/V9 has real outcome data to calibrate
    where that sweet spot actually sits, rather than guessing at it.
    """
    return _log_scale_score(market_cap_usd, floor=10_000, ceiling=50_000_000)


def age_score(created_at: datetime, now: datetime) -> float:
    """100 at the moment of discovery, decaying linearly to 0 over 30
    days -- this is a DISCOVERY platform; freshness is rewarded, not
    maturity."""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    age_days = (now - created_at).total_seconds() / 86400
    return max(0.0, min(100.0, 100.0 * (1 - age_days / 30)))


def liquidity_growth_score(
    earliest_liquidity: Decimal | None, latest_liquidity: Decimal | None
) -> float:
    """50 = neutral (no history, or 0% change). +100% growth -> 100
    (capped). Liquidity going to zero (rug pull) -> 0. Returns the
    neutral midpoint rather than 0 when history is missing -- a brand
    new token shouldn't be penalized as if it already failed."""
    if earliest_liquidity is None or latest_liquidity is None or earliest_liquidity <= 0:
        return 50.0
    pct_change = (float(latest_liquidity) - float(earliest_liquidity)) / float(earliest_liquidity)
    return max(0.0, min(100.0, 50.0 + pct_change * 50.0))


@dataclass
class ScoreBreakdown:
    liquidity: float
    volume: float
    market_cap: float
    age: float
    liquidity_growth: float
    contract_safety: float
    social_signal: float
    developer_activity: float

    @property
    def composite(self) -> float:
        return round(sum(getattr(self, key) * weight for key, weight in WEIGHTS.items()), 2)

    def to_dict(self) -> dict:
        result = {
            key: {"score": round(getattr(self, key), 2), "weight": WEIGHTS[key]} for key in WEIGHTS
        }
        result["composite"] = self.composite
        return result
    
    
def contract_safety_score(safety_score: int | None) -> float:
    """Directly uses ContractSecurity.safety_score (already 0-100, from
    M13's compute_contract_risk) -- no further transformation needed,
    unlike the log-scale USD factors above.

    None (never scanned) returns 50, matching compute_contract_risk's
    own "no data = neutral" convention from M13 -- an unscanned token
    should score the same here as one GoPlus has no data for, since
    from the ranking engine's perspective they're indistinguishable:
    absence of a security opinion either way.
    """
    if safety_score is None:
        return 50.0
    return float(safety_score)


def social_signal_score(social_score: int | None, possible_inorganic_growth: bool) -> float:
    """Pass-through of SocialScore.score (already 0-100 from M16), with
    one adjustment: a flagged inorganic-growth token gets its social
    contribution HALVED, not zeroed -- the flag means 'be skeptical of
    this number,' not 'this token has zero social value.' Zeroing it
    entirely would be an overcorrection for a heuristic that itself
    admits uncertainty (see member_growth_signal's docstring in M16).

    None (never scanned, or no Telegram link at all -- the two cases
    are indistinguishable from the ranking engine's view, same as
    contract_safety_score's None handling in M14) returns 50, neutral.
    """
    if social_score is None:
        return 50.0
    if possible_inorganic_growth:
        return social_score * 0.5
    return float(social_score)


def developer_activity_score(score: int | None) -> float:
    """Direct pass-through of DeveloperActivity.score (already 0-100
    from M19), same shape as contract_safety_score (M14) and
    social_signal_score (M17). None -- meaning EITHER never scanned OR
    no repo link exists at all, indistinguishable at this layer, same
    as every other *_score None-handling in this file -- returns
    neutral 50.

    Given most tokens will have no repo link (see M19's coverage
    note), this factor will sit at 50 for the large majority of
    tokens most of the time. That's expected and correct: absence of
    developer activity data is not evidence the project lacks
    developers -- plenty of legitimate projects don't publish a public
    repo, or don't link it from DexScreener."""
    if score is None:
        return 50.0
    return float(score)
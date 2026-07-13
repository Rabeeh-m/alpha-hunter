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
    "liquidity": 0.25,
    "volume": 0.20,
    "market_cap": 0.15,
    "age": 0.15,
    "liquidity_growth": 0.25,
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

    @property
    def composite(self) -> float:
        return round(sum(getattr(self, key) * weight for key, weight in WEIGHTS.items()), 2)

    def to_dict(self) -> dict:
        result = {
            key: {"score": round(getattr(self, key), 2), "weight": WEIGHTS[key]} for key in WEIGHTS
        }
        result["composite"] = self.composite
        return result
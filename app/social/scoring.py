from __future__ import annotations

import math
from dataclasses import dataclass, field

# A growth spike beyond this multiplier between scans doesn't get
# REWARDED the way liquidity_growth_score (M8) rewards liquidity
# increases -- it gets FLAGGED. Real organic community growth is
# gradual; a channel jumping from 500 to 5000 members between two scans
# a few hours apart is a much stronger signal of bot-purchased/inflated
# membership than of genuine interest. This is a deliberately different
# shape of function from every other *_growth_score in the codebase.
INORGANIC_GROWTH_MULTIPLIER_THRESHOLD = 3.0


def member_size_score(member_count: int | None) -> float:
    """50 -> 0, 50,000 -> 100. Same log-scale reasoning as liquidity_score (M8)."""
    if member_count is None or member_count <= 0:
        return 0.0
    normalized = (math.log10(member_count) - math.log10(50)) / (math.log10(50_000) - math.log10(50))
    return max(0.0, min(100.0, normalized * 100))


def activity_score(message_count_24h: int | None) -> float:
    """1 message/day -> 0, 200 messages/day -> 100."""
    if message_count_24h is None or message_count_24h <= 0:
        return 0.0
    normalized = (math.log10(message_count_24h) - math.log10(1)) / (math.log10(200) - math.log10(1))
    return max(0.0, min(100.0, normalized * 100))


def member_growth_signal(previous_count: int | None, current_count: int | None) -> tuple[float, bool]:
    """Returns (score, possible_inorganic_growth). 50 = neutral (no
    history or no change) -- same 'don't penalize missing history'
    convention as liquidity_growth_score (M8). A growth ratio above
    INORGANIC_GROWTH_MULTIPLIER_THRESHOLD flags the boolean AND caps the
    score at a mediocre 40 rather than rewarding it -- fast growth here
    is treated as suspicious, not celebrated, unlike every USD-based
    growth factor elsewhere in this codebase."""
    if previous_count is None or current_count is None or previous_count <= 0:
        return 50.0, False

    ratio = current_count / previous_count
    if ratio >= INORGANIC_GROWTH_MULTIPLIER_THRESHOLD:
        return 40.0, True

    pct_change = (current_count - previous_count) / previous_count
    return max(0.0, min(100.0, 50.0 + pct_change * 200)), False  # steeper than liquidity's *50 -- % moves are naturally smaller here


@dataclass
class SocialBreakdown:
    member_size: float
    activity: float
    member_growth: float
    possible_inorganic_growth: bool
    weights: dict = field(default_factory=lambda: {"member_size": 0.4, "activity": 0.35, "member_growth": 0.25})

    @property
    def composite(self) -> int:
        raw = (
            self.member_size * self.weights["member_size"]
            + self.activity * self.weights["activity"]
            + self.member_growth * self.weights["member_growth"]
        )
        return round(raw)

    def to_dict(self) -> dict:
        return {
            "member_size": {"score": round(self.member_size, 2), "weight": self.weights["member_size"]},
            "activity": {"score": round(self.activity, 2), "weight": self.weights["activity"]},
            "member_growth": {"score": round(self.member_growth, 2), "weight": self.weights["member_growth"]},
            "possible_inorganic_growth": self.possible_inorganic_growth,
            "composite": self.composite,
        }
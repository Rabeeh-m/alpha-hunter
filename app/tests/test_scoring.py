from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.ranking.scoring import age_score, liquidity_growth_score, liquidity_score, market_cap_score
from app.ranking.scoring import contract_safety_score


def test_liquidity_score_clips_below_floor():
    assert liquidity_score(Decimal("500")) == 0.0


def test_liquidity_score_at_ceiling():
    assert liquidity_score(Decimal("1000000")) == pytest.approx(100.0, abs=0.5)


def test_liquidity_score_none_is_zero():
    assert liquidity_score(None) == 0.0


def test_liquidity_score_midpoint_between_floor_and_ceiling():
    score = liquidity_score(Decimal("50000"))
    assert 0 < score < 100


def test_age_score_full_at_discovery():
    now = datetime.now(UTC)
    assert age_score(now, now) == pytest.approx(100.0)


def test_age_score_zero_after_30_days():
    now = datetime.now(UTC)
    assert age_score(now - timedelta(days=30), now) == pytest.approx(0.0, abs=0.5)


def test_age_score_midpoint_at_15_days():
    now = datetime.now(UTC)
    assert age_score(now - timedelta(days=15), now) == pytest.approx(50.0, abs=1)


def test_liquidity_growth_neutral_without_history():
    assert liquidity_growth_score(None, Decimal("1000")) == 50.0


def test_liquidity_growth_rewards_doubling():
    assert liquidity_growth_score(Decimal("1000"), Decimal("2000")) == pytest.approx(100.0)


def test_liquidity_growth_penalizes_rug_to_zero():
    assert liquidity_growth_score(Decimal("1000"), Decimal("0")) == pytest.approx(0.0)


def test_market_cap_score_penalizes_size_v1_simplification():
    """Documents the known V1 limitation -- larger cap always scores
    higher for now, even though that's not quite right for a discovery
    tool. See the docstring on market_cap_score() for the plan to fix this."""
    assert market_cap_score(Decimal("40000000")) > market_cap_score(Decimal("500000"))
    

def test_contract_safety_score_passes_through_directly():
    assert contract_safety_score(85) == 85.0


def test_contract_safety_score_none_is_neutral():
    assert contract_safety_score(None) == 50.0


def test_weights_still_sum_to_one():
    from app.ranking.scoring import WEIGHTS
    assert abs(sum(WEIGHTS.values()) - 1.0) < 0.0001
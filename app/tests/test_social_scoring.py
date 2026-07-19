from __future__ import annotations

from app.social.scoring import member_growth_signal, member_size_score


def test_member_size_score_scales_log():
    assert member_size_score(None) == 0.0
    assert 0 < member_size_score(1000) < 100
    assert member_size_score(50_000) == pytest.approx(100.0, abs=1)


def test_member_growth_neutral_without_history():
    score, flagged = member_growth_signal(None, 1000)
    assert score == 50.0
    assert flagged is False


def test_member_growth_flags_implausible_spike():
    score, flagged = member_growth_signal(500, 2000)  # 4x
    assert flagged is True
    assert score == 40.0


def test_member_growth_rewards_modest_organic_growth():
    score, flagged = member_growth_signal(1000, 1200)  # +20%
    assert flagged is False
    assert score > 50.0


import pytest  # placed at bottom deliberately -- move to top in your actual file; flagged so you notice and fix import ordering before running ruff

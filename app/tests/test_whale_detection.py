from __future__ import annotations

from decimal import Decimal

from app.models.whale_event import WhaleEventType
from app.wallets.whale_detection import MIN_NEW_POSITION_USD, classify_balance_change


def test_new_position_above_threshold_detected():
    detection = classify_balance_change(None, Decimal("10000"), price_usd=Decimal("1"))
    assert detection is not None
    assert detection.event_type == WhaleEventType.NEW_POSITION
    assert detection.change_pct is None


def test_new_position_below_threshold_ignored():
    detection = classify_balance_change(None, Decimal("100"), price_usd=Decimal("1"))
    assert detection is None


def test_increase_above_both_thresholds_detected():
    detection = classify_balance_change(Decimal("10000"), Decimal("15000"), price_usd=Decimal("1"))
    assert detection is not None
    assert detection.event_type == WhaleEventType.INCREASED
    assert detection.change_pct == Decimal("0.5")


def test_decrease_above_both_thresholds_detected():
    detection = classify_balance_change(Decimal("10000"), Decimal("5000"), price_usd=Decimal("1"))
    assert detection is not None
    assert detection.event_type == WhaleEventType.DECREASED


def test_small_pct_change_on_large_balance_ignored_if_usd_high_but_pct_low():
    # 5% change on a huge balance -- fails the 15% pct bar even though
    # the USD delta is large. Both thresholds must be met.
    detection = classify_balance_change(Decimal("1000000"), Decimal("1050000"), price_usd=Decimal("1"))
    assert detection is None


def test_large_pct_change_on_tiny_balance_ignored_below_usd_floor():
    detection = classify_balance_change(Decimal("10"), Decimal("20"), price_usd=Decimal("1"))
    assert detection is None  # +100% but only $10 absolute -- noise


def test_no_price_data_skips_increase_decrease_detection():
    detection = classify_balance_change(Decimal("10000"), Decimal("15000"), price_usd=None)
    assert detection is None
from __future__ import annotations

from app.models.wallet import WalletType
from app.wallets.classification import classify_holder


def test_rank_1_is_whale_with_highest_confidence():
    wallet_type, confidence = classify_holder(rank=1, total_ranked=20)
    assert wallet_type == WalletType.WHALE
    assert confidence == 90


def test_rank_4_and_beyond_stays_unknown():
    wallet_type, confidence = classify_holder(rank=4, total_ranked=20)
    assert wallet_type == WalletType.UNKNOWN
    assert confidence is None
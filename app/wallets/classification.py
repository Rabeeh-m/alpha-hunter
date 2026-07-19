from __future__ import annotations

from decimal import Decimal

from app.models.wallet import WalletType


# V2-M1 heuristic: ONLY rank-within-this-token informs the tag. This is
# deliberately conservative -- it does NOT claim to detect real smart
# money, VCs, or exchanges (those need cross-token pattern data or a
# labeled-address database, neither of which exists yet; see Step 137).
# A top-3 holder gets tagged WHALE with confidence decaying by rank;
# everything else stays UNKNOWN. Treat this as "worth a human look," not
# a verified classification.
def classify_holder(rank: int, total_ranked: int) -> tuple[WalletType, Decimal | None]:
    if rank <= 3:
        confidence = Decimal(str(max(40, 90 - (rank - 1) * 20)))  # 90, 70, 50
        return WalletType.WHALE, confidence
    return WalletType.UNKNOWN, None

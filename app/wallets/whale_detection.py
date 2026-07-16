from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models.whale_event import WhaleEventType

# Both thresholds must be met for INCREASED/DECREASED -- percentage alone
# lets tiny holders trigger noise (1 token -> 2 tokens = "+100%"); USD
# alone lets already-massive wallets trigger on statistically
# insignificant moves. NEW_POSITION uses a separate, lower bar since
# there's no "previous balance" to compute a % against.
MIN_CHANGE_PCT = Decimal("0.15")
MIN_CHANGE_USD = Decimal("1000")
MIN_NEW_POSITION_USD = Decimal("2000")


@dataclass
class WhaleEventDetection:
    event_type: WhaleEventType
    change_pct: Decimal | None
    change_usd: Decimal | None


def classify_balance_change(
    previous_balance: Decimal | None, new_balance: Decimal, price_usd: Decimal | None
) -> WhaleEventDetection | None:
    """Returns None if the change isn't significant enough to record.
    price_usd may be None (token has no known price) -- in that case
    change_usd is also None and only the NEW_POSITION path (which
    doesn't need USD) can still fire; INCREASED/DECREASED require a
    price to evaluate the USD threshold and are skipped without one."""

    if previous_balance is None or previous_balance == 0:
        change_usd = (new_balance * price_usd) if price_usd is not None else None
        if change_usd is not None and change_usd < MIN_NEW_POSITION_USD:
            return None
        return WhaleEventDetection(event_type=WhaleEventType.NEW_POSITION, change_pct=None, change_usd=change_usd)

    if price_usd is None:
        return None  # can't evaluate the USD threshold without a price

    delta = new_balance - previous_balance
    change_pct = delta / previous_balance
    change_usd = delta * price_usd

    if abs(change_pct) < MIN_CHANGE_PCT or abs(change_usd) < MIN_CHANGE_USD:
        return None

    event_type = WhaleEventType.INCREASED if delta > 0 else WhaleEventType.DECREASED
    return WhaleEventDetection(event_type=event_type, change_pct=change_pct, change_usd=change_usd)
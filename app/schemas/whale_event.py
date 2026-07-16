from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.chain import Chain
from app.models.wallet import WalletType
from app.models.whale_event import WhaleEvent, WhaleEventType


class WhaleEventRead(BaseModel):
    id: UUID
    token_symbol: str
    token_chain: Chain
    wallet_address: str
    wallet_label: str | None
    wallet_type: WalletType
    event_type: WhaleEventType
    previous_balance: Decimal | None
    new_balance: Decimal
    change_pct: Decimal | None
    change_usd: Decimal | None
    detected_at: datetime

    @classmethod
    def from_event(cls, event: WhaleEvent) -> "WhaleEventRead":
        return cls(
            id=event.id, token_symbol=event.token.symbol, token_chain=event.token.chain,
            wallet_address=event.wallet.address, wallet_label=event.wallet.label,
            wallet_type=event.wallet.wallet_type, event_type=event.event_type,
            previous_balance=event.previous_balance, new_balance=event.new_balance,
            change_pct=event.change_pct, change_usd=event.change_usd, detected_at=event.detected_at,
        )
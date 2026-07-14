from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.wallet import WalletType


class WalletHoldingRead(BaseModel):
    address: str
    wallet_type: WalletType
    confidence_score: Decimal | None
    approximate_balance: Decimal
    rank: int
    scanned_at: datetime

    model_config = {"from_attributes": True}
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ContractSecurityRead(BaseModel):
    safety_score: int
    flags: list[str]
    is_honeypot: bool
    is_mintable: bool
    is_open_source: bool
    buy_tax: Decimal | None
    sell_tax: Decimal | None
    owner_address: str | None
    scanned_at: datetime

    model_config = {"from_attributes": True}

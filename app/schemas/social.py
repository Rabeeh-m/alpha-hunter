from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SocialScoreRead(BaseModel):
    score: int
    factor_breakdown: dict
    possible_inorganic_growth: bool
    scanned_at: datetime

    model_config = {"from_attributes": True}
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.narrative_classification import Narrative


class NarrativeClassificationRead(BaseModel):
    primary_narrative: Narrative
    confidence: Decimal
    reasoning: str
    classified_at: datetime

    model_config = {"from_attributes": True}

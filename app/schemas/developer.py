from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DeveloperActivityRead(BaseModel):
    score: int
    flags: list[str]
    stars: int
    forks: int
    contributors_count: int
    last_commit_at: datetime | None
    is_fork: bool
    is_archived: bool
    scanned_at: datetime

    model_config = {"from_attributes": True}

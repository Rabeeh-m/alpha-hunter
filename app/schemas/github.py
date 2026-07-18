from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GitHubRepo(BaseModel):
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    pushed_at: datetime | None = None
    fork: bool = False
    archived: bool = False


class GitHubRelease(BaseModel):
    published_at: datetime | None = None
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobStats:
    """Best-effort in-memory stats for cheap health checks. The durable
    source of truth is job_runs -- these just avoid a DB round trip on
    every /health/scheduler poll."""

    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_run_at: datetime | None = None
    last_duration_ms: int | None = None
    last_status: str | None = None
    last_error: str | None = None


@dataclass
class JobDefinition:
    id: str
    name: str
    description: str
    category: str
    func: Callable[[], Awaitable[dict[str, int]]]
    interval_seconds: int
    enabled: bool = True
    stats: JobStats = field(default_factory=JobStats)


class JobRegistry:
    """Single source of truth for 'what jobs exist.' The scheduler, the
    execution wrapper, and the /jobs API all read from this instance --
    adding a new job means adding one JobDefinition here, never touching
    scheduler or execution logic."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobDefinition] = {}

    def register(self, job: JobDefinition) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> JobDefinition | None:
        return self._jobs.get(job_id)

    def all(self) -> list[JobDefinition]:
        return list(self._jobs.values())


job_registry = JobRegistry()
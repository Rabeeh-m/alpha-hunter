from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.database.session import async_session_factory
from app.models.job_run import JobRun, JobStatus
from app.scheduler.execution import execute_job
from app.scheduler.registry import JobDefinition


async def _succeeding_job() -> dict[str, int]:
    return {"provider-a": 3}


async def _failing_job() -> dict[str, int]:
    raise RuntimeError("simulated provider outage")


async def test_execute_job_persists_success_run():
    job = JobDefinition(
        id="test-success-job",
        name="Test Success",
        description="",
        category="test",
        func=_succeeding_job,
        interval_seconds=60,
    )

    await execute_job(job)

    assert job.stats.execution_count == 1
    assert job.stats.success_count == 1
    assert job.stats.last_status == JobStatus.SUCCESS.value

    async with async_session_factory() as session:
        result = await session.execute(
            select(JobRun).where(JobRun.job_id == "test-success-job")
        )
        run = result.scalars().first()
        assert run is not None
        assert run.status == JobStatus.SUCCESS
        assert run.records_collected == 3


async def test_execute_job_persists_failure_run():
    job = JobDefinition(
        id="test-failing-job",
        name="Test Failure",
        description="",
        category="test",
        func=_failing_job,
        interval_seconds=60,
    )

    await execute_job(job)

    assert job.stats.failure_count == 1
    assert job.stats.last_status == JobStatus.FAILED.value
    assert "simulated provider outage" in (job.stats.last_error or "")
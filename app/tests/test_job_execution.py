from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.job_run import JobRun, JobStatus
from app.scheduler.execution import execute_job
from app.scheduler.registry import JobDefinition


async def _succeeding_job() -> dict[str, int]:
    return {"provider-a": 3}


async def _failing_job() -> dict[str, int]:
    raise RuntimeError("simulated provider outage")


@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_factory = MagicMock(return_value=mock_session)
    return mock_factory, mock_session


async def test_execute_job_persists_success_run(mock_session_factory):
    mock_factory, mock_session = mock_session_factory

    with patch("app.scheduler.execution.async_session_factory", mock_factory):
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

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


async def test_execute_job_persists_failure_run(mock_session_factory):
    mock_factory, mock_session = mock_session_factory

    with patch("app.scheduler.execution.async_session_factory", mock_factory):
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
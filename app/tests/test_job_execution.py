from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import JobAlreadyRunning
from app.models.job_run import JobStatus
from app.scheduler.execution import execute_job, trigger_job_now
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


async def test_execute_job_skips_when_already_running(mock_session_factory):
    mock_factory, mock_session = mock_session_factory

    with (
        patch("app.scheduler.execution.async_session_factory", mock_factory),
        patch("app.scheduler.execution.job_lock") as mock_lock,
    ):
        mock_lock.return_value.__aenter__.side_effect = JobAlreadyRunning(
            "Job 'test-skip-job' is already running",
            details={"job_id": "test-skip-job"},
        )
        mock_lock.return_value.__aexit__ = AsyncMock()

        job = JobDefinition(
            id="test-skip-job",
            name="Test Already Running",
            description="",
            category="test",
            func=lambda: {"x": 1},
            interval_seconds=60,
        )

        await execute_job(job)

    assert job.stats.execution_count == 1
    assert job.stats.success_count == 1
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


async def test_execute_job_with_job_already_running_skips_job_func(mock_session_factory):
    mock_factory, mock_session = mock_session_factory
    func_called = False

    async def never_called():
        nonlocal func_called
        func_called = True
        return {"x": 1}

    with (
        patch("app.scheduler.execution.async_session_factory", mock_factory),
        patch("app.scheduler.execution.job_lock") as mock_lock,
    ):
        mock_lock.return_value.__aenter__.side_effect = JobAlreadyRunning(
            "Job 'test-skip' is already running",
            details={"job_id": "test-skip"},
        )
        mock_lock.return_value.__aexit__ = AsyncMock()

        job = JobDefinition(
            id="test-skip",
            name="Test Skip",
            description="",
            category="test",
            func=never_called,
            interval_seconds=60,
        )
        await execute_job(job)

    assert func_called is False


async def test_trigger_job_now_returns_true_for_registered_job(mock_session_factory):
    mock_factory, mock_session = mock_session_factory
    job = JobDefinition(
        id="test-trigger",
        name="Test Trigger",
        description="",
        category="test",
        func=lambda: {"x": 1},
        interval_seconds=60,
    )

    with (
        patch("app.scheduler.execution.async_session_factory", mock_factory),
        patch("app.scheduler.execution.job_registry") as mock_registry,
    ):
        mock_registry.get.return_value = job
        result = await trigger_job_now("test-trigger")

    assert result is True
    mock_registry.get.assert_called_once_with("test-trigger")


async def test_trigger_job_now_returns_false_for_missing_job():
    with patch("app.scheduler.execution.job_registry") as mock_registry:
        mock_registry.get.return_value = None
        result = await trigger_job_now("nonexistent")

    assert result is False
    mock_registry.get.assert_called_once_with("nonexistent")

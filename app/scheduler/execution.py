from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

import structlog

from app.core.database.session import async_session_factory
from app.core.exceptions import JobAlreadyRunning
from app.core.locks import job_lock
from app.core.logging import get_logger
from app.models.job_run import JobRun, JobStatus
from app.scheduler.registry import JobDefinition, job_registry

log = get_logger(__name__)


async def execute_job(job: JobDefinition) -> None:
    """Every scheduled job runs through this. It is the ONE place that
    handles locking, timing, structured logging with correlation_id, and
    persistence -- no job implementation duplicates this plumbing.

    Retry note: transient HTTP errors are already retried inside each
    collector's client (tenacity — see M3/M4). A second retry loop here
    would double-retry the same failure and turn one clear "provider is
    down" signal into three quick, confusing ones. A failed job simply
    waits for its next scheduled interval, or can be re-triggered
    immediately via POST /jobs/{id}/run.
    """
    correlation_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(job_id=job.id, correlation_id=correlation_id)

    started_at = datetime.now(UTC)
    start_perf = time.perf_counter()
    log.info("job_started", job_name=job.name, category=job.category)

    status = JobStatus.SUCCESS
    error_message: str | None = None
    records_collected = 0
    records_failed = 0

    try:
        async with job_lock(job.id):
            result = await job.func()
            records_collected = sum(result.values())
    except JobAlreadyRunning:
        log.warning("job_skipped_already_running", job_name=job.name)
        structlog.contextvars.unbind_contextvars("job_id", "correlation_id")
        return
    except Exception as exc:  # noqa: BLE001 -- must never propagate into the scheduler's own loop
        status = JobStatus.FAILED
        error_message = str(exc)
        records_failed = 1
        log.error("job_failed", job_name=job.name, error=str(exc), exc_info=True)
    finally:
        duration_ms = int((time.perf_counter() - start_perf) * 1000)
        finished_at = datetime.now(UTC)

        job.stats.execution_count += 1
        job.stats.last_run_at = finished_at
        job.stats.last_duration_ms = duration_ms
        job.stats.last_status = status.value
        job.stats.last_error = error_message
        if status == JobStatus.SUCCESS:
            job.stats.success_count += 1
        elif status == JobStatus.FAILED:
            job.stats.failure_count += 1

        async with async_session_factory() as session:
            session.add(
                JobRun(
                    job_id=job.id,
                    correlation_id=correlation_id,
                    status=status,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    records_collected=records_collected,
                    records_failed=records_failed,
                    error_message=error_message,
                )
            )
            await session.commit()

        log.info(
            "job_completed",
            job_name=job.name,
            status=status.value,
            duration_ms=duration_ms,
            records_collected=records_collected,
        )
        structlog.contextvars.unbind_contextvars("job_id", "correlation_id")


async def trigger_job_now(job_id: str) -> bool:
    """Backs POST /jobs/{id}/run for manual triggers."""
    job = job_registry.get(job_id)
    if job is None:
        return False
    await execute_job(job)
    return True
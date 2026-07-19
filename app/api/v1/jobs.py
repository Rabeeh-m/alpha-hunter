from __future__ import annotations

from contextlib import suppress
from datetime import datetime

from apscheduler.jobstores.base import JobLookupError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scheduler.execution import trigger_job_now
from app.scheduler.registry import JobDefinition, job_registry
from app.scheduler.scheduler import scheduler

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSummary(BaseModel):
    id: str
    name: str
    description: str
    category: str
    enabled: bool
    interval_seconds: int
    execution_count: int
    success_count: int
    failure_count: int
    last_run_at: datetime | None
    last_duration_ms: int | None
    last_status: str | None
    next_run_at: datetime | None


def _to_summary(job: JobDefinition) -> JobSummary:
    ap_job = scheduler.get_job(job.id)
    return JobSummary(
        id=job.id,
        name=job.name,
        description=job.description,
        category=job.category,
        enabled=job.enabled,
        interval_seconds=job.interval_seconds,
        execution_count=job.stats.execution_count,
        success_count=job.stats.success_count,
        failure_count=job.stats.failure_count,
        last_run_at=job.stats.last_run_at,
        last_duration_ms=job.stats.last_duration_ms,
        last_status=job.stats.last_status,
        next_run_at=getattr(ap_job, "next_run_time", None) if ap_job else None,
    )


@router.get("", response_model=list[JobSummary])
async def list_jobs() -> list[JobSummary]:
    return [_to_summary(j) for j in job_registry.all()]


@router.get("/{job_id}", response_model=JobSummary)
async def get_job(job_id: str) -> JobSummary:
    job = job_registry.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return _to_summary(job)


@router.post("/{job_id}/run")
async def run_job(job_id: str) -> dict[str, str]:
    if not await trigger_job_now(job_id):
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return {"status": "triggered", "job_id": job_id}


@router.post("/{job_id}/pause")
async def pause_job(job_id: str) -> dict[str, str]:
    job = job_registry.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    with suppress(JobLookupError):
        scheduler.pause_job(job_id)
    job.enabled = False
    return {"status": "paused", "job_id": job_id}


@router.post("/{job_id}/resume")
async def resume_job(job_id: str) -> dict[str, str]:
    job = job_registry.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    with suppress(JobLookupError):
        scheduler.resume_job(job_id)
    job.enabled = True
    return {"status": "resumed", "job_id": job_id}


# "disable"/"enable" are aliased to pause/resume -- APScheduler doesn't
# distinguish "temporarily paused" from "administratively disabled";
# building two code paths that do the same thing would just be duplication.
@router.post("/{job_id}/disable")
async def disable_job(job_id: str) -> dict[str, str]:
    return await pause_job(job_id)


@router.post("/{job_id}/enable")
async def enable_job(job_id: str) -> dict[str, str]:
    return await resume_job(job_id)

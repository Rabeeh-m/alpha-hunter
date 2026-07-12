from __future__ import annotations

from fastapi import APIRouter

from app.scheduler.registry import job_registry
from app.scheduler.scheduler import scheduler

router = APIRouter(tags=["system"])


@router.get("/health/scheduler")
async def health_scheduler() -> dict:
    jobs = job_registry.all()
    total_runs = sum(j.stats.execution_count for j in jobs)
    total_success = sum(j.stats.success_count for j in jobs)
    return {
        "scheduler_running": scheduler.running,
        "job_count": len(jobs),
        "total_executions": total_runs,
        "success_rate": (total_success / total_runs) if total_runs else None,
    }


@router.get("/health/jobs")
async def health_jobs() -> list[dict]:
    return [
        {
            "id": j.id,
            "enabled": j.enabled,
            "last_status": j.stats.last_status,
            "last_run_at": j.stats.last_run_at,
            "failure_count": j.stats.failure_count,
        }
        for j in job_registry.all()
    ]
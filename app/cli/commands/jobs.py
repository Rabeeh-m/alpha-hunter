from __future__ import annotations

import asyncio

import typer
from sqlalchemy import select

from app.core.database.session import async_session_factory
from app.core.logging import configure_logging
from app.models.job_run import JobRun
from app.scheduler.execution import execute_job
from app.scheduler.registry import job_registry
from app.scheduler.scheduler import register_jobs

jobs_app = typer.Typer(help="Inspect and manually trigger scheduled jobs.")


@jobs_app.command("list")
def list_jobs() -> None:
    """List registered jobs with their most recent PERSISTED run.

    Reads job_runs from the database, not in-memory JobStats -- the CLI
    is a separate process from the running API server and has no
    visibility into that process's memory. The database is the only
    state visible across process boundaries.
    """
    configure_logging()
    register_jobs()
    asyncio.run(_print_jobs())


async def _print_jobs() -> None:
    async with async_session_factory() as session:
        for job in job_registry.all():
            result = await session.execute(
                select(JobRun)
                .where(JobRun.job_id == job.id)
                .order_by(JobRun.started_at.desc())
                .limit(1)
            )
            last_run = result.scalars().first()
            status_line = (
                f"last: {last_run.status.value} @ {last_run.started_at.isoformat()}"
                if last_run
                else "last: never run"
            )
            typer.echo(f"{job.id:<24} {job.name:<32} {status_line}")


@jobs_app.command("run")
def run_job(job_id: str) -> None:
    """Trigger a single job immediately, outside its normal interval."""
    configure_logging()
    register_jobs()
    job = job_registry.get(job_id)
    if job is None:
        typer.secho(f"Unknown job '{job_id}'. Run 'jobs list' to see available jobs.", fg="red")
        raise typer.Exit(code=1)

    asyncio.run(execute_job(job))
    typer.secho(
        f"Triggered '{job_id}' -- check 'jobs list' or /health/jobs for the result.", fg="green"
    )

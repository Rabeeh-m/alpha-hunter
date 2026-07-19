from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # e.g. one provider returned 0 while another succeeded


class JobRun(Base):
    """One row per job execution.

    Deliberately NOT split into job_runs/job_failures -- a failure is a
    run with status=FAILED; splitting them forces a JOIN for any "recent
    activity including failures" query for no benefit. `scheduled_jobs`
    (job *definitions*) is also intentionally not a table -- definitions
    live in code (app/scheduler/registry.py), the standard APScheduler
    pattern for a single-tenant system like this one.
    """

    __tablename__ = "job_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    job_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status_enum"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    records_collected: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<JobRun {self.job_id} {self.status} @ {self.started_at}>"

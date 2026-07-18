from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DeveloperActivity(Base):
    __tablename__ = "developer_activities"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tokens.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    score: Mapped[int] = mapped_column(nullable=False)
    flags: Mapped[list] = mapped_column(JSONB, nullable=False)
    stars: Mapped[int] = mapped_column(default=0, nullable=False)
    forks: Mapped[int] = mapped_column(default=0, nullable=False)
    contributors_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TokenSocialSnapshot(Base):
    """One reading of Telegram channel stats, per scan. Append-only --
    growth (member_count over time) can only be computed from history,
    same reasoning as TokenSnapshot (M7). No retention policy yet, same
    flagged gap as M7's table."""

    __tablename__ = "token_social_snapshots"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_count: Mapped[int | None] = mapped_column(nullable=True)
    message_count_24h: Mapped[int | None] = mapped_column(nullable=True)

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

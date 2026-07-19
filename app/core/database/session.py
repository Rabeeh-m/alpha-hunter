from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

# Settings are loaded once at import time (they are simple pydantic settings)
_settings = get_settings()

# Module‑level placeholders for lazy singletons
_engine = None  # type: ignore[assignment]
_async_session_factory = None  # type: ignore[assignment]


def get_engine():
    """Return a lazily‑created :class:`AsyncEngine` bound to the current event loop.

    The engine (and its connection pool) must be created after the event loop is
    running; otherwise connections become attached to the wrong loop, causing the
    ``RuntimeError: Future attached to a different loop`` seen in the test suite.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            str(_settings.database_url),
            echo=_settings.database_echo,
            pool_size=_settings.database_pool_size,
            max_overflow=_settings.database_max_overflow,
            pool_pre_ping=True,  # detects stale connections before using them
        )
    return _engine


def get_async_session_factory():
    """Return a lazily‑created :class:`async_sessionmaker`.

    The factory is bound to the engine returned by :func:`get_engine`.  It is
    created on first use so that it is associated with the event loop that is
    active when the test (or the application) first needs a session.
    """
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,  # objects stay usable after commit
            autoflush=False,
        )
    return _async_session_factory


# Backward compatible aliases for existing imports
# These let existing ``from app.core.database.session import async_session_factory``
# continue working. ``async_session_factory`` is a callable that
# returns the lazily‑initialised sessionmaker, matching the previous API.
# Backward‑compatible callable aliases


def engine() -> AsyncEngine:
    """Return the lazily‑created async engine.

    This function mirrors the previous ``engine`` object but ensures the engine is
    instantiated only after an event loop is running.
    """
    return get_engine()


# Backward‑compatible alias for the async sessionmaker
async_session_factory = get_async_session_factory()


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: ``db: AsyncSession = Depends(get_db)``.

    Uses the lazily‑initialized session factory. The factory itself is callable
    to produce an :class:`AsyncSession`, so we invoke it with ``()`` inside the async with block.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

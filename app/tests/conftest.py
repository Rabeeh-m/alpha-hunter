import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.chain import Chain
from app.models.job_run import JobRun
from app.models.token import Token


@pytest.fixture(scope="session")
def test_engine():
    """Create a test SQLite engine with a single shared connection.

    Using StaticPool ensures all sessions share the same in-memory database,
    which persists for the test session. This is faster than PostgreSQL and
    avoids connection pooling issues.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session", autouse=True)
async def init_db(test_engine):
    """Create all tables in the test database once per session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Provide a transactional database session for a test.

    Each test gets a fresh transaction that is rolled back after the test,
    ensuring isolation while sharing the same in-memory database.
    """
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()



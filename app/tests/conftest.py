from decimal import Decimal

import pytest
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return compiler.process(JSON(), **kw)

from app.core.database import Base
from app.models.chain import Chain
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


@pytest.fixture
def app_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
async def seeded_tokens(db_session: AsyncSession) -> list[Token]:
    tokens = [
        Token(chain=Chain.BASE, contract_address="0xaaa", name="Alpha Coin", symbol="ALPHA", liquidity_usd=Decimal("50000")),
        Token(chain=Chain.BASE, contract_address="0xbbb", name="Beta Coin", symbol="BETA", liquidity_usd=None),
        Token(chain=Chain.ETHEREUM, contract_address="0xccc", name="Gamma Token", symbol="GAMMA", liquidity_usd=Decimal("10000")),
    ]
    for t in tokens:
        db_session.add(t)
    await db_session.flush()
    return tokens



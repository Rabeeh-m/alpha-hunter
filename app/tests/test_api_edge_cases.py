from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository

import tempfile

_TMPDIR = tempfile.mkdtemp(prefix="alpha_hunter_edge_")
URI = f"sqlite+aiosqlite:///{_TMPDIR}/edge.db"


@pytest.fixture(scope="session")
def edge_engine():
    engine = create_async_engine(URI, connect_args={"check_same_thread": False}, poolclass=NullPool)
    return engine


@pytest.fixture(scope="session", autouse=True)
async def init_edge_db(edge_engine):
    async with edge_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await edge_engine.dispose()


@pytest.fixture
async def db(edge_engine) -> AsyncSession:
    async_session_factory = async_sessionmaker(
        bind=edge_engine,
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


def _build_client(session):
    from app.main import create_app

    @asynccontextmanager
    async def noop_lifespan(_app) -> AsyncGenerator[None]:
        yield

    app = create_app()
    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides[get_db] = lambda: session
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return app, client


# -----------------------------------------------------------------------
# tokens.py
# -----------------------------------------------------------------------

@pytest.mark.usefixtures("app_env")
async def test_tokens_list_returns_page(db):
    repo = TokenRepository(db)
    token = await repo.add(Token(
        chain=Chain.BASE, contract_address="0xpage1", name="Page Token", symbol="PAGE",
        volume_24h_usd=Decimal("1000"),
    ))
    await db.flush()

    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["symbol"] == "PAGE"


@pytest.mark.usefixtures("app_env")
async def test_tokens_list_returns_empty_page(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/tokens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.usefixtures("app_env")
async def test_tokens_get_returns_404(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.get(f"/api/v1/tokens/{fake_id}")
    assert resp.status_code == 404





@pytest.mark.usefixtures("app_env")
async def test_tokens_snapshots_returns_404(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.get(f"/api/v1/tokens/{fake_id}/snapshots")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_tokens_snapshots_returns_empty_list(db):
    repo = TokenRepository(db)
    token = await repo.add(Token(
        chain=Chain.BASE, contract_address="0xsnp1", name="Snap Token", symbol="SNP",
    ))
    await db.flush()

    _, client = _build_client(db)
    async with client:
        resp = await client.get(f"/api/v1/tokens/{token.id}/snapshots")
    assert resp.status_code == 200
    assert resp.json() == []


# -----------------------------------------------------------------------
# jobs.py
# -----------------------------------------------------------------------

@pytest.fixture
def with_jobs():
    from app.scheduler.scheduler import register_jobs
    register_jobs()
    yield
    from app.scheduler.registry import job_registry
    job_registry._jobs.clear()


@pytest.mark.usefixtures("app_env")
async def test_jobs_list_returns_summaries(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.usefixtures("app_env")
async def test_jobs_get_returns_404(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/api/v1/jobs/nonexistent_job")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_jobs_run_returns_404(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/nonexistent_job/run")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_jobs_pause_returns_404(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/nonexistent_job/pause")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_jobs_resume_returns_404(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/nonexistent_job/resume")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_jobs_disable_returns_404(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/nonexistent_job/disable")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_jobs_enable_returns_404(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/nonexistent_job/enable")
    assert resp.status_code == 404


@pytest.mark.usefixtures("app_env")
async def test_jobs_run_triggers_job(db, with_jobs):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/refresh_dexscreener/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "triggered"


@pytest.mark.usefixtures("app_env")
async def test_jobs_pause_catches_job_lookup_error(db, with_jobs):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/refresh_dexscreener/pause")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "paused"


@pytest.mark.usefixtures("app_env")
async def test_jobs_resume_catches_job_lookup_error(db, with_jobs):
    _, client = _build_client(db)
    async with client:
        resp = await client.post("/api/v1/jobs/refresh_dexscreener/resume")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resumed"


# -----------------------------------------------------------------------
# wallets.py — uncovered lines 71, 78 (empty results)
# -----------------------------------------------------------------------

@pytest.mark.usefixtures("app_env")
async def test_wallets_whale_events_returns_empty_for_nonexistent_token(db):
    _, client = _build_client(db)
    fake_id = uuid4()
    async with client:
        resp = await client.get(f"/api/v1/tokens/{fake_id}/wallets/whale-events")
    assert resp.status_code == 200
    assert resp.json() == []


# -----------------------------------------------------------------------
# health.py
# -----------------------------------------------------------------------

@pytest.mark.usefixtures("app_env")
async def test_health_scheduler(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/health/scheduler")
    assert resp.status_code == 200
    data = resp.json()
    assert "scheduler_running" in data
    assert "job_count" in data


@pytest.mark.usefixtures("app_env")
async def test_health_jobs(db):
    _, client = _build_client(db)
    async with client:
        resp = await client.get("/health/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

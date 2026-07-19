from __future__ import annotations

import httpx
import pytest


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/alpha_hunter_test"
    )
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    from app.main import create_app

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_health_scheduler_returns_expected_shape(client):
    response = await client.get("/health/scheduler")
    assert response.status_code == 200
    body = response.json()
    assert "scheduler_running" in body
    assert "job_count" in body
    assert "total_executions" in body
    assert "success_rate" in body


async def test_health_jobs_returns_list(client):
    response = await client.get("/health/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

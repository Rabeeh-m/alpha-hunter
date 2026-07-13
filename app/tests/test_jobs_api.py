from __future__ import annotations

import httpx
import pytest

from app.scheduler.registry import JobDefinition, job_registry


async def _dummy_job() -> dict[str, int]:
    return {"noop": 0}


@pytest.fixture(autouse=True)
def _register_test_job():
    """Registers a throwaway job so these tests don't depend on the real
    scheduler jobs being registered yet (order-independent from
    app.main import side effects)."""
    test_job = JobDefinition(
        id="test-api-job", name="Test API Job", description="for API tests",
        category="test", func=_dummy_job, interval_seconds=60,
    )
    job_registry.register(test_job)
    yield
    job_registry._jobs.pop("test-api-job", None)


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/alpha_hunter_test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    from app.main import create_app
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_list_jobs_includes_registered_job(client):
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 200
    ids = [j["id"] for j in response.json()]
    assert "test-api-job" in ids


async def test_get_job_returns_404_for_unknown_id(client):
    response = await client.get("/api/v1/jobs/not-a-real-job")
    assert response.status_code == 404


async def test_get_job_returns_summary_for_known_id(client):
    response = await client.get("/api/v1/jobs/test-api-job")
    assert response.status_code == 200
    assert response.json()["name"] == "Test API Job"


async def test_pause_then_resume_job(client):
    pause_response = await client.post("/api/v1/jobs/test-api-job/pause")
    assert pause_response.status_code == 200
    assert job_registry.get("test-api-job").enabled is False

    resume_response = await client.post("/api/v1/jobs/test-api-job/resume")
    assert resume_response.status_code == 200
    assert job_registry.get("test-api-job").enabled is True


async def test_pause_unknown_job_returns_404(client):
    response = await client.post("/api/v1/jobs/not-a-real-job/pause")
    assert response.status_code == 404


async def test_disable_and_enable_are_aliased_to_pause_resume(client):
    disable_response = await client.post("/api/v1/jobs/test-api-job/disable")
    assert disable_response.status_code == 200
    assert job_registry.get("test-api-job").enabled is False

    enable_response = await client.post("/api/v1/jobs/test-api-job/enable")
    assert enable_response.status_code == 200
    assert job_registry.get("test-api-job").enabled is True
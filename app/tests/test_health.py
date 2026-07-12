from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/alpha_hunter_test"
    )
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")


@pytest.mark.usefixtures("app_env")
async def test_health_endpoint_returns_ok():
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

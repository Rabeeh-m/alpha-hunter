from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database.session import async_session_factory
from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository


@pytest.fixture
def app_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://alpha_hunter:alpha_hunter@localhost:5432/alpha_hunter")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
async def api_test_token():
    """Uses a unique tag in the symbol so this test can find exactly its
    own row via the search API without colliding with other test/dev
    data, and cleans up afterward via the repository's delete()."""
    tag = uuid.uuid4().hex[:8]
    async with async_session_factory() as session:
        repo = TokenRepository(session)
        token = Token(
            chain=Chain.BASE,
            contract_address=f"0xapitest{tag}",
            name=f"API Test Token {tag}",
            symbol=f"APITEST{tag}",
            liquidity_usd=12345,
        )
        await repo.add(token)
        await session.commit()
        yield token, tag
        await repo.delete(token)
        await session.commit()


@pytest.mark.usefixtures("app_env")
async def test_list_tokens_search_and_pagination_envelope(api_test_token):
    from app.main import create_app

    token, tag = api_test_token
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tokens", params={"q": tag, "page_size": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total"] == 1
    assert body["items"][0]["symbol"] == f"APITEST{tag}"
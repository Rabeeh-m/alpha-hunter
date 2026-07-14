from __future__ import annotations

import httpx
import pytest

from app.core.database.session import get_db
from app.core.exceptions import InvalidSortField
from app.models.chain import Chain
from app.repositories.token_repository import TokenRepository


async def test_search_filters_by_symbol(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, total = await repo.search(search="ALPHA")
    assert total == 1
    assert results[0].symbol == "ALPHA"


async def test_search_filters_by_chain(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, total = await repo.search(chain=Chain.ETHEREUM)
    assert total == 1
    assert results[0].chain == Chain.ETHEREUM


async def test_search_sorts_with_nulls_last(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, _ = await repo.search(sort="-liquidity_usd")
    assert results[0].symbol == "ALPHA"   # highest liquidity, first
    assert results[-1].symbol == "BETA"   # NULL liquidity, always last


async def test_search_raises_on_unknown_sort_field(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    with pytest.raises(InvalidSortField):
        await repo.search(sort="not_a_real_field; DROP TABLE tokens;")


async def test_search_pagination(db_session, seeded_tokens):
    repo = TokenRepository(db_session)
    results, total = await repo.search(page=1, page_size=2)
    assert total == 3
    assert len(results) == 2


@pytest.mark.usefixtures("app_env")
async def test_list_tokens_invalid_sort_returns_400(db_session):
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tokens", params={"sort": "malicious_field"})

    assert response.status_code == 400
    app.dependency_overrides.clear()
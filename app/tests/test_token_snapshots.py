from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chain import Chain
from app.models.token import Token
from app.repositories.token_repository import TokenRepository
from app.repositories.token_snapshot_repository import TokenSnapshotRepository


@pytest.fixture
async def seeded_token(db_session: AsyncSession) -> Token:
    repo = TokenRepository(db_session)
    token = Token(
        chain=Chain.BASE,
        contract_address=f"0xsnap_{uuid4().hex[:12]}",
        name="Snap Coin",
        symbol="SNAP",
        liquidity_usd=5000,
    )
    return await repo.add(token)


async def test_add_snapshot_captures_current_token_state(db_session, seeded_token):
    repo = TokenSnapshotRepository(db_session)
    snapshot = await repo.add_snapshot(seeded_token)

    assert snapshot.token_id == seeded_token.id
    assert snapshot.liquidity_usd == 5000


async def test_list_for_token_excludes_snapshots_before_since(db_session, seeded_token):
    repo = TokenSnapshotRepository(db_session)
    await repo.add_snapshot(seeded_token)
    await db_session.flush()

    recent = await repo.list_for_token(
        seeded_token.id, since=datetime.now(UTC) - timedelta(hours=1)
    )
    future_cutoff = await repo.list_for_token(
        seeded_token.id, since=datetime.now(UTC) + timedelta(hours=1)
    )

    assert len(recent) == 1
    assert len(future_cutoff) == 0


async def test_get_token_returns_404_for_unknown_id(db_session):
    from app.core.database import get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tokens/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


async def test_get_token_snapshots_returns_empty_list_for_new_token(db_session, seeded_token):
    from app.core.database import get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/tokens/{seeded_token.id}/snapshots", params={"hours": 1}
        )

    assert response.status_code == 200
    assert response.json() == []

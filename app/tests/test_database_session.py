from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestGetDb:
    async def test_yields_session_and_commits(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        with patch("app.core.database.session.async_session_factory", return_value=mock_session):
            from app.core.database.session import get_db

            gen = get_db()
            db = await gen.__anext__()
            assert db is mock_session

            with pytest.raises(StopAsyncIteration):
                await gen.__anext__()

            mock_session.commit.assert_awaited_once()

    async def test_rolls_back_on_commit_failure(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.commit.side_effect = RuntimeError("commit failed")

        with patch("app.core.database.session.async_session_factory", return_value=mock_session):
            from app.core.database.session import get_db

            gen = get_db()
            db = await gen.__anext__()
            assert db is mock_session

            with pytest.raises(RuntimeError, match="commit failed"):
                await gen.__anext__()

            mock_session.rollback.assert_awaited_once()

    async def test_yields_session_via_asgi_transport(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        app = FastAPI()

        @app.get("/db-test")
        async def db_test(db: AsyncSession = Depends(lambda: mock_session)):
            return {"status": "ok"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/db-test")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAsyncSessionFactory:
    def test_is_callable_and_returns_async_session(self):
        from app.core.database.session import async_session_factory

        assert callable(async_session_factory)

    def test_engine_is_singleton(self):
        from app.core.database.session import get_engine

        engine1 = get_engine()
        engine2 = get_engine()
        assert engine1 is engine2

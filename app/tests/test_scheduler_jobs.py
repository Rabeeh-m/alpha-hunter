from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.scheduler.jobs import compute_alpha_scores, refresh_dexscreener, refresh_geckoterminal


@pytest.fixture
def mock_session_factory():
    """Patches async_session_factory used inside app.scheduler.jobs so
    these tests never touch a real DB -- they're testing the WIRING
    (does refresh_dexscreener construct the right repos/service and
    call ingest_all), not the ingestion logic itself, which already has
    its own dedicated tests from M3/M4/M7."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_factory = AsyncMock(return_value=mock_session)
    return mock_factory, mock_session


async def test_refresh_dexscreener_calls_ingest_all_and_commits(mock_session_factory):
    mock_factory, mock_session = mock_session_factory

    with patch("app.scheduler.jobs.async_session_factory", mock_factory), \
         patch("app.scheduler.jobs.DexScreenerProvider") as MockProvider, \
         patch("app.scheduler.jobs.TokenIngestionService") as MockService:
        mock_provider_instance = AsyncMock()
        MockProvider.return_value = mock_provider_instance
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_all.return_value = {"dexscreener": 5}
        MockService.return_value = mock_service_instance

        result = await refresh_dexscreener()

        assert result == {"dexscreener": 5}
        mock_service_instance.ingest_all.assert_awaited_once()
        mock_session.commit.assert_awaited_once()
        mock_provider_instance.close.assert_awaited_once()


async def test_refresh_dexscreener_closes_provider_even_on_failure(mock_session_factory):
    """The `finally: await provider.close()` in refresh_dexscreener must
    run even when ingestion raises -- otherwise a failing job leaks an
    open httpx client every time it fails."""
    mock_factory, _ = mock_session_factory

    with patch("app.scheduler.jobs.async_session_factory", mock_factory), \
         patch("app.scheduler.jobs.DexScreenerProvider") as MockProvider, \
         patch("app.scheduler.jobs.TokenIngestionService") as MockService:
        mock_provider_instance = AsyncMock()
        MockProvider.return_value = mock_provider_instance
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_all.side_effect = RuntimeError("provider down")
        MockService.return_value = mock_service_instance

        with pytest.raises(RuntimeError, match="provider down"):
            await refresh_dexscreener()

        mock_provider_instance.close.assert_awaited_once()


async def test_refresh_geckoterminal_calls_ingest_all(mock_session_factory):
    mock_factory, mock_session = mock_session_factory

    with patch("app.scheduler.jobs.async_session_factory", mock_factory), \
         patch("app.scheduler.jobs.GeckoTerminalProvider") as MockProvider, \
         patch("app.scheduler.jobs.TokenIngestionService") as MockService:
        MockProvider.return_value = AsyncMock()
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_all.return_value = {"geckoterminal": 8}
        MockService.return_value = mock_service_instance

        result = await refresh_geckoterminal()

        assert result == {"geckoterminal": 8}
        mock_session.commit.assert_awaited_once()


async def test_compute_alpha_scores_calls_ranking_service(mock_session_factory):
    mock_factory, mock_session = mock_session_factory

    with patch("app.scheduler.jobs.async_session_factory", mock_factory), \
         patch("app.scheduler.jobs.RankingService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.compute_all.return_value = 12
        MockService.return_value = mock_service_instance

        result = await compute_alpha_scores()

        assert result == {"tokens_scored": 12}
        mock_session.commit.assert_awaited_once()
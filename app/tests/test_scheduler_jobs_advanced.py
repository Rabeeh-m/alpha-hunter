from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.chain import Chain
from app.scheduler.jobs import (
    classify_unclassified_narratives,
    scan_top_tokens_for_developer_activity,
    scan_top_tokens_for_social_activity,
    scan_top_tokens_for_whale_activity,
)


def _make_token(contract_address: str, chain: Chain = Chain.BASE) -> MagicMock:
    token = MagicMock(spec=["chain", "contract_address"])
    token.chain = chain
    token.contract_address = contract_address
    return token


@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_factory = MagicMock(return_value=mock_session)
    return mock_factory, mock_session


@pytest.fixture
def mock_tokens():
    return [_make_token("0xaaa"), _make_token("0xbbb"), _make_token("0xccc")]


class TestScanTopTokensForWhaleActivity:
    async def test_scans_evm_tokens(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory
        tokens = [_make_token("0xaaa"), _make_token("0xccc", Chain.ETHEREUM)]

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.EtherscanClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
            patch("app.scheduler.jobs.WalletDiscoveryService") as MockService,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.return_value = (tokens, len(tokens))
            MockTokenRepo.return_value = repo_instance
            service_instance = AsyncMock()
            MockService.return_value = service_instance

            result = await scan_top_tokens_for_whale_activity()

        assert result == {"tokens_scanned": 2}
        assert service_instance.scan_token.call_count == 2
        mock_session.commit.assert_awaited_once()
        mock_client_instance.close.assert_awaited_once()

    async def test_skips_solana_tokens(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory
        tokens = [_make_token("0xsol", Chain.SOLANA), _make_token("0xeth", Chain.ETHEREUM)]

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.EtherscanClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
            patch("app.scheduler.jobs.WalletDiscoveryService") as MockService,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.return_value = (tokens, len(tokens))
            MockTokenRepo.return_value = repo_instance
            service_instance = AsyncMock()
            MockService.return_value = service_instance

            result = await scan_top_tokens_for_whale_activity()

        assert result == {"tokens_scanned": 1}
        service_instance.scan_token.assert_awaited_once()
        args = service_instance.scan_token.call_args[0][0]
        assert args.chain == Chain.ETHEREUM

    async def test_closes_client_on_error(self, mock_session_factory):
        mock_factory, _ = mock_session_factory

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.EtherscanClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.side_effect = RuntimeError("db down")
            MockTokenRepo.return_value = repo_instance

            with pytest.raises(RuntimeError, match="db down"):
                await scan_top_tokens_for_whale_activity()

            mock_client_instance.close.assert_awaited_once()


class TestScanTopTokensForSocialActivity:
    async def test_scans_tokens(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory
        tokens = [_make_token("0xaaa"), _make_token("0xbbb")]

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.TelegramClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
            patch("app.scheduler.jobs.SocialIntelligenceService") as MockService,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.return_value = (tokens, len(tokens))
            MockTokenRepo.return_value = repo_instance
            service_instance = AsyncMock()
            MockService.return_value = service_instance

            result = await scan_top_tokens_for_social_activity()

        assert result == {"tokens_scanned": 2, "tokens_skipped_no_link": 0}
        assert service_instance.scan_token.call_count == 2
        mock_session.commit.assert_awaited_once()
        mock_client_instance.close.assert_awaited_once()

    async def test_skips_missing_telegram_link(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory
        tokens = [_make_token("0xaaa"), _make_token("0xbbb")]

        from app.services.social_intelligence_service import NoTelegramLinkAvailable

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.TelegramClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
            patch("app.scheduler.jobs.SocialIntelligenceService") as MockService,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.return_value = (tokens, len(tokens))
            MockTokenRepo.return_value = repo_instance
            service_instance = AsyncMock()
            service_instance.scan_token.side_effect = [NoTelegramLinkAvailable("0xaaa"), None]
            MockService.return_value = service_instance

            result = await scan_top_tokens_for_social_activity()

        assert result == {"tokens_scanned": 1, "tokens_skipped_no_link": 1}
        assert service_instance.scan_token.call_count == 2

    async def test_closes_client_on_error(self, mock_session_factory):
        mock_factory, _ = mock_session_factory

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.TelegramClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.side_effect = RuntimeError("db down")
            MockTokenRepo.return_value = repo_instance

            with pytest.raises(RuntimeError, match="db down"):
                await scan_top_tokens_for_social_activity()

            mock_client_instance.close.assert_awaited_once()


class TestClassifyUnclassifiedNarratives:
    async def test_calls_service_and_returns_result(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.AnthropicClassifierClient") as MockClient,
            patch("app.scheduler.jobs.NarrativeRepository") as MockRepo,
            patch("app.scheduler.jobs.NarrativeClassificationService") as MockService,
        ):
            MockClient.return_value = AsyncMock()
            repo_instance = AsyncMock()
            MockRepo.return_value = repo_instance
            service_instance = AsyncMock()
            service_instance.classify_unclassified_batch.return_value = {
                "classified": 5,
                "errors": 0,
            }
            MockService.return_value = service_instance

            result = await classify_unclassified_narratives()

        assert result == {"classified": 5, "errors": 0}
        mock_session.commit.assert_awaited_once()

    async def test_returns_empty_result_when_no_unclassified(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.AnthropicClassifierClient") as MockClient,
            patch("app.scheduler.jobs.NarrativeRepository") as MockRepo,
            patch("app.scheduler.jobs.NarrativeClassificationService") as MockService,
        ):
            MockClient.return_value = AsyncMock()
            repo_instance = AsyncMock()
            MockRepo.return_value = repo_instance
            service_instance = AsyncMock()
            service_instance.classify_unclassified_batch.return_value = {
                "classified": 0,
                "errors": 0,
            }
            MockService.return_value = service_instance

            result = await classify_unclassified_narratives()

        assert result == {"classified": 0, "errors": 0}
        mock_session.commit.assert_awaited_once()


class TestScanTopTokensForDeveloperActivity:
    async def test_scans_tokens(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory
        tokens = [_make_token("0xaaa"), _make_token("0xbbb")]

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.GitHubClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
            patch("app.scheduler.jobs.DeveloperIntelligenceService") as MockService,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.return_value = (tokens, len(tokens))
            MockTokenRepo.return_value = repo_instance
            service_instance = AsyncMock()
            MockService.return_value = service_instance

            result = await scan_top_tokens_for_developer_activity()

        assert result == {"tokens_scanned": 2, "tokens_skipped": 0}
        assert service_instance.scan_token.call_count == 2
        mock_session.commit.assert_awaited_once()
        mock_client_instance.close.assert_awaited_once()

    async def test_skips_tokens_without_repo(self, mock_session_factory):
        mock_factory, mock_session = mock_session_factory
        tokens = [_make_token("0xaaa"), _make_token("0xbbb"), _make_token("0xccc")]

        from app.services.developer_intelligence_service import NoRepoLinkAvailable, RepoNotFound

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.GitHubClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
            patch("app.scheduler.jobs.DeveloperIntelligenceService") as MockService,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.return_value = (tokens, len(tokens))
            MockTokenRepo.return_value = repo_instance
            service_instance = AsyncMock()
            service_instance.scan_token.side_effect = [
                NoRepoLinkAvailable("0xaaa"),
                RepoNotFound("0xbbb"),
                None,
            ]
            MockService.return_value = service_instance

            result = await scan_top_tokens_for_developer_activity()

        assert result == {"tokens_scanned": 1, "tokens_skipped": 2}
        assert service_instance.scan_token.call_count == 3

    async def test_closes_client_on_error(self, mock_session_factory):
        mock_factory, _ = mock_session_factory

        with (
            patch("app.scheduler.jobs.async_session_factory", mock_factory),
            patch("app.scheduler.jobs.GitHubClient") as MockClient,
            patch("app.scheduler.jobs.TokenRepository") as MockTokenRepo,
        ):
            mock_client_instance = AsyncMock()
            MockClient.return_value = mock_client_instance
            repo_instance = AsyncMock()
            repo_instance.search.side_effect = RuntimeError("db down")
            MockTokenRepo.return_value = repo_instance

            with pytest.raises(RuntimeError, match="db down"):
                await scan_top_tokens_for_developer_activity()

            mock_client_instance.close.assert_awaited_once()

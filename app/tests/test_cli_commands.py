from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from app.cli.main import app
from app.models.chain import Chain

runner = CliRunner()

UUID_HEX = "550e8400e29b41d4a716446655440000"
TOKEN_ID = uuid4()


@pytest.fixture
def mock_session():
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    return mock


def _make_mock_token(**kwargs):
    token = MagicMock(spec=["id", "chain", "contract_address", "symbol", "name"])
    token.id = kwargs.get("id", TOKEN_ID)
    token.chain = kwargs.get("chain", Chain.BASE)
    token.contract_address = kwargs.get("contract_address", "0xabc")
    token.symbol = kwargs.get("symbol", "TEST")
    token.name = kwargs.get("name", "Test Token")
    return token


class TestDbCommands:
    @patch("app.cli.commands.db.command.upgrade")
    @patch("app.cli.commands.db.Config")
    def test_upgrade_calls_alembic(self, mock_config_cls, mock_upgrade):
        mock_config_cls.return_value = "cfg"
        result = runner.invoke(app, ["db", "upgrade"])
        assert result.exit_code == 0
        mock_upgrade.assert_called_once_with("cfg", "head")

    @patch("app.cli.commands.db.command.upgrade")
    @patch("app.cli.commands.db.Config")
    def test_upgrade_with_custom_revision(self, mock_config_cls, mock_upgrade):
        mock_config_cls.return_value = "cfg"
        result = runner.invoke(app, ["db", "upgrade", "abc123"])
        assert result.exit_code == 0
        mock_upgrade.assert_called_once_with("cfg", "abc123")

    @patch("app.cli.commands.db.command.downgrade")
    @patch("app.cli.commands.db.Config")
    def test_downgrade_requires_confirmation(self, mock_config_cls, mock_downgrade):
        mock_config_cls.return_value = "cfg"
        result = runner.invoke(app, ["db", "downgrade", "abc123"], input="y\n")
        assert result.exit_code == 0
        mock_downgrade.assert_called_once_with("cfg", "abc123")

    @patch("app.cli.commands.db.command.downgrade")
    @patch("app.cli.commands.db.Config")
    def test_downgrade_aborts_without_confirmation(self, mock_config_cls, mock_downgrade):
        mock_config_cls.return_value = "cfg"
        result = runner.invoke(app, ["db", "downgrade", "abc123"], input="n\n")
        assert result.exit_code != 0
        mock_downgrade.assert_not_called()

    @patch("app.cli.commands.db.command.current")
    @patch("app.cli.commands.db.Config")
    def test_current_calls_alembic(self, mock_config_cls, mock_current):
        mock_config_cls.return_value = "cfg"
        result = runner.invoke(app, ["db", "current"])
        assert result.exit_code == 0
        mock_current.assert_called_once_with("cfg", verbose=True)


class TestIngestCommand:
    @patch("app.cli.commands.ingest.async_session_factory")
    @patch("app.cli.commands.ingest.TokenIngestionService")
    @patch("app.cli.commands.ingest.DexScreenerProvider")
    @patch("app.cli.commands.ingest.GeckoTerminalProvider")
    def test_ingest_all(self, mock_gt, mock_ds, mock_svc, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        mock_ds_instance = AsyncMock()
        mock_ds.return_value = mock_ds_instance
        mock_gt_instance = AsyncMock()
        mock_gt.return_value = mock_gt_instance
        svc_instance = AsyncMock()
        svc_instance.ingest_all.return_value = {"dexscreener": 5, "geckoterminal": 3}
        mock_svc.return_value = svc_instance

        result = runner.invoke(app, ["ingest"])
        assert result.exit_code == 0
        assert "5 tokens ingested" in result.output
        assert "3 tokens ingested" in result.output
        mock_session.commit.assert_awaited_once()
        mock_ds_instance.close.assert_awaited_once()
        mock_gt_instance.close.assert_awaited_once()

    @patch("app.cli.commands.ingest.async_session_factory")
    @patch("app.cli.commands.ingest.TokenIngestionService")
    @patch("app.cli.commands.ingest.DexScreenerProvider")
    @patch("app.cli.commands.ingest.GeckoTerminalProvider")
    def test_ingest_dexscreener_only(self, mock_gt, mock_ds, mock_svc, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        mock_ds_instance = AsyncMock()
        mock_ds.return_value = mock_ds_instance
        mock_gt_instance = AsyncMock()
        mock_gt.return_value = mock_gt_instance
        svc_instance = AsyncMock()
        svc_instance.ingest_all.return_value = {"dexscreener": 5}
        mock_svc.return_value = svc_instance

        result = runner.invoke(app, ["ingest", "--provider", "dexscreener"])
        assert result.exit_code == 0
        assert "5 tokens ingested" in result.output

    @patch("app.cli.commands.ingest.async_session_factory")
    @patch("app.cli.commands.ingest.TokenIngestionService")
    @patch("app.cli.commands.ingest.DexScreenerProvider")
    @patch("app.cli.commands.ingest.GeckoTerminalProvider")
    def test_ingest_geckoterminal_only(self, mock_gt, mock_ds, mock_svc, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        mock_ds_instance = AsyncMock()
        mock_ds.return_value = mock_ds_instance
        mock_gt_instance = AsyncMock()
        mock_gt.return_value = mock_gt_instance
        svc_instance = AsyncMock()
        svc_instance.ingest_all.return_value = {"geckoterminal": 3}
        mock_svc.return_value = svc_instance

        result = runner.invoke(app, ["ingest", "--provider", "geckoterminal"])
        assert result.exit_code == 0
        assert "3 tokens ingested" in result.output

    def test_ingest_unknown_provider_exits(self):
        result = runner.invoke(app, ["ingest", "--provider", "not-real"])
        assert result.exit_code == 1
        assert "Unknown provider" in result.output


class TestNarrativeCommands:
    @patch("app.cli.commands.narratives.async_session_factory")
    @patch("app.cli.commands.narratives.NarrativeClassificationService")
    @patch("app.cli.commands.narratives.NarrativeRepository")
    @patch("app.cli.commands.narratives.AnthropicClassifierClient")
    @patch("app.cli.commands.narratives.TokenRepository")
    def test_classify_token(self, mock_token_repo_cls, mock_client_cls, mock_repo_cls, mock_svc_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token = _make_mock_token()
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = token
        mock_token_repo_cls.return_value = token_repo
        mock_client_cls.return_value = AsyncMock()
        mock_repo_cls.return_value = AsyncMock()
        mock_svc_cls.return_value = AsyncMock()

        result = runner.invoke(app, ["narrative", "classify", UUID_HEX])
        assert result.exit_code == 0
        assert "Classified TEST" in result.output

    @patch("app.cli.commands.narratives.async_session_factory")
    @patch("app.cli.commands.narratives.TokenRepository")
    def test_classify_token_not_found(self, mock_token_repo_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = None
        mock_token_repo_cls.return_value = token_repo

        result = runner.invoke(app, ["narrative", "classify", UUID_HEX])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("app.cli.commands.narratives.async_session_factory")
    @patch("app.cli.commands.narratives.NarrativeClassificationService")
    @patch("app.cli.commands.narratives.NarrativeRepository")
    @patch("app.cli.commands.narratives.AnthropicClassifierClient")
    def test_classify_batch(self, mock_client_cls, mock_repo_cls, mock_svc_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        mock_client_cls.return_value = AsyncMock()
        mock_repo_cls.return_value = AsyncMock()
        svc = AsyncMock()
        svc.classify_unclassified_batch.return_value = {"classified": 5, "failed": 0}
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["narrative", "classify-batch", "--limit", "10"])
        assert result.exit_code == 0
        assert "Classified: 5" in result.output
        assert "Failed: 0" in result.output


class TestRankCommand:
    @patch("app.cli.commands.rank.async_session_factory")
    @patch("app.cli.commands.rank.RankingService")
    def test_rank_runs_scoring(self, mock_svc_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        svc = AsyncMock()
        svc.compute_all.return_value = 15
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["rank"])
        assert result.exit_code == 0
        assert "Scored 15 tokens" in result.output
        mock_session.commit.assert_awaited_once()


class TestSecurityCommands:
    @patch("app.cli.commands.security.async_session_factory")
    @patch("app.cli.commands.security.ContractSecurityService")
    @patch("app.cli.commands.security.ContractSecurityRepository")
    @patch("app.cli.commands.security.GoPlusClient")
    @patch("app.cli.commands.security.TokenRepository")
    def test_scan_token(self, mock_token_repo_cls, mock_client_cls, mock_repo_cls, mock_svc_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token = _make_mock_token()
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = token
        mock_token_repo_cls.return_value = token_repo
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_repo_cls.return_value = AsyncMock()
        svc = AsyncMock()
        svc.scan_token.return_value = 85
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["security", "scan", UUID_HEX])
        assert result.exit_code == 0
        assert "safety_score=85" in result.output
        mock_client.close.assert_awaited_once()

    @patch("app.cli.commands.security.async_session_factory")
    @patch("app.cli.commands.security.TokenRepository")
    def test_scan_token_not_found(self, mock_token_repo_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = None
        mock_token_repo_cls.return_value = token_repo

        result = runner.invoke(app, ["security", "scan", UUID_HEX])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("app.cli.commands.security.async_session_factory")
    @patch("app.cli.commands.security.ContractSecurityService")
    @patch("app.cli.commands.security.ContractSecurityRepository")
    @patch("app.cli.commands.security.GoPlusClient")
    @patch("app.cli.commands.security.TokenRepository")
    def test_scan_unsupported_chain(self, mock_token_repo_cls, mock_client_cls, mock_repo_cls, mock_svc_cls, mock_factory, mock_session):
        from app.services.contract_security_service import UnsupportedChainForSecurityScan

        mock_factory.return_value = mock_session
        token = _make_mock_token(chain=Chain.SOLANA)
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = token
        mock_token_repo_cls.return_value = token_repo
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_repo_cls.return_value = AsyncMock()
        svc = AsyncMock()
        svc.scan_token.side_effect = UnsupportedChainForSecurityScan("solana not supported")
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["security", "scan", UUID_HEX])
        assert result.exit_code == 1
        assert "not supported" in result.output
        mock_client.close.assert_awaited_once()


class TestSocialCommands:
    @patch("app.cli.commands.social.async_session_factory")
    @patch("app.cli.commands.social.SocialIntelligenceService")
    @patch("app.cli.commands.social.SocialSnapshotRepository")
    @patch("app.cli.commands.social.SocialScoreRepository")
    @patch("app.cli.commands.social.TelegramClient")
    @patch("app.cli.commands.social.TokenRepository")
    def test_scan_token(self, mock_token_repo_cls, mock_client_cls, mock_score_repo_cls, mock_snapshot_repo_cls, mock_svc_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token = _make_mock_token()
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = token
        mock_token_repo_cls.return_value = token_repo
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_score_repo_cls.return_value = AsyncMock()
        mock_snapshot_repo_cls.return_value = AsyncMock()
        svc = AsyncMock()
        svc.scan_token.return_value = 7
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["social", "scan", UUID_HEX])
        assert result.exit_code == 0
        assert "social_score=7" in result.output
        mock_client.close.assert_awaited_once()

    @patch("app.cli.commands.social.async_session_factory")
    @patch("app.cli.commands.social.TokenRepository")
    def test_scan_token_not_found(self, mock_token_repo_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = None
        mock_token_repo_cls.return_value = token_repo

        result = runner.invoke(app, ["social", "scan", UUID_HEX])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("app.cli.commands.social.async_session_factory")
    @patch("app.cli.commands.social.SocialIntelligenceService")
    @patch("app.cli.commands.social.SocialSnapshotRepository")
    @patch("app.cli.commands.social.SocialScoreRepository")
    @patch("app.cli.commands.social.TelegramClient")
    @patch("app.cli.commands.social.TokenRepository")
    def test_scan_no_telegram_link(self, mock_token_repo_cls, mock_client_cls, mock_score_repo_cls, mock_snapshot_repo_cls, mock_svc_cls, mock_factory, mock_session):
        from app.services.social_intelligence_service import NoTelegramLinkAvailable

        mock_factory.return_value = mock_session
        token = _make_mock_token()
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = token
        mock_token_repo_cls.return_value = token_repo
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_score_repo_cls.return_value = AsyncMock()
        mock_snapshot_repo_cls.return_value = AsyncMock()
        svc = AsyncMock()
        svc.scan_token.side_effect = NoTelegramLinkAvailable("no link")
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["social", "scan", UUID_HEX])
        assert result.exit_code == 1
        assert "no link" in result.output.lower()
        mock_client.close.assert_awaited_once()


class TestWalletsCommands:
    @patch("app.cli.commands.wallets.async_session_factory")
    @patch("app.cli.commands.wallets.WalletDiscoveryService")
    @patch("app.cli.commands.wallets.WalletHoldingRepository")
    @patch("app.cli.commands.wallets.WalletRepository")
    @patch("app.cli.commands.wallets.EtherscanClient")
    @patch("app.cli.commands.wallets.TokenRepository")
    def test_scan_token(self, mock_token_repo_cls, mock_client_cls, mock_wallet_repo_cls, mock_holding_repo_cls, mock_svc_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token = _make_mock_token()
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = token
        mock_token_repo_cls.return_value = token_repo
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_wallet_repo_cls.return_value = AsyncMock()
        mock_holding_repo_cls.return_value = AsyncMock()
        svc = AsyncMock()
        svc.scan_token.return_value = 42
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["wallets", "scan", UUID_HEX])
        assert result.exit_code == 0
        assert "42 holders found" in result.output
        mock_client.close.assert_awaited_once()

    @patch("app.cli.commands.wallets.async_session_factory")
    @patch("app.cli.commands.wallets.TokenRepository")
    def test_scan_token_not_found(self, mock_token_repo_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = None
        mock_token_repo_cls.return_value = token_repo

        result = runner.invoke(app, ["wallets", "scan", UUID_HEX])
        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("app.cli.commands.wallets.async_session_factory")
    @patch("app.cli.commands.wallets.WalletDiscoveryService")
    @patch("app.cli.commands.wallets.WalletHoldingRepository")
    @patch("app.cli.commands.wallets.WalletRepository")
    @patch("app.cli.commands.wallets.EtherscanClient")
    @patch("app.cli.commands.wallets.TokenRepository")
    def test_scan_unsupported_chain(self, mock_token_repo_cls, mock_client_cls, mock_wallet_repo_cls, mock_holding_repo_cls, mock_svc_cls, mock_factory, mock_session):
        from app.services.wallet_discovery_service import UnsupportedChainForWalletScan

        mock_factory.return_value = mock_session
        token = _make_mock_token(chain=Chain.SOLANA)
        token_repo = AsyncMock()
        token_repo.get_by_id.return_value = token
        mock_token_repo_cls.return_value = token_repo
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_wallet_repo_cls.return_value = AsyncMock()
        mock_holding_repo_cls.return_value = AsyncMock()
        svc = AsyncMock()
        svc.scan_token.side_effect = UnsupportedChainForWalletScan("solana not supported")
        mock_svc_cls.return_value = svc

        result = runner.invoke(app, ["wallets", "scan", UUID_HEX])
        assert result.exit_code == 1
        assert "not supported" in result.output
        mock_client.close.assert_awaited_once()


class TestWhalesCommands:
    @patch("app.cli.commands.whales.async_session_factory")
    @patch("app.cli.commands.whales.WhaleEventRepository")
    def test_recent_shows_events(self, mock_repo_cls, mock_factory, mock_session):
        from datetime import datetime, timezone

        mock_factory.return_value = mock_session
        mock_token = MagicMock(spec=["symbol"])
        mock_token.symbol = "PEPE"
        mock_wallet = MagicMock()
        mock_wallet.label = "Whale1"
        mock_wallet.address = "0xdeadbeef0123456789abcdef"
        mock_event = MagicMock(spec=["detected_at", "token", "event_type", "change_usd", "wallet"])
        mock_event.detected_at = datetime(2026, 7, 19, tzinfo=timezone.utc)
        mock_event.token = mock_token
        mock_event.event_type.value = "new_position"
        mock_event.change_usd = 50000
        mock_event.wallet = mock_wallet
        repo = AsyncMock()
        repo.list_recent.return_value = [mock_event]
        mock_repo_cls.return_value = repo

        result = runner.invoke(app, ["whales", "recent", "--limit", "5"])
        assert result.exit_code == 0
        assert "PEPE" in result.output
        assert "Whale1" in result.output
        assert "+$50,000" in result.output

    @patch("app.cli.commands.whales.async_session_factory")
    @patch("app.cli.commands.whales.WhaleEventRepository")
    def test_recent_empty(self, mock_repo_cls, mock_factory, mock_session):
        mock_factory.return_value = mock_session
        repo = AsyncMock()
        repo.list_recent.return_value = []
        mock_repo_cls.return_value = repo

        result = runner.invoke(app, ["whales", "recent"])
        assert result.exit_code == 0
        assert "No whale events detected yet" in result.output

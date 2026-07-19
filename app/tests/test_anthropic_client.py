from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.collectors.anthropic_client import AnthropicClassifierClient
from app.models.narrative_classification import Narrative


@pytest.fixture(autouse=True)
def mock_anthropic_sdk(monkeypatch):
    monkeypatch.setattr(
        "app.collectors.anthropic_client.get_settings",
        lambda: MagicMock(
            anthropic_api_key=MagicMock(get_secret_value=lambda: "sk-test"),
        ),
    )


@pytest.fixture
def mock_messages_create():
    with patch("app.collectors.anthropic_client.AsyncAnthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages = AsyncMock()
        mock_cls.return_value = mock_client
        yield mock_client.messages


class TestAnthropicClassifierClient:
    async def test_classify_returns_parsed_result(self, mock_messages_create):
        mock_messages_create.create.return_value = MagicMock(
            content=[
                MagicMock(
                    type="text",
                    text='{"primary_narrative": "meme", "confidence": 85, "reasoning": "Animal name in symbol"}',
                )
            ]
        )
        client = AnthropicClassifierClient()
        result = await client.classify("DOGE", "Dogecoin", "uniswap")
        assert result.primary_narrative == Narrative.MEME
        assert result.confidence == 85

    async def test_classify_handles_markdown_fences(self, mock_messages_create):
        mock_messages_create.create.return_value = MagicMock(
            content=[
                MagicMock(
                    type="text",
                    text='```json\n{"primary_narrative": "defi", "confidence": 70, "reasoning": "DeFi protocol"}\n```',
                )
            ]
        )
        client = AnthropicClassifierClient()
        result = await client.classify("UNI", "Uniswap", "uniswap")
        assert result.primary_narrative == Narrative.DEFI
        assert result.confidence == 70

    async def test_classify_without_dex(self, mock_messages_create):
        mock_messages_create.create.return_value = MagicMock(
            content=[
                MagicMock(
                    type="text",
                    text='{"primary_narrative": "other", "confidence": 30, "reasoning": "Unclear from name"}',
                )
            ]
        )
        client = AnthropicClassifierClient()
        result = await client.classify("XYZ", "XYZ Token", None)
        assert result.primary_narrative == Narrative.OTHER
        assert result.confidence == 30
        assert result.reasoning == "Unclear from name"

    async def test_raises_value_error_when_no_text_block(self, mock_messages_create):
        mock_messages_create.create.return_value = MagicMock(
            content=[MagicMock(type="tool_use", id="call_1")]
        )
        client = AnthropicClassifierClient()
        with pytest.raises(ValueError, match="no text content"):
            await client.classify("TEST", "Test", None)

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_on_timeout_then_succeeds(self, mock_sleep, mock_messages_create):
        call_count = 0

        async def _create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("timed out")
            return MagicMock(
                content=[
                    MagicMock(
                        type="text",
                        text='{"primary_narrative": "meme", "confidence": 80, "reasoning": "Meme coin"}',
                    )
                ]
            )

        mock_messages_create.create.side_effect = _create
        client = AnthropicClassifierClient()
        result = await client.classify("PEPE", "Pepe", None)
        assert result.primary_narrative == Narrative.MEME
        assert call_count == 2

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_raises_after_exhausting_retries(self, mock_sleep, mock_messages_create):
        mock_messages_create.create.side_effect = TimeoutError("timed out")
        client = AnthropicClassifierClient()
        with pytest.raises(TimeoutError):
            await client.classify("FAIL", "Failing Token", None)

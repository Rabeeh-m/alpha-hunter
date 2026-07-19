from __future__ import annotations

import httpx
import pytest
import respx

from app.collectors.telegram_client import TelegramClient, extract_channel_name


class TestExtractChannelName:
    def test_standard_url(self):
        assert extract_channel_name("https://t.me/mychannel") == "mychannel"

    def test_s_url(self):
        assert extract_channel_name("https://t.me/s/mychannel") == "mychannel"

    def test_non_telegram_url(self):
        assert extract_channel_name("https://example.com") is None

    def test_empty_string(self):
        assert extract_channel_name("") is None


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url="https://t.me") as client:
        yield client


SAMPLE_PREVIEW_HTML = """
<div class="tgme_page_extra">12,345 subscribers</div>
<div class="tgme_widget_message_wrap"><time datetime="2026-07-15T10:00:00+00:00">10:00</time></div>
"""


class TestTelegramClient:
    @respx.mock
    async def test_get_channel_stats_parses_response(self, http_client):
        respx.get("https://t.me/s/mychannel").mock(
            return_value=httpx.Response(200, text=SAMPLE_PREVIEW_HTML)
        )
        client = TelegramClient(http_client=http_client)
        stats = await client.get_channel_stats("https://t.me/mychannel")
        assert stats is not None
        assert stats.member_count == 12345

    @respx.mock
    async def test_returns_none_on_404(self, http_client):
        respx.get("https://t.me/s/mychannel").mock(return_value=httpx.Response(404))
        client = TelegramClient(http_client=http_client)
        stats = await client.get_channel_stats("https://t.me/mychannel")
        assert stats is None

    @respx.mock
    async def test_returns_none_for_invalid_url(self, http_client):
        client = TelegramClient(http_client=http_client)
        stats = await client.get_channel_stats("https://example.com")
        assert stats is None

    @respx.mock
    async def test_retry_on_transport_error_then_succeeds(self, http_client):
        call_count = 0

        def _handler(request):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TransportError("connection reset")
            return httpx.Response(200, text=SAMPLE_PREVIEW_HTML)

        respx.get("https://t.me/s/mychannel").mock(side_effect=_handler)
        client = TelegramClient(http_client=http_client)
        stats = await client.get_channel_stats("https://t.me/mychannel")
        assert stats is not None
        assert call_count == 2

    @respx.mock
    async def test_raises_after_exhausting_retries(self, http_client):
        respx.get("https://t.me/s/mychannel").mock(
            side_effect=httpx.TransportError("connection reset")
        )
        client = TelegramClient(http_client=http_client)
        with pytest.raises(httpx.TransportError):
            await client.get_channel_stats("https://t.me/mychannel")

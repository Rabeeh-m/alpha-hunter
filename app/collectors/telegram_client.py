from __future__ import annotations

import re

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.social.telegram_parser import TelegramChannelStats, parse_telegram_preview_html

log = get_logger(__name__)

_CHANNEL_NAME_RE = re.compile(r"t\.me/(?:s/)?([A-Za-z0-9_]+)")


def extract_channel_name(telegram_url: str) -> str | None:
    match = _CHANNEL_NAME_RE.search(telegram_url)
    return match.group(1) if match else None


class TelegramClient:
    """Fetches the public preview page for a Telegram channel -- no
    auth, no bot token, works for any public channel. Private/invite-only
    channels are structurally unreachable this way and will just return
    empty stats, not an error (the page itself renders as inaccessible)."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(
            base_url="https://t.me", timeout=10.0, follow_redirects=True
        )

    @retry(
        stop=stop_after_attempt(2),  # lower than other clients -- this is best-effort scraping,
        wait=wait_exponential(
            multiplier=1, min=1, max=5
        ),  # not worth hammering a page with no API contract
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def get_channel_stats(self, telegram_url: str) -> TelegramChannelStats | None:
        channel_name = extract_channel_name(telegram_url)
        if channel_name is None:
            log.warning("telegram_url_unparseable", url=telegram_url)
            return None

        response = await self._client.get(f"/s/{channel_name}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return parse_telegram_preview_html(response.text)

    async def close(self) -> None:
        await self._client.aclose()

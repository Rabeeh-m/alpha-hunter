from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.logging import get_logger

log = get_logger(__name__)

_MEMBER_COUNT_RE = re.compile(r'([\d,]+)\s+(?:subscribers|members)', re.IGNORECASE)
_MESSAGE_TIME_RE = re.compile(r'<time[^>]*datetime="([^"]+)"')


@dataclass
class TelegramChannelStats:
    member_count: int | None
    message_count_24h: int


def parse_telegram_preview_html(html: str) -> TelegramChannelStats:
    """Best-effort regex parsing of t.me/s/<channel>'s public preview
    page. THIS IS NOT A STABLE API -- Telegram can change this markup at
    any time without notice, and this function has no way to know when
    that happens except by silently returning worse data.

    Design choice: on any parse failure, return None/0 rather than raise.
    A broken scraper degrading to 'no data' is recoverable (same neutral
    handling as GoPlus returning nothing in M13); a broken scraper
    crashing the whole scheduled job is not.
    """
    member_match = _MEMBER_COUNT_RE.search(html)
    member_count = None
    if member_match:
        try:
            member_count = int(member_match.group(1).replace(",", ""))
        except ValueError:
            log.warning("telegram_parse_member_count_failed")

    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=24)
    message_count_24h = 0
    for match in _MESSAGE_TIME_RE.finditer(html):
        try:
            msg_time = datetime.fromisoformat(match.group(1))
            if msg_time >= cutoff:
                message_count_24h += 1
        except ValueError:
            continue  # one malformed timestamp shouldn't invalidate the whole count

    return TelegramChannelStats(member_count=member_count, message_count_24h=message_count_24h)
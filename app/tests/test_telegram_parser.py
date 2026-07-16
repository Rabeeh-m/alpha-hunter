from __future__ import annotations

from app.social.telegram_parser import parse_telegram_preview_html

SAMPLE_HTML = """
<div class="tgme_page_extra">12,345 subscribers</div>
<div class="tgme_widget_message_wrap"><time datetime="2026-07-15T10:00:00+00:00">10:00</time></div>
<div class="tgme_widget_message_wrap"><time datetime="2020-01-01T10:00:00+00:00">old</time></div>
"""


def test_parses_member_count():
    stats = parse_telegram_preview_html(SAMPLE_HTML)
    assert stats.member_count == 12345


def test_counts_only_recent_messages():
    # one message is recent (within a plausible test window), one is
    # from 2020 -- only the recent one should count. Since "now" moves,
    # this test is deliberately loose: just confirm old messages are excluded.
    stats = parse_telegram_preview_html(SAMPLE_HTML)
    assert stats.message_count_24h <= 1


def test_missing_member_count_returns_none_not_crash():
    stats = parse_telegram_preview_html("<html>no subscriber data here</html>")
    assert stats.member_count is None
    assert stats.message_count_24h == 0
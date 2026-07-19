from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

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


def test_k_suffix_member_count_does_not_match_regex():
    html = '<div class="tgme_page_extra">1.2K subscribers</div>'
    stats = parse_telegram_preview_html(html)
    assert stats.member_count is None


def test_empty_html_returns_defaults():
    stats = parse_telegram_preview_html("")
    assert stats.member_count is None
    assert stats.message_count_24h == 0


def test_no_message_time_tags_returns_zero_messages():
    html = '<div class="tgme_page_extra">500 subscribers</div>'
    stats = parse_telegram_preview_html(html)
    assert stats.member_count == 500
    assert stats.message_count_24h == 0


def test_counts_recent_messages_within_24h():
    recent = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    old = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
    html = f"""
    <div class="tgme_page_extra">100 subscribers</div>
    <div class="tgme_widget_message_wrap"><time datetime="{recent}">recent</time></div>
    <div class="tgme_widget_message_wrap"><time datetime="{old}">old</time></div>
    """
    stats = parse_telegram_preview_html(html)
    assert stats.member_count == 100
    assert stats.message_count_24h == 1


def test_member_count_value_error_logged_and_returns_none():
    class _FakeMatch:
        def group(self, n):
            return "not-a-number"

    with patch("app.social.telegram_parser._MEMBER_COUNT_RE") as mock_re:
        mock_re.search.return_value = _FakeMatch()
        stats = parse_telegram_preview_html("<div>ignored</div>")
    assert stats.member_count is None


def test_malformed_timestamp_skipped_gracefully():
    html = """
    <div class="tgme_page_extra">100 subscribers</div>
    <div class="tgme_widget_message_wrap"><time datetime="not-a-real-date">bad</time></div>
    <div class="tgme_widget_message_wrap"><time datetime="2026-01-01T00:00:00+00:00">valid but old</time></div>
    """
    stats = parse_telegram_preview_html(html)
    assert stats.member_count == 100
    assert stats.message_count_24h == 0
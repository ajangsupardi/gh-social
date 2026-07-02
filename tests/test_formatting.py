"""Tests for gh_social.formatting — output helpers."""

from __future__ import annotations

from gh_social.formatting import truncate

# ── Truncate ─────────────────────────────────────────────────────────────────


class TestTruncate:
    def test_short_text_unchanged(self):
        assert truncate("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert truncate("hello", 5) == "hello"

    def test_long_text_truncated(self):
        result = truncate("hello world", 5)
        assert result == "hello…"
        assert len(result) == 6

    def test_empty_string(self):
        assert truncate("", 10) == ""

    def test_unicode_ellipsis(self):
        result = truncate("abcdefghijklmnop", 10)
        assert result.endswith("…")
        assert len(result) == 11  # 10 chars + ellipsis

    def test_single_char(self):
        assert truncate("a", 1) == "a"

    def test_single_char_truncated(self):
        result = truncate("ab", 1)
        assert result == "a…"

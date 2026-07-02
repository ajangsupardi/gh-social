"""Tests for gh_social.tools.social — username extraction, repo parsing, and helpers."""

from __future__ import annotations

import pytest

from gh_social.tools.social import extract_username, parse_repo_url

# ── Username Extraction ──────────────────────────────────────────────────────


class TestExtractUsername:
    def test_plain_username(self):
        assert extract_username("octocat") == "octocat"

    def test_username_with_hyphen(self):
        assert extract_username("my-user") == "my-user"

    def test_username_with_underscore(self):
        assert extract_username("my_user") == "my_user"

    def test_full_url(self):
        assert extract_username("https://github.com/octocat") == "octocat"

    def test_full_url_with_trailing_slash(self):
        assert extract_username("https://github.com/octocat/") == "octocat"

    def test_url_with_extra_path(self):
        assert extract_username("https://github.com/octocat/repos") == "octocat"

    def test_username_with_leading_slash(self):
        assert extract_username("/octocat") == "octocat"

    def test_username_with_trailing_slash(self):
        assert extract_username("octocat/") == "octocat"

    def test_username_with_spaces(self):
        assert extract_username("  octocat  ") == "octocat"

    def test_invalid_input_exits(self):
        with pytest.raises(SystemExit):
            extract_username("invalid user with spaces!")

    def test_empty_input_exits(self):
        with pytest.raises(SystemExit):
            extract_username("")

    def test_url_without_github(self):
        with pytest.raises(SystemExit):
            extract_username("https://gitlab.com/user")

    def test_complex_url(self):
        url = "https://github.com/octocat?tab=repositories"
        assert extract_username(url) == "octocat"

    def test_ssh_url(self):
        with pytest.raises(SystemExit):
            extract_username("git@github.com:user/repo.git")


# ── Repo URL Parsing ────────────────────────────────────────────────────────


class TestParseRepoUrl:
    def test_owner_repo_format(self):
        assert parse_repo_url("ajangsupardi/gh-social") == ("ajangsupardi", "gh-social")

    def test_full_url(self):
        url = "https://github.com/ajangsupardi/gh-social"
        assert parse_repo_url(url) == ("ajangsupardi", "gh-social")

    def test_full_url_with_trailing_slash(self):
        url = "https://github.com/ajangsupardi/gh-social/"
        assert parse_repo_url(url) == ("ajangsupardi", "gh-social")

    def test_url_with_extra_path(self):
        url = "https://github.com/ajangsupardi/gh-social/tree/main"
        assert parse_repo_url(url) == ("ajangsupardi", "gh-social")

    def test_url_with_dot_in_repo(self):
        url = "https://github.com/user/repo.name"
        assert parse_repo_url(url) == ("user", "repo.name")

    def test_owner_repo_with_underscore(self):
        assert parse_repo_url("my_user/my_repo") == ("my_user", "my_repo")

    def test_owner_repo_with_hyphen(self):
        assert parse_repo_url("my-user/my-repo") == ("my-user", "my-repo")

    def test_input_with_spaces(self):
        assert parse_repo_url("  ajangsupardi/gh-social  ") == ("ajangsupardi", "gh-social")

    def test_invalid_no_slash(self):
        with pytest.raises(SystemExit):
            parse_repo_url("invalid")

    def test_invalid_single_word(self):
        with pytest.raises(SystemExit):
            parse_repo_url("noreferrer")

    def test_invalid_url_no_path(self):
        with pytest.raises(SystemExit):
            parse_repo_url("https://github.com")

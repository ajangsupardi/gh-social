"""Tests for gh_social.models — bot detection and data models."""

from __future__ import annotations

from gh_social.models import TargetUser, is_bot, is_default_avatar

# ── Avatar Detection ─────────────────────────────────────────────────────────


class TestIsDefaultAvatar:
    def test_identicon_avatar(self):
        url = "https://avatars.githubusercontent.com/u/12345?v=4"
        assert not is_default_avatar(url)

    def test_default_identicon(self):
        url = "https://avatars.githubusercontent.com/u/0?v=4"
        assert is_default_avatar(url)

    def test_identicons_in_url(self):
        url = "https://github.com/identicons/myapp.png"
        assert is_default_avatar(url)

    def test_custom_avatar(self):
        url = "https://avatars.githubusercontent.com/u/12345?sizes=460x460"
        assert not is_default_avatar(url)


# ── Bot Detection ────────────────────────────────────────────────────────────


class TestIsBot:
    def test_human_account(self):
        user = {
            "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
            "bio": "Software developer",
            "public_repos": 10,
        }
        assert not is_bot(user)

    def test_bot_default_avatar_and_empty_bio(self):
        user = {
            "avatar_url": "https://avatars.githubusercontent.com/u/0?v=4",
            "bio": "",
            "public_repos": 5,
        }
        assert is_bot(user)

    def test_bot_empty_bio_and_zero_repos(self):
        user = {
            "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
            "bio": "",
            "public_repos": 0,
        }
        assert is_bot(user)

    def test_bot_all_three_conditions(self):
        user = {
            "avatar_url": "https://avatars.githubusercontent.com/u/0?v=4",
            "bio": "   ",
            "public_repos": 0,
        }
        assert is_bot(user)

    def test_human_with_bio_and_repos(self):
        user = {
            "avatar_url": "https://avatars.githubusercontent.com/u/0?v=4",
            "bio": "I write code",
            "public_repos": 20,
        }
        assert not is_bot(user)

    def test_missing_bio_treated_as_empty(self):
        user = {
            "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
            "public_repos": 1,
        }
        assert not is_bot(user)

    def test_missing_repos_treated_as_zero(self):
        user = {
            "avatar_url": "https://avatars.githubusercontent.com/u/0?v=4",
            "bio": "",
        }
        assert is_bot(user)


# ── Data Model ───────────────────────────────────────────────────────────────


class TestTargetUser:
    def test_default_status(self):
        user = TargetUser(
            login="testuser",
            name="Test User",
            bio="A test user",
            public_repos=5,
            followers=100,
            avatar_url="https://avatars.githubusercontent.com/u/12345",
            is_bot=False,
            already_following=False,
        )
        assert user.status == "pending"

    def test_custom_status(self):
        user = TargetUser(
            login="testuser",
            name="Test User",
            bio="",
            public_repos=0,
            followers=0,
            avatar_url="",
            is_bot=True,
            already_following=True,
            status="success",
        )
        assert user.status == "success"
        assert user.is_bot is True
        assert user.already_following is True

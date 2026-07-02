"""Data models — TargetUser and enrich functions."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from gh_social.api import api_get
from gh_social.formatting import console

# ── Bot Detection ────────────────────────────────────────────────────────────


def is_default_avatar(avatar_url: str) -> bool:
    """Check if avatar is a default GitHub avatar."""
    return "identicons" in avatar_url or "avatars.githubusercontent.com/u/0" in avatar_url


def is_bot(user: dict[str, Any]) -> bool:
    """Detect bot/spam accounts. 2 out of 3 conditions = bot."""
    flags = 0

    if user.get("avatar_url") and is_default_avatar(user["avatar_url"]):
        flags += 1

    bio = (user.get("bio") or "").strip()
    if not bio:
        flags += 1

    if user.get("public_repos", 0) == 0:
        flags += 1

    return flags >= 2


# ── Data Model ───────────────────────────────────────────────────────────────


@dataclass
class TargetUser:
    login: str
    name: str
    bio: str
    public_repos: int
    followers: int
    avatar_url: str
    is_bot: bool
    already_following: bool
    status: str = "pending"  # pending, success, failed, skipped


# ── Enrich ───────────────────────────────────────────────────────────────────


def enrich_user(login: str) -> TargetUser:
    """Fetch full details for a single user."""
    response = api_get(f"users/{login}")
    assert isinstance(response, dict)
    user: dict[str, Any] = response
    return TargetUser(
        login=user.get("login", login),
        name=user.get("name") or "",
        bio=(user.get("bio") or "").strip(),
        public_repos=user.get("public_repos", 0),
        followers=user.get("followers", 0),
        avatar_url=user.get("avatar_url", ""),
        is_bot=is_bot(user),
        already_following=False,
    )


def enrich_users_concurrent(logins: list[str], verbose: bool = True) -> list[TargetUser]:
    """Enrich multiple users concurrently."""
    results: list[TargetUser | None] = [None] * len(logins)

    # Use higher workers for enrich (read-only GET requests, not affected by follow anti-spam)
    enrich_workers = min(20, len(logins))

    with ThreadPoolExecutor(max_workers=enrich_workers) as executor:
        future_to_idx = {executor.submit(enrich_user, login): i for i, login in enumerate(logins)}

        done_count = 0
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            done_count += 1  # noqa: SIM113 — enumerate() wrong for as_completed order
            if verbose:
                console.print(
                    f"\r  [dim]Fetching user details... {done_count}/{len(logins)}[/dim]", end=""
                )
            try:
                results[idx] = future.result()
            except Exception as e:
                if verbose:
                    console.print(f"\n  [yellow]⚠️  Failed: {logins[idx]} — {e}[/yellow]")

    if verbose and logins:
        console.print("\r  [dim]Fetching user details... done[/dim]" + " " * 20)

    return [r for r in results if r is not None]

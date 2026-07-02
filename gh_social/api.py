"""GitHub API — session, auth, pagination, follow/unfollow."""

from __future__ import annotations

import subprocess
import sys
from typing import Any

import requests

from gh_social.formatting import console

# ── Constants ────────────────────────────────────────────────────────────────

MAX_WORKERS = 1
PER_PAGE = 100
API_BASE = "https://api.github.com"

# ── Session ──────────────────────────────────────────────────────────────────

_session: requests.Session | None = None


def get_session() -> requests.Session:
    """Create session with auth token from gh CLI."""
    global _session
    if _session is None:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(
                "\n  [bold red]❌ No logged-in user detected. Run `gh auth login` first.[/bold red]\n"
            )
            sys.exit(1)

        token = result.stdout.strip()
        _session = requests.Session()
        _session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
    return _session


# ── HTTP Methods ─────────────────────────────────────────────────────────────


def api_get(endpoint: str) -> dict[str, Any] | list[dict[str, Any]]:
    """GET request to GitHub API."""
    url = f"{API_BASE}/{endpoint.lstrip('/')}"
    resp = get_session().get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def api_put(endpoint: str) -> bool:
    """PUT request to GitHub API. Return True if successful."""
    url = f"{API_BASE}/{endpoint.lstrip('/')}"
    resp = get_session().put(url, timeout=15)
    return resp.status_code == 204


# ── Pagination ───────────────────────────────────────────────────────────────


def api_paginate(endpoint: str, limit: int = 0, verbose: bool = False) -> list[dict[str, Any]]:
    """Manual pagination with progress indicator."""
    items: list[dict[str, Any]] = []
    page = 1
    sep = "?" if "?" not in endpoint else "&"

    while True:
        url = f"{endpoint}{sep}per_page={PER_PAGE}&page={page}"
        if verbose:
            console.print(f"\r  [dim]Fetching page {page}... ({len(items)} users)[/dim]", end="")
        try:
            batch = api_get(url)
        except Exception:
            break

        if not isinstance(batch, list) or not batch:
            break

        items.extend(batch)

        if limit and len(items) >= limit:
            items = items[:limit]
            break

        if len(batch) < PER_PAGE:
            break

        page += 1

    if verbose:
        console.print(
            f"\r  [dim]Fetching page {page}... done ({len(items)} users)[/dim]" + " " * 20
        )

    return items


# ── GitHub Helpers ───────────────────────────────────────────────────────────


def get_current_user() -> str:
    """Get the current authenticated user's username."""
    data = api_get("user")
    assert isinstance(data, dict)
    return data["login"]


def check_rate_limit() -> dict[str, Any]:
    """Check GitHub API rate limit."""
    data = api_get("rate_limit")
    assert isinstance(data, dict)
    resources = data["resources"]
    assert isinstance(resources, dict)
    return resources["core"]


def follow_user(username: str) -> bool:
    """Follow a user via GitHub API."""
    return api_put(f"user/following/{username}")


def unfollow_user(username: str) -> bool:
    """Unfollow a user via GitHub API."""
    url = f"{API_BASE}/user/following/{username}"
    resp = get_session().delete(url, timeout=15)
    return resp.status_code == 204

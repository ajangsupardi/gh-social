"""Follow Back, Unfollow & Stargazers tool."""

from __future__ import annotations

import re
import sys
import time
from argparse import Namespace
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from gh_social.api import (
    MAX_WORKERS,
    api_get,
    api_paginate,
    check_rate_limit,
    follow_user,
    get_current_user,
    get_session,
    unfollow_user,
)
from gh_social.formatting import (
    confirm_action,
    console,
    print_error,
    print_info,
    print_json,
    print_success,
    print_table,
    print_warning,
)
from gh_social.models import TargetUser, enrich_users_concurrent

# ── Shared Helpers ───────────────────────────────────────────────────────────


def extract_username(input_str: str) -> str:
    """Extract username from URL or raw username."""
    match = re.search(r"github\.com/([a-zA-Z0-9_-]+)", input_str)
    if match:
        return match.group(1)

    cleaned = input_str.strip().strip("/")
    if re.match(r"^[a-zA-Z0-9_-]+$", cleaned):
        return cleaned

    print_error(f"Invalid input: {input_str}")
    print_info("Use a username or GitHub URL, e.g. ajangsupardi")
    sys.exit(1)


def parse_repo_url(input_str: str) -> tuple[str, str]:
    """Parse owner/repo or GitHub URL → (owner, repo)."""
    # Try full URL: https://github.com/owner/repo
    match = re.search(r"github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)", input_str)
    if match:
        return match.group(1), match.group(2)

    # Try owner/repo format
    cleaned = input_str.strip().strip("/")
    match = re.match(r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$", cleaned)
    if match:
        return match.group(1), match.group(2)

    print_error(f"Invalid repo format: {input_str}")
    print_info("Use owner/repo or GitHub URL, e.g. ajangsupardi/gh-social")
    sys.exit(1)


def _init_session(verbose: bool = True) -> tuple[dict[str, Any], str]:
    """Initialize session, check rate limit, get current user. Returns (rate, me)."""
    if verbose:
        print_info("Loading initial data...")

    get_session()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_rate = executor.submit(check_rate_limit)
        future_me = executor.submit(get_current_user)
        rate = future_rate.result()
        me = future_me.result()

    if verbose:
        console.print(f"  [dim]Rate limit: {rate['remaining']}/{rate['limit']}[/dim]")
        console.print(f"  [dim]Your account: {me}[/dim]")

    if rate["remaining"] < 20:
        print_error("Rate limit almost exhausted! Try again later.")
        sys.exit(1)

    return rate, me


def _fetch_pairs(
    endpoint_a: str,
    endpoint_b: str,
    limit_a: int = 0,
    limit_b: int = 0,
    verbose: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch two paginated endpoints concurrently. Returns (list_a, list_b)."""
    if verbose:
        print_info("Fetching followers & following...")

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(api_paginate, endpoint_a, limit=limit_a, verbose=verbose)
        future_b = executor.submit(api_paginate, endpoint_b, limit=limit_b, verbose=verbose)
        return future_a.result(), future_b.result()


def _calculate_delay(limit: int) -> float:
    """Calculate dynamic delay based on actual target count to avoid GitHub anti-spam."""
    if limit <= 0:
        return 0.0
    if limit < 50:
        return 0.15
    return min(limit // 50 * 0.15, 3.15)


def _execute_concurrent(
    targets: list[TargetUser],
    action_fn: Callable[[Any], bool],
    action_label: str,
    delay: float = 1.0,
) -> tuple[int, int]:
    """Execute an action concurrently on all targets. Returns (success, failed)."""
    console.print(f"\n  [bold]🚀 Starting {action_label}...[/bold]\n")
    success = 0
    failed = 0

    def do_action(target: TargetUser):
        time.sleep(delay)
        ok = action_fn(target.login)
        target.status = "success" if ok else "failed"
        return target, ok

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(do_action, t): t for t in targets}
        done_count = 0
        for future in as_completed(futures):
            target, ok = future.result()
            done_count += 1  # noqa: SIM113 — enumerate() wrong for as_completed order
            label = f"[{done_count}/{len(targets)}] {target.login}"
            if ok:
                success += 1
                console.print(f"  [green]✅ {label}[/green]")
            else:
                failed += 1
                console.print(f"  [red]❌ {label}[/red]")

    # Verify: fetch actual following list to confirm follows were processed
    if action_label == "follow" and success > 0:
        console.print("\n  [dim]Verifying follows...[/dim]")
        me = get_current_user()
        actual_following = api_paginate(f"users/{me}/following", verbose=False)
        actual_logins = {u["login"] for u in actual_following}

        verified = 0
        for t in targets:
            if t.status == "success" and t.login in actual_logins:
                verified += 1
            elif t.status == "success":
                t.status = "failed"

        if verified < success:
            console.print(
                f"  [yellow]⚠️  {success - verified} follows were accepted by API "
                f"but not processed by GitHub (anti-spam)[/yellow]"
            )
            success = verified

    return success, failed


def _print_summary(
    action_label: str,
    success: int,
    failed: int,
    skipped: int,
    elapsed: float,
) -> None:
    """Print execution summary."""
    console.print(f"\n  {'━' * 44}")
    console.print("  [bold]Summary:[/bold]")
    console.print(f"  [green]✅ {action_label}: {success}[/green]")
    if failed:
        console.print(f"  [red]❌ Failed: {failed}[/red]")
    if skipped:
        console.print(f"  [yellow]⏭️  Bots skipped: {skipped}[/yellow]")
    console.print(f"  [dim]Total time: {elapsed:.1f}s[/dim]\n")


# ── Follow Back ──────────────────────────────────────────────────────────────


def follow_back(args: Namespace) -> None:
    """Follow all followers of a GitHub user."""
    target_user = extract_username(args.user)
    skip_bots = not args.include_bots
    verbose = not args.json

    if verbose:
        console.print("\n  [bold]🔍 GitHub Follow Back Tool[/bold]")
        console.print(f"  {'━' * 44}")

    t_start = time.time()

    # 1. Init session + validate target
    _, me = _init_session(verbose=verbose)

    if verbose:
        console.print(f"  [dim]Target: {target_user}[/dim]")

    try:
        api_get(f"users/{target_user}")
    except Exception:
        print_error(f"User '{target_user}' not found on GitHub.")
        sys.exit(1)

    # 2. Fetch followers + following
    followers, following = _fetch_pairs(
        endpoint_a=f"users/{target_user}/followers",
        endpoint_b=f"users/{me}/following",
        limit_a=args.limit,
        verbose=verbose,
    )

    following_logins = {u["login"] for u in following}

    if not followers:
        if args.json:
            print("[]")
        else:
            print_warning(f"{target_user} has no followers.")
        sys.exit(0)

    # 3. Filter: followers you haven't followed yet + skip self
    unfollowed_logins = [
        f["login"] for f in followers if f["login"] not in following_logins and f["login"] != me
    ]

    if verbose:
        console.print(
            f"  [dim]Followers: {len(followers)} | Following: {len(following)} "
            f"| Targets: {len(unfollowed_logins)}[/dim]"
        )

    if not unfollowed_logins:
        if args.json:
            print("[]")
        else:
            print_success("You're already following all followers!")
        sys.exit(0)

    # 4. Enrich + categorize
    all_targets = enrich_users_concurrent(unfollowed_logins, verbose=verbose)

    followable = []
    skipped_bots = []
    for t in all_targets:
        if skip_bots and t.is_bot:
            t.status = "skipped"
            skipped_bots.append(t)
        else:
            followable.append(t)

    t_elapsed = time.time() - t_start

    # 5. Output
    if args.json:
        print_json(followable, skipped_bots)
        sys.exit(0)

    print_table(followable, skipped_bots, mode="follow")
    print_info(f"Preparation time: {t_elapsed:.1f}s")

    if not followable:
        print_success("No new users to follow.")
        sys.exit(0)

    # 6. Execute or dry-run
    if not args.execute:
        console.print("\n  [dim]💡 Dry-run mode. Add --execute to follow.[/dim]\n")
        sys.exit(0)

    if not confirm_action(
        f"About to follow {len(followable)} users from {target_user}'s followers. Continue?",
        default=False,
    ):
        print_info("Cancelled.")
        sys.exit(0)

    # Calculate delay: use user-specified delay if provided, otherwise dynamic based on actual targets
    delay = args.delay if args.delay > 0 else _calculate_delay(len(followable))
    if verbose:
        console.print(f"  [dim]Delay: {delay}s between follows[/dim]")

    success, failed = _execute_concurrent(followable, follow_user, "follow", delay=delay)
    _print_summary("Followed", success, failed, len(skipped_bots), time.time() - t_start)


# ── Unfollow Non-Followback ──────────────────────────────────────────────────


def unfollow_non_followers(args: Namespace) -> None:
    """Unfollow users who don't follow you back."""
    skip_bots = not args.include_bots
    verbose = not args.json

    if verbose:
        console.print("\n  [bold]🔍 GitHub Unfollow Tool[/bold]")
        console.print(f"  {'━' * 44}")

    t_start = time.time()

    # 1. Init session
    _, me = _init_session(verbose=verbose)

    # 2. Fetch followers + following
    followers, following = _fetch_pairs(
        endpoint_a=f"users/{me}/followers",
        endpoint_b=f"users/{me}/following",
        limit_a=0,
        limit_b=args.limit,
        verbose=verbose,
    )

    followers_logins = {u["login"] for u in followers}

    if not following:
        if args.json:
            print("[]")
        else:
            print_warning("You're not following anyone.")
        sys.exit(0)

    # 3. Filter: following who DON'T follow back
    non_followback_logins = [f["login"] for f in following if f["login"] not in followers_logins]

    if verbose:
        console.print(
            f"  [dim]Following: {len(following)} | Followers: {len(followers)} "
            f"| Not following back: {len(non_followback_logins)}[/dim]"
        )

    if not non_followback_logins:
        if args.json:
            print("[]")
        else:
            print_success("Everyone you follow follows you back!")
        sys.exit(0)

    # 4. Enrich + categorize
    all_targets = enrich_users_concurrent(non_followback_logins, verbose=verbose)

    unfollowable = []
    skipped_bots = []
    for t in all_targets:
        t.already_following = True
        if skip_bots and t.is_bot:
            t.status = "skipped"
            skipped_bots.append(t)
        else:
            unfollowable.append(t)

    t_elapsed = time.time() - t_start

    # 5. Output
    if args.json:
        print_json(unfollowable, skipped_bots)
        sys.exit(0)

    print_table(unfollowable, skipped_bots, mode="unfollow")
    print_info(f"Preparation time: {t_elapsed:.1f}s")

    if not unfollowable:
        print_success("No users to unfollow.")
        sys.exit(0)

    # 6. Execute or dry-run
    if not args.execute:
        console.print("\n  [dim]💡 Dry-run mode. Add --execute to unfollow.[/dim]\n")
        sys.exit(0)

    if not confirm_action(
        f"About to unfollow {len(unfollowable)} users who don't follow back. Continue?",
        default=False,
    ):
        print_info("Cancelled.")
        sys.exit(0)

    # Calculate delay: use user-specified delay if provided, otherwise dynamic based on actual targets
    delay = args.delay if args.delay > 0 else _calculate_delay(len(unfollowable))
    if verbose:
        console.print(f"  [dim]Delay: {delay}s between unfollows[/dim]")

    success, failed = _execute_concurrent(unfollowable, unfollow_user, "unfollow", delay=delay)
    _print_summary("Unfollowed", success, failed, len(skipped_bots), time.time() - t_start)


# ── Follow Stargazers ───────────────────────────────────────────────────────


def follow_stargazers(args: Namespace) -> None:
    """Follow users who starred a GitHub repository."""
    owner, repo = parse_repo_url(args.repo)
    skip_bots = not args.include_bots
    verbose = not args.json

    if verbose:
        console.print("\n  [bold]⭐ GitHub Follow Stargazers[/bold]")
        console.print(f"  {'━' * 44}")

    t_start = time.time()

    # 1. Init session + validate repo
    _, me = _init_session(verbose=verbose)

    if verbose:
        console.print(f"  [dim]Target: {owner}/{repo}[/dim]")

    try:
        api_get(f"repos/{owner}/{repo}")
    except Exception:
        print_error(f"Repository '{owner}/{repo}' not found on GitHub.")
        sys.exit(1)

    # 2. Fetch stargazers + following
    if verbose:
        print_info("Fetching stargazers & following...")

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_stars = executor.submit(
            api_paginate, f"repos/{owner}/{repo}/stargazers", limit=args.limit, verbose=verbose
        )
        future_following = executor.submit(api_paginate, f"users/{me}/following", verbose=verbose)
        stargazers = future_stars.result()
        following = future_following.result()

    following_logins = {u["login"] for u in following}

    if not stargazers:
        if args.json:
            print("[]")
        else:
            print_warning(f"{owner}/{repo} has no stargazers.")
        sys.exit(0)

    # 3. Filter: stargazers you haven't followed yet + skip self
    unfollowed_logins = [
        s["login"] for s in stargazers if s["login"] not in following_logins and s["login"] != me
    ]

    if verbose:
        console.print(
            f"  [dim]Stargazers: {len(stargazers)} | Following: {len(following)} "
            f"| Targets: {len(unfollowed_logins)}[/dim]"
        )

    if not unfollowed_logins:
        if args.json:
            print("[]")
        else:
            print_success("You're already following all stargazers!")
        sys.exit(0)

    # 4. Enrich + categorize
    all_targets = enrich_users_concurrent(unfollowed_logins, verbose=verbose)

    followable = []
    skipped_bots = []
    for t in all_targets:
        if skip_bots and t.is_bot:
            t.status = "skipped"
            skipped_bots.append(t)
        else:
            followable.append(t)

    t_elapsed = time.time() - t_start

    # 5. Output
    if args.json:
        print_json(followable, skipped_bots)
        sys.exit(0)

    print_table(followable, skipped_bots, mode="follow")
    print_info(f"Preparation time: {t_elapsed:.1f}s")

    if not followable:
        print_success("No new users to follow.")
        sys.exit(0)

    # 6. Execute or dry-run
    if not args.execute:
        console.print("\n  [dim]💡 Dry-run mode. Add --execute to follow.[/dim]\n")
        sys.exit(0)

    if not confirm_action(
        f"About to follow {len(followable)} stargazers of {owner}/{repo}. Continue?",
        default=False,
    ):
        print_info("Cancelled.")
        sys.exit(0)

    # Calculate delay: use user-specified delay if provided, otherwise dynamic based on actual targets
    delay = args.delay if args.delay > 0 else _calculate_delay(len(followable))
    if verbose:
        console.print(f"  [dim]Delay: {delay}s between follows[/dim]")

    success, failed = _execute_concurrent(followable, follow_user, "follow", delay=delay)
    _print_summary("Followed", success, failed, len(skipped_bots), time.time() - t_start)

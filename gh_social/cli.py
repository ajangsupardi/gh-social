"""CLI dispatcher — router for all tools."""

from __future__ import annotations

import argparse
import sys
from types import SimpleNamespace
from typing import Any

from gh_social import __version__
from gh_social.formatting import (
    confirm_action,
    console,
    print_banner,
    print_error,
    print_exit_message,
    print_info,
    print_menu,
    rich_input,
)
from gh_social.tools.social import follow_back, follow_stargazers, unfollow_non_followers

# ── Tools Registry ───────────────────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "id": "follow",
        "name": "Follow Back",
        "desc": "Follow all followers of a target user",
        "handler": follow_back,
        "needs_user": True,
    },
    {
        "id": "unfollow",
        "name": "Unfollow",
        "desc": "Unfollow users who don't follow you back",
        "handler": unfollow_non_followers,
        "needs_user": False,
    },
    {
        "id": "stargazers",
        "name": "Follow Stargazers",
        "desc": "Follow users who starred a repo",
        "handler": follow_stargazers,
        "needs_user": False,
        "needs_repo": True,
    },
]


def _add_common_args(parser: argparse.ArgumentParser):
    """Add common arguments used by all tools."""
    parser.add_argument("--execute", action="store_true", help="Execute action (default: dry-run)")
    parser.add_argument(
        "--limit", type=int, default=0, help="Limit number of users processed (0 = all)"
    )
    parser.add_argument("--include-bots", action="store_true", help="Include bot accounts")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Seconds between API calls (0 = auto, based on limit)",
    )


# ── Interactive Menu ─────────────────────────────────────────────────────────


def interactive_menu():
    """Interactive mode — select a tool from the menu."""
    while True:
        print_banner(__version__)
        print_menu(TOOLS)

        try:
            choice = console.input(f"  [bold]→[/bold] Choice (0-{len(TOOLS)}): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print_info("Cancelled.")
            sys.exit(0)

        if choice == "0":
            print_exit_message()
            sys.exit(0)

        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(TOOLS):
            print()
            print_error("Invalid choice.")
            continue

        tool = TOOLS[int(choice) - 1]
        args = _collect_tool_args(tool)

        if args is None:
            continue

        try:
            tool["handler"](args)
        except KeyboardInterrupt:
            print()
            print_info("Cancelled.")
        except SystemExit:
            pass

        console.input("\n  [dim]Press Enter to return to menu...[/dim]")


def _collect_tool_args(tool: dict[str, Any]) -> SimpleNamespace | None:
    """Collect arguments interactively for the selected tool."""
    print_banner(__version__)

    console.print(f"  [bold white]{tool['name']}[/bold white]\n")

    args = SimpleNamespace(
        execute=False,
        limit=0,
        include_bots=False,
        json=False,
        delay=0,
    )

    if tool["needs_user"]:
        username = rich_input("Target username or URL")
        if not username:
            print()
            print_error("Username cannot be empty.")
            return None
        args.user = username

    if tool.get("needs_repo"):
        repo = rich_input("Repository (owner/repo or URL)")
        if not repo:
            print()
            print_error("Repository cannot be empty.")
            return None
        args.repo = repo

    args.include_bots = confirm_action("Include bot accounts?", default=False)

    limit_str = rich_input("Limit number of users (0 = all)", "0")
    try:
        args.limit = int(limit_str)
    except ValueError:
        args.limit = 0

    args.execute = confirm_action("Execute action? (No = dry-run preview)", default=False)

    if not args.execute:
        print()
        print_info("Mode: Dry-run (preview only)")

    proceed = confirm_action("Continue?", default=True)

    if not proceed:
        print()
        print_info("Cancelled.")
        return None

    return args


# ── CLI Entry Point ──────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="gh-social",
        description="gh-social — CLI tools for GitHub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gh-social                                      # Interactive mode
  gh-social follow ajangsupardi                  # Dry-run follow back
  gh-social follow ajangsupardi --execute
  gh-social stargazers ajangsupardi/gh-social
  gh-social stargazers ajangsupardi/gh-social --execute
  gh-social unfollow                             # Dry-run unfollow
  gh-social unfollow --execute
  gh-social --version
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available tools")

    # ── Follow Back ──────────────────────────────────────────────────────
    follow_parser = subparsers.add_parser(
        "follow",
        help="Follow all followers of a target user",
        description="Follow all followers of a GitHub user.",
    )
    follow_parser.add_argument("user", help="Target username or GitHub URL")
    _add_common_args(follow_parser)

    # ── Unfollow ─────────────────────────────────────────────────────────
    unfollow_parser = subparsers.add_parser(
        "unfollow",
        help="Unfollow users who don't follow you back",
        description="Unfollow users who don't follow you back.",
    )
    _add_common_args(unfollow_parser)

    # ── Follow Stargazers ───────────────────────────────────────────────
    stargazers_parser = subparsers.add_parser(
        "stargazers",
        help="Follow users who starred a repo",
        description="Follow users who starred a GitHub repository.",
    )
    stargazers_parser.add_argument("repo", help="Repository (owner/repo or GitHub URL)")
    _add_common_args(stargazers_parser)

    return parser


def main():
    # ── No args → Interactive Menu ──────────────────────────────────────
    if len(sys.argv) == 1:
        interactive_menu()
        return

    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        interactive_menu()
        return

    if args.command == "follow":
        follow_back(args)
    elif args.command == "unfollow":
        unfollow_non_followers(args)
    elif args.command == "stargazers":
        follow_stargazers(args)

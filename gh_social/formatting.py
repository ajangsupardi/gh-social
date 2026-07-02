"""Output formatting — rich-based interactive and table output, JSON."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from gh_social.models import TargetUser

# ── Rich Console ─────────────────────────────────────────────────────────────

console = Console()

# ── Helpers ──────────────────────────────────────────────────────────────────


def truncate(text: str, length: int) -> str:
    return text[:length] + "…" if len(text) > length else text


# ── Interactive Mode ─────────────────────────────────────────────────────────


def print_banner(version: str) -> None:
    """Display banner with rich panel."""
    title = Text(f"🔍  gh-social  v{version}", style="bold white")
    console.print(Panel(title, border_style="cyan", padding=(0, 2)))


def print_menu(tools: list[dict[str, Any]]) -> None:
    """Display tool menu with rich styling."""
    console.print()
    console.print("  [bold]Choose a tool:[/bold]\n")

    for i, tool in enumerate(tools, 1):
        num = Text(f"  {i}.", style="cyan bold")
        name = Text(f"  {tool['name']:<16}", style="white bold")
        desc = Text(f" — {tool['desc']}", style="dim")
        line = Text()
        line.append_text(num)
        line.append_text(name)
        line.append_text(desc)
        console.print(line)

    console.print()
    exit_line = Text()
    exit_line.append_text(Text("  0.", style="red bold"))
    exit_line.append_text(Text(f"  {'Exit':<16}", style="red bold"))
    console.print(exit_line)
    console.print()


def rich_input(prompt: str, default: str = "") -> str:
    """Input with default value using rich styling."""
    if default:
        display = f"  [bold cyan]→[/bold cyan] {prompt} [dim][{default}][/dim]: "
    else:
        display = f"  [bold cyan]→[/bold cyan] {prompt}: "
    try:
        value = console.input(display).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        raise SystemExit(0) from None
    return value if value else default


def confirm_action(prompt: str, default: bool = False) -> bool:
    """Yes/no confirmation using rich prompt."""
    try:
        return Confirm.ask(f"  [bold yellow]⚠[/bold yellow]  {prompt}", default=default)
    except (KeyboardInterrupt, EOFError):
        print()
        raise SystemExit(0) from None


# ── Status Messages ──────────────────────────────────────────────────────────


def print_success(message: str) -> None:
    console.print(f"  [bold green]✅ {message}[/bold green]")


def print_error(message: str) -> None:
    console.print(f"  [bold red]❌ {message}[/bold red]")


def print_warning(message: str) -> None:
    console.print(f"  [bold yellow]⚠️  {message}[/bold yellow]")


def print_info(message: str) -> None:
    console.print(f"  [dim]{message}[/dim]")


def print_exit_message() -> None:
    console.print()
    console.print("  [dim]Goodbye![/dim]\n")


# ── Table Output ─────────────────────────────────────────────────────────────


def print_table(
    targets: list[TargetUser],
    skipped: list[TargetUser],
    mode: str = "follow",
) -> None:
    """Display target follow/unfollow table using rich."""
    if not targets and not skipped:
        if mode == "follow":
            print_success("No new users to follow.")
        else:
            print_success("No users to unfollow.")
        return

    if targets:
        table = Table(show_header=True, header_style="bold", show_lines=False)
        table.add_column("#", justify="right", style="dim", width=4)
        table.add_column("Username", style="white", min_width=20)
        table.add_column("Name", style="white", min_width=18)
        table.add_column("Bio", style="dim", min_width=28, max_width=40)
        table.add_column("Repos", justify="right", width=6)
        table.add_column("Bot", justify="center", width=4)

        for i, t in enumerate(targets, 1):
            name = truncate(t.name, 18) if t.name else "[dim](none)[/dim]"
            bio = truncate(t.bio, 38) if t.bio else "[dim](none)[/dim]"
            bot = "[yellow]⚠[/yellow]" if t.is_bot else "[green]✓[/green]"
            repos_style = "red" if t.public_repos == 0 else "white"
            table.add_row(
                str(i),
                t.login,
                name,
                bio,
                f"[{repos_style}]{t.public_repos}[/{repos_style}]",
                bot,
            )

        console.print()
        console.print(table)

        bots_in_targets = sum(1 for t in targets if t.is_bot)
        humans = len(targets) - bots_in_targets
        total_bots = bots_in_targets + len(skipped)
        total = len(targets) + len(skipped)
        console.print(
            f"\n  [dim]Total: {total} targets — {humans} users, {total_bots} bots detected[/dim]"
        )

    if skipped:
        console.print(
            f"\n  [yellow]⏭️  {len(skipped)} bot accounts skipped "
            f"(use --include-bots to include)[/yellow]"
        )


# ── JSON Output ──────────────────────────────────────────────────────────────


def print_json(targets: list[TargetUser], skipped: list[TargetUser]) -> None:
    """Output in JSON format."""
    all_users = []
    for t in targets + skipped:
        all_users.append(
            {
                "login": t.login,
                "name": t.name,
                "bio": t.bio,
                "public_repos": t.public_repos,
                "followers": t.followers,
                "is_bot": t.is_bot,
                "already_following": t.already_following,
                "status": t.status,
            }
        )
    print(json.dumps(all_users, indent=2, ensure_ascii=False))

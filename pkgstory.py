#!/usr/bin/env python3
import re
import sys
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box

LOG_PATH = Path("/var/log/pacman.log")
console = Console()

LINE_RE = re.compile(
    r"\[(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\]]*)\] "
    r"\[(?P<src>ALPM|PACMAN)\] "
    r"(?P<msg>.+)"
)
ALPM_RE = re.compile(
    r"(?P<action>installed|removed|upgraded|downgraded)\s+"
    r"(?P<pkg>[^\s]+)\s+"
    r"\((?P<ver>.+)\)"
)

def parse_ts(ts_str: str) -> datetime:
    ts_str = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", ts_str)
    try:
        return datetime.fromisoformat(ts_str).astimezone(timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def parse_log(path: Path) -> tuple[list[dict], list[dict]]:
    all_events: list[dict] = []
    transaction = 0
    in_transaction = False
    chroot_transactions: set[int] = set()
    current_tx_is_chroot = False

    for line in path.read_text(errors="replace").splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        ts  = parse_ts(m.group("ts"))
        src = m.group("src")
        msg = m.group("msg").strip()

        if src == "PACMAN" and msg.startswith("Running") and "-r /mnt" in msg:
            current_tx_is_chroot = True

        if src == "ALPM":
            if msg == "transaction started":
                transaction += 1
                in_transaction = True
                if current_tx_is_chroot:
                    chroot_transactions.add(transaction)
                    current_tx_is_chroot = False
                continue
            if msg == "transaction completed":
                in_transaction = False
                current_tx_is_chroot = False
                continue
            am = ALPM_RE.match(msg)
            if am and in_transaction:
                all_events.append({
                    "ts":          ts,
                    "action":      am.group("action"),
                    "pkg":         am.group("pkg"),
                    "ver":         am.group("ver"),
                    "transaction": transaction,
                    "chroot":      transaction in chroot_transactions,
                })

    manual_events = [e for e in all_events if not e["chroot"]]
    return all_events, manual_events

def analyse(all_events: list[dict], manual_events: list[dict]) -> dict:
    if not all_events:
        return {}

    first    = all_events[0]["ts"]
    last     = all_events[-1]["ts"]
    age_days = max((last - first).days, 1)

    installs   = [e for e in all_events if e["action"] == "installed"]
    removes    = [e for e in all_events if e["action"] == "removed"]
    upgrades   = [e for e in all_events if e["action"] == "upgraded"]
    downgrades = [e for e in all_events if e["action"] == "downgraded"]

    base_pkg_count = sum(1 for e in installs if e["chroot"])

    first_manual = []
    for e in manual_events:
        if e["action"] == "installed":
            first_manual.append(e["pkg"])
            if len(first_manual) >= 10:
                break

    pkg_upgrade_count: dict[str, int] = defaultdict(int)
    for e in upgrades:
        pkg_upgrade_count[e["pkg"]] += 1

    day_activity: dict[str, int] = defaultdict(int)
    for e in all_events:
        day_activity[e["ts"].strftime("%Y-%m-%d")] += 1

    busiest_day   = max(day_activity, key=day_activity.__getitem__)
    busiest_count = day_activity[busiest_day]

    active_days = sorted(day_activity.keys())
    longest_gap = 0
    if len(active_days) > 1:
        for i in range(1, len(active_days)):
            d1  = datetime.strptime(active_days[i-1], "%Y-%m-%d")
            d2  = datetime.strptime(active_days[i],   "%Y-%m-%d")
            longest_gap = max(longest_gap, (d2 - d1).days)

    most_upgraded = sorted(pkg_upgrade_count.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "first_date":       first,
        "last_date":        last,
        "age_days":         age_days,
        "total_installs":   len(installs),
        "total_removes":    len(removes),
        "total_upgrades":   len(upgrades),
        "total_downgrades": len(downgrades),
        "base_pkg_count":   base_pkg_count,
        "busiest_day":      busiest_day,
        "busiest_count":    busiest_count,
        "most_upgraded":    most_upgraded,
        "first_manual":     first_manual,
        "active_days":      len(active_days),
        "longest_gap":      longest_gap,
        "day_activity":     day_activity,
    }

def render_story(stats: dict) -> None:
    console.print()
    console.print(Panel.fit(
        "[bold cyan]pkgstory[/bold cyan]  [dim]your arch journey, told through pacman.log[/dim]",
        box=box.ROUNDED,
    ))
    console.print()

    console.print(Rule("[bold]Chapter 1 — The Beginning[/bold]", style="cyan"))
    console.print()
    start = stats["first_date"].strftime("%B %d, %Y")
    console.print(f"  Your Arch journey began on [bold cyan]{start}[/bold cyan].")
    console.print(f"  That was [bold]{stats['age_days']} days ago[/bold].")
    console.print(f"  archinstall set up [bold]{stats['base_pkg_count']} packages[/bold] automatically.\n")
    if stats["first_manual"]:
        console.print("  The first things [bold]you[/bold] chose to install after that:\n")
        for i, pkg in enumerate(stats["first_manual"], 1):
            console.print(f"    [cyan]{i}.[/cyan] {pkg}")
    else:
        console.print("  [dim]No manual installs detected yet.[/dim]")
    console.print()

    console.print(Rule("[bold]Chapter 2 — The Numbers[/bold]", style="cyan"))
    console.print()
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Stat", style="dim")
    table.add_column("Value", style="bold")
    table.add_row("Packages installed",  str(stats["total_installs"]))
    table.add_row("Packages removed",    str(stats["total_removes"]))
    table.add_row("Packages upgraded",   str(stats["total_upgrades"]))
    if stats["total_downgrades"]:
        table.add_row("Packages downgraded", f"[yellow]{stats['total_downgrades']}[/yellow]")
    table.add_row("Days with activity",  str(stats["active_days"]))
    console.print(table)
    console.print()

    console.print(Rule("[bold]Chapter 3 — Chaos and Calm[/bold]", style="cyan"))
    console.print()
    busiest = datetime.strptime(stats["busiest_day"], "%Y-%m-%d").strftime("%B %d, %Y")
    console.print(f"  Your most chaotic day was [bold yellow]{busiest}[/bold yellow]")
    console.print(f"  — [bold]{stats['busiest_count']} package events[/bold] in a single day.\n")
    if stats["longest_gap"] > 1:
        console.print(f"  Your longest quiet streak: [bold]{stats['longest_gap']} days[/bold] without touching pacman.")
        if stats["longest_gap"] > 30:
            console.print("  [dim]you were clearly busy. or things were just working.[/dim]")
        elif stats["longest_gap"] > 7:
            console.print("  [dim]a week of stability. rare on arch.[/dim]")
        else:
            console.print("  [dim]couldn't stay away for long.[/dim]")
    console.print()

    if stats["most_upgraded"]:
        console.print(Rule("[bold]Chapter 4 — The Frequent Flyers[/bold]", style="cyan"))
        console.print()
        console.print("  Packages you've upgraded the most:\n")
        for pkg, count in stats["most_upgraded"]:
            bar = "█" * min(count, 30)
            console.print(f"  [cyan]{pkg:<30}[/cyan] {bar} [dim]{count}x[/dim]")
        console.print()

    console.print(Rule("[bold]Chapter 5 — Activity Map[/bold]", style="cyan"))
    console.print()
    console.print("  Package events per day:\n")
    day_activity = stats["day_activity"]
    max_activity = max(day_activity.values()) if day_activity else 1
    for day in sorted(day_activity.keys()):
        count  = day_activity[day]
        filled = int((count / max_activity) * 20)
        bar    = "█" * filled + "░" * (20 - filled)
        d      = datetime.strptime(day, "%Y-%m-%d").strftime("%b %d")
        color  = "red" if count == max_activity else "cyan" if count > max_activity * 0.5 else "dim"
        console.print(f"  [dim]{d}[/dim]  [{color}]{bar}[/{color}]  [dim]{count}[/dim]")
    console.print()

    console.print(Rule(style="cyan"))
    console.print()
    total = stats["total_installs"] + stats["total_removes"] + stats["total_upgrades"]
    console.print(f"  [bold]{total} total package events[/bold] across [bold]{stats['age_days']} days[/bold].")
    console.print(f"  [dim]that's {total / stats['age_days']:.1f} events per day on average.[/dim]")
    console.print()

def render_pkg(pkg: str, all_events: list[dict]) -> int:
    pkg_events = [e for e in all_events if e["pkg"].lower() == pkg.lower()]

    if not pkg_events:
        console.print(f"\n[red]No history found for '{pkg}'[/red]")
        console.print("[dim]Check the package name or try a partial match.[/dim]")
        return 1

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{pkg}[/bold cyan]  [dim]package history[/dim]",
        box=box.ROUNDED,
    ))
    console.print()

    installs   = [e for e in pkg_events if e["action"] == "installed"]
    upgrades   = [e for e in pkg_events if e["action"] == "upgraded"]
    removes    = [e for e in pkg_events if e["action"] == "removed"]
    downgrades = [e for e in pkg_events if e["action"] == "downgraded"]

    action_color = {"installed": "green", "upgraded": "cyan", "removed": "red", "downgraded": "yellow"}
    action_icon  = {"installed": "↓", "upgraded": "↑", "removed": "✗", "downgraded": "↓"}

    for e in pkg_events:
        date       = e["ts"].strftime("%b %d %Y  %H:%M")
        color      = action_color[e["action"]]
        icon       = action_icon[e["action"]]
        chroot_tag = "  [dim](archinstall)[/dim]" if e.get("chroot") else ""
        console.print(
            f"  [dim]{date}[/dim]  "
            f"[{color}]{icon} {e['action']:<12}[/{color}]"
            f"  {e['ver']}{chroot_tag}"
        )

    console.print()

    first_seen = pkg_events[0]["ts"]
    last_seen  = pkg_events[-1]["ts"]
    span_days  = max((last_seen - first_seen).days, 1)

    console.print(f"  [bold]{len(pkg_events)} total events[/bold]")
    if installs:
        console.print(f"  first installed: [cyan]{first_seen.strftime('%B %d, %Y')}[/cyan]")
    if removes:
        console.print(f"  [red]removed {len(removes)} time(s)[/red]")
    if downgrades:
        console.print(f"  [yellow]downgraded {len(downgrades)} time(s)[/yellow]")
    if upgrades:
        avg_days = span_days / len(upgrades)
        console.print(f"  upgraded [bold]{len(upgrades)} time(s)[/bold] over {span_days} days")
        console.print(f"  average time between upgrades: [bold cyan]{avg_days:.1f} days[/bold cyan]")
        console.print()
        if avg_days <= 3:
            console.print("  [red]⚡ extremely fast moving[/red] — watch this package after every update")
        elif avg_days <= 7:
            console.print("  [yellow]🔥 fast moving[/yellow] — upgrades roughly weekly")
        elif avg_days <= 14:
            console.print("  [cyan]steady[/cyan] — upgrades every couple of weeks")
        elif avg_days <= 30:
            console.print("  [dim]slow and stable[/dim] — upgrades monthly")
        else:
            console.print("  [dim]very stable[/dim] — rarely changes")

    console.print()
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pkgstory",
        description="Your Arch journey, told through pacman.log",
        epilog="Examples:\n  pkgstory                    full story\n  pkgstory --pkg firefox      history of a single package\n  pkgstory --pkg mesa         upgrade velocity for mesa\n  pkgstory /path/to/log       use a custom log file",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("log", nargs="?", default=str(LOG_PATH), help="Path to pacman.log")
    parser.add_argument("--pkg", metavar="NAME", help="Show full history for a single package")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        console.print(f"[red]Log not found:[/red] {log_path}")
        return 1

    console.print(f"[dim]Reading {log_path}...[/dim]")
    all_events, manual_events = parse_log(log_path)

    if not all_events:
        console.print("[yellow]No package events found in log.[/yellow]")
        return 1

    if args.pkg:
        return render_pkg(args.pkg, all_events)

    stats = analyse(all_events, manual_events)
    render_story(stats)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[Cancelled]")
        sys.exit(0)

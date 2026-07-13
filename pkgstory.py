#!/usr/bin/env python3
import re
import sys
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

# ── Parser ────────────────────────────────────────────────────────────────────

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

def parse_log(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(errors="replace").splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        ts = parse_ts(m.group("ts"))
        src = m.group("src")
        msg = m.group("msg").strip()

        if src == "ALPM":
            am = ALPM_RE.match(msg)
            if am:
                events.append({
                    "ts": ts,
                    "action": am.group("action"),
                    "pkg": am.group("pkg"),
                    "ver": am.group("ver"),
                })
    return events

# ── Analysis ──────────────────────────────────────────────────────────────────

def analyse(events: list[dict]) -> dict:
    if not events:
        return {}

    first = events[0]["ts"]
    last  = events[-1]["ts"]
    age_days = max((last - first).days, 1)

    installs   = [e for e in events if e["action"] == "installed"]
    removes    = [e for e in events if e["action"] == "removed"]
    upgrades   = [e for e in events if e["action"] == "upgraded"]
    downgrades = [e for e in events if e["action"] == "downgraded"]

    # package install counts
    pkg_install_count: dict[str, int] = defaultdict(int)
    pkg_upgrade_count: dict[str, int] = defaultdict(int)
    for e in installs:
        pkg_install_count[e["pkg"]] += 1
    for e in upgrades:
        pkg_upgrade_count[e["pkg"]] += 1

    # activity per day
    day_activity: dict[str, int] = defaultdict(int)
    for e in events:
        day = e["ts"].strftime("%Y-%m-%d")
        day_activity[day] += 1

    busiest_day   = max(day_activity, key=day_activity.__getitem__)
    busiest_count = day_activity[busiest_day]

    # update streaks — longest gap between days with activity
    active_days = sorted(day_activity.keys())
    longest_gap = 0
    if len(active_days) > 1:
        for i in range(1, len(active_days)):
            d1 = datetime.strptime(active_days[i-1], "%Y-%m-%d")
            d2 = datetime.strptime(active_days[i],   "%Y-%m-%d")
            gap = (d2 - d1).days
            longest_gap = max(longest_gap, gap)

    # most upgraded packages
    most_upgraded = sorted(pkg_upgrade_count.items(), key=lambda x: x[1], reverse=True)[:5]

    # first 10 packages installed (excluding base system bulk install)
    # the first transaction is usually base install, skip it
    first_manual = []
    seen_ts = None
    for e in installs:
        if seen_ts is None:
            seen_ts = e["ts"]
        if e["ts"] == seen_ts:
            continue  # skip base install batch
        first_manual.append(e["pkg"])
        if len(first_manual) >= 10:
            break

    return {
        "first_date":    first,
        "last_date":     last,
        "age_days":      age_days,
        "total_installs": len(installs),
        "total_removes":  len(removes),
        "total_upgrades": len(upgrades),
        "total_downgrades": len(downgrades),
        "busiest_day":   busiest_day,
        "busiest_count": busiest_count,
        "most_upgraded": most_upgraded,
        "first_manual":  first_manual,
        "active_days":   len(active_days),
        "longest_gap":   longest_gap,
        "day_activity":  day_activity,
    }

# ── Story rendering ───────────────────────────────────────────────────────────

def render_story(stats: dict) -> None:
    console.print()
    console.print(Panel.fit(
        "[bold cyan]pkgstory[/bold cyan]  [dim]your arch journey, told through pacman.log[/dim]",
        box=box.ROUNDED,
    ))
    console.print()

    # Chapter 1 — The Beginning
    console.print(Rule("[bold]Chapter 1 — The Beginning[/bold]", style="cyan"))
    console.print()
    start = stats["first_date"].strftime("%B %d, %Y")
    console.print(f"  Your Arch journey began on [bold cyan]{start}[/bold cyan].")
    console.print(f"  That was [bold]{stats['age_days']} days ago[/bold].\n")

    if stats["first_manual"]:
        console.print("  The first things you reached for after base install:")
        for i, pkg in enumerate(stats["first_manual"], 1):
            console.print(f"    [cyan]{i}.[/cyan] {pkg}")
    console.print()

    # Chapter 2 — The Numbers
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

    # Chapter 3 — Chaos and Calm
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

    # Chapter 4 — Most Upgraded
    if stats["most_upgraded"]:
        console.print(Rule("[bold]Chapter 4 — The Frequent Flyers[/bold]", style="cyan"))
        console.print()
        console.print("  Packages you've upgraded the most:\n")
        for pkg, count in stats["most_upgraded"]:
            bar = "█" * min(count, 30)
            console.print(f"  [cyan]{pkg:<30}[/cyan] {bar} [dim]{count}x[/dim]")
        console.print()

    # Chapter 5 — Activity heatmap (last 17 days or all days)
    console.print(Rule("[bold]Chapter 5 — Activity Map[/bold]", style="cyan"))
    console.print()
    console.print("  Package events per day:\n")

    day_activity = stats["day_activity"]
    max_activity = max(day_activity.values()) if day_activity else 1

    for day in sorted(day_activity.keys()):
        count = day_activity[day]
        filled = int((count / max_activity) * 20)
        bar = "█" * filled + "░" * (20 - filled)
        d = datetime.strptime(day, "%Y-%m-%d").strftime("%b %d")
        color = "red" if count == max_activity else "cyan" if count > max_activity * 0.5 else "dim"
        console.print(f"  [dim]{d}[/dim]  [{color}]{bar}[/{color}]  [dim]{count}[/dim]")

    console.print()

    # Closing
    console.print(Rule(style="cyan"))
    console.print()
    total = stats["total_installs"] + stats["total_removes"] + stats["total_upgrades"]
    console.print(f"  [bold]{total} total package events[/bold] across [bold]{stats['age_days']} days[/bold].")
    console.print(f"  [dim]that's {total / stats['age_days']:.1f} events per day on average.[/dim]")
    console.print()

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else LOG_PATH

    if not path.exists():
        console.print(f"[red]Log not found:[/red] {path}")
        return 1

    console.print(f"[dim]Reading {path}...[/dim]")
    events = parse_log(path)

    if not events:
        console.print("[yellow]No package events found in log.[/yellow]")
        return 1

    stats = analyse(events)
    render_story(stats)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[Cancelled]")
        sys.exit(0)

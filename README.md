# pkgstory

Your Arch Linux journey, told through `pacman.log`.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Platform](https://img.shields.io/badge/platform-Arch%20Linux-blue)
![AUR](https://img.shields.io/aur/version/pkgstory)

## Install

**From the AUR (recommended):**
```bash
paru -S pkgstory
```

**From source:**
```bash
git clone https://github.com/Kolgrim33/pkgstory.git
cd pkgstory
pip install --break-system-packages rich
make install
```

## What it does

Most Arch users have a `pacman.log` going back to the day they installed. pkgstory reads it and turns it into something worth reading — your full package history, narrated with personality.

## Usage

```bash
pkgstory                    # your full arch story
pkgstory --pkg firefox      # full history of a single package
pkgstory --pkg mesa         # upgrade velocity for mesa
pkgstory /path/to/log       # use a custom log file
pkgstory --help             # show usage
```

## Full story
╭────────────────────────────────────────────────────────╮
│ pkgstory  your arch journey, told through pacman.log   │
╰────────────────────────────────────────────────────────╯
───────────── Chapter 1 — The Beginning ──────────────
Your Arch journey began on June 26, 2026.
That was 16 days ago.
archinstall set up 554 packages automatically.
The first things you chose to install after that:
1. firefox
2. git
3. paru
4. neovim
...
────────────── Chapter 2 — The Numbers ───────────────
Packages installed   1464
Packages removed     26
Packages upgraded    6
Days with activity   14
───────────── Chapter 3 — Chaos and Calm ─────────────
Your most chaotic day was June 26, 2026
— 957 package events in a single day.
Your longest quiet streak: 3 days without touching pacman.
couldn't stay away for long.
────────── Chapter 4 — The Frequent Flyers ───────────
Packages you've upgraded the most:
hyprpaper                      █ 1x
mesa                           █ 1x
────────────── Chapter 5 — Activity Map ──────────────
Package events per day:
Jun 26  ████████████████████  957
Jun 27  ░░░░░░░░░░░░░░░░░░░░  6
Jul 03  ██░░░░░░░░░░░░░░░░░░  127
...
─────────────────────────────────────────────────────
1496 total package events across 16 days.
that's 93.5 events per day on average.

## Package history

```bash
pkgstory --pkg mesa
```
╭───────────────────────╮
│ mesa  package history │
╰───────────────────────╯
Jun 26 2026  18:41  ↓ installed     24.1.0-1  (archinstall)
Jul 09 2026  14:23  ↑ upgraded      24.1.0-1 → 24.2.0-1
2 total events
first installed: June 26, 2026
upgraded 1 time over 13 days
average time between upgrades: 13.0 days
steady — upgrades every couple of weeks

Shows the full install/upgrade/remove/downgrade timeline, whether a package was installed by archinstall or manually, and upgrade velocity — how fast this package moves on a rolling release.

## Fuzzy search

Mistyped a package name? pkgstory suggests the closest match:

```bash
pkgstory --pkg brave
```
No history found for 'brave'
did you mean:
pkgstory --pkg brave-bin

## Why it exists

Every existing pacman log tool is either a GUI viewer or a raw stats counter. None of them tell you a story. pkgstory is the first terminal-native tool that narrates your Arch history with personality — and the only one that shows upgrade velocity per package.

## Requirements

- Python 3.11+
- `rich` — installed automatically via AUR, or `pip install --break-system-packages rich`
- `/var/log/pacman.log` — present on every Arch install by default

## Also check out

- [hyprkit](https://github.com/Kolgrim33/hyprkit) — a companion CLI for managing Hyprland (`paru -S hyprkit-git`)

## Roadmap

- `--since 30d` — story for the last N days only
- `--search <term>` — search across all package names
- Chapter 6 — biggest single update session
- Chapter 7 — package categories breakdown
- Weekly digest mode

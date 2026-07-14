# pkgstory

Your Arch Linux journey, told through `pacman.log`.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Platform](https://img.shields.io/badge/platform-Arch%20Linux-blue)

## What it does

Most Arch users have a `pacman.log` going back to the day they installed. pkgstory reads it and turns it into something worth reading.

```bash
python pkgstory.py
```
Chapter 1 — The Beginning
Your Arch journey began on June 26, 2026.
That was 16 days ago.
The first things you reached for after base install:
1. hyprland
2. waybar
3. kitty

Chapter 2 — The Numbers
Packages installed   1464
Packages removed     26
Packages upgraded    6
Days with activity   14

Chapter 3 — Chaos and Calm
Your most chaotic day was June 26, 2026
— 957 package events in a single day.
Your longest quiet streak: 3 days without touching pacman.


Chapter 4 — The Frequent Flyers
Packages you've upgraded the most:
hyprpaper    █ 1x
mesa         █ 1x

Chapter 5 — Activity Map
Jun 26  ████████████████████  957

Jun 27  ░░░░░░░░░░░░░░░░░░░░  6

Jul 03  ██░░░░░░░░░░░░░░░░░░  127


## Why it exists

Every existing pacman log tool is either a GUI viewer or a raw stats counter. None of them tell you a story. pkgstory is the first terminal-native tool that narrates your Arch history with personality.

## Install

```bash
git clone https://github.com/Kolgrim33/pkgstory.git
cd pkgstory
pip install --break-system-packages rich
python pkgstory.py
```

## Usage

```bash
# reads /var/log/pacman.log by default
python pkgstory.py

# point it at a specific log
python pkgstory.py /path/to/pacman.log
```

## Requirements

- Python 3.11+
- `rich` — `pip install --break-system-packages rich`
- `/var/log/pacman.log` (present on every Arch install by default)

## Roadmap

- Fix Chapter 1 to skip base install batch and show your real first choices
- Chapter 6 — package categories (dev tools vs multimedia vs system)
- Chapter 7 — biggest single update (most packages in one pacman -Syu)
- `pkgstory --since 30d` — story for the last N days only
- `pkgstory --pkg firefox` — full history of a single package
- Weekly digest mode

# Changelog

## [0.3.0] - 2026-07-14
### Added
- `--pkg <name>` flag — full history of a single package
- Upgrade velocity rating per package (extremely fast / fast / steady / slow / very stable)
- Average days between upgrades
- archinstall tag on packages installed during initial setup
- Install as system command via `/usr/local/bin/pkgstory`
- Usage examples in `--help`

## [0.2.0] - 2026-07-13
### Added
- Chapter 1 now correctly skips archinstall chroot transactions
- Detects `-r /mnt` commands to identify automated installer packages
- Shows real first manual installs (what you actually chose after base install)
- `analyse()` now separates all_events from manual_events

### Fixed
- Chapter 1 was showing base system deps instead of user's first choices

## [0.1.0] - 2026-07-12
### Added
- Initial release
- Parses `/var/log/pacman.log` for installs, removes, upgrades, downgrades
- Chapter 1: journey start date and first packages installed
- Chapter 2: total package event counts
- Chapter 3: busiest day and longest quiet streak
- Chapter 4: most frequently upgraded packages
- Chapter 5: activity heatmap across all days
- Closing summary with events per day average
- Custom log path support via positional argument

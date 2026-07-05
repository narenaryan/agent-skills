---
name: macos-disk-space-recovery
description: Use when a Mac is low on disk space or Finder/System Data is vague - measures APFS usage, ranks real offenders, separates safe cache cleanup from risky data deletion, stops apps that recreate files, and re-measures reclaimed space
---

# macOS Disk Space Recovery

Treat Finder storage bars as hints. Start with APFS free space, then rank real directories by size before deleting anything.

## First measurements

Run these first and report both used and free space:

```bash
df -h /
diskutil info "/System/Volumes/Data"
tmutil listlocalsnapshots /
```

Then rank likely offenders instead of guessing:

```bash
du -hd 1 "$HOME" 2>/dev/null | sort -h
du -hd 1 "$HOME/Library" 2>/dev/null | sort -h
du -hd 1 /private/var 2>/dev/null | sort -h
```

## Offender map

| Path family | Typical contents | Deletion risk |
|-------------|------------------|---------------|
| `~/Library/Caches`, app cache folders, logs | rebuildable cache and logs | low |
| `~/Downloads`, large project folders, archives | user files | ask first |
| `~/Library/Application Support` | app state, downloads, models | medium to high |
| `~/Library/Group Containers`, `~/Library/Containers` | sandboxed app data | high |
| `~/.cache`, `~/.local`, `~/.ollama` | tool caches, package data, local models | medium |
| `/private/var/vm`, `/private/var/db` | swap, system databases | do not delete manually |

Commonly missed large paths: `~/.ollama`, Docker data, Xcode DerivedData, simulators, Steam libraries, Microsoft app data, JetBrains caches, WhatsApp group containers, and large image-generation app containers.

## Cleanup order

1. Clear low-risk caches and logs first.
2. Identify one large app or folder family at a time.
3. Ask before deleting anything that can remove user content or reset app state.
4. Quit the owning app before deleting its support or container directories.
5. Re-measure after every significant deletion and report the delta.

## App-family removal pattern

When asked to remove an app family, clarify whether the scope is:

- only caches
- Library data but not `/Applications`
- a full uninstall including app bundles

Before deleting app data, stop recreating processes:

```bash
pgrep -ifl 'Brave|Steam|Docker|WhatsApp|OneDrive|JetBrains'
```

If files reappear or deletion reports `Directory not empty`, the app or helper is still running. Quit it, then retry.

## Decision rules

- Prefer measured facts over generic advice.
- Do not manually delete swap, sleep, or other `/private/var/vm` files.
- Treat `tmutil` snapshots as a special case; remove them only if they actually exist and are materially large.
- Separate "space used by app data" from "app installed in `/Applications`".
- Quote paths with spaces such as `Library/Group Containers`.

## Pitfalls

- Blaming Apple update caches without checking sizes first.
- Deleting large sandbox folders while the app is still running, then assuming the cleanup failed.
- Reporting only `df` output and missing APFS container free space from `diskutil`.
- Removing browser or editor support folders without warning that profiles, sessions, or settings may be lost.
- Deleting many categories at once and losing the ability to say which action reclaimed the space.

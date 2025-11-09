
# Secret Santa Trustee — Encrypted Edition

A privacy-first Secret Santa helper for small groups, with an optional AES-encrypted backup of assignments.  
Each participant privately looks up their recipient; no one else’s assignment is shown.

- Python 3.8+
- Cross-platform: Windows
- No network access required

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Install](#install)
- [Quick Start (Interactive Menu)](#quick-start-interactive-menu)
- [Command-Line Usage](#command-line-usage)
  - [Options](#options)
  - [Examples](#examples)
- [Encrypted Backup](#encrypted-backup)
- [How the Reveal Flow Works](#how-the-reveal-flow-works)
- [Privacy & Data Handling](#privacy--data-handling)
- [Troubleshooting](#troubleshooting)
- [Notes on Terminals](#notes-on-terminals)
- [License](#license)

---

## Features
- **Private reveal**: each participant sees only their own recipient.
- **Derangement**: nobody gifts to themselves.
- **Optional encrypted backup**: creates an AES ZIP archive of assignments; the password is split into per-person segments.
- **Clear screen and scrollback** after each reveal to reduce shoulder-surfing.
- **Temporary files only**: created in the OS temp directory and deleted on exit.
- **Interactive menu** or **command-line flags**; deterministic runs via `--seed`.

---

## Requirements
- Python ≥ 3.8
- Package: `pyzipper` (for encrypted backup)

> If you do not enable encrypted backup, the script still runs without network or external services.

---

## Install
```bash
pip install pyzipper
````

> You may wish to use a virtual environment: `python -m venv .venv && source .venv/bin/activate` (PowerShell: `.venv\Scripts\Activate`).

---

## Quick Start (Interactive Menu)

Run with an on-screen configuration menu:

```bash
python3 "Trustee Encrypted V2.py"
```

The menu lets you choose:

* **Screen clearing**: manual (press Enter) or auto-clear after N seconds.
* **Encrypted backup**: enable/disable.

---

## Command-Line Usage

You can bypass the menu and control behavior via flags:

```bash
python3 "Trustee Encrypted V2.py" [OPTIONS]
```

### Options

| Option           | Type / Values   | Effect                                                                            |
| ---------------- | --------------- | --------------------------------------------------------------------------------- |
| `--timeout N`    | integer `N ≥ 0` | Auto-clear after N seconds. (`0` = clear immediately.)                            |
| `--no-enter`     | flag            | Clear immediately after showing the recipient (same as `--timeout 0`).            |
| `--allow-repeat` | flag            | Allow a participant to view their assignment multiple times. Default is one-shot. |
| `--seed INT`     | integer         | Use a fixed PRNG seed for deterministic assignments.                              |
| `--no-backup`    | flag            | Disable encrypted ZIP backup.                                                     |
| `--skip-menu`    | flag            | Skip the interactive menu and only use the above flags/defaults.                  |

### Examples

```bash
# Default (interactive menu; manual clear by Enter)
python3 "Trustee Encrypted V2.py"

# Auto-clear after 5 seconds
python3 "Trustee Encrypted V2.py" --timeout 5 --skip-menu

# Instant clear + deterministic pairings
python3 "Trustee Encrypted V2.py" --no-enter --seed 123 --skip-menu

# Disable backup and keep manual Enter mode
python3 "Trustee Encrypted V2.py" --no-backup --skip-menu
```

---

## Encrypted Backup

When enabled, the program creates:

```
secret_santa_YYYYMMDD_HHMMSS.zip
```

in the script directory. It generates a numeric password whose length is **4 × (number of participants)** and splits it into equal **per-person segments**:

```
[Part 1] 1234
[Part 2] 5678
...
```

To decrypt the ZIP, concatenate all segments **in order** to reconstruct the full password.
The ZIP uses AES encryption and is compatible with tools such as 7-Zip and WinRAR.

---

## How the Reveal Flow Works

1. Organizer inputs all participant names (comma-separated).
2. The program builds a **derangement** (no self-assignment).
3. Each participant types their name (case-insensitive) to view their recipient.
4. After viewing, the screen (and scrollback, if supported) is cleared.
5. Temporary files are removed on exit.

If multiple participants differ only by case (e.g., `alice`, `Alice`), the script will prompt for disambiguation.

---

## Privacy & Data Handling

* Assignments are stored in a temporary JSON file in the OS temp directory and removed on exit.
* If encrypted backup is **disabled**, no persistent copy is written.
* If encrypted backup is **enabled**, a single AES ZIP is written; each participant receives a password segment on their reveal screen.
* The program does **not** access the network or external services.

# Local_Secret_Santa_Trustee
Merry Christmas!!!!

# Secret Santa Trustee

A simple, privacy-first Secret Santa helper for small groups.

The organizer enters a list of names, and each participant privately learns their recipient by typing their own name. The program generates a **derangement** (nobody gifts to themselves), shows only the relevant match, and clears the screen so the next person cannot see any previous results. A temporary assignment file is created and deleted automatically when the session ends.

## Features

- **Private reveal:** only one person’s assignment is ever shown.
- **Screen + scrollback clearing:** prevents snooping.
- **No persistent data:** temporary file auto-deleted on exit.
- **Case-insensitive lookup** for convenience.
- **Optional one-shot viewing** (default): each person may see only once.
- **Configurable via CLI flags.**

## Usage

```bash
python3 SecretSantaTrustee.py

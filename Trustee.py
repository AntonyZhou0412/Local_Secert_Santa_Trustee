#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secret Santa Trustee

A single-run, privacy-first Secret Santa helper.

1. The organizer enters all participant names.
2. The program randomly pairs everyone so that nobody gifts to themselves
   (this is a *derangement*).
3. It writes the assignments to a temporary file for the duration of the run.
4. Each participant enters their name to privately learn their recipient.
   After each reveal, the screen and scrollback are cleared for privacy.
5. When the session ends (or is interrupted), the temporary file is deleted.

Python: 3.8+
"""

import atexit
import json
import os
import random
import signal
import sys
import tempfile
import time
import argparse
from typing import Dict, List, Optional, Set

# ============ Default behavior ============
ONE_SHOT_REVEAL_DEFAULT = True     # each person may view only once
REVEAL_NEEDS_ENTER_DEFAULT = True  # press Enter to clear after viewing
REVEAL_TIMEOUT_SEC_DEFAULT = False  # set an integer number of seconds for auto-clear
# ==========================================

TMP_ASSIGN_PATH: Optional[str] = None


def clear_screen_and_scrollback() -> None:
    """Clear current screen AND scrollback/history."""
    sys.stdout.write("\033[2J\033[H")  # clear visible screen & move cursor home
    sys.stdout.write("\033[3J")        # clear scrollback
    sys.stdout.flush()
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass


def exit_cleanup() -> None:
    """Remove the temporary assignment file if it exists."""
    global TMP_ASSIGN_PATH
    if TMP_ASSIGN_PATH and os.path.exists(TMP_ASSIGN_PATH):
        try:
            os.remove(TMP_ASSIGN_PATH)
        except Exception:
            pass  # best-effort deletion


def install_signal_handlers() -> None:
    """Ensure Ctrl+C (SIGINT) and SIGTERM trigger a clean exit."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: sys.exit(0))


def prompt_names() -> List[str]:
    """Prompt for comma-separated names and return a de-duplicated list."""
    print("Enter all participant names, comma-separated (at least 2):")
    raw = input("> ").strip()
    names = [n.strip() for n in raw.split(",") if n.strip()]

    seen = set()
    uniq: List[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            uniq.append(n)

    if len(uniq) < 2:
        print("Need at least 2 distinct names. Exiting.")
        sys.exit(1)
    return uniq


def gen_derangement(names: List[str]) -> Dict[str, str]:
    """Generate a derangement (no one gifts to themselves) by shuffle-and-check."""
    givers = names[:]
    receivers = names[:]
    while True:
        random.shuffle(receivers)
        if all(g != r for g, r in zip(givers, receivers)):
            return dict(zip(givers, receivers))


def write_tmp_assign(assignments: Dict[str, str]) -> None:
    """Write assignments to a secure temp file (auto-deleted on exit)."""
    global TMP_ASSIGN_PATH
    fd, path = tempfile.mkstemp(prefix="secret_santa_", suffix=".json")
    os.close(fd)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(assignments, f, ensure_ascii=False, indent=2)
    TMP_ASSIGN_PATH = path


def wait_then_clear(needs_enter: bool, timeout_sec: Optional[int]) -> None:
    """Wait before clearing the screen, based on settings.

    If an auto-clear timeout is configured (timeout_sec is an int >= 0), this
    now prints a brief English instruction so the viewer knows the message will
    disappear after X seconds and to pass the device to the next person.
    """
    if needs_enter:
        input("\n(Press Enter to clear, and pass to next person)")
    elif isinstance(timeout_sec, int) and timeout_sec >= 0:
        # Provide an explicit prompt for the automatic-clear case.
        if timeout_sec == 0:
            # No wait: inform user immediately before clearing.
            print("\n(Clearing now. Please pass the device to the next person.)")
            # no sleep required for 0
        else:
            # Auto-clear after N seconds: show message with X substituted.
            print(f"\n(This message will be automatically cleared in {timeout_sec} seconds. Please pass the device to the next person afterward.)")
            time.sleep(timeout_sec)
    clear_screen_and_scrollback()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Secret Santa Trustee")
    parser.add_argument(
        "--allow-repeat",
        action="store_true",
        help="Allow repeated views by the same participant (default: disabled).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Auto-clear after N seconds (disables 'press Enter' prompt).",
    )
    parser.add_argument(
        "--no-enter",
        action="store_true",
        help="Clear immediately after reveal (same as --timeout 0).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Set PRNG seed for reproducible assignments (optional).",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Runtime configuration
    one_shot_reveal = not args.allow_repeat
    if args.no_enter:
        reveal_needs_enter = False
        reveal_timeout_sec = 0
    elif args.timeout is not None:
        reveal_needs_enter = False
        reveal_timeout_sec = args.timeout
    else:
        reveal_needs_enter = REVEAL_NEEDS_ENTER_DEFAULT
        reveal_timeout_sec = REVEAL_TIMEOUT_SEC_DEFAULT

    if args.seed is not None:
        random.seed(args.seed)

    print("Secret Santa Trustee")
    install_signal_handlers()
    atexit.register(exit_cleanup)

    names = prompt_names()
    assignments = gen_derangement(names)
    write_tmp_assign(assignments)

    # Build case-insensitive lookup that preserves duplicates differing only by case
    lc_to_names: Dict[str, List[str]] = {}
    for original in names:
        lc_to_names.setdefault(original.lower(), []).append(original)
    viewed: set[str] = set()

    clear_screen_and_scrollback()
    print("Assignments generated. Private reveal mode started.")
    print("Type your NAME to see whom you gift to (case-insensitive).")
    print("Type 'exit' or 'quit' to end (temporary file will be deleted).")

    while True:
        try:
            query = input("\nEnter your name: ").strip()
            if not query:
                print("Please enter a non-empty name.")
                continue
            if query.lower() in ("exit", "quit"):
                print("Exiting. Temporary file cleaned up. Happy holidays!")
                return

            key = query.lower()
            if key not in lc_to_names:
                print("Name not found. Please re-check spelling and try again.")
                continue

            candidates = lc_to_names[key]
            real_name: str | None = None

            if query in candidates:
                real_name = query
            elif len(candidates) == 1:
                real_name = candidates[0]
            else:
                print("Multiple participants match that entry:")
                for idx, candidate in enumerate(candidates, start=1):
                    print(f"  {idx}. {candidate}")

                while True:
                    selection = input(
                        "Enter the number or exact name (or type 'cancel' to abort): "
                    ).strip()

                    if not selection:
                        print("Please enter a selection.")
                        continue

                    if selection.lower() in {"cancel", "abort", "back"}:
                        print("Selection canceled. Returning to main prompt.")
                        break

                    if selection.isdigit():
                        idx = int(selection)
                        if 1 <= idx <= len(candidates):
                            real_name = candidates[idx - 1]
                            break
                        print("Number out of range. Try again.")
                        continue

                    if selection in candidates:
                        real_name = selection
                        break

                    print("Input did not match any option. Try again.")

                if real_name is None:
                    continue

            if one_shot_reveal and real_name in viewed:
                print("You have already viewed your assignment.")
                continue

            recipient = assignments[real_name]

            clear_screen_and_scrollback()
            print(f"*** ONLY FOR {real_name} ***")
            print(f"You will gift to: {recipient}")
            viewed.add(real_name)

            # After clearing, loop simply asks for the next name
            wait_then_clear(reveal_needs_enter, reveal_timeout_sec)

        except EOFError:
            print("\nEOF received. Exiting.")
            return


if __name__ == "__main__":
    main()

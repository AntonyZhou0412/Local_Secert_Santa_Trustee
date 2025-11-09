#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secret Santa Trustee

A single-run, privacy-first Secret Santa helper with encrypted backup.

1. The organizer enters all participant names.
2. The program randomly pairs everyone so that nobody gifts to themselves
   (this is a *derangement*).
3. It writes the assignments to a temporary file for the duration of the run.
4. Creates an encrypted ZIP backup in the script's directory.
5. Each participant enters their name to privately learn their recipient
   AND their portion of the encryption password.
   After each reveal, the screen and scrollback are cleared for privacy.
6. When the session ends (or is interrupted), the temporary file is deleted.

Python: 3.8+
Dependencies: pip install pyzipper
"""

import atexit
import json
import os
import random
import secrets
import signal
import sys
import tempfile
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
try:
    import pyzipper
except ImportError:
    print("Error: pyzipper module not found.")
    print("Please install it with: pip install pyzipper")
    sys.exit(1)

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


def show_configuration_menu() -> Tuple[bool, Optional[int], bool]:
    """
    Display configuration menu to let users choose operation modes.
    
    Returns:
        tuple: (use_manual_mode, timeout_seconds, use_password_mode)
            - use_manual_mode: True means manual mode (press Enter to switch)
            - timeout_seconds: If not manual mode, number of seconds for auto-clear
            - use_password_mode: True means generate encrypted backup
    """
    clear_screen_and_scrollback()
    print("=" * 60)
    print("Secret Santa Trustee - Configuration Settings")
    print("=" * 60)
    print()
    
    # Option 1: Screen clearing mode
    print("[Option 1] Screen clearing after viewing results:")
    print("  Enter 0: Manual mode - Press Enter to clear screen")
    print("  Enter N (positive integer): Auto mode - Clear after N seconds")
    print()
    
    timeout_seconds = None
    use_manual_mode = True
    
    while True:
        choice = input("Enter timeout value (0 for manual) [default: 0]: ").strip()
        
        # Default to manual mode (0)
        if not choice:
            use_manual_mode = True
            timeout_seconds = None
            break
        
        # Try to parse as integer
        try:
            value = int(choice)
            if value < 0:
                print("Invalid input. Please enter 0 or a positive integer.")
                continue
            
            if value == 0:
                # Manual mode
                use_manual_mode = True
                timeout_seconds = None
            else:
                # Auto mode with specified timeout
                use_manual_mode = False
                timeout_seconds = value
            break
            
        except ValueError:
            print("Invalid input. Please enter a valid number (0 or positive integer).")
    
    print()
    print("=" * 60)
    
    # Option 2: Password mode
    print("[Option 2] Generate encrypted backup file:")
    print("  [1] Yes - Create encrypted ZIP archive, each person gets a password part")
    print("  [2] No  - Do not create backup file")
    print()
    
    while True:
        choice = input("Please choose (1/2) [default: 1]: ").strip()
        if not choice or choice == "1":
            use_password_mode = True
            break
        elif choice == "2":
            use_password_mode = False
            break
        else:
            print("Invalid input. Please enter 1 or 2")
    
    print()
    print("=" * 60)
    print("Configuration complete!")
    if use_manual_mode:
        print(f"  - Screen clearing: Manual (Press Enter)")
    else:
        print(f"  - Screen clearing: Auto (Clear after {timeout_seconds} seconds)")
    print(f"  - Encrypted backup: {'Enabled' if use_password_mode else 'Disabled'}")
    print("=" * 60)
    print()
    input("Press Enter to continue...")
    
    return use_manual_mode, timeout_seconds, use_password_mode


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


def generate_secure_numeric_password(length: int) -> str:
    """Generate a secure random password consisting only of digits."""
    return ''.join(secrets.choice('0123456789') for _ in range(length))


def split_password_into_parts(password: str, num_parts: int) -> List[str]:
    """Split password into N equal parts (each 4 digits)."""
    part_length = len(password) // num_parts
    return [password[i:i + part_length] for i in range(0, len(password), part_length)]


def create_encrypted_backup(assignments: Dict[str, str], num_participants: int) -> Tuple[str, str]:
    """Create an encrypted ZIP file containing the assignments in the script's directory.
    
    Returns:
        tuple: (zip_file_path, password)
    """
    # Generate password: 4 * n digits
    password_length = 4 * num_participants
    password = generate_secure_numeric_password(password_length)
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create txt file with assignments (temporary)
    txt_fd, txt_path = tempfile.mkstemp(prefix="secret_santa_", suffix=".txt")
    try:
        with os.fdopen(txt_fd, 'w', encoding='utf-8') as f:
            f.write("Secret Santa Assignments\n")
            f.write("=" * 50 + "\n\n")
            for giver, receiver in sorted(assignments.items()):
                f.write(f"{giver} -> {receiver}\n")
        
        # Create encrypted ZIP file in the script's directory
        zip_filename = f"secret_santa_{timestamp}.zip"
        zip_path = os.path.join(script_dir, zip_filename)
        
        with pyzipper.AESZipFile(
            zip_path,
            'w',
            compression=pyzipper.ZIP_LZMA,
            encryption=pyzipper.WZ_AES
        ) as zf:
            zf.setpassword(password.encode('utf-8'))
            # Add the txt file to zip with just the basename
            zf.write(txt_path, os.path.basename(txt_path))
        
        return zip_path, password
    
    finally:
        # Clean up the temporary txt file
        try:
            os.remove(txt_path)
        except Exception:
            pass


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
    """Wait before clearing the screen, based on settings."""
    if needs_enter:
        input("\n(Press Enter to clear, and pass to next person)")
    elif isinstance(timeout_sec, int) and timeout_sec >= 0:
        if timeout_sec == 0:
            print("\n(Clearing now. Please pass the device to the next person.)")
        else:
            print(f"\n(This message will be automatically cleared in {timeout_sec} seconds. Please pass the device to the next person afterward.)")
            time.sleep(timeout_sec)
    clear_screen_and_scrollback()


def build_arg_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
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
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating encrypted backup ZIP file.",
    )
    parser.add_argument(
        "--skip-menu",
        action="store_true",
        help="Skip configuration menu and use command-line arguments or defaults.",
    )
    return parser


def main() -> None:
    """Main entry point for the Secret Santa Trustee program."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # Show configuration menu unless --skip-menu is specified
    if not args.skip_menu and not any([args.no_enter, args.timeout is not None]):
        use_manual_mode, timeout_seconds, use_password_mode = show_configuration_menu()
        
        # Set parameters based on menu choices
        reveal_needs_enter = use_manual_mode
        reveal_timeout_sec = timeout_seconds if not use_manual_mode else False
        no_backup = not use_password_mode
    else:
        # Use command-line arguments
        if args.no_enter:
            reveal_needs_enter = False
            reveal_timeout_sec = 0
        elif args.timeout is not None:
            reveal_needs_enter = False
            reveal_timeout_sec = args.timeout
        else:
            reveal_needs_enter = REVEAL_NEEDS_ENTER_DEFAULT
            reveal_timeout_sec = REVEAL_TIMEOUT_SEC_DEFAULT
        
        no_backup = args.no_backup

    one_shot_reveal = not args.allow_repeat

    # Set random seed if specified
    if args.seed is not None:
        random.seed(args.seed)

    clear_screen_and_scrollback()
    print("Secret Santa Trustee")
    install_signal_handlers()
    atexit.register(exit_cleanup)

    # Get participant names and generate assignments
    names = prompt_names()
    assignments = gen_derangement(names)
    write_tmp_assign(assignments)

    # Create encrypted backup if enabled
    password_parts: List[str] = []
    zip_path: Optional[str] = None
    
    if not no_backup:
        try:
            zip_path, full_password = create_encrypted_backup(assignments, len(names))
            password_parts = split_password_into_parts(full_password, len(names))
            print(f"\nEncrypted backup created: {os.path.basename(zip_path)}")
            print(f"Location: {os.path.dirname(zip_path)}")
            time.sleep(2)  # Brief pause before clearing
        except Exception as e:
            print(f"\nWarning: Failed to create encrypted backup: {e}")
            time.sleep(2)

    # Build case-insensitive lookup that preserves duplicates differing only by case
    lc_to_names: Dict[str, List[str]] = {}
    for original in names:
        lc_to_names.setdefault(original.lower(), []).append(original)
    viewed: Set[str] = set()

    # Start private reveal mode
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
            real_name: Optional[str] = None

            # Handle exact match or single candidate
            if query in candidates:
                real_name = query
            elif len(candidates) == 1:
                real_name = candidates[0]
            else:
                # Multiple matches - ask for clarification
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

            # Check if already viewed (one-shot mode)
            if one_shot_reveal and real_name in viewed:
                print("You have already viewed your assignment.")
                continue

            recipient = assignments[real_name]

            # Display assignment
            clear_screen_and_scrollback()
            print(f"*** ONLY FOR {real_name} ***")
            print(f"\nYou will gift to: {recipient}")
            
            # Show password part if backup was created
            if password_parts and zip_path:
                # Find this person's position in the original names list
                person_index = names.index(real_name)
                password_part = password_parts[person_index]
                print(f"\n{'='*50}")
                print("YOUR PART OF THE ENCRYPTION PASSWORD:")
                print(f"[Part {person_index + 1}] {password_part}")
                print(f"{'='*50}")
                print("\n📝 Save this password part securely!")
                print("All participants must combine their parts (in order)")
                print(f"to unlock: {os.path.basename(zip_path)}")
            
            viewed.add(real_name)

            # Wait and clear screen
            wait_then_clear(reveal_needs_enter, reveal_timeout_sec)

        except EOFError:
            print("\nEOF received. Exiting.")
            return


if __name__ == "__main__":
    main()

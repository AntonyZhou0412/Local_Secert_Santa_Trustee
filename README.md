# Local_Secret_Santa_Trustee
Merry Christmas!!!!

# Secret Santa Trustee

A simple, privacy-first Secret Santa helper for small groups.

The organizer enters a list of names, and each participant privately learns their recipient by typing their own name. The program generates a **derangement** (nobody gifts to themselves), shows only the relevant match, and clears the screen so the next person cannot see any previous results. A temporary assignment file is created and deleted automatically when the session ends.

---

## 🎄 Features

- **Private reveal:** only one person’s assignment is ever shown.
- **Screen + scrollback clearing:** prevents snooping.
- **No persistent data:** temporary file auto-deleted on exit.
- **Case-insensitive lookup** for convenience.
- **Optional one-shot viewing** (default): each person may see only once.
- **Configurable via CLI flags.**

---

## 🧭 Default Mode (Enter-to-Clear)

By default, the program runs in **manual mode**:

- Each participant types their name to see their gift recipient.
- After viewing, the program displays:
  > (Press Enter to clear, and pass to next person)
- When the participant presses **Enter**, the screen and scrollback are cleared.

This ensures maximum privacy for small, in-person groups.

To run the program in this default mode:

```bash
python3 Trustee.py
```

---

## ⚙️ Other Modes & Options

You can customize the reveal and clearing behavior using command-line flags.

### Auto-Clear Mode
Automatically clears after a fixed delay.

```bash
python3 Trustee.py --timeout 5
```
This means the message will be automatically erased after **5 seconds**. The program displays:
> (This message will be automatically cleared in 5 seconds. Please pass the device to the next person afterward.)

### Instant-Clear Mode
Immediately clears after showing the recipient (no waiting, no Enter press):

```bash
python3 Trustee.py --no-enter
```
Displays:
> (Clearing now. Please pass the device to the next person.)

### Allow Repeat Viewing
By default, each participant can view their result **only once**. To allow multiple reveals per person:

```bash
python3 Trustee.py --allow-repeat
```

### Reproducible Results (Seed)
You can provide a seed for deterministic pairings:

```bash
python3 Trustee.py --seed 123
```
This ensures the same name list always produces the same assignments.

---

## 💡 Example Commands

```bash
# Default: manual enter mode
python3 Trustee.py

# 5-second auto-clear
python3 Trustee.py --timeout 5

# Instant clear (no waiting)
python3 Trustee.py --no-enter

# Allow repeat viewing
python3 Trustee.py --allow-repeat

# Combine options
python3 Trustee.py --timeout 3 --allow-repeat --seed 42
```

---

## 🧹 Notes

- Temporary assignment file is deleted automatically on exit.
- Works on Windows, macOS, and Linux.
- The program clears both the **screen** and the **scrollback buffer**, but some terminals may not fully support the latter.

---

## 🎅 Credits

Developed with care to make your Secret Santa draws private, fun, and stress-free!

Happy holidays and enjoy your Secret Santa! 🎁

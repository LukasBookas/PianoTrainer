"""
Console song selection with arrow keys (curses).

No song -> None. Exactly one song -> picked directly. Several -> arrow menu.
Falls back to a simple numbered menu when curses is unavailable (e.g. Windows
without 'windows-curses', or output redirected in an IDE).
"""

import os
import sys

try:
    import curses
except ImportError:
    curses = None  # no curses -> fall back to the text menu later

from config import MIDI_EXTENSIONS


def list_songs(folder: str) -> list[str]:
    """Returns the sorted list of MIDI files in the folder (full paths)."""
    if not os.path.isdir(folder):
        return []
    dateien = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(MIDI_EXTENSIONS)
    ]
    return sorted(dateien)


def _safe_addstr(win, y, x, text, attr=0) -> None:
    """addstr that won't crash when the text runs past the screen edge."""
    height, width = win.getmaxyx()
    if y >= height:
        return
    try:
        win.addstr(y, x, text[: max(0, width - x - 1)], attr)
    except curses.error:
        pass


def _run_menu(stdscr, title: str, options: list[str]):
    """Shows the menu; returns the chosen index, or None on cancel."""
    curses.curs_set(0)
    stdscr.keypad(True)

    idx = 0   # currently highlighted entry
    top = 0   # topmost visible entry (for scrolling long lists)

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        kopf, fuss = 2, 1
        sichtbar = max(1, height - kopf - fuss)

        # Keep the highlighted entry within the visible window.
        if idx < top:
            top = idx
        elif idx >= top + sichtbar:
            top = idx - sichtbar + 1

        _safe_addstr(stdscr, 0, 0, title, curses.A_BOLD)
        for zeile, i in enumerate(range(top, min(top + sichtbar, len(options)))):
            markiert = i == idx
            text = ("> " if markiert else "  ") + options[i]
            attr = curses.A_REVERSE if markiert else curses.A_NORMAL
            _safe_addstr(stdscr, kopf + zeile, 0, text, attr)
        _safe_addstr(stdscr, height - 1, 0,
                     "Pfeile: waehlen | Enter: bestaetigen | q: abbrechen",
                     curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(options)
        elif key in (curses.KEY_ENTER, 10, 13):
            return idx
        elif key in (27, ord("q")):  # Esc or q
            return None


def _curses_usable() -> bool:
    """True only if curses exists AND we have a real terminal (not redirected)."""
    if curses is None or os.environ.get("PIANO_NO_CURSES"):
        return False
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _text_menu(songs: list[str], namen: list[str]):
    """Simple numbered fallback menu when curses is unavailable."""
    print("Song waehlen:")
    for i, name in enumerate(namen):
        print(f"  [{i}] {name}")
    while True:
        wahl = input("Nummer eingeben (oder q zum Abbrechen): ").strip()
        if wahl.lower() == "q":
            return None
        if wahl.isdigit() and 0 <= int(wahl) < len(songs):
            return songs[int(wahl)]
        print("Ungueltige Eingabe.")


def choose_song(folder: str):
    """Lets the user pick a song. Returns the full path, or None (none found or cancelled)."""
    songs = list_songs(folder)

    if not songs:
        return None
    if len(songs) == 1:
        return songs[0]

    namen = [os.path.basename(s) for s in songs]

    if _curses_usable():
        try:
            idx = curses.wrapper(_run_menu, "Song waehlen:", namen)
            return None if idx is None else songs[idx]
        except Exception:
            pass  # on any problem, fall back to the text menu

    return _text_menu(songs, namen)
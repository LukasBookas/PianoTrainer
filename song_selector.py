"""
Konsolen-Auswahl der Songs mit Pfeiltasten (curses).

- Kein Song im Ordner   -> None
- Genau ein Song        -> wird direkt gewaehlt (keine GUI)
- Mehrere Songs         -> Auswahlmenue mit Pfeil hoch/runter, Enter = waehlen

Hinweis: curses ist unter Linux/macOS Standard. Unter Windows zusaetzlich
'windows-curses' installieren (pip install windows-curses).
"""

import curses
import os

from config import MIDI_EXTENSIONS


def list_songs(folder: str) -> list[str]:
    """Liefert die sortierte Liste der MIDI-Dateien im Ordner (volle Pfade)."""
    if not os.path.isdir(folder):
        return []
    dateien = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(MIDI_EXTENSIONS)
    ]
    return sorted(dateien)


def _safe_addstr(win, y, x, text, attr=curses.A_NORMAL) -> None:
    """addstr, das nicht abstuerzt, wenn der Text ueber den Rand laeuft."""
    height, width = win.getmaxyx()
    if y >= height:
        return
    try:
        win.addstr(y, x, text[: max(0, width - x - 1)], attr)
    except curses.error:
        pass


def _run_menu(stdscr, title: str, options: list[str]):
    """Zeigt das Menue, gibt den gewaehlten Index zurueck oder None bei Abbruch."""
    curses.curs_set(0)
    stdscr.keypad(True)

    idx = 0   # aktuell markierter Eintrag
    top = 0   # oberster sichtbarer Eintrag (fuers Scrollen bei langen Listen)

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        kopf, fuss = 2, 1
        sichtbar = max(1, height - kopf - fuss)

        # Scroll-Fenster so verschieben, dass die Markierung sichtbar bleibt.
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
        elif key in (27, ord("q")):  # Esc oder q
            return None


def choose_song(folder: str):
    """
    Laesst den Nutzer einen Song waehlen.
    Rueckgabe: voller Pfad zur gewaehlten Datei, oder None
    (kein Song vorhanden ODER Auswahl abgebrochen).
    """
    songs = list_songs(folder)

    if not songs:
        return None
    if len(songs) == 1:
        return songs[0]  # nur ein Lied -> direkt nehmen

    namen = [os.path.basename(s) for s in songs]
    idx = curses.wrapper(_run_menu, "Song waehlen:", namen)
    if idx is None:
        return None
    return songs[idx]

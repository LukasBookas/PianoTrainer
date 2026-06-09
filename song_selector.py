"""
Konsolen-Auswahl der Songs mit Pfeiltasten (curses).

- Kein Song im Ordner   -> None
- Genau ein Song        -> wird direkt gewaehlt (keine GUI)
- Mehrere Songs         -> Auswahlmenue mit Pfeil hoch/runter, Enter = waehlen

Hinweis: curses ist unter Linux/macOS Standard. Unter Windows zusaetzlich
'windows-curses' installieren (pip install windows-curses). Ist curses nicht
verfuegbar, faellt die Auswahl automatisch auf ein einfaches Nummern-Menue zurueck.
"""

import os
import sys

try:
    import curses
except ImportError:
    curses = None  # kein curses -> spaeter Fallback auf Text-Menue

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


def _safe_addstr(win, y, x, text, attr=0) -> None:
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


def _curses_usable() -> bool:
    """
    True nur, wenn curses vorhanden ist UND ein echtes Terminal vorliegt.
    In IDE-Ausgabefenstern o.ae. ist die Ausgabe umgeleitet -> dort wuerde
    curses ("Redirection is not supported.") abstuerzen. Mit PIANO_NO_CURSES
    laesst sich die Pfeiltasten-Auswahl auch von Hand abschalten.
    """
    if curses is None or os.environ.get("PIANO_NO_CURSES"):
        return False
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def _text_menu(songs: list[str], namen: list[str]):
    """Einfaches Nummern-Menue als Fallback, wenn curses nicht verfuegbar ist."""
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
    """
    Laesst den Nutzer einen Song waehlen.
    Rueckgabe: voller Pfad zur gewaehlten Datei, oder None
    (kein Song vorhanden ODER Auswahl abgebrochen).
    """
    songs = list_songs(folder)

    if not songs:
        return None
    if len(songs) == 1:
        return songs[0]  # nur ein Lied? -> direkt nehmen

    namen = [os.path.basename(s) for s in songs]

    if _curses_usable():
        try:
            idx = curses.wrapper(_run_menu, "Song waehlen:", namen)
            return None if idx is None else songs[idx]
        except Exception:
            pass  # bei Problemen sauber auf das Text-Menue zurueckfallen

    return _text_menu(songs, namen)
#!/usr/bin/env python3
"""
Klavier-Trainer -- Einstiegspunkt.

Ablauf:
  1. Song aus dem Songs-Ordner waehlen (Pfeiltasten; bei nur einem Song direkt).
  2. Stueck laden und in Schritte zerlegen.
  3. MIDI-Keyboard waehlen (bei nur einem Geraet automatisch).
  4. Schritt fuer Schritt durch das Stueck fuehren.

Aufruf:
  python main.py                 # nutzt SONGS_DIR aus config.py
  python main.py /mnt/usb        # Ordner direkt angeben (z.B. USB-Stick am Pi)

Benoetigt:  pip install -r requirements.txt
Beenden:    Strg + C
"""

import sys

from config import SONGS_DIR, LED_SERIAL_PORT, LED_BAUD
from song_selector import choose_song, list_songs
from song_loader import load_steps
from midi_input import select_input_port
from led_output import LedOutput
from trainer import run_trainer


def main() -> None:
    folder = sys.argv[1] if len(sys.argv) > 1 else SONGS_DIR

    song = choose_song(folder)
    if song is None:
        if not list_songs(folder):
            print(f"Keine MIDI-Songs in '{folder}' gefunden.")
            print("Lege .mid/.midi-Dateien dort ab oder gib einen anderen Ordner an.")
        else:
            print("Auswahl abgebrochen.")
        return

    print(f"Gewaehlt: {song}")
    print("Lade Noten ...")
    steps = load_steps(song)

    port = select_input_port()
    led = LedOutput(LED_SERIAL_PORT, LED_BAUD)
    try:
        run_trainer(steps, port, led)
    finally:
        led.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbgebrochen.")

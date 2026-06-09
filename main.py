#!/usr/bin/env python3
"""
Piano trainer entry point.

Flow: pick a song -> load and split it into steps -> pick a MIDI keyboard ->
walk through the piece step by step.

Usage:
  python main.py                 # uses SONGS_DIR from config.py
  python main.py /mnt/usb        # pass the songs folder directly (e.g. USB stick on the Pi)

Requires:  pip install -r requirements.txt
Quit:      Ctrl + C
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
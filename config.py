"""
Zentrale Einstellungen fuer den Klavier-Trainer.
"""

import os

# Ordner mit den MIDI-Songs.
#   - Lokal zum Testen z.B. "./songs"
#   - Auf dem Raspberry Pi der USB-Stick, typischerweise etwas wie
#     "/media/pi/USBSTICK" oder "/mnt/usb".
# Per Umgebungsvariable ueberschreibbar, ohne den Code zu aendern:
#   PIANO_SONGS_DIR=/mnt/usb python main.py
SONGS_DIR = os.environ.get("PIANO_SONGS_DIR", "./songs")

# Welche Dateiendungen als Songs gelten.
MIDI_EXTENSIONS = (".mid", ".midi")

# --- Arduino / LED-Ausgabe ---
# Serieller Port des Arduino:
#   None  -> automatisch suchen (empfohlen; findet PC-COM-Port wie auch /dev/ttyUSB0 am Pi)
#   sonst fest vorgeben, z.B. "COM3" (Windows) oder "/dev/ttyUSB0" (Pi/Linux)
# Per Umgebungsvariable ueberschreibbar:  PIANO_LED_PORT=/dev/ttyUSB0 python main.py
LED_SERIAL_PORT = os.environ.get("PIANO_LED_PORT") or None

# Muss mit der Baudrate im Arduino-Sketch uebereinstimmen.
LED_BAUD = 115200

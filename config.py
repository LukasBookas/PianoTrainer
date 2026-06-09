"""
Central settings for the piano trainer.
"""

import os

# Folder containing the MIDI songs (e.g. "./songs", or a USB stick on the Pi
# like "/media/pi/USBSTICK"). Override with PIANO_SONGS_DIR.
SONGS_DIR = os.environ.get("PIANO_SONGS_DIR", "./songs")

# File extensions treated as songs.
MIDI_EXTENSIONS = (".mid", ".midi")

# Arduino serial port: None = auto-detect (recommended). Otherwise a fixed port
# like "COM3" (Windows) or "/dev/ttyUSB0" (Pi/Linux). Override with PIANO_LED_PORT.
LED_SERIAL_PORT = os.environ.get("PIANO_LED_PORT") or None

# Must match the baud rate in the Arduino sketch.
LED_BAUD = 115200
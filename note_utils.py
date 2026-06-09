"""
Hilfsfunktionen rund um MIDI-Notennummern.
"""

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(midi_nr: int) -> str:
    """Wandelt eine MIDI-Notennummer (0-127) in z.B. 'C4' um (Konvention 60 = C4)."""
    return f"{NOTE_NAMES[midi_nr % 12]}{midi_nr // 12 - 1}"

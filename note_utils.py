"""
Helpers for MIDI note numbers.
"""

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(midi_nr: int) -> str:
    """Converts a MIDI note number (0-127) to e.g. 'C4' (convention: 60 = C4)."""
    return f"{NOTE_NAMES[midi_nr % 12]}{midi_nr // 12 - 1}"
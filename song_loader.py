"""
Loads a MIDI file and splits it into steps.

A step is a sorted set of MIDI note numbers that start at the same offset --
i.e. either a single note or a chord.
"""

from music21 import converter, chord, note as m21note


def load_steps(midi_path: str) -> list[list[int]]:
    """Parses the MIDI file and returns the ordered list of steps."""
    stueck = converter.parse(midi_path)

    # Merge all parts (both hands etc.) and group notes by start time.
    nach_offset: dict[float, set[int]] = {}
    for element in stueck.flatten().notes:
        offset = round(float(element.offset), 4)
        gruppe = nach_offset.setdefault(offset, set())
        if isinstance(element, chord.Chord):
            for p in element.pitches:
                gruppe.add(p.midi)
        elif isinstance(element, m21note.Note):
            gruppe.add(element.pitch.midi)

    return [sorted(nach_offset[o]) for o in sorted(nach_offset)]
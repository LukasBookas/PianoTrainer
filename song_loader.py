"""
Laedt eine MIDI-Datei und zerlegt sie in Schritte.

Ein Schritt ist ein sortiertes Set von MIDI-Notennummern, die zur gleichen Zeit
(gleicher Offset) beginnen -> also entweder eine Einzelnote oder ein Akkord.
"""

from music21 import converter, chord, note as m21note


def load_steps(midi_path: str) -> list[list[int]]:
    """Parst die MIDI-Datei und gibt die geordnete Liste der Schritte zurueck."""
    stueck = converter.parse(midi_path)

    # Alle Parts (beide Haende usw.) zusammenfuehren und nach Startzeit gruppieren.
    nach_offset: dict[float, set[int]] = {}
    for element in stueck.flatten().notes:
        offset = round(float(element.offset), 4)  # Startzeit in Viertelnoten
        gruppe = nach_offset.setdefault(offset, set())
        if isinstance(element, chord.Chord):
            for p in element.pitches:
                gruppe.add(p.midi)
        elif isinstance(element, m21note.Note):
            gruppe.add(element.pitch.midi)

    # Nach Zeit sortieren -> Reihenfolge der Schritte.
    return [sorted(nach_offset[o]) for o in sorted(nach_offset)]

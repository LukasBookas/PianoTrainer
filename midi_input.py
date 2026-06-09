"""
Auswahl des MIDI-Eingangs (z.B. das angeschlossene Keyboard).
"""

import sys

import mido


def select_input_port() -> str:
    """
    Gibt den Namen eines MIDI-Eingangs zurueck.
    Ist nur ein Geraet vorhanden (typisch auf dem Raspberry Pi), wird es
    automatisch gewaehlt. Bei mehreren wird per Nummer abgefragt.
    """
    eingaenge = mido.get_input_names()

    if not eingaenge:
        print("Kein MIDI-Eingang gefunden. Keyboard eingeschaltet? USB verbunden?")
        sys.exit(1)

    if len(eingaenge) == 1:
        print(f"Keyboard: {eingaenge[0]}")
        return eingaenge[0]

    print("Gefundene MIDI-Eingaenge:")
    for i, name in enumerate(eingaenge):
        print(f"  [{i}] {name}")
    while True:
        wahl = input("Welches Geraet? Nummer: ").strip()
        if wahl.isdigit() and 0 <= int(wahl) < len(eingaenge):
            return eingaenge[int(wahl)]
        print("Ungueltige Eingabe.")

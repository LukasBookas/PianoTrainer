"""
Der eigentliche Trainer: fuehrt Schritt fuer Schritt durch ein Stueck.

Es wird erst zum naechsten Schritt gewechselt, wenn alle benoetigten Tasten des
aktuellen Schritts (frisch) gedrueckt wurden. Tempo und Notenlaengen werden
bewusst ignoriert -- es geht nur darum, *welche* Tasten als naechstes kommen.
"""

import mido

from note_utils import note_name


def _zeige_schritt(index: int, gesamt: int, noten: list[int]) -> None:
    namen = " + ".join(note_name(n) for n in noten)
    print(f"[{index + 1}/{gesamt}]  Spiele:  {namen}")


def run_trainer(steps: list[list[int]], port_name: str, led=None) -> None:
    """
    Spielt das Stueck Schritt fuer Schritt durch, lauschend auf port_name.
    led: optionales LedOutput-Objekt fuer die Arduino-Anzeige (None = nur Konsole).
    """
    if not steps:
        print("Keine Noten im Stueck gefunden.")
        return

    print("\nLos geht's! (Strg+C zum Abbrechen)\n")

    with mido.open_input(port_name) as port:
        index = 0
        fehler_gesamt = 0
        _zeige_schritt(index, len(steps), steps[index])
        benoetigt = set(steps[index])
        korrekt_gespielt: set[int] = set()  # benoetigte Noten, die schon (frisch) sitzen
        if led:
            led.light(steps[index])

        for msg in port:
            ist_note_on = msg.type == "note_on" and msg.velocity > 0
            if not ist_note_on:
                continue  # note_off etc. zaehlen nicht fuer den Fortschritt

            if msg.note in benoetigt:
                korrekt_gespielt.add(msg.note)
                # Schritt geschafft, sobald alle benoetigten Noten gedrueckt wurden.
                if benoetigt.issubset(korrekt_gespielt):
                    print("   ok\n")
                    index += 1
                    if index >= len(steps):
                        print(f"Geschafft! Stueck komplett gespielt. Fehler: {fehler_gesamt}")
                        if led:
                            led.clear()
                        return
                    _zeige_schritt(index, len(steps), steps[index])
                    benoetigt = set(steps[index])
                    korrekt_gespielt = set()
                    if led:
                        led.light(steps[index])
            else:
                # Falsche Taste: Feedback ausgeben, aber den Fortschritt nicht blockieren.
                fehler_gesamt += 1
                fehlend = sorted(benoetigt - korrekt_gespielt) or sorted(benoetigt)
                erwartet = " + ".join(note_name(n) for n in fehlend)
                print(f"   FALSCH: gedrueckt {note_name(msg.note)}, erwartet {erwartet}")

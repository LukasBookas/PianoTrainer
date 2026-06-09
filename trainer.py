"""
The trainer core: walks through a piece step by step.

Advances to the next step only once every required key of the current step has
been pressed. Tempo and note lengths are intentionally ignored -- only *which*
keys come next matters.

Held notes: keys still held from the previous step (legato / shared tones) count
as already played without needing to be released and re-struck.

LED feedback (if an Arduino is connected): notes to press glow turquoise,
correctly pressed (incl. held) ones turn blue until the step changes, wrong ones
flash red briefly.
"""

import mido

from note_utils import note_name


def _zeige_schritt(index: int, gesamt: int, noten: list[int]) -> None:
    namen = " + ".join(note_name(n) for n in noten)
    print(f"[{index + 1}/{gesamt}]  Spiele:  {namen}")


def _beginne_schritt(index: int, steps: list[list[int]], gehalten: set[int], led):
    """
    Prepares a step: displays it, lights the target notes, and counts already
    held required notes as played. Returns (required, correctly_played) as sets.
    """
    _zeige_schritt(index, len(steps), steps[index])
    benoetigt = set(steps[index])
    korrekt_gespielt = benoetigt & gehalten  # held shared tones count immediately
    if led:
        led.target(steps[index])
        for n in sorted(korrekt_gespielt):
            led.mark_correct(n)
    return benoetigt, korrekt_gespielt


def run_trainer(steps: list[list[int]], port_name: str, led=None) -> None:
    """
    Plays the piece step by step, listening on port_name.
    led: optional LedOutput for the Arduino display (None = console only).
    """
    if not steps:
        print("Keine Noten im Stueck gefunden.")
        return

    print("\nLos geht's! (Strg+C zum Abbrechen)\n")

    with mido.open_input(port_name) as port:
        index = 0
        fehler_gesamt = 0
        gehalten: set[int] = set()  # currently physically held keys

        benoetigt, korrekt_gespielt = _beginne_schritt(index, steps, gehalten, led)

        def _zum_naechsten_schritt() -> bool:
            """
            Advances to the next step, skipping any that are already fully
            satisfied by held keys. Returns True when the piece is finished.
            """
            nonlocal index, benoetigt, korrekt_gespielt
            while True:
                index += 1
                if index >= len(steps):
                    print(f"Geschafft! Stueck komplett gespielt. Fehler: {fehler_gesamt}")
                    if led:
                        led.clear()
                    return True
                benoetigt, korrekt_gespielt = _beginne_schritt(index, steps, gehalten, led)
                if not benoetigt.issubset(korrekt_gespielt):
                    return False
                print("   (gehalten) ok\n")

        for msg in port:
            typ = msg.type

            # Track releases (note_off, or note_on with velocity 0); does not
            # drive progress.
            if typ == "note_off" or (typ == "note_on" and msg.velocity == 0):
                gehalten.discard(msg.note)
                continue
            if typ != "note_on":
                continue  # ignore controllers, aftertouch, etc.

            # From here: a fresh key press (note_on, velocity > 0).
            gehalten.add(msg.note)

            if msg.note in benoetigt:
                if msg.note not in korrekt_gespielt:
                    korrekt_gespielt.add(msg.note)
                    if led:
                        led.mark_correct(msg.note)

                if benoetigt.issubset(korrekt_gespielt):
                    print("   ok\n")
                    if _zum_naechsten_schritt():
                        return
            else:
                # Wrong key: flash red, report, but don't block progress.
                fehler_gesamt += 1
                fehlend = sorted(benoetigt - korrekt_gespielt) or sorted(benoetigt)
                erwartet = " + ".join(note_name(n) for n in fehlend)
                print(f"   FALSCH: gedrueckt {note_name(msg.note)}, erwartet {erwartet}")
                if led:
                    led.flash_wrong(msg.note)
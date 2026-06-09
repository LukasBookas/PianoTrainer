"""
Der eigentliche Trainer: fuehrt Schritt fuer Schritt durch ein Stueck.

Es wird erst zum naechsten Schritt gewechselt, wenn alle benoetigten Tasten des
aktuellen Schritts gedrueckt wurden. Tempo und Notenlaengen werden bewusst
ignoriert -- es geht nur darum, *welche* Tasten als naechstes kommen.

Gehaltene Toene: Der Trainer merkt sich, welche Tasten du gerade gedrueckt
haeltst (ueber note_off). Verlangt der naechste Schritt eine Note, die du aus
dem vorigen Schritt noch haeltst (gemeinsamer Ton / Legato), zaehlt sie sofort
als gespielt -- du musst sie nicht erst loslassen und neu anschlagen.

LED-Rueckmeldung (falls ein Arduino angeschlossen ist):
  - zu drueckende Tasten leuchten tuerkis,
  - korrekt gedrueckte (auch durchgehaltene) werden blau und bleiben es, bis der
    Schritt wechselt,
  - falsch gedrueckte blinken kurz rot.
"""

import mido

from note_utils import note_name


def _zeige_schritt(index: int, gesamt: int, noten: list[int]) -> None:
    namen = " + ".join(note_name(n) for n in noten)
    print(f"[{index + 1}/{gesamt}]  Spiele:  {namen}")


def _beginne_schritt(index: int, steps: list[list[int]], gehalten: set[int], led):
    """
    Bereitet einen Schritt vor: zeigt ihn an, leuchtet die Zielnoten tuerkis und
    uebernimmt bereits gehaltene benoetigte Noten direkt als 'schon gespielt'
    (diese leuchten sofort blau).
    Rueckgabe: (benoetigt, korrekt_gespielt) als Mengen.
    """
    _zeige_schritt(index, len(steps), steps[index])
    benoetigt = set(steps[index])
    korrekt_gespielt = benoetigt & gehalten  # durchgehaltene gemeinsame Toene zaehlen sofort
    if led:
        led.target(steps[index])
        for n in sorted(korrekt_gespielt):
            led.mark_correct(n)
    return benoetigt, korrekt_gespielt


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
        gehalten: set[int] = set()  # aktuell physisch gedrueckte Tasten

        benoetigt, korrekt_gespielt = _beginne_schritt(index, steps, gehalten, led)

        def _zum_naechsten_schritt() -> bool:
            """
            Geht zum naechsten Schritt weiter. Schritte, die durch bereits
            gehaltene Tasten schon vollstaendig erfuellt sind, werden gleich
            mit uebersprungen. Rueckgabe True, wenn das Stueck fertig ist.
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
                    return False  # hier wird wieder auf eine Eingabe gewartet
                # Schritt bereits komplett durchgehalten -> als geschafft melden, weiter
                print("   (gehalten) ok\n")

        for msg in port:
            typ = msg.type

            # Loslassen mitschreiben (note_off oder note_on mit velocity 0),
            # treibt den Fortschritt aber nicht voran.
            if typ == "note_off" or (typ == "note_on" and msg.velocity == 0):
                gehalten.discard(msg.note)
                continue
            if typ != "note_on":
                continue  # andere Nachrichten (Controller, Aftertouch ...) ignorieren

            # Ab hier: frischer Tastendruck (note_on, velocity > 0).
            gehalten.add(msg.note)

            if msg.note in benoetigt:
                # Richtige Taste: blau faerben (nur beim ersten frischen Druck).
                if msg.note not in korrekt_gespielt:
                    korrekt_gespielt.add(msg.note)
                    if led:
                        led.mark_correct(msg.note)

                # Schritt geschafft, sobald alle benoetigten Noten gedrueckt wurden.
                if benoetigt.issubset(korrekt_gespielt):
                    print("   ok\n")
                    if _zum_naechsten_schritt():
                        return
            else:
                # Falsche Taste: kurz rot blinken, Feedback ausgeben, Fortschritt nicht blockieren.
                fehler_gesamt += 1
                fehlend = sorted(benoetigt - korrekt_gespielt) or sorted(benoetigt)
                erwartet = " + ".join(note_name(n) for n in fehlend)
                print(f"   FALSCH: gedrueckt {note_name(msg.note)}, erwartet {erwartet}")
                if led:
                    led.flash_wrong(msg.note)
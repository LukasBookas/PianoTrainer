"""
Sendet an den Arduino (LED-Anzeige), welche Noten wie leuchten sollen -- per USB-Serial.

Protokoll (eine Textzeile pro Befehl):
  T 60 64 67\n   -> diese MIDI-Noten als "zu druecken" anzeigen (Prompt-Farbe);
                    setzt die vorherige Anzeige komplett zurueck.
  B 60\n         -> diese (korrekt gedrueckte) Note blau faerben; bleibt blau,
                    bis der naechste T-Befehl kommt (also solange der Schritt
                    diese Note verlangt).
  F 62\n         -> diese (falsch gedrueckte) Note kurz rot aufblitzen lassen.
  C\n            -> alle LEDs aus.

Faellt sauber zurueck: ist kein Arduino verbunden oder pyserial nicht installiert,
laeuft der Trainer trotzdem normal weiter -- nur eben ohne LED-Ausgabe. So kannst
du die Logik auch ohne angeschlossene Hardware testen.
"""

import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None


def _auto_detect_port():
    """Sucht den ersten plausiblen USB-Serial-Port (Arduino / CH340 / FTDI ...)."""
    if serial is None:
        return None
    schluessel = ("arduino", "ch340", "ch9102", "ftdi", "wch",
                  "usb-serial", "usb serial", "ttyusb", "ttyacm")
    for p in list_ports.comports():
        text = f"{p.device} {p.description} {p.manufacturer or ''}".lower()
        if any(s in text for s in schluessel):
            return p.device
    return None


class LedOutput:
    """Duenne Huelle um die serielle Verbindung zum Arduino."""

    def __init__(self, port=None, baud=115200):
        self._ser = None

        if serial is None:
            print("Hinweis: pyserial nicht installiert -> ohne LED-Ausgabe. (pip install pyserial)")
            return

        if port is None:
            port = _auto_detect_port()
        if port is None:
            print("Hinweis: kein Arduino gefunden -> Trainer laeuft ohne LED-Ausgabe.")
            return

        try:
            self._ser = serial.Serial(port, baud, timeout=1)
            time.sleep(2)  # der Arduino macht beim Verbinden einen Reset -> kurz warten
            print(f"LED-Ausgabe aktiv ueber {port}.")
        except Exception as e:
            print(f"Hinweis: Port '{port}' nicht nutzbar ({e}) -> ohne LED-Ausgabe.")
            self._ser = None

    def _send(self, line: str) -> None:
        """Schickt eine fertige Befehlszeile an den Arduino (ignoriert Fehler)."""
        if not self._ser:
            return
        try:
            self._ser.write(line.encode("ascii"))
        except Exception:
            pass

    def target(self, notes) -> None:
        """Zeigt die als naechstes zu drueckenden Noten an (Prompt-Farbe, tuerkis).

        Setzt zugleich die vorherige Anzeige (inkl. blauer Noten) komplett zurueck.
        """
        self._send("T " + " ".join(str(n) for n in notes) + "\n")

    # Alter Name aus frueheren Versionen -> bleibt nutzbar.
    light = target

    def mark_correct(self, note) -> None:
        """Faerbt eine korrekt gedrueckte Note blau (bleibt bis zum naechsten Schritt)."""
        self._send(f"B {note}\n")

    def flash_wrong(self, note) -> None:
        """Laesst eine falsch gedrueckte Note kurz rot aufleuchten."""
        self._send(f"F {note}\n")

    def clear(self) -> None:
        """Schaltet alle LEDs aus."""
        self._send("C\n")

    def close(self) -> None:
        if self._ser:
            self.clear()
            self._ser.close()
            self._ser = None

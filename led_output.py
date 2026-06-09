"""
Sendet die aktuell zu drueckenden Noten an den Arduino (LED-Anzeige) per USB-Serial.

Protokoll (eine Textzeile pro Befehl):
  L 60 64 67\n   -> diese MIDI-Noten aufleuchten lassen
  C\n            -> alle LEDs aus

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

    def light(self, notes) -> None:
        """Laesst genau die angegebenen MIDI-Noten leuchten (vorherige gehen aus)."""
        if not self._ser:
            return
        zeile = "L " + " ".join(str(n) for n in notes) + "\n"
        try:
            self._ser.write(zeile.encode("ascii"))
        except Exception:
            pass

    def clear(self) -> None:
        """Schaltet alle LEDs aus."""
        if not self._ser:
            return
        try:
            self._ser.write(b"C\n")
        except Exception:
            pass

    def close(self) -> None:
        if self._ser:
            self.clear()
            self._ser.close()
            self._ser = None

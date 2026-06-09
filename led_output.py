"""
Sends LED commands to the Arduino over USB serial.

Protocol (one text line per command):
  T 60 64 67   -> show these MIDI notes as "to press" (prompt color); resets the display.
  B 60         -> mark a correctly pressed note blue (stays until the next T command).
  F 62         -> briefly flash a wrongly pressed note red.
  C            -> all LEDs off.

Degrades gracefully: with no Arduino or no pyserial, the trainer keeps running
without LED output, so the logic can be tested without hardware.
"""

import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None


def _auto_detect_port():
    """Finds the first plausible USB-serial port (Arduino / CH340 / FTDI ...)."""
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
    """Thin wrapper around the serial connection to the Arduino."""

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
            time.sleep(2)  # Arduino resets on connect -> wait briefly
            print(f"LED-Ausgabe aktiv ueber {port}.")
        except Exception as e:
            print(f"Hinweis: Port '{port}' nicht nutzbar ({e}) -> ohne LED-Ausgabe.")
            self._ser = None

    def _send(self, line: str) -> None:
        """Sends a ready-made command line to the Arduino (errors ignored)."""
        if not self._ser:
            return
        try:
            self._ser.write(line.encode("ascii"))
        except Exception:
            pass

    def target(self, notes) -> None:
        """Shows the notes to press next and resets the previous display."""
        self._send("T " + " ".join(str(n) for n in notes) + "\n")

    light = target  # backwards-compatible alias

    def mark_correct(self, note) -> None:
        """Marks a correctly pressed note blue until the next step."""
        self._send(f"B {note}\n")

    def flash_wrong(self, note) -> None:
        """Briefly flashes a wrongly pressed note red."""
        self._send(f"F {note}\n")

    def clear(self) -> None:
        """Turns all LEDs off."""
        self._send("C\n")

    def close(self) -> None:
        if self._ser:
            self.clear()
            self._ser.close()
            self._ser = None
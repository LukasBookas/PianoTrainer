# Piano Trainer

Ein konsolenbasierter Klavier-Trainer, der ein MIDI-Keyboard ausliest und dich
Schritt für Schritt durch ein Stück führt: Er zeigt die als nächstes zu
drückende(n) Taste(n) an und schaltet erst weiter, wenn du sie richtig gespielt
hast. Optional werden die zu drückenden Tasten zusätzlich über einen
adressierbaren LED-Streifen (an einem Arduino) angezeigt.

## Funktionen

- Liest ein USB-MIDI-Keyboard aus (getestet mit Thomann DP-28 Plus).
- Lädt MIDI-Dateien und zerlegt sie in Schritte (Einzelnoten oder Akkorde).
- Führt Schritt für Schritt durch das Stück; wartet pro Schritt, bis alle
  benötigten Tasten gespielt wurden.
- Fehler-Feedback: bei falscher Taste Ausgabe von "gedrückt X, erwartet Y";
  am Ende eine Fehlerbilanz.
- Song-Auswahl mit Pfeiltasten (bei nur einem Song automatisch).
- Optionale LED-Anzeige über einen Arduino (USB-Serial). Ohne Arduino läuft
  alles unverändert weiter.

Tempo und Notenlängen werden bewusst ignoriert — es geht nur darum, *welche*
Tasten als nächstes kommen.

## Funktionsweise

```
MIDI-Keyboard ──USB──> Rechner (Python)
                         │  lädt Song, zerlegt in Schritte,
                         │  vergleicht mit gespielten Noten
                         └──USB-Serial──> Arduino ──> LED-Streifen
```

Der Rechner (PC oder Raspberry Pi) ist das "Gehirn". Der Arduino ist nur die
LED-Ausgabe und bekommt pro Schritt mitgeteilt, welche Noten leuchten sollen.

MIDI-Konvention: Note 60 = C4. Ein 88-Tasten-Klavier reicht von Note 21 (A0)
bis 108 (C8).

## Voraussetzungen

- Python 3.10+
- Ein USB-MIDI-Keyboard
- Optional: Arduino + adressierbarer LED-Streifen (SK6812 RGBW / WS2812B RGB)

Python-Abhängigkeiten:

```bash
pip install -r requirements.txt
```

Hinweis: Falls `python-rtmidi` beim Installieren einen Build-Fehler wirft (z.B.
auf einem Raspberry Pi), die ALSA-Header nachinstallieren:

```bash
sudo apt install libasound2-dev libjack-dev build-essential
```

Unter Windows wird für die Pfeiltasten-Auswahl zusätzlich `windows-curses`
benötigt (`pip install windows-curses`). Unter Linux/macOS ist `curses`
bereits enthalten.

## Songs

Lege MIDI-Dateien (`.mid` / `.midi`) in den Songs-Ordner (Standard: `./songs`).
Kostenlose, legale Quellen für klassische Klavier-MIDIs sind z.B.
[piano-midi.de](http://www.piano-midi.de), [mfiles.co.uk](https://www.mfiles.co.uk/classical-midi.htm)
oder das Yamaha Disklavier Education Network.

## Benutzung

```bash
python main.py                 # nutzt den Songs-Ordner aus config.py
python main.py /pfad/zu/songs  # Ordner direkt angeben (z.B. USB-Stick am Pi)
```

Bei mehreren Songs erscheint ein Auswahlmenü (Pfeil hoch/runter, Enter zum
Bestätigen). Bei genau einem Song startet dieser direkt. Beenden mit `Strg + C`.

## Konfiguration

Alles in `config.py` (oder per Umgebungsvariable):

| Einstellung        | Bedeutung                                              |
|--------------------|--------------------------------------------------------|
| `SONGS_DIR`        | Ordner mit den MIDI-Songs (z.B. der USB-Stick am Pi).  |
| `LED_SERIAL_PORT`  | Serieller Port des Arduino. `None` = automatisch suchen. |
| `LED_BAUD`         | Baudrate; muss zum Arduino-Sketch passen (115200).     |

Umgebungsvariablen: `PIANO_SONGS_DIR`, `PIANO_LED_PORT`.

## Arduino (LED-Ausgabe)

1. Arduino IDE installieren und Board "Arduino Nano" wählen (bei Klonen ggf.
   Prozessor "ATmega328P (Old Bootloader)").
2. Bibliothek "Adafruit NeoPixel" über den Library Manager installieren.
3. `led_strip.ino` öffnen, `NUM_LEDS` und `LOWEST_NOTE` anpassen und für
   SK6812 RGBW den Typ `NEO_GRBW` (für reines WS2812B `NEO_GRB`) verwenden.
4. Auf den Arduino hochladen.

Protokoll (vom Rechner an den Arduino, je eine Textzeile):

```
L 60 64 67   -> diese MIDI-Noten leuchten lassen
C            -> alle LEDs aus
```

### Verkabelung der LEDs

- **Daten in Reihe:** Mehrere Streifen über DOUT → DIN verketten (ein logischer
  Streifen). Datenleitung mit ~330 Ω in Reihe.
- **Strom parallel:** 5V und GND aus einem externen Netzteil in jeden Streifen
  einspeisen — nicht alles durch den ersten Streifen ziehen.
- **Gemeinsame Masse:** GND von Arduino, LED-Netzteil und Streifen verbinden.
- Der LED-Streifen wird **nicht** vom Arduino mit Strom versorgt.

## Projektstruktur

| Datei              | Aufgabe                                                |
|--------------------|--------------------------------------------------------|
| `main.py`          | Einstiegspunkt, verbindet die Module.                  |
| `config.py`        | Einstellungen (Songs-Ordner, Arduino-Port).            |
| `song_selector.py` | Song-Auswahl mit Pfeiltasten (curses).                 |
| `song_loader.py`   | MIDI-Datei in Schritte zerlegen (music21).             |
| `midi_input.py`    | MIDI-Keyboard auswählen/öffnen.                        |
| `trainer.py`       | Die eigentliche Schritt-für-Schritt-Logik.             |
| `led_output.py`    | Sendet die zu leuchtenden Noten an den Arduino.        |
| `note_utils.py`    | Notennummer → Notenname.                               |
| `led_strip.ino`    | Arduino-Sketch für die LED-Anzeige.                    |

## Ausblick

Langfristiges Ziel: ein eigenständiges Gerät, bei dem der Arduino *alles*
übernimmt (MIDI-Eingang über die 5-polige DIN-MIDI-Buchse via Optokoppler,
Song im Flash, LED-Ausgabe) — ohne PC oder Raspberry Pi.

## Lizenz

Veröffentlicht unter der MIT-Lizenz, siehe [LICENSE](LICENSE).

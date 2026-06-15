# 🎹 Arduino Klavier-Trainer

Ein interaktiver Trainings-System für Klavier basierend auf Arduino Nano mit visuellen LED-Hinweisen. Das System liest MIDI-Noten ein und führt Dich durch Melodien mit farbigen LED-Anzeigen.

## 🎯 Features

- **Ereignis-gesteuerte Zustandsmaschine** – Keine Takt-abhängigkeit, flexibles Tempo
- **4-Zustands-System pro Note:**
  - 🔘 **PENDING** – Noch nicht dran (LED aus)
  - 🔵 **ARMED** – Jetzt drücken (hell türkis)
  - 🔵 **HOLDING** – Weitermachen halten (dunkelblau)
  - ✅ **DONE** – Fertig, darfst loslassen (LED aus)

- **Intelligente Haltedauer-Kontrolle:**
  - Jede Note hat eine konfigurierbare Mindest-Haltedauer
  - Zu früh losgelassen? → Rote LED + Note wird neu angefordert
  - Länger halten als nötig? → Egal, wird ignoriert

- **Akkord-Unterstützung** – Mehrere Noten gleichzeitig möglich
- **Überlappende Noten** – Der Spielkopf rückt nur weiter, wenn Du alle fälligen Noten drückst
- **Fehler-Feedback** – Rote Blitze für zu frühe oder falsche Tasten
- **Erfolgs-Animation** – Grüne LED-Show beim Abschluss

## 🔧 Hardware-Anforderungen

| Komponente | Typ | Notizen |
|-----------|------|---------|
| **Mikro** | Arduino Nano (ATmega328P) | 16 MHz, 328P empfohlen |
| **LED-Streifen** | WS2812B oder SK6812 RGBW | 1x Status-LED + 1x pro Klaviertaste |
| **MIDI-Eingang** | Serial @ 31.250 baud | Optokoppler an D0 (Serial RX) |
| **Datenleitung LEDs** | Digital Pin D6 | Programmierbar im Code |
| **Stromversorgung** | 5V für LEDs | Je nach Streifen-Länge: 1–5A |

### Pin-Belegung

```
Arduino Nano
├─ D0 (RX)     → Optokoppler (MIDI-Eingang)
├─ D6          → LED-Streifen Datenleitung
├─ 5V          → LED-Streifen VCC (über Transistor/FET empfohlen)
└─ GND         → LED-Streifen GND + Optokoppler GND
```

## 📋 Software-Anforderungen

- **Arduino IDE** 1.8.0 oder neuer
- **Adafruit NeoPixel Library** (≥ 1.10.0)
  - Installieren über: `Sketch → Bibliotheken einbinden → Bibliotheken verwalten`
  - Suche: `Adafruit NeoPixel`

## 🎵 Konfiguration

Öffne den Sketch und stelle diese Werte am Anfang an Deine Hardware an:

```cpp
// Wie viele Tasten hat Dein Klavier?
const int NUM_KEYS = 88;    // 88, 76, 61, 49, 37 ...

// MIDI-Nummer der HÖCHSTEN Taste (unter LED 2)
// Beispiele: 108 = C8, 96 = C7, 84 = C6
const int TOP_NOTE = 108;

// Mindest-Haltedauer einer VIERTEL-Note in Millisekunden
// Größer = bewusstere Übung, Kleiner = lockerer spielen
const unsigned long MIN_QUARTER_MS = 400;
```

### MIDI-Nummern Referenz

| Note | MIDI | Note | MIDI |
|------|------|------|------|
| C4   | 60   | C6   | 84   |
| D4   | 62   | D6   | 86   |
| E4   | 64   | E6   | 88   |
| F4   | 65   | F6   | 89   |
| G4   | 67   | G6   | 91   |
| A4   | 69   | A6   | 93   |
| C7   | 96   | C8   | 108  |

## 🎼 Noten eingeben

Noten sind im SONG-Array definiert:

```cpp
struct Note { uint8_t pitch; uint16_t start; uint16_t dur; };

const Note SONG[] = {
  // pitch, start (Tick), duration (Ticks)
  // 1/16-Raster: 4 = Viertel, 8 = Halbe, 16 = Ganze
  {84, 0, 4},    // C6, Takt 0, Viertel
  {86, 4, 4},    // D6, Takt 4, Viertel
  {88, 8, 8},    // E6, Takt 8, Halbe
  // ...
};
```

### Akkorde erstellen

Mehrere Noten mit gleichem `start`-Wert = Akkord:

```cpp
{84, 0, 4},  // C
{88, 0, 4},  // E  } gleichzeitig ab Tick 0
{91, 0, 4},  // G
```

### Noten überlappen lassen (z.B. Haltenote)

```cpp
{96, 0, 16},   // C7 - lange halten, während...
{84, 0, 4},    // ...C6
{86, 4, 4},    // D6
{88, 8, 4},    // E6
// Erst wenn alle drei (C6, D6, E6) gedrueckt UND C7 lange genug 
// gehalten wurde, wird C7 "DONE"
```

## 🚀 Erste Schritte

1. **Arduino IDE installieren** → [arduino.cc/en/software](https://www.arduino.cc/en/software)

2. **Adafruit NeoPixel Bibliothek installieren:**
   - Arduino IDE öffnen
   - `Sketch → Bibliotheken einbinden → Bibliotheken verwalten`
   - "Adafruit NeoPixel" suchen und installieren

3. **Sketch laden:**
   - Code kopieren → Neuer Sketch
   - Board wählen: `Tools → Board → Arduino AVR Boards → Arduino Nano`
   - Prozessor: `ATmega328P (Old Bootloader)` (oder `(New Bootloader)`)
   - COM-Port auswählen

4. **Konfigurieren:**
   - `NUM_KEYS`, `TOP_NOTE`, `MIN_QUARTER_MS` anpassen
   - Deine Melodie ins `SONG`-Array eingeben

5. **Hochladen & Testen:**
   - Upload-Button drücken
   - MIDI-Keyboard anschließen
   - Spielen! 🎹

## 🎨 LED-Farben

| Farbe | Bedeutung | LED-Status |
|-------|-----------|-----------|
| 🔴 Rot | Fehler/zu früh losgelassen | Blinkt 300ms |
| 🔵 Hell-Türkis | Jetzt drücken (ARMED) | Leuchtet |
| 🔵 Dunkelblau | Weitermachen halten (HOLDING) | Leuchtet |
| 🟢 Grün | Fertig/Status | Leuchtet |
| ⚫ Aus | Nicht aktiv (PENDING/DONE) | Aus |

## 🔌 MIDI-Verbindung

Das System erwartet MIDI über Serial (31.250 baud) mit optischer Isolation:

```
MIDI IN (5-polig DIN)  →  [Optokoppler]  →  Arduino D0 (RX)
                             PC817
```

Oder verwende einen MIDI-USB-Adapter direkt am Arduino:
- TX vom Adapter → D0 (RX) mit Strombegrenzung (z.B. 1kΩ Widerstand)

## 📊 Zustands-Diagramm

```
        PENDING ──┐
           ↓      │ (Onset erreicht)
         ARMED ───┘
           ↓
    (richtige Taste)
           ↓
        HOLDING
           ↓ (min. Haltedauer + Spielkopf vorbei)
         DONE

Bei Fehler: HOLDING → ARMED (rote LED, neu versuchen)
```

## ⚙️ Eingebaute Konstanten

```cpp
const int     LED_DATA_PIN = 6;           // WS2812 Daten-Pin
const uint8_t BRIGHTNESS   = 120;         // 0–255
const long    MIDI_BAUD    = 31250;       // Standard MIDI
const unsigned long FLASH_MS = 300;       // Fehler-Blinken
const unsigned long DONE_MS  = 1500;      // Erfolgs-Animation
```

## 🐛 Debugging

- **Serial Monitor (9600 baud)** öffnen und `totalErrors` checken
- LEDs blinken nicht? → `BRIGHTNESS` erhöhen oder LED-Versorgung checken
- MIDI wird nicht erkannt? → Optokoppler-Verdrahtung kontrollieren
- Falsche Noten gefordert? → `TOP_NOTE` und `NUM_KEYS` überprüfen

## 📝 Lizenz

MIT License – frei nutzbar, modifizierbar, weitergabe

## 🤝 Beitragen

Fehler gefunden? Verbesserungsideen? → Issues und Pull Requests willkommen!

---

**Viel Erfolg beim Üben!** 🎵

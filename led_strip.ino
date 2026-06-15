/*
 * LED-Ausgabe fuer den Klavier-Trainer.
 *
 * Empfaengt ueber USB-Serial vom Pi/PC, welche Noten wie leuchten sollen, und
 * steuert einen adressierbaren LED-Streifen (SK6812 RGBW / WS2812B RGB).
 *
 * Aufbau des Streifens:
 *   - LED 0 ist eine reine Status-LED ("Power on") und leuchtet dauerhaft gruen.
 *   - Die Noten-LEDs laufen von HOCH nach TIEF: LED 1 = hoechste Note,
 *     letzte LED = tiefste Note (Streifen wurde von rechts nach links verbaut).
 *
 * Protokoll (eine Textzeile pro Befehl):
 *   T 60 64 67\n   -> diese MIDI-Noten als "zu druecken" anzeigen (tuerkis);
 *                     setzt die vorherige Anzeige komplett zurueck.
 *   B 60\n         -> diese (korrekt gedrueckte) Note blau faerben; bleibt blau,
 *                     bis der naechste T-Befehl kommt.
 *   F 62\n         -> diese (falsch gedrueckte) Note kurz rot aufblitzen lassen.
 *   C\n            -> alle Noten-LEDs aus (Status-LED bleibt gruen).
 *
 * Bibliothek: "Adafruit NeoPixel" (ueber Library Manager installieren).
 */

#include <Adafruit_NeoPixel.h>

const int DATA_PIN    = 6;    // Datenleitung zum Streifen (mit ~330 Ohm in Reihe)
const int NUM_LEDS    = 89;   // GESAMT inkl. Status-LED! 88 Tasten + 1 Status = 89 -> ANPASSEN!
const int LOWEST_NOTE = 21;   // tiefste angezeigte MIDI-Note (21 = A0 beim 88-Tasten-Klavier)

const int STATUS_LED  = 0;                 // erste LED = Power-/Status-Anzeige
const int NOTE_LEDS   = NUM_LEDS - 1;      // LEDs, die fuer Noten zur Verfuegung stehen
const int HIGHEST_NOTE = LOWEST_NOTE + NOTE_LEDS - 1;  // Note auf LED 1

const unsigned long FLASH_MS = 300;  // wie lange eine falsche Note rot blinkt (ms)

// SK6812 RGBW -> NEO_GRBW.  Reines WS2812B (RGB) -> stattdessen NEO_GRB verwenden.
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_GRBW + NEO_KHZ800);

// Farben (in setup() gesetzt, da strip.Color() zur Laufzeit ausgewertet wird).
uint32_t COLOR_TARGET;   // "zu druecken"      -> tuerkis
uint32_t COLOR_CORRECT;  // korrekt gedrueckt  -> blau
uint32_t COLOR_WRONG;    // falsch gedrueckt   -> rot
uint32_t COLOR_STATUS;   // Status-LED         -> gruen

// Pro LED der ruhende Zustand: 0 = aus, 1 = Ziel (tuerkis), 2 = korrekt (blau).
// Index 0 (Status-LED) wird nie benutzt, bleibt aber der Einfachheit halber im Array.
uint8_t steady[NUM_LEDS];
// Pro LED: millis()-Zeitpunkt, bis zu dem sie rot blinkt (0 = kein Blinken).
unsigned long flashUntil[NUM_LEDS];

bool dirty = true;   // true -> Streifen muss neu gezeichnet werden

char buffer[80];
int  bufPos = 0;

// MIDI-Note -> LED-Index. Der Streifen laeuft von hoch nach tief, LED 0 ist
// die Status-LED, daher: hoechste Note = Index 1, tiefste = NUM_LEDS - 1.
int noteToIdx(int note) {
  if (note < LOWEST_NOTE || note > HIGHEST_NOTE) return -1;
  return 1 + (HIGHEST_NOTE - note);
}

// Setzt fuer alle Noten in der (Leerzeichen-getrennten) Liste den ruhenden Zustand.
void setNotes(char *list, uint8_t state) {
  char *tok = strtok(list, " ");
  while (tok != NULL) {
    int idx = noteToIdx(atoi(tok));
    if (idx >= 0) steady[idx] = state;
    tok = strtok(NULL, " ");
  }
}

// Startet fuer alle Noten in der Liste das rote Blinken.
void flashNotes(char *list) {
  unsigned long until = millis() + FLASH_MS;
  if (until == 0) until = 1;  // 0 ist als "kein Blinken" reserviert
  char *tok = strtok(list, " ");
  while (tok != NULL) {
    int idx = noteToIdx(atoi(tok));
    if (idx >= 0) flashUntil[idx] = until;
    tok = strtok(NULL, " ");
  }
}

void clearAll() {
  for (int i = 0; i < NUM_LEDS; i++) {
    steady[i] = 0;
    flashUntil[i] = 0;
  }
}

void handleLine(char *line) {
  switch (line[0]) {
    case 'C':                                      // alles aus (ausser Status-LED)
      clearAll();
      break;
    case 'T':                                      // neue Zielnoten -> Anzeige zuruecksetzen
      for (int i = 0; i < NUM_LEDS; i++) steady[i] = 0;
      setNotes(line + 1, 1);
      break;
    case 'B':                                      // korrekt gedrueckt -> blau
      setNotes(line + 1, 2);
      break;
    case 'F':                                      // falsch gedrueckt -> kurz rot
      flashNotes(line + 1);
      break;
    default:
      return;                                      // unbekannter Befehl -> ignorieren
  }
  dirty = true;
}

// Zeichnet den gesamten Streifen anhand von steady[] und flashUntil[].
void render() {
  unsigned long now = millis();

  // Status-LED leuchtet immer gruen, unabhaengig von allen Befehlen.
  strip.setPixelColor(STATUS_LED, COLOR_STATUS);

  for (int i = 1; i < NUM_LEDS; i++) {
    uint32_t color;
    if (flashUntil[i] != 0 && now < flashUntil[i]) {
      color = COLOR_WRONG;          // rotes Blinken hat Vorrang
    } else if (steady[i] == 1) {
      color = COLOR_TARGET;
    } else if (steady[i] == 2) {
      color = COLOR_CORRECT;
    } else {
      color = 0;                    // aus
    }
    strip.setPixelColor(i, color);
  }
  strip.show();
}

void setup() {
  Serial.begin(115200);             // muss zu LED_BAUD in config.py passen
  strip.begin();
  strip.setBrightness(120);         // begrenzt Helligkeit/Stromverbrauch

  COLOR_TARGET  = strip.Color(0, 80, 120, 0);   // tuerkis ("zu druecken")
  COLOR_CORRECT = strip.Color(0, 0, 200, 0);    // blau   (korrekt gedrueckt)
  COLOR_WRONG   = strip.Color(200, 0, 0, 0);    // rot    (falsch gedrueckt)
  COLOR_STATUS  = strip.Color(0, 60, 0, 0);     // gruen  (Status/Power, gedimmt)

  clearAll();
  render();                         // zeigt sofort die gruene Status-LED
}

void loop() {
  // 1) Eingehende Befehle einlesen.
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (bufPos > 0) {
        buffer[bufPos] = '\0';
        handleLine(buffer);
        bufPos = 0;
      }
    } else if (bufPos < (int)sizeof(buffer) - 1) {
      buffer[bufPos++] = c;
    }
  }

  // 2) Abgelaufene rote Blink-Phasen beenden.
  unsigned long now = millis();
  for (int i = 1; i < NUM_LEDS; i++) {
    if (flashUntil[i] != 0 && now >= flashUntil[i]) {
      flashUntil[i] = 0;
      dirty = true;
    }
  }

  // 3) Nur neu zeichnen, wenn sich etwas geaendert hat.
  if (dirty) {
    render();
    dirty = false;
  }
}

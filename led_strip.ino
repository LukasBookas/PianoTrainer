/*
 * LED-Ausgabe fuer den Klavier-Trainer.
 *
 * Empfaengt ueber USB-Serial vom Pi/PC, welche Noten leuchten sollen, und
 * steuert einen adressierbaren LED-Streifen (SK6812 RGBW / WS2812B RGB).
 *
 * Protokoll (eine Textzeile pro Befehl):
 *   L 60 64 67\n   -> diese MIDI-Noten aufleuchten lassen (vorherige gehen aus)
 *   C\n            -> alle LEDs aus
 *
 * Bibliothek: "Adafruit NeoPixel" (ueber Library Manager installieren).
 */

#include <Adafruit_NeoPixel.h>

const int DATA_PIN    = 6;    // Datenleitung zum Streifen (mit ~330 Ohm in Reihe)
const int NUM_LEDS    = 88;   // Anzahl LEDs auf deinem Streifen -> ANPASSEN!
const int LOWEST_NOTE = 21;   // MIDI-Note der ersten LED (21 = A0 beim 88-Tasten-Klavier)

// SK6812 RGBW -> NEO_GRBW.  Reines WS2812B (RGB) -> stattdessen NEO_GRB verwenden.
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_GRBW + NEO_KHZ800);

char buffer[64];
int  bufPos = 0;

void clearStrip() {
  strip.clear();
  strip.show();
}

void lightNote(int note) {
  int idx = note - LOWEST_NOTE;
  if (idx >= 0 && idx < NUM_LEDS) {
    strip.setPixelColor(idx, strip.Color(0, 80, 120, 0));  // tuerkis; Farbe frei waehlbar
  }
}

void handleLine(char *line) {
  if (line[0] == 'C') {            // alles aus
    clearStrip();
    return;
  }
  if (line[0] == 'L') {            // diese Noten leuchten
    strip.clear();
    char *tok = strtok(line + 1, " ");
    while (tok != NULL) {
      int note = atoi(tok);
      if (note > 0) lightNote(note);
      tok = strtok(NULL, " ");
    }
    strip.show();
  }
}

void setup() {
  Serial.begin(115200);           // muss zu LED_BAUD in config.py passen
  strip.begin();
  strip.setBrightness(120);       // begrenzt Helligkeit/Stromverbrauch
  clearStrip();
}

void loop() {
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
}

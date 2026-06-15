/*
 * Eigenstaendiger Klavier-Trainer fuer Arduino Nano (ATmega328P).
 *
 * EREIGNIS-ZUSTANDSMASCHINE, KEIN Takt. Drei Ereignisse: druecken, loslassen,
 * Zeit-abgelaufen. Jede Note hat eine MINDEST-Haltedauer (aus der MIDI-Laenge).
 *
 * Pro Note vier Zustaende:
 *   PENDING  - noch nicht dran                       -> LED aus
 *   ARMED    - jetzt druecken                        -> HELL tuerkis
 *   HOLDING  - gedrueckt, weiter halten              -> DUNKELBLAU
 *   DONE     - fertig, du darfst loslassen           -> LED aus
 *
 * HOLDING -> DONE NUR wenn BEIDES gilt:
 *   (1) die Mindest-Haltedauer ist abgelaufen (lang genug gehalten), UND
 *   (2) alle ueberlagernden Noten sind angetriggert (der Spielkopf ist ueber
 *       das Ende dieser Note hinaus -> alle waehrend ihrer Laufzeit startenden
 *       Noten wurden gedrueckt).
 *
 * Der Spielkopf rueckt nur weiter, wenn du die faelligen Noten drueckst -> du
 * kannst dir beliebig viel Zeit lassen, nur nicht zu frueh loslassen.
 * Zu frueh losgelassen -> rot + die Note wird wieder ARMED (neu druecken/halten).
 * Laenger halten als noetig -> egal.
 *
 * ============================================================================
 *  EINSTELLEN: oben die zwei Klavier-Werte + Mindesttempo. Fertig.
 * ============================================================================
 *
 * STREIFEN: LED 1 (Index 0) = Status gruen. LED 2 = hoechste Taste, dann je
 * Halbton tiefer. Verkabelung: Daten D6, MIDI an D0 ueber Optokoppler.
 * Bibliothek: "Adafruit NeoPixel".
 */

#include <Adafruit_NeoPixel.h>

// ======================================================================
// ===========  FUER DEIN KLAVIER SETZEN  ===============================
// ======================================================================

const int NUM_KEYS = 88;    // Wie viele Tasten hat dein Klavier? (88, 76, 61, 49 ...)
const int TOP_NOTE = 108;   // MIDI-Nummer der HOECHSTEN Taste (die unter LED 2). Dein "Offset".

// Mindest-Haltedauer einer VIERTELnote in ms. Bestimmt, wie lange eine Note
// mindestens gehalten werden muss (halbe = 2x, ganze = 4x). Laenger halten ist
// immer ok, nur nicht kuerzer. Kleiner = lockerer, groesser = bewusster ueben.
const unsigned long MIN_QUARTER_MS = 400;

// ======================================================================
// ===========  AB HIER NICHTS MEHR AENDERN MUESSEN  ====================
// ======================================================================

const int     LED_DATA_PIN = 6;
const uint8_t BRIGHTNESS   = 120;
const long    MIDI_BAUD    = 31250;

const int STATUS_LED = 0;
const int NUM_LEDS   = NUM_KEYS + 1;   // 1 Status-LED + je 1 LED pro Taste; fehlende LEDs bleiben dunkel

const unsigned long FLASH_MS = 300;    // Dauer eines roten Fehler-Blitzes
const unsigned long DONE_MS  = 1500;   // wie lange am Ende alles gruen leuchtet
const long          ONSET_NONE = 0x7FFFFFFFL;  // "kein Onset mehr" (Stueck durch)

// SK6812 RGBW -> NEO_GRBW.  Reines WS2812B (RGB) -> NEO_GRB verwenden.
Adafruit_NeoPixel strip(NUM_LEDS, LED_DATA_PIN, NEO_GRBW + NEO_KHZ800);

uint32_t COLOR_PRESS;    // jetzt druecken   -> hell tuerkis
uint32_t COLOR_HOLD;     // weiter halten    -> dunkelblau
uint32_t COLOR_WRONG;    // falsch/zu frueh  -> rot
uint32_t COLOR_DONE;     // geschafft        -> gruen
uint32_t COLOR_STATUS;   // Status/Power-on  -> gruen

// ---------- Lied als Noten-Events ----------
// pitch, start (Tick), dur (Ticks).  1/16-Raster: 4=Viertel, 8=halbe, 16=ganze.
// Noten duerfen sich ueberlappen. Akkord = mehrere Noten mit gleichem start
// (dur darf unterschiedlich sein). MIDI: 60=C4, 84=C6 (C84 D86 E88 F89 G91 A93).
struct Note { uint8_t pitch; uint16_t start; uint16_t dur; };

const Note SONG[] = {
  // >>> DEMO-Haltenote (hohes C7): bleibt dunkelblau liegen, waehrend du C D E F
  //     spielst, und erlischt erst, wenn alle vier gedrueckt sind UND C7 lang
  //     genug gehalten wurde. Diese Zeile entfernen fuer reine Melodie. <<<
  {96, 0, 16},

  // "Alle meine Entchen"
  {84,  0,4},{86,  4,4},{88,  8,4},{89, 12,4},   {91, 16,8},{91, 24,8},   // C D E F | G G
  {93, 32,4},{93, 36,4},{93, 40,4},{93, 44,4},   {91, 48,16},             // A A A A | G(ganze)
  {93, 64,4},{93, 68,4},{93, 72,4},{93, 76,4},   {91, 80,16},             // A A A A | G(ganze)
  {89, 96,4},{89,100,4},{89,104,4},{89,108,4},   {88,112,8},{88,120,8},   // F F F F | E E
  {86,128,4},{86,132,4},{86,136,4},{86,140,4},   {84,144,16},             // D D D D | C(ganze)
};
const int SONG_LEN = sizeof(SONG) / sizeof(SONG[0]);

// ---------- Zustand ----------
enum St { PENDING, ARMED, HOLDING, DONE };
St            st[SONG_LEN];
unsigned long deadline[SONG_LEN];        // ms-Zeitpunkt, ab dem die Mindesthaltezeit erfuellt ist
int           activeFor[128];            // pitch -> gehaltene Note (Index) oder -1
long          currentOnset = 0;          // Position des Spielkopfs (Tick)
unsigned long flashUntil[NUM_LEDS];
bool          needRender = true;
unsigned long totalErrors = 0;

void handleMidiByte(uint8_t b);          // Vorwaerts-Deklaration

// ---------- Helfer ----------
int noteToIdx(int note) {
  int idx = 1 + (TOP_NOTE - note);
  if (idx < 1 || idx >= NUM_LEDS) return -1;
  return idx;
}
long noteEnd(int i)        { return (long)SONG[i].start + SONG[i].dur; }
unsigned long minHoldMs(int i) { return (unsigned long)SONG[i].dur * MIN_QUARTER_MS / 4; }

void setFlash(int idx) {
  if (idx < 0) return;
  unsigned long u = millis() + FLASH_MS;
  if (u == 0) u = 1;
  flashUntil[idx] = u;
}

long firstOnset() {
  long best = ONSET_NONE;
  for (int i = 0; i < SONG_LEN; i++) if (SONG[i].start < best) best = SONG[i].start;
  return best;
}
long nextOnset(long after) {
  long best = ONSET_NONE;
  for (int i = 0; i < SONG_LEN; i++)
    if ((long)SONG[i].start > after && (long)SONG[i].start < best) best = SONG[i].start;
  return best;
}

// Noten am aktuellen Onset scharfschalten.
void armOnset() {
  for (int i = 0; i < SONG_LEN; i++)
    if ((long)SONG[i].start == currentOnset && st[i] == PENDING) st[i] = ARMED;
}

// Sind alle Noten des aktuellen Onsets gedrueckt? -> Spielkopf weiterruecken.
void checkAdvance() {
  bool any = false, allPressed = true;
  for (int i = 0; i < SONG_LEN; i++) {
    if ((long)SONG[i].start == currentOnset) {
      any = true;
      if (st[i] != HOLDING && st[i] != DONE) allPressed = false;
    }
  }
  if (any && allPressed) {
    currentOnset = nextOnset(currentOnset);
    armOnset();
  }
}

// HOLDING -> DONE, sobald Mindesthaltezeit abgelaufen UND Spielkopf hinter dem Ende.
void recomputeDone() {
  unsigned long now = millis();
  for (int i = 0; i < SONG_LEN; i++) {
    if (st[i] == HOLDING && now >= deadline[i] && currentOnset >= noteEnd(i)) {
      st[i] = DONE;
      needRender = true;
    }
  }
}

bool allDone() {
  for (int i = 0; i < SONG_LEN; i++) if (st[i] != DONE) return false;
  return true;
}

void render() {
  unsigned long now = millis();
  for (int i = 0; i < NUM_LEDS; i++)
    strip.setPixelColor(i, (i == STATUS_LED) ? COLOR_STATUS : 0);

  // HOLDING (dunkelblau) hat Vorrang. Eine ARMED-Note leuchtet NUR hell, wenn
  // ihre Taste gerade NICHT gedrueckt ist. Muss derselbe Ton direkt erneut
  // gespielt werden, bleibt die LED zunaechst AUS (= erst loslassen!) und
  // leuchtet erst nach dem Loslassen wieder als "druecken" auf.
  for (int i = 0; i < SONG_LEN; i++) {
    int idx = noteToIdx(SONG[i].pitch);
    if (idx < 0) continue;
    if (st[i] == HOLDING) {
      strip.setPixelColor(idx, COLOR_HOLD);                       // dunkelblau: halten
    } else if (st[i] == ARMED && activeFor[SONG[i].pitch] == -1) {
      strip.setPixelColor(idx, COLOR_PRESS);                      // hell: druecken (Taste frei)
    }
    // ARMED + Taste noch gehalten -> ausgeblendet (erst loslassen)
    // PENDING / DONE -> aus
  }

  for (int i = 1; i < NUM_LEDS; i++)
    if (flashUntil[i] != 0 && now < flashUntil[i]) strip.setPixelColor(i, COLOR_WRONG);

  strip.show();
}

void finishSong() {
  for (int i = 0; i < NUM_LEDS; i++) strip.setPixelColor(i, COLOR_DONE);
  strip.show();
  delay(DONE_MS);
  for (int i = 0; i < SONG_LEN; i++) st[i] = PENDING;
  for (int p = 0; p < 128; p++) activeFor[p] = -1;
  for (int i = 0; i < NUM_LEDS; i++) flashUntil[i] = 0;
  totalErrors = 0;
  currentOnset = firstOnset();
  armOnset();
  needRender = true;
}

// ---------- Ereignisse ----------
void noteOn(uint8_t note) {
  int j = -1;
  for (int i = 0; i < SONG_LEN; i++)
    if (st[i] == ARMED && SONG[i].pitch == note) { j = i; break; }

  if (j >= 0) {                          // richtige, faellige Taste
    st[j] = HOLDING;
    deadline[j] = millis() + minHoldMs(j);
    activeFor[note] = j;
    checkAdvance();
  } else {                               // falsch oder zu frueh (vorgegriffen)
    totalErrors++;
    setFlash(noteToIdx(note));
  }
  needRender = true;
}

void noteOff(uint8_t note) {
  int j = activeFor[note];
  if (j >= 0) {
    if (st[j] == HOLDING) {              // zu frueh losgelassen -> neu druecken/halten
      totalErrors++;
      setFlash(noteToIdx(note));
      st[j] = ARMED;
    }
    activeFor[note] = -1;                // bei DONE einfach sauber freigeben
  }
  needRender = true;
}

// ---------- MIDI einlesen (Note-On/Off, inkl. Running-Status) ----------
uint8_t midiStatus = 0, midiData1 = 0;
bool    haveData1  = false;

void handleMidiByte(uint8_t b) {
  if (b & 0x80) {
    if (b >= 0xF8) return;
    if (b >= 0xF0) { midiStatus = 0; haveData1 = false; return; }
    midiStatus = b; haveData1 = false; return;
  }
  if (midiStatus == 0) return;

  uint8_t cmd = midiStatus & 0xF0;
  if (cmd == 0x90 || cmd == 0x80) {
    if (!haveData1) { midiData1 = b; haveData1 = true; }
    else {
      uint8_t note = midiData1, vel = b;
      haveData1 = false;
      if (cmd == 0x90 && vel > 0) noteOn(note);     // vel 0 = Note-Off
      else                        noteOff(note);
    }
  } else if (cmd == 0xC0 || cmd == 0xD0) {
    haveData1 = false;
  } else {
    haveData1 = !haveData1;
  }
}

// ---------- Setup / Loop ----------
void setup() {
  Serial.begin(MIDI_BAUD);
  strip.begin();
  strip.setBrightness(BRIGHTNESS);

  COLOR_PRESS  = strip.Color(0, 80, 120, 0);   // hell tuerkis
  COLOR_HOLD   = strip.Color(0, 0, 70, 0);     // dunkelblau
  COLOR_WRONG  = strip.Color(200, 0, 0, 0);    // rot
  COLOR_DONE   = strip.Color(0, 160, 0, 0);    // gruen (fertig)
  COLOR_STATUS = strip.Color(0, 120, 0, 0);    // gruen (Status)

  for (int i = 0; i < SONG_LEN; i++) st[i] = PENDING;
  for (int p = 0; p < 128; p++) activeFor[p] = -1;
  for (int i = 0; i < NUM_LEDS; i++) flashUntil[i] = 0;

  currentOnset = firstOnset();
  armOnset();
  needRender = true;
}

void loop() {
  // 1) MIDI-Ereignisse.
  while (Serial.available() > 0) handleMidiByte((uint8_t)Serial.read());

  // 2) Zeit-Ereignis: Mindesthaltezeiten pruefen.
  recomputeDone();

  // 3) Rote Blitze ablaufen lassen.
  unsigned long now = millis();
  for (int i = 0; i < NUM_LEDS; i++)
    if (flashUntil[i] != 0 && now >= flashUntil[i]) { flashUntil[i] = 0; needRender = true; }

  // 4) Stueck komplett? -> feiern, von vorn.
  if (allDone()) { finishSong(); return; }

  // 5) Nur bei Aenderung neu zeichnen.
  if (needRender) { render(); needRender = false; }
}

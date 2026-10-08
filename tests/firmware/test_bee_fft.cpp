// PC-Test der FFT-Auswertung (bee_fft.h) mit künstlichen Signalen
// g++ -std=c++11 -O2 -o t tests/firmware/test_bee_fft.cpp && ./t
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
#include <cstdio>
#include <cmath>
#include <cstdlib>
#include <vector>
#include "../../firmware/STM32_LORA_261008_ZS/bee_fft.h"

static BfArbeit arbeit;
static uint16_t roh[BF_ROH];
static int anz = 0, fehler = 0;
static uint32_t saat = 12345;
static double gleich01() { saat = saat * 1664525u + 1013904223u; return (saat >> 8) / 16777216.0; }
static double gauss() { double u = gleich01() + 1e-12, v = gleich01(); return sqrt(-2 * log(u)) * cos(2 * M_PI * v); }

struct Ton { double hz, amp; };
static void signal(std::vector<Ton> t, double rauschen = 0, double phase = 0.3) {
  for (int i = 0; i < BF_ROH; i++) {
    double x = 2048;
    for (auto &k : t) x += k.amp * sin(2 * M_PI * k.hz * i / BF_FS_ADC + phase);
    if (rauschen > 0) x += rauschen * gauss();
    x = floor(x + 0.5);
    if (x < 0) x = 0;
    if (x > 4095) x = 4095;
    roh[i] = (uint16_t)x;
  }
}
static double db(double amp) { return 20 * log10(amp / 2048.0); }
static void nah(const char *was, double ist, double soll, double tol) {
  anz++;
  if (fabs(ist - soll) > tol) { fehler++; printf("FEHL - %s: %.3f statt %.3f (±%.2f)\n", was, ist, soll, tol); }
}
static void wahr(const char *was, bool b) { anz++; if (!b) { fehler++; printf("FEHL - %s\n", was); } }

int main() {
  bf_init(&arbeit);
  char t[160];

  // 1. Sinus 247,3 Hz, Amplitude 1000
  signal({{247.3, 1000}});
  BfErgebnis e = bf_auswerten(&arbeit, roh, 0);
  wahr("Sinus: gültig", e.gueltig);
  nah("Sinus: Frequenz", e.spitze_hz, 247.3, 0.3);
  nah("Sinus: Spitzenpegel", e.spitze_db, db(1000), 0.5);
  nah("Sinus: Band 140–260", e.band_db[1], db(1000), 0.5);
  nah("Sinus: Gesamtpegel", e.gesamt_db, db(1000), 0.5);
  wahr("Sinus: andere Bänder mindestens 40 dB tiefer", e.band_db[0] < db(1000) - 40 && e.band_db[3] < db(1000) - 40);

  // 2. Frequenzlauf 60–900 Hz: Frequenz- und Pegelfehler (Lattenzaun-Effekt)
  double fmax = 0, lmax = 0;
  for (double f = 61.3; f <= 897; f += 13.7) {
    signal({{f, 800}});
    e = bf_auswerten(&arbeit, roh, 0);
    fmax = fmax > fabs(e.spitze_hz - f) ? fmax : fabs(e.spitze_hz - f);
    lmax = lmax > fabs(e.spitze_db - db(800)) ? lmax : fabs(e.spitze_db - db(800));
  }
  nah("Frequenzlauf: größter Frequenzfehler", fmax, 0, 0.3);
  nah("Frequenzlauf: größter Pegelfehler", lmax, 0, 0.5);
  printf("info - Frequenzlauf 61–897 Hz: Frequenzfehler max. %.3f Hz, Pegelfehler max. %.3f dB\n", fmax, lmax);

  // 3. Aliasing: Töne oberhalb des Nutzbands (nach der Dezimierung gespiegelt) stark gedämpft
  double schlechtest = -200;
  for (double f = 1140; f < 4000; f += 97) {
    signal({{f, 2000}});
    e = bf_auswerten(&arbeit, roh, 0);
    double rel = e.gesamt_db - db(2000);
    if (rel > schlechtest) schlechtest = rel;
  }
  snprintf(t, sizeof t, "Aliasing 1140–4000 Hz: höchster Restpegel %.1f dB unter dem Ton", -schlechtest);
  wahr(t, schlechtest < -45);
  printf("info - %s\n", t);

  // 4. Brummen 50 Hz stark, Summen 180 Hz schwächer: Spitze = 180 Hz
  signal({{50, 1800}, {180, 300}});
  e = bf_auswerten(&arbeit, roh, 0);
  nah("50 Hz wird ignoriert: Spitze bei 180 Hz", e.spitze_hz, 180, 0.5);
  nah("50 Hz wird ignoriert: Pegel 180 Hz", e.spitze_db, db(300), 0.6);

  // 4b. Starkes Brummen, sehr leiser Ton: Ausläufer des 50-Hz-Tons bei 60 Hz zählen nicht als Spitze
  signal({{50, 2000}, {300, 15}});
  e = bf_auswerten(&arbeit, roh, 0);
  nah("Ausläufer 50 Hz: Spitze beim leisen Ton 300 Hz", e.spitze_hz, 300, 0.5);

  // 5. Zwei Töne in verschiedenen Bändern
  signal({{150, 600}, {475, 200}});
  e = bf_auswerten(&arbeit, roh, 0);
  nah("Zwei Töne: Spitze 150 Hz", e.spitze_hz, 150, 0.3);
  nah("Zwei Töne: Band 140–260", e.band_db[1], db(600), 0.5);
  nah("Zwei Töne: Band 440–560", e.band_db[4], db(200), 0.5);

  // 6. Weißes Rauschen: Gesamtpegel entspricht der Leistung im Bereich 60–900 Hz
  double sigma = 300;
  signal({}, sigma);
  e = bf_auswerten(&arbeit, roh, 0);
  // Rauschleistung σ² verteilt sich bei 8192 Hz auf 0–4096 Hz; der FIR lässt 0–1025 Hz durch;
  // davon liegt 60–900 Hz (+ eine Linie) im Auswertebereich; sinusgleich: A² = 2·Leistung
  double erwartet = 10 * log10(2 * sigma * sigma * (1025.0 / 4096.0) * ((900 - 60 + 4) / 1024.0) / (2048.0 * 2048.0));
  nah("Rauschen: Gesamtpegel", e.gesamt_db, erwartet, 1.0);
  double summe = 0;
  for (int b = 0; b < BF_BAENDER; b++) summe += pow(10, e.band_db[b] / 10);
  nah("Rauschen: Summe der Bänder = Gesamtpegel", 10 * log10(summe), e.gesamt_db, 0.05);

  // 7. Stille: ungültig, Pegel an der Untergrenze, keine NaN
  signal({});
  e = bf_auswerten(&arbeit, roh, 0);
  wahr("Stille: ungültig", !e.gueltig);
  wahr("Stille: Pegel an der Untergrenze", e.gesamt_db == BF_UNTERGRENZE_DB && e.band_db[2] == BF_UNTERGRENZE_DB);

  // 8. Zu viele verpasste Abtastungen: verworfen
  signal({{247.3, 1000}});
  e = bf_auswerten(&arbeit, roh, BF_ROH / 50);
  wahr("Überläufe > 1 %: verworfen", !e.gueltig);

  // 9. Übersteuerung (Sinus größer als Vollausschlag) wird nicht stumm
  signal({{300, 3000}});
  e = bf_auswerten(&arbeit, roh, 0);
  wahr("Übersteuerung: gültig, Spitze bei 300 Hz", e.gueltig && fabs(e.spitze_hz - 300) < 0.5);

  printf("bee_fft: %d von %d Prüfungen bestanden\n", anz - fehler, anz);
  return fehler ? 1 : 0;
}

// FFT-Auswertung des Mikrofonsignals (GY-MAX4466) – Rechenteil ohne Arduino-Abhängigkeit
// Konzept: docs/fft-konzept.md
//   ADC 8192 Hz → FIR-Tiefpass (127 Koeffizienten, Hamming) und Dezimierung 4 → 2048 Hz
//   → 8 Blöcke zu 512 Werten, 50 % Überlappung, Hann-Fenster → gemittelte Leistung (Welch), Teilung 4,0 Hz
//   → Spitze 60–900 Hz (parabolisch interpoliert), Gesamtpegel und 6 Bandpegel in dBFS
// dBFS: 0 dBFS = Sinus mit Vollausschlag des ADC (Amplitude 2048 bei 12 Bit). Bandpegel sind auf
// dieselbe Skala bezogen (sinusgleiche Leistung), unabhängig von Fensterlänge und Fenster.
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
#ifndef BEE_FFT_H
#define BEE_FFT_H

#include <stdint.h>
#include <math.h>

#define BF_FS_ADC 8192
#define BF_DEZ 4
#define BF_FS (BF_FS_ADC / BF_DEZ)          // 2048 Hz
#define BF_N 512                            // FFT-Länge → 4,0 Hz Teilung
#define BF_LOG2N 9
#define BF_BLOECKE 8
#define BF_HOP (BF_N / 2)
#define BF_TAPS 127
#define BF_NDEZ ((BF_BLOECKE - 1) * BF_HOP + BF_N)       // 2304 Werte nach der Dezimierung
#define BF_ROH (BF_NDEZ * BF_DEZ + BF_TAPS - 1)            // 9342 ADC-Werte (ca. 1,14 s)
#define BF_FIR_GRENZE_HZ 1025.0f
#define BF_F_MIN 60.0f
#define BF_F_MAX 900.0f
#define BF_BAENDER 6
#define BF_VOLLAUSSCHLAG 2048.0f
#define BF_UNTERGRENZE_DB (-127.5f)
#define BF_RAND_TOL_HZ 0.5f                 // Toleranz an den Bereichsgrenzen für die interpolierte Frequenz
#define BF_SNR_DB 10.0f                     // Spitze gilt nur, wenn sie so weit über dem Median der Linien 60–900 Hz liegt

static const float bf_grenzen[BF_BAENDER + 1] = { 60.0f, 140.0f, 260.0f, 360.0f, 440.0f, 560.0f, 900.0f };

struct BfErgebnis {
  bool gueltig;             // Messung brauchbar: Takt eingehalten und Signal vorhanden → Gesamt- und Bandpegel gelten
  bool spitze_gueltig;      // zusätzlich eine deutliche Spitze (≥ BF_SNR_DB über dem Median) → Frequenz und Spitzenpegel gelten
  float snr_db;             // Abstand der Spitze zum Median der Linien (Diagnose)
  float spitze_hz;
  float spitze_db;          // dBFS
  float gesamt_db;          // dBFS, 60–900 Hz
  float band_db[BF_BAENDER];
};

struct BfArbeit {
  float fir[BF_TAPS];
  float cos_t[BF_N / 2], sin_t[BF_N / 2];
  float fenster[BF_N];
  float fenster_summe, enbw;
  float dez[BF_NDEZ];
  float re[BF_N], im[BF_N];
  float leistung[BF_N / 2 + 1];
  bool bereit;
};

static inline void bf_init(BfArbeit *a) {
  const float PI_F = 3.14159265358979f;
  // FIR: gefensterter sinc, Hamming, Verstärkung 1 bei 0 Hz
  float s = 0, fc = BF_FIR_GRENZE_HZ / BF_FS_ADC, m = (BF_TAPS - 1) / 2.0f;
  for (int k = 0; k < BF_TAPS; k++) {
    float x = k - m;
    float h = (x == 0) ? 2.0f * fc : sinf(2.0f * PI_F * fc * x) / (PI_F * x);
    h *= 0.54f - 0.46f * cosf(2.0f * PI_F * k / (BF_TAPS - 1));
    a->fir[k] = h; s += h;
  }
  for (int k = 0; k < BF_TAPS; k++) a->fir[k] /= s;
  for (int k = 0; k < BF_N / 2; k++) { a->cos_t[k] = cosf(2.0f * PI_F * k / BF_N); a->sin_t[k] = -sinf(2.0f * PI_F * k / BF_N); }
  float sw = 0, sw2 = 0;
  for (int n = 0; n < BF_N; n++) {   // Hann (periodisch)
    float w = 0.5f - 0.5f * cosf(2.0f * PI_F * n / BF_N);
    a->fenster[n] = w; sw += w; sw2 += w * w;
  }
  a->fenster_summe = sw;
  a->enbw = BF_N * sw2 / (sw * sw);   // 1,5 Linien beim Hann-Fenster
  a->bereit = true;
}

// Radix-2-FFT, komplex, in place
static inline void bf_fft(BfArbeit *a) {
  float *re = a->re, *im = a->im;
  for (int i = 1, j = 0; i < BF_N; i++) {
    int bit = BF_N >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { float t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; }
  }
  for (int len = 2; len <= BF_N; len <<= 1) {
    int schritt = BF_N / len, halb = len / 2;
    for (int i = 0; i < BF_N; i += len) {
      for (int k = 0; k < halb; k++) {
        float wr = a->cos_t[k * schritt], wi = a->sin_t[k * schritt];
        int p = i + k, q = p + halb;
        float tr = re[q] * wr - im[q] * wi, ti = re[q] * wi + im[q] * wr;
        re[q] = re[p] - tr; im[q] = im[p] - ti;
        re[p] += tr; im[p] += ti;
      }
    }
  }
}

static inline float bf_db(float leistung) {   // Leistung (Amplitude²) → dBFS, begrenzt
  float bezug = BF_VOLLAUSSCHLAG * BF_VOLLAUSSCHLAG;
  if (!(leistung > 0)) return BF_UNTERGRENZE_DB;
  float d = 10.0f * log10f(leistung / bezug);
  if (d < BF_UNTERGRENZE_DB) d = BF_UNTERGRENZE_DB;
  return d;
}

// Parabolische Interpolation in dB: Versatz der Spitze gegen Linie k, begrenzt auf ±0,5 Linien
static inline float bf_versatz(float p1, float p2, float p3) {
  float l1 = 10.0f * log10f(p1 + 1e-12f), l2 = 10.0f * log10f(p2 + 1e-12f), l3 = 10.0f * log10f(p3 + 1e-12f);
  float nenner = l1 - 2.0f * l2 + l3, d = 0;
  if (nenner < 0) d = 0.5f * (l1 - l3) / nenner;
  if (d > 0.5f) d = 0.5f;
  if (d < -0.5f) d = -0.5f;
  return d;
}

// roh: BF_ROH ADC-Werte (0–4095) mit 8192 Hz; ueberlaeufe: Zahl verpasster Abtastzeitpunkte
static inline BfErgebnis bf_auswerten(BfArbeit *a, const uint16_t *roh, uint32_t ueberlaeufe) {
  BfErgebnis e;
  e.gueltig = false; e.spitze_gueltig = false; e.snr_db = 0; e.spitze_hz = 0; e.spitze_db = BF_UNTERGRENZE_DB; e.gesamt_db = BF_UNTERGRENZE_DB;
  for (int b = 0; b < BF_BAENDER; b++) e.band_db[b] = BF_UNTERGRENZE_DB;
  if (!a->bereit) bf_init(a);
  if (ueberlaeufe > BF_ROH / 100) return e;   // mehr als 1 % der Abtastungen verpasst: Messung verwerfen

  // Gleichanteil
  double mittel = 0;
  for (int i = 0; i < BF_ROH; i++) mittel += roh[i];
  float dc = (float)(mittel / BF_ROH);

  // Tiefpass und Dezimierung
  for (int m = 0; m < BF_NDEZ; m++) {
    const uint16_t *x = roh + m * BF_DEZ;
    float s = 0;
    for (int k = 0; k < BF_TAPS; k++) s += a->fir[k] * ((float)x[k] - dc);
    a->dez[m] = s;
  }

  // Welch
  for (int k = 0; k <= BF_N / 2; k++) a->leistung[k] = 0;
  float skal = 2.0f / a->fenster_summe;
  for (int b = 0; b < BF_BLOECKE; b++) {
    const float *y = a->dez + b * BF_HOP;
    float m = 0;
    for (int n = 0; n < BF_N; n++) m += y[n];
    m /= BF_N;
    for (int n = 0; n < BF_N; n++) { a->re[n] = (y[n] - m) * a->fenster[n]; a->im[n] = 0; }
    bf_fft(a);
    for (int k = 0; k <= BF_N / 2; k++) {
      float ar = a->re[k] * skal, ai = a->im[k] * skal;
      a->leistung[k] += (ar * ar + ai * ai) / BF_BLOECKE;   // Sinus der Amplitude A: Spitze = A²
    }
  }

  const float df = (float)BF_FS / BF_N;   // 4,0 Hz
  int kmin = (int)ceilf(BF_F_MIN / df), kmax = (int)floorf(BF_F_MAX / df);

  // Spitze: größtes lokales Maximum, dessen interpolierte Frequenz im Bereich 60–900 Hz liegt.
  // (Ein Ton bei 59 Hz erzeugt bei 60 Hz ein lokales Maximum; interpoliert liegt es unter 60 Hz und zählt nicht.)
  int kp = -1;
  float dp = 0;
  for (int k = kmin; k <= kmax; k++) {
    float p = a->leistung[k];
    if (!(p > 0) || p < a->leistung[k - 1] || p < a->leistung[k + 1] || (kp >= 0 && p <= a->leistung[kp])) continue;
    float d = bf_versatz(a->leistung[k - 1], p, a->leistung[k + 1]);
    float f = (k + d) * df;
    if (f < BF_F_MIN - BF_RAND_TOL_HZ || f > BF_F_MAX + BF_RAND_TOL_HZ) continue;
    kp = k; dp = d;
  }
  if (kp >= 0) {
    float l1 = 10.0f * log10f(a->leistung[kp - 1] + 1e-12f), l2 = 10.0f * log10f(a->leistung[kp] + 1e-12f),
          l3 = 10.0f * log10f(a->leistung[kp + 1] + 1e-12f);
    float d = dp;
    float lmax = l2 - 0.25f * (l1 - l3) * d;
    e.spitze_hz = (kp + d) * df;
    e.spitze_db = bf_db(powf(10.0f, lmax / 10.0f));

    // Abstand zum Median der Linien im Bereich (robust gegen die Spitze selbst). Bei reinem Rauschen liegt
    // das größte Maximum nach der Mittelung über 8 Blöcke nur wenige dB über dem Median.
    int n = 0;
    for (int k = kmin; k <= kmax; k++) {          // Einfügesortierung in re[] (nach der FFT frei), ca. 210 Werte
      float p = a->leistung[k];
      int j = n++;
      while (j > 0 && a->re[j - 1] > p) { a->re[j] = a->re[j - 1]; j--; }
      a->re[j] = p;
    }
    float median = (n & 1) ? a->re[n / 2] : 0.5f * (a->re[n / 2 - 1] + a->re[n / 2]);
    e.snr_db = (median > 0) ? 10.0f * log10f(a->leistung[kp] / median) : 99.0f;
    e.spitze_gueltig = e.snr_db >= BF_SNR_DB;
  }

  // Gesamt- und Bandpegel (sinusgleiche Leistung: Summe / ENBW)
  float gesamt = 0;
  for (int k = kmin; k <= kmax; k++) gesamt += a->leistung[k];
  e.gesamt_db = bf_db(gesamt / a->enbw);
  e.gueltig = gesamt > 0;                         // Stille (konstantes Signal) ist kein Messwert
  if (!e.gueltig) e.spitze_gueltig = false;
  for (int b = 0; b < BF_BAENDER; b++) {
    float s = 0;
    for (int k = kmin; k <= kmax; k++) {
      float f = k * df;
      if (f >= bf_grenzen[b] && (f < bf_grenzen[b + 1] || (b == BF_BAENDER - 1 && f <= bf_grenzen[b + 1]))) s += a->leistung[k];
    }
    e.band_db[b] = bf_db(s / a->enbw);
  }
  return e;
}

#endif

// Funkformat v2 (FPort 2) – Kodierer, siehe docs/funkformat-v2.md
// Gleiche Regeln wie der Referenz-Kodierer tests/formatter/kodierer_v2.js (Begrenzen statt Überlaufen).
// Ohne Arduino-Abhängigkeit, damit er auf dem PC getestet werden kann.
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
#ifndef FUNKFORMAT_V2_H
#define FUNKFORMAT_V2_H

#include <stdint.h>
#include <stddef.h>
#include <math.h>

#define FF2_VERSION 2
#define FF2_MAX_BAENDER 12

// Bits im Kopf (= Reihenfolge der Werte im Paket)
enum {
  FF2_T_AUSSEN = 0, FF2_H_AUSSEN, FF2_DRUCK, FF2_T_INNEN1, FF2_T_INNEN2, FF2_GEWICHT1, FF2_GEWICHT2,
  FF2_VBATT, FF2_VSOLAR, FF2_LICHT, FF2_H_INNEN, FF2_FFT_SPITZE, FF2_FFT_GESAMT, FF2_FFT_BAENDER,
  FF2_SERVICE, FF2_ZUSTAND, FF2_MESSZEIT, FF2_FIRMWARE, FF2_T_CPU
};

// Zustandsbits (erstes Byte von Bit 15)
#define FF2_Z_ZEIT_OK       0x01
#define FF2_Z_FEHLER_AUSSEN 0x02
#define FF2_Z_FEHLER_DS1    0x04
#define FF2_Z_FEHLER_DS2    0x08
#define FF2_Z_FEHLER_WAAGE1 0x10
#define FF2_Z_FEHLER_WAAGE2 0x20
#define FF2_Z_AKKU_NIEDRIG  0x40

// Neustart-Grund (zweites Byte von Bit 15)
enum { FF2_NS_KEINER = 0, FF2_NS_EINSCHALTEN, FF2_NS_PIN, FF2_NS_WATCHDOG, FF2_NS_SOFTWARE, FF2_NS_UNTERSPANNUNG, FF2_NS_LOWPOWER };

struct FunkWerteV2 {
  uint32_t vorhanden;          // Bit k gesetzt = Wert k senden
  float t_aussen, h_aussen, druck_hpa, t_innen1, t_innen2;
  float gewicht1_kg, gewicht2_kg, vbatt_v, vsolar_v, licht_lx, h_innen;
  float fft_hz, fft_db, fft_gesamt_db;
  uint8_t fft_anzahl;
  float fft_baender_db[FF2_MAX_BAENDER];
  float service;
  uint8_t zustand, neustart;
  uint32_t messzeit, firmware;
  float t_cpu;
};

static inline void ff2_leeren(FunkWerteV2 *w) {
  uint8_t *p = (uint8_t *)w;
  for (size_t i = 0; i < sizeof(FunkWerteV2); i++) p[i] = 0;
}
static inline void ff2_setze(FunkWerteV2 *w, int bit) { w->vorhanden |= (uint32_t)1 << bit; }

// Runden wie Math.round in JavaScript (x.5 nach oben), dann begrenzen
static inline double ff2_rund(double x) { return floor(x + 0.5); }
static inline long ff2_grenze(double x, long lo, long hi) {
  if (!(x == x)) return lo;  // NaN
  double r = ff2_rund(x);
  if (r < (double)lo) return lo;
  if (r > (double)hi) return hi;
  return (long)r;
}

struct Ff2Puffer {
  uint8_t *b;
  size_t n, max;
  bool voll;
};
static inline void ff2_b(Ff2Puffer *p, uint8_t v) { if (p->n < p->max) p->b[p->n++] = v; else p->voll = true; }
static inline void ff2_i16(Ff2Puffer *p, double x) { uint16_t v = (uint16_t)(int16_t)ff2_grenze(x, -32768, 32767); ff2_b(p, v >> 8); ff2_b(p, v & 0xFF); }
static inline void ff2_u16(Ff2Puffer *p, double x) { uint16_t v = (uint16_t)ff2_grenze(x, 0, 65535); ff2_b(p, v >> 8); ff2_b(p, v & 0xFF); }
static inline void ff2_i24(Ff2Puffer *p, double x) {
  uint32_t v = (uint32_t)ff2_grenze(x, -8388608L, 8388607L) & 0xFFFFFFUL;
  ff2_b(p, (v >> 16) & 0xFF); ff2_b(p, (v >> 8) & 0xFF); ff2_b(p, v & 0xFF);
}
static inline void ff2_u32(Ff2Puffer *p, uint32_t v) { ff2_b(p, v >> 24); ff2_b(p, (v >> 16) & 0xFF); ff2_b(p, (v >> 8) & 0xFF); ff2_b(p, v & 0xFF); }
static inline uint8_t ff2_pegel(double dbfs) { return (uint8_t)ff2_grenze(-dbfs * 2.0, 0, 255); }
static inline uint8_t ff2_feuchte(double p) { return (uint8_t)ff2_grenze(p * 2.0, 0, 200); }

// Kodiert die Werte; Rückgabe: Länge in Byte, 0 wenn der Puffer zu klein ist
static inline size_t ff2_kodiere(const FunkWerteV2 *w, uint8_t *puffer, size_t max) {
  Ff2Puffer p = { puffer, 0, max, false };
  uint32_t k = w->vorhanden & 0x7FFFFUL;   // nur Bits 0–18 sind festgelegt
  ff2_b(&p, FF2_VERSION);
  ff2_u32(&p, k);
#define HAT(bit) (k & ((uint32_t)1 << (bit)))
  if (HAT(FF2_T_AUSSEN)) ff2_i16(&p, w->t_aussen * 100.0);
  if (HAT(FF2_H_AUSSEN)) ff2_b(&p, ff2_feuchte(w->h_aussen));
  if (HAT(FF2_DRUCK)) ff2_u16(&p, w->druck_hpa * 10.0);
  if (HAT(FF2_T_INNEN1)) ff2_i16(&p, w->t_innen1 * 100.0);
  if (HAT(FF2_T_INNEN2)) ff2_i16(&p, w->t_innen2 * 100.0);
  if (HAT(FF2_GEWICHT1)) ff2_i24(&p, w->gewicht1_kg * 1000.0);
  if (HAT(FF2_GEWICHT2)) ff2_i24(&p, w->gewicht2_kg * 1000.0);
  if (HAT(FF2_VBATT)) ff2_u16(&p, w->vbatt_v * 1000.0);
  if (HAT(FF2_VSOLAR)) ff2_u16(&p, w->vsolar_v * 1000.0);
  if (HAT(FF2_LICHT)) ff2_u16(&p, w->licht_lx);
  if (HAT(FF2_H_INNEN)) ff2_b(&p, ff2_feuchte(w->h_innen));
  if (HAT(FF2_FFT_SPITZE)) { ff2_u16(&p, w->fft_hz * 10.0); ff2_b(&p, ff2_pegel(w->fft_db)); }
  if (HAT(FF2_FFT_GESAMT)) ff2_b(&p, ff2_pegel(w->fft_gesamt_db));
  if (HAT(FF2_FFT_BAENDER)) {
    uint8_t n = w->fft_anzahl > FF2_MAX_BAENDER ? FF2_MAX_BAENDER : w->fft_anzahl;
    ff2_b(&p, n);
    for (uint8_t i = 0; i < n; i++) ff2_b(&p, ff2_pegel(w->fft_baender_db[i]));
  }
  if (HAT(FF2_SERVICE)) ff2_b(&p, (uint8_t)ff2_grenze(w->service, 0, 255));
  if (HAT(FF2_ZUSTAND)) { ff2_b(&p, w->zustand & 0x7F); ff2_b(&p, w->neustart); }
  if (HAT(FF2_MESSZEIT)) ff2_u32(&p, w->messzeit);
  if (HAT(FF2_FIRMWARE)) ff2_u32(&p, w->firmware);
  if (HAT(FF2_T_CPU)) ff2_i16(&p, w->t_cpu * 100.0);
#undef HAT
  return p.voll ? 0 : p.n;
}

#endif

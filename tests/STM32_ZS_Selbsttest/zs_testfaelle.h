/*
   zs_testfaelle.h - Testfälle für beelogger_zeitsync.h

   Wird von zwei Programmen benutzt:
     - tests/host/test_zeitsync.cpp     (am PC mit g++/clang übersetzen)
     - tests/STM32_ZS_Selbsttest/       (Arduino-Sketch, läuft auf der BlackPill)

   Vorher einbinden: beelogger_zeitsync.h und zs_testvektoren.h
*/
#ifndef ZS_TESTFAELLE_H
#define ZS_TESTFAELLE_H

#include <stdio.h>
#include <stdint.h>

typedef void (*zs_ausgabe_t)(const char *);

static zs_ausgabe_t zs_t_aus;
static uint32_t zs_t_ok, zs_t_fehler;
static char zs_t_buf[160];

#define ZS_PRUEFE(bed, ...)                                    \
  do {                                                         \
    if (bed) { zs_t_ok++; }                                    \
    else {                                                     \
      zs_t_fehler++;                                           \
      if (zs_t_fehler <= 40) {                                 \
        snprintf(zs_t_buf, sizeof(zs_t_buf), __VA_ARGS__);     \
        zs_t_aus(zs_t_buf);                                    \
      }                                                        \
    }                                                          \
  } while (0)

// einfacher Zufallsgenerator, gleiche Folge auf PC und STM32
static uint32_t zs_t_lcg = 12345;
static uint32_t zs_t_zufall() { zs_t_lcg = zs_t_lcg * 1664525UL + 1013904223UL; return zs_t_lcg; }

static void zs_test_gps() {
  // 1.1.2026 00:00:00 UTC = 1767225600 Unix = 1451260818 GPS (mit 18 Schaltsekunden)
  ZS_PRUEFE(zs_gps_zu_unix(1451260818UL) == 1767225600UL, "GPS->Unix falsch: %lu", (unsigned long)zs_gps_zu_unix(1451260818UL));
  ZS_PRUEFE(zs_unix_zu_gps(1767225600UL) == 1451260818UL, "Unix->GPS falsch");
  ZS_PRUEFE(zs_netz_utc_ms(1451260818UL, 2500) == (int64_t)1767225602500LL, "Netzzeit ms falsch");
  ZS_PRUEFE(!zs_netzzeit_gueltig(1700000000UL), "2023 darf nicht gueltig sein");
  ZS_PRUEFE(zs_netzzeit_gueltig(1791417600UL), "8.10.2026 muss gueltig sein");
  ZS_PRUEFE(!zs_netzzeit_gueltig(2019686400UL), "2034 darf nicht gueltig sein (Sketch: Jahr 22..33)");
  // Fehler, den das MCCI-Beispiel macht (ohne Schaltsekunden): 18 s
  ZS_PRUEFE(1451260818UL + ZS_GPS_UNIX_OFFSET - zs_gps_zu_unix(1451260818UL) == 18, "Schaltsekunden nicht beruecksichtigt");
}

static void zs_test_warten() {
  ZS_PRUEFE(zs_warte_ms_bis_volle_sekunde(1767225600123LL) == 877, "Warten 123 ms");
  ZS_PRUEFE(zs_naechste_volle_sekunde(1767225600123LL) == 1767225601UL, "Zielsekunde 123 ms");
  ZS_PRUEFE(zs_warte_ms_bis_volle_sekunde(1767225600000LL) == 0, "Warten 0 ms");
  ZS_PRUEFE(zs_naechste_volle_sekunde(1767225600000LL) == 1767225600UL, "Zielsekunde 0 ms");
  ZS_PRUEFE(zs_warte_ms_bis_volle_sekunde(1767225600999LL) == 1, "Warten 999 ms");
}

static void zs_test_kalender() {
  // Hin- und Rückrechnung jeden Tag 1970 ... 2100
  uint32_t fehler = 0;
  int32_t tage_2100 = zs_tage_aus_datum(2100, 1, 1);
  for (int32_t z = 0; z <= tage_2100; z++) {
    int32_t j; uint8_t m, t;
    zs_datum_aus_tagen(z, &j, &m, &t);
    if (zs_tage_aus_datum(j, m, t) != z) fehler++;
  }
  ZS_PRUEFE(fehler == 0, "Kalender Hin/Rueck: %lu Fehler", (unsigned long)fehler);
  ZS_PRUEFE(tage_2100 == 47482, "Tage bis 1.1.2100: %ld", (long)tage_2100);
  ZS_PRUEFE(zs_wochentag(0) == 4, "1.1.1970 ist Donnerstag");
  ZS_PRUEFE(zs_wochentag(zs_tage_aus_datum(2026, 10, 8)) == 4, "8.10.2026 ist Donnerstag");
  ZS_PRUEFE(zs_letzter_sonntag(2026, 3) == zs_tage_aus_datum(2026, 3, 29), "letzter So Maerz 2026 = 29.");
  ZS_PRUEFE(zs_letzter_sonntag(2026, 10) == zs_tage_aus_datum(2026, 10, 25), "letzter So Okt 2026 = 25.");
  ZS_PRUEFE(zs_letzter_sonntag(2027, 10) == zs_tage_aus_datum(2027, 10, 31), "letzter So Okt 2027 = 31.");
  ZS_PRUEFE(zs_tage_aus_datum(2024, 2, 29) + 1 == zs_tage_aus_datum(2024, 3, 1), "Schaltjahr 2024");
}

static void zs_test_ortszeit() {
  uint32_t f_sz = 0, f_h = 0, f_m = 0;
  for (uint32_t i = 0; i < ZS_TV_ANZAHL; i++) {
    uint32_t u = zs_tv_ortszeit[i].utc;
    uint32_t ort = zs_ortszeit(u, 1);
    if (zs_eu_sommerzeit(u) != zs_tv_ortszeit[i].mesz) {
      f_sz++;
      ZS_PRUEFE(0, "Sommerzeit falsch bei UTC %lu", (unsigned long)u);
    }
    if (zs_stunde(ort) != zs_tv_ortszeit[i].stunde) { f_h++; ZS_PRUEFE(0, "Ortsstunde falsch bei UTC %lu", (unsigned long)u); }
    if (zs_monat(ort) != zs_tv_ortszeit[i].monat) { f_m++; ZS_PRUEFE(0, "Ortsmonat falsch bei UTC %lu", (unsigned long)u); }
  }
  ZS_PRUEFE(f_sz + f_h + f_m == 0, "Ortszeit: %lu Abweichungen von %lu Vektoren",
            (unsigned long)(f_sz + f_h + f_m), (unsigned long)ZS_TV_ANZAHL);
}

static void zs_test_nacht() {
  // Nacht 23 ... 6 Uhr (über Mitternacht)
  ZS_PRUEFE(zs_ist_nacht(23, 23, 6), "23 Uhr ist Nacht");
  ZS_PRUEFE(zs_ist_nacht(0, 23, 6), "0 Uhr ist Nacht");
  ZS_PRUEFE(zs_ist_nacht(5, 23, 6), "5 Uhr ist Nacht");
  ZS_PRUEFE(!zs_ist_nacht(6, 23, 6), "6 Uhr ist Tag");
  ZS_PRUEFE(!zs_ist_nacht(22, 23, 6), "22 Uhr ist Tag");
  // ohne Mitternacht
  ZS_PRUEFE(zs_ist_nacht(2, 1, 5), "2 Uhr in 1..5");
  ZS_PRUEFE(!zs_ist_nacht(5, 1, 5), "5 Uhr nicht in 1..5");
  ZS_PRUEFE(!zs_ist_nacht(3, 4, 4), "leeres Fenster");
}

static void zs_test_weckzeit() {
  static const uint16_t intervalle[] = { 5, 10, 15, 20, 30, 60, 120, 7 };
  uint32_t f = 0;
  for (uint8_t ii = 0; ii < sizeof(intervalle) / sizeof(intervalle[0]); ii++) {
    uint32_t I = (uint32_t)intervalle[ii] * 60UL;
    for (uint8_t slot = 0; slot <= 9; slot++) {
      for (uint16_t n = 0; n < 300; n++) {
        uint32_t jetzt = 1767225600UL + (zs_t_zufall() % (400UL * 86400UL));
        uint32_t t = zs_naechste_weckzeit(jetzt, intervalle[ii], slot, 10, 120);
        uint8_t ok = (t >= jetzt + 120) && (t - I < jetzt + 120)
                     && ((t + I - 1UL - slot * 10UL) % I == 0);
        if (!ok) {
          f++;
          ZS_PRUEFE(0, "Weckzeit falsch: I=%u slot=%u jetzt=%lu t=%lu", intervalle[ii], slot,
                    (unsigned long)jetzt, (unsigned long)t);
        }
      }
    }
  }
  ZS_PRUEFE(f == 0, "Weckzeit: %lu Fehler", (unsigned long)f);

  // Beispiele mit runden Zeiten (8.10.2026 12:03:20 UTC)
  uint32_t basis = 1791417600UL + 12UL * 3600 + 3 * 60 + 20;
  ZS_PRUEFE(zs_naechste_weckzeit(basis, 10, 0, 10, 120) == 1791417600UL + 12UL * 3600 + 10 * 60 + 1, "Slot 0: 12:10:01");
  ZS_PRUEFE(zs_naechste_weckzeit(basis, 10, 3, 10, 120) == 1791417600UL + 12UL * 3600 + 10 * 60 + 31, "Slot 3: 12:10:31");
  ZS_PRUEFE(zs_naechste_weckzeit(basis, 10, 9, 10, 120) == 1791417600UL + 12UL * 3600 + 11 * 60 + 31, "Slot 9: 12:11:31");
  ZS_PRUEFE(zs_naechste_weckzeit(basis, 30, 0, 10, 120) == 1791417600UL + 12UL * 3600 + 30 * 60 + 1, "Nacht 30 min: 12:30:01");
  // knapp vor einem Rasterpunkt: Mindestschlaf 2 min -> nächster Punkt
  uint32_t knapp = 1791417600UL + 12UL * 3600 + 9 * 60 + 0;   // 12:09:00
  ZS_PRUEFE(zs_naechste_weckzeit(knapp, 10, 0, 10, 120) == 1791417600UL + 12UL * 3600 + 20 * 60 + 1, "Mindestschlaf");
  // Mitternacht: nie genau 00:00:00 und kein Wachfenster über Mitternacht
  uint32_t vor_mitternacht = 1791417600UL + 23UL * 3600 + 55 * 60;  // 23:55:00
  uint32_t w = zs_naechste_weckzeit(vor_mitternacht, 10, 0, 10, 120);
  ZS_PRUEFE(w % 86400UL != 0, "nicht um 00:00:00");
  ZS_PRUEFE(w == 1791417600UL + 24UL * 3600 + 1, "00:00:01 statt 23:59:59");
  // kein Logger (Slot 0..9, 10 s) wacht in den letzten 2 min vor Mitternacht (Raster 5..120 min)
  {
    static const uint16_t iv[] = { 5, 10, 15, 20, 30, 60, 120 };
    uint8_t ok_mn = 1;
    for (uint8_t a = 0; a < sizeof(iv) / sizeof(iv[0]); a++)
      for (uint8_t sl = 0; sl <= 9; sl++)
        for (uint32_t j = 0; j < 86400UL; j += 37) {
          uint32_t ww = zs_naechste_weckzeit(1791417600UL + j, iv[a], sl, 10, 120);
          if (ww % 86400UL > 86400UL - 120UL) ok_mn = 0;
        }
    ZS_PRUEFE(ok_mn, "Wecken kurz vor Mitternacht gefunden");
  }
  // Slots aller Logger liegen im selben Zyklus 10 s auseinander
  uint32_t t0 = zs_naechste_weckzeit(basis, 10, 0, 10, 120);
  uint8_t abst_ok = 1;
  for (uint8_t s = 1; s <= 9; s++) {
    uint32_t ts = zs_naechste_weckzeit(t0 - 200, 10, s, 10, 120);
    if (ts != t0 + s * 10UL) abst_ok = 0;
  }
  ZS_PRUEFE(abst_ok, "Slots nicht 10 s auseinander");
}

static void zs_test_faellig() {
  const uint32_t T = 1791417600UL;  // 8.10.2026
  // nie abgeglichen, nie versucht -> sofort
  ZS_PRUEFE(zs_abgleich_faellig(T, 0, 0, 0, 24, 60) == 1, "nie versucht -> faellig");
  // nie abgeglichen, Versuch vor 10 min -> warten
  ZS_PRUEFE(zs_abgleich_faellig(T, 0, T - 600, 0, 24, 60) == 0, "Pause nach Fehlversuch");
  ZS_PRUEFE(zs_abgleich_faellig(T, 0, T - 3600, 0, 24, 60) == 1, "nach 60 min erneut");
  // abgeglichen vor 3 h -> nein
  ZS_PRUEFE(zs_abgleich_faellig(T, T - 3 * 3600, T - 3 * 3600, 1, 24, 60) == 0, "vor 3 h abgeglichen");
  // abgeglichen vor 24 h -> ja
  ZS_PRUEFE(zs_abgleich_faellig(T, T - 24 * 3600, T - 24 * 3600, 1, 24, 60) == 1, "nach 24 h");
  // 25 h, letzter Versuch vor 20 min fehlgeschlagen -> nein
  ZS_PRUEFE(zs_abgleich_faellig(T, T - 25 * 3600, T - 1200, 1, 24, 60) == 0, "Fehlversuch-Pause");
  // Uhr zurückgesprungen (POR, Jahr 2022) -> sofort
  ZS_PRUEFE(zs_abgleich_faellig(1640995200UL, T - 3600, T - 3600, 1, 24, 60) == 1, "Uhr zurueckgesprungen");
}

static void zs_test_annehmen() {
  ZS_PRUEFE(zs_korrektur_annehmen(0, (int64_t)7200 * 1000, 0, 0, 600) == 1, "erste Korrektur (Ortszeit->UTC) annehmen");
  ZS_PRUEFE(zs_korrektur_annehmen(1, 1500, 0, 0, 600) == 1, "kleine Korrektur annehmen");
  ZS_PRUEFE(zs_korrektur_annehmen(1, -1500, 0, 0, 600) == 1, "kleine negative Korrektur annehmen");
  ZS_PRUEFE(zs_korrektur_annehmen(1, (int64_t)3600 * 1000, 0, 0, 600) == 0, "Sprung 1 h ohne Bestaetigung ablehnen");
  ZS_PRUEFE(zs_korrektur_annehmen(1, (int64_t)3601 * 1000, 1, 3600, 600) == 1, "Sprung 1 h bestaetigt annehmen");
  ZS_PRUEFE(zs_korrektur_annehmen(1, (int64_t)3600 * 1000, 1, -3600, 600) == 0, "andere Richtung nicht bestaetigt");
  ZS_PRUEFE(zs_korrektur_annehmen(1, (int64_t)3600 * 1000, 1, 1800, 600) == 0, "andere Groesse nicht bestaetigt");
  ZS_PRUEFE(zs_korrektur_annehmen(1, (int64_t)1800 * 1000, 1, 3600, 600) == 0, "kleinere Groesse nicht bestaetigt");
  ZS_PRUEFE(zs_korrektur_annehmen(1, -(int64_t)86400 * 1000, 1, -86396, 600) == 1, "-1 Tag bestaetigt (+/-5 s)");
  // Uhr-Plausibilität beim Wecken
  const uint32_t G = 1791417600UL + 12UL * 3600;
  ZS_PRUEFE(zs_uhr_plausibel(G, G, 6 * 3600, 600) == 1, "Wecken zur geplanten Zeit");
  ZS_PRUEFE(zs_uhr_plausibel(G + 2, G, 6 * 3600, 600) == 1, "Wecken 2 s spaeter");
  ZS_PRUEFE(zs_uhr_plausibel(G - 3600, G, 6 * 3600, 600) == 1, "Taster 1 h frueher");
  ZS_PRUEFE(zs_uhr_plausibel(G + 7200, G, 6 * 3600, 600) == 0, "Uhr 2 h vor (System-Check, MESZ)");
  ZS_PRUEFE(zs_uhr_plausibel(G + 900, G, 6 * 3600, 600) == 0, "Wecken 15 min nach Plan");
  ZS_PRUEFE(zs_uhr_plausibel(G - 7 * 3600, G, 6 * 3600, 600) == 0, "7 h vor Plan");
  ZS_PRUEFE(zs_uhr_plausibel(G - 86400, G, 6 * 3600, 600) == 0, "Uhr 1 Tag zurueck");
  ZS_PRUEFE(zs_uhr_plausibel(G, 0, 6 * 3600, 600) == 0, "keine geplante Weckzeit");
  // Prüfwort
  uint32_t r[5] = { 1, 2, 3, 4, 5 };
  uint32_t p0 = zs_pruefwort(r, 5);
  uint32_t null5[5] = { 0, 0, 0, 0, 0 };
  ZS_PRUEFE(zs_pruefwort(null5, 5) != 0, "Pruefwort von leeren Registern darf nicht 0 sein");
  uint8_t bit_ok = 1;
  for (uint8_t i = 0; i < 5; i++)
    for (uint8_t b = 0; b < 32; b++) {
      r[i] ^= (1UL << b);
      if (zs_pruefwort(r, 5) == p0) bit_ok = 0;
      r[i] ^= (1UL << b);
    }
  ZS_PRUEFE(bit_ok, "Pruefwort erkennt nicht jeden 1-Bit-Fehler");
  r[0] = 2; r[1] = 1;
  ZS_PRUEFE(zs_pruefwort(r, 5) != p0, "Pruefwort erkennt vertauschte Register nicht");
  // Zeitreferenz
  ZS_PRUEFE(zs_vergangen_ok(2500) && !zs_vergangen_ok(-1) && !zs_vergangen_ok(60000), "vergangen_ok");
  float p = zs_gang_ppm(-1728, 86400);
  ZS_PRUEFE(p > 19.9f && p < 20.1f, "Gang 20 ppm vor");
  p = zs_gang_ppm(864, 86400);
  ZS_PRUEFE(p < -9.9f && p > -10.1f, "Gang 10 ppm nach");
}

// Ganze Kette wie im Sketch, mit nachgebildeter MCCI-Referenz:
// Uplink-Ende zur wahren Zeit T, Netz liefert GPS-Sekunden + 1/256-Bruchteil,
// MCCI rechnet tLocal auf die volle Sekunde zurück.
static void zs_test_kette() {
  const int64_t TICKS = 62500;            // MCCI: OSTICKS_PER_SEC bei 16 us
  uint32_t f = 0;
  for (uint16_t n = 0; n < 2000; n++) {
    int64_t wahr_txende_us = (int64_t)(1767225600ULL + (zs_t_zufall() % (300UL * 86400UL))) * 1000000LL
                             + (int64_t)(zs_t_zufall() % 1000000UL);
    int64_t ticks_txende = (int64_t)(zs_t_zufall() % 100000000UL);   // beliebiger Tick-Stand
    // Netz: Zeitpunkt Uplink-Ende in GPS, Sekunde + Bruchteil (abgerundet auf 1/256 s)
    int64_t gps_us = wahr_txende_us - (int64_t)(ZS_GPS_UNIX_OFFSET - ZS_SCHALTSEKUNDEN) * 1000000LL;
    uint32_t gps_s = (uint32_t)(gps_us / 1000000LL);
    uint8_t frac = (uint8_t)(((gps_us % 1000000LL) * 256) / 1000000LL);
    // MCCI: tLocal = txend - frac * ms2osticks(1000) / 256
    int64_t tLocal = ticks_txende - (int64_t)frac * TICKS / 256;
    // 2,7 s später wertet der Sketch aus
    int64_t ticks_jetzt = ticks_txende + (int64_t)(2.7 * TICKS);
    uint32_t vergangen_ms = (uint32_t)(((ticks_jetzt - tLocal) * 1000) / TICKS);
    int64_t netz_ms = zs_netz_utc_ms(gps_s, vergangen_ms);
    int64_t wahr_ms = (wahr_txende_us + 2700000LL) / 1000;
    int64_t d = netz_ms - wahr_ms;
    if (d < 0) d = -d;
    if (d > 6) {   // Quantisierung 1/256 s = 3,9 ms + Rundung
      f++;
      ZS_PRUEFE(0, "Kette: Abweichung %ld ms", (long)(netz_ms - wahr_ms));
    }
  }
  ZS_PRUEFE(f == 0, "Kette: %lu Faelle > 6 ms", (unsigned long)f);
}

static int zs_tests_ausfuehren(zs_ausgabe_t ausgabe) {
  zs_t_aus = ausgabe;
  zs_t_ok = 0; zs_t_fehler = 0; zs_t_lcg = 12345;
  zs_test_gps();
  zs_test_warten();
  zs_test_kalender();
  zs_test_ortszeit();
  zs_test_nacht();
  zs_test_weckzeit();
  zs_test_faellig();
  zs_test_annehmen();
  zs_test_kette();
  snprintf(zs_t_buf, sizeof(zs_t_buf), "ZS-Tests: %lu bestanden, %lu fehlgeschlagen",
           (unsigned long)zs_t_ok, (unsigned long)zs_t_fehler);
  zs_t_aus(zs_t_buf);
  return (int)zs_t_fehler;
}

#endif

/*
   beelogger_zeitsync.h  -  Rechenlogik für den Zeitabgleich per LoRaWAN DeviceTimeReq
   und das feste Weckraster mit Versatz je Logger.

   Diese Datei enthält bewusst KEINE Arduino-, RTC- oder LMIC-Aufrufe.
   Dadurch läuft genau derselbe Code
     - im Sketch auf dem STM32 und
     - in den Testprogrammen am PC (tests/host) bzw. im Selbsttest-Sketch.

   Zeitbasis: Unix-Sekunden. Nach dem ersten erfolgreichen Abgleich läuft die RTC in UTC.
   Vor dem ersten Abgleich hält die RTC die Compile-Zeit (Ortszeit) aus dem System-Check.

   Version 08.10.2026 (Test, Review-Stand 2), Ergänzung zu beelogger STM32_LORA_260705
   Lizenz: GPL v3 wie der beelogger-Sketch
*/
#ifndef BEELOGGER_ZEITSYNC_H
#define BEELOGGER_ZEITSYNC_H

#include <stdint.h>

/****************************************************************/
// Konstanten
/****************************************************************/
#define ZS_GPS_UNIX_OFFSET  315964800UL   // 6.1.1980 00:00 UTC (GPS-Epoche) minus 1.1.1970
#define ZS_SCHALTSEKUNDEN   18            // GPS - UTC, gilt seit 1.1.2017 (Stand 10/2026, IERS)
#define ZS_MIN_GUELTIG      1704067200UL  // 1.1.2024 00:00 UTC: frühere Netzzeit = unplausibel
#define ZS_MAX_GUELTIG      2019686400UL  // 1.1.2034 00:00 UTC: Sketch akzeptiert RTC-Jahr nur 22..33
#define ZS_SEK_PRO_TAG      86400UL
// Gültigkeit: Schaltsekunden-Stand und Datumsgrenze sind bewusst fest kodiert.
// Kündigt der IERS eine neue Schaltsekunde an, ZS_SCHALTSEKUNDEN anpassen.
// ZS_MAX_GUELTIG folgt der Jahresprüfung 22...33 im Original-Sketch (get_data_from_ram).

/****************************************************************/
// Netzzeit
/****************************************************************/

// GPS-Sekunden (DeviceTimeAns) -> Unix-Sekunden UTC
static inline uint32_t zs_gps_zu_unix(uint32_t gps_s) {
  return gps_s + ZS_GPS_UNIX_OFFSET - ZS_SCHALTSEKUNDEN;
}

// Unix-Sekunden UTC -> GPS-Sekunden (nur für Tests)
static inline uint32_t zs_unix_zu_gps(uint32_t unix_s) {
  return unix_s - ZS_GPS_UNIX_OFFSET + ZS_SCHALTSEKUNDEN;
}

// UTC in Millisekunden "jetzt":
//   gps_s       = tNetwork aus LMIC_getNetworkTimeReference() (Sekunden ab GPS-Epoche,
//                 MCCI hat tLocal bereits auf die volle Sekunde zurückgerechnet)
//   vergangen_ms = osticks2ms(os_getTime() - tLocal)
static inline int64_t zs_netz_utc_ms(uint32_t gps_s, uint32_t vergangen_ms) {
  return (int64_t)zs_gps_zu_unix(gps_s) * 1000 + (int64_t)vergangen_ms;
}

static inline uint8_t zs_netzzeit_gueltig(uint32_t unix_s) {
  return (unix_s >= ZS_MIN_GUELTIG) && (unix_s < ZS_MAX_GUELTIG);
}

// Wartezeit bis zur nächsten vollen Sekunde und diese Sekunde selbst.
// Die STM32-RTC übernimmt beim Stellen keine Sekundenbruchteile, deshalb
// wird erst gewartet und dann auf die volle Sekunde gestellt.
static inline uint16_t zs_warte_ms_bis_volle_sekunde(int64_t utc_ms) {
  return (uint16_t)((1000 - (utc_ms % 1000)) % 1000);
}
static inline uint32_t zs_naechste_volle_sekunde(int64_t utc_ms) {
  return (uint32_t)((utc_ms + zs_warte_ms_bis_volle_sekunde(utc_ms)) / 1000);
}

/****************************************************************/
// Kalender (proleptisch gregorianisch, Algorithmus nach H. Hinnant)
/****************************************************************/

// Tage seit 1.1.1970 aus Datum
static inline int32_t zs_tage_aus_datum(int32_t j, uint8_t m, uint8_t t) {
  j -= (m <= 2);
  const int32_t era = (j >= 0 ? j : j - 399) / 400;
  const uint32_t yoe = (uint32_t)(j - era * 400);
  const uint32_t doy = (153u * (m + (m > 2 ? -3 : 9)) + 2u) / 5u + t - 1u;
  const uint32_t doe = yoe * 365u + yoe / 4u - yoe / 100u + doy;
  return era * 146097 + (int32_t)doe - 719468;
}

// Datum aus Tagen seit 1.1.1970
static inline void zs_datum_aus_tagen(int32_t z, int32_t *j, uint8_t *m, uint8_t *t) {
  z += 719468;
  const int32_t era = (z >= 0 ? z : z - 146096) / 146097;
  const uint32_t doe = (uint32_t)(z - era * 146097);
  const uint32_t yoe = (doe - doe / 1460u + doe / 36524u - doe / 146096u) / 365u;
  const uint32_t doy = doe - (365u * yoe + yoe / 4u - yoe / 100u);
  const uint32_t mp = (5u * doy + 2u) / 153u;
  const uint32_t d = doy - (153u * mp + 2u) / 5u + 1u;
  const uint32_t mm = mp < 10 ? mp + 3 : mp - 9;
  *j = (int32_t)yoe + era * 400 + (mm <= 2);
  *m = (uint8_t)mm;
  *t = (uint8_t)d;
}

// Wochentag: 0 = Sonntag ... 6 = Samstag
static inline uint8_t zs_wochentag(int32_t tage) {
  return (uint8_t)(tage >= -4 ? (tage + 4) % 7 : (tage + 5) % 7 + 6);
}

// Tag (Tage seit 1970) des letzten Sonntags im Monat
static inline int32_t zs_letzter_sonntag(int32_t j, uint8_t m) {
  int32_t erster_naechster = (m == 12) ? zs_tage_aus_datum(j + 1, 1, 1) : zs_tage_aus_datum(j, m + 1, 1);
  int32_t letzter = erster_naechster - 1;
  return letzter - zs_wochentag(letzter);
}

// EU-Sommerzeit: letzter Sonntag im März 01:00 UTC bis letzter Sonntag im Oktober 01:00 UTC
static inline uint8_t zs_eu_sommerzeit(uint32_t utc) {
  int32_t j; uint8_t m, t;
  zs_datum_aus_tagen((int32_t)(utc / ZS_SEK_PRO_TAG), &j, &m, &t);
  uint32_t beginn = (uint32_t)zs_letzter_sonntag(j, 3) * ZS_SEK_PRO_TAG + 3600UL;
  uint32_t ende   = (uint32_t)zs_letzter_sonntag(j, 10) * ZS_SEK_PRO_TAG + 3600UL;
  return (utc >= beginn) && (utc < ende);
}

// Ortszeit (MEZ/MESZ bei std_h = 1) aus UTC
static inline uint32_t zs_ortszeit(uint32_t utc, int8_t std_h) {
  return (uint32_t)((int64_t)utc + 3600L * (std_h + (zs_eu_sommerzeit(utc) ? 1 : 0)));
}

static inline uint8_t zs_stunde(uint32_t t) { return (uint8_t)((t % ZS_SEK_PRO_TAG) / 3600UL); }

static inline uint8_t zs_monat(uint32_t t) {
  int32_t j; uint8_t m, d;
  zs_datum_aus_tagen((int32_t)(t / ZS_SEK_PRO_TAG), &j, &m, &d);
  return m;
}

// Nachtfenster, auch über Mitternacht (z. B. 23 ... 6)
static inline uint8_t zs_ist_nacht(uint8_t h, uint8_t anfang, uint8_t ende) {
  if (anfang == ende) return 0;
  if (anfang < ende) return (h >= anfang) && (h < ende);
  return (h >= anfang) || (h < ende);
}

/****************************************************************/
// Weckraster
/****************************************************************/
// Nächste Weckzeit auf einem festen Raster, gemessen ab 1.1.1970:
//   Weckzeit = k * Intervall + Slot * Abstand + 1 s
// +1 s statt -1 s wie im Original: kein Wecken um xx:00:00 UND kein Wachfenster, das
// über Mitternacht läuft (sonst kann STM32RTC 1.3.7 nach Mitternacht ein veraltetes
// Datum aus den gesperrten Schattenregistern liefern).
// Ergebnis ist die kleinste solche Zeit, die mindestens min_schlaf_s nach "jetzt" liegt.
// Bei Intervallen, die 24 h ganzzahlig teilen (5, 10, 15, 20, 30, 60, 120 min ...),
// liegt das Raster auf runden Uhrzeiten.
static inline uint32_t zs_naechste_weckzeit(uint32_t jetzt, uint16_t intervall_min,
                                            uint8_t slot, uint8_t abstand_s,
                                            uint16_t min_schlaf_s) {
  uint32_t I = (uint32_t)intervall_min * 60UL;
  if (I == 0) I = 300;
  uint32_t phase = ((uint32_t)slot * abstand_s + 1UL) % I;   // Slot * Abstand + 1, modulo I
  uint32_t frueheste = jetzt + min_schlaf_s;
  uint32_t k = frueheste / I;
  uint32_t t = k * I + phase;
  if (t < frueheste) t += I;
  return t;
}

/****************************************************************/
// Wann abfragen, was annehmen
/****************************************************************/
// rtc_ist_utc: 1, wenn die RTC schon einmal per Netz gestellt wurde
// letzter_sync / letzter_versuch: Unix-Zeit (RTC), 0 = nie
static inline uint8_t zs_abgleich_faellig(uint32_t jetzt, uint32_t letzter_sync,
                                          uint32_t letzter_versuch, uint8_t rtc_ist_utc,
                                          uint16_t intervall_h, uint16_t wiederholung_min) {
  // Uhr unplausibel zurückgesprungen (z. B. nach POR): sofort
  if ((letzter_versuch != 0 && jetzt < letzter_versuch) || (letzter_sync != 0 && jetzt < letzter_sync)) return 1;
  // nach erfolglosem Versuch Pause einhalten
  uint8_t pause_vorbei = (letzter_versuch == 0) || (letzter_versuch <= letzter_sync) ||
                         (jetzt - letzter_versuch >= (uint32_t)wiederholung_min * 60UL);
  if (!rtc_ist_utc || letzter_sync == 0) return pause_vorbei;
  if (jetzt - letzter_sync >= (uint32_t)intervall_h * 3600UL) return pause_vorbei;
  return 0;
}

// Große Korrekturen bei schon synchroner Uhr nur annehmen, wenn die vorige (abgelehnte)
// Antwort dieselbe Korrektur verlangt hat (+/- ZS_GLEICH_S). Zwei unabhängige,
// übereinstimmende Netzzeiten = die eigene Uhr ist falsch, nicht das Netz.
#define ZS_GLEICH_S 5
static inline uint8_t zs_korrektur_annehmen(uint8_t rtc_ist_utc, int64_t korrektur_ms,
                                            uint8_t hat_vorige, int32_t vorige_korrektur_s,
                                            uint32_t max_sprung_s) {
  if (!rtc_ist_utc) return 1;
  int64_t betrag = korrektur_ms < 0 ? -korrektur_ms : korrektur_ms;
  if (betrag <= (int64_t)max_sprung_s * 1000) return 1;
  if (!hat_vorige) return 0;
  int64_t d = korrektur_ms / 1000 - (int64_t)vorige_korrektur_s;
  if (d < 0) d = -d;
  return d <= ZS_GLEICH_S;
}

// Ist die RTC beim Wecken plausibel? Erwartet wird ein Wecken zur geplanten Zeit
// (RTC-Alarm) oder früher (Taster, max. fruehestens_s vorher). Liegt die Uhr deutlich
// danach oder weit davor, hat jemand sie verstellt (System-Check, Selbsttest, Flashen
// mit anderer Firmware) -> nicht mehr als abgeglichen betrachten.
static inline uint8_t zs_uhr_plausibel(uint32_t jetzt, uint32_t geplant,
                                       uint32_t fruehestens_s, uint32_t spaetestens_s) {
  if (geplant == 0) return 0;
  if (jetzt > geplant + spaetestens_s) return 0;
  if (jetzt + fruehestens_s < geplant) return 0;
  return 1;
}

// Prüfwort für die ZS-Backup-Register (Magic + Version + XOR über die Daten)
#define ZS_BKP_MAGIC 0x5A530002UL   // "ZS", Layout-Version 2
static inline uint32_t zs_pruefwort(const uint32_t *r, uint8_t n) {
  uint32_t x = ZS_BKP_MAGIC;
  for (uint8_t i = 0; i < n; i++) x ^= (r[i] + 0x9E3779B9UL * (i + 1)) ^ (r[i] >> 7);
  return x;
}

// Plausible Zeit seit dem Uplink-Ende (MCCI tLocal) bis zur Auswertung
static inline uint8_t zs_vergangen_ok(int32_t vergangen_ms) {
  return vergangen_ms >= 0 && vergangen_ms <= 15000;
}

// Gangabweichung der RTC in ppm (positiv = RTC läuft vor)
// korrektur_ms = Netzzeit - RTC-Zeit beim Abgleich
static inline float zs_gang_ppm(int64_t korrektur_ms, uint32_t sekunden_seit_sync) {
  if (sekunden_seit_sync < 600) return 0.0f;
  return (float)(-korrektur_ms) * 1000.0f / (float)sekunden_seit_sync;
}

#endif  // BEELOGGER_ZEITSYNC_H

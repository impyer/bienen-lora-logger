/****************************************************************/
// ZS: Zeitabgleich per LoRaWAN DeviceTimeReq (MCCI LMIC) und Weckraster
/****************************************************************/
// 08.10.2026 Testversion, Review-Stand 2
//
// Ablauf:
//  1. Daten_Senden(): ist ein Abgleich fällig, hängt zs_abfrage_vorbereiten() die
//     Zeitabfrage (DeviceTimeReq, 1 Byte) an das normale Datenpaket an.
//  2. Das Netz antwortet im selben Empfangsfenster (RX1 nach 1 s oder RX2 nach 2 s).
//     MCCI ruft zs_netzzeit_callback() vor EV_TXCOMPLETE auf.
//  3. Nach dem Senden stellt zs_abfrage_auswerten() die RTC auf UTC.
//  4. Alarm_konfigurieren() berechnet die nächste Weckzeit mit zs_weckzeit():
//     festes Raster in UTC plus LOGGER_SLOT * SLOT_ABSTAND_S + 1 s.
//
// Ohne Antwort läuft alles weiter wie bisher, nur ohne Korrektur.
//
// Backup-Register (STM32F4, 32 bit):
//  11 letzter erfolgreicher Abgleich     14 geplante Weckzeit (Plausibilität beim Wecken)
//  12 letzte Abfrage                     15 zuletzt abgelehnte Korrektur [s]
//  13 Status (UTC, Zähler, Korrektur)    16 Prüfwort über 11-15 (Magic + Version)

#if defined(STM32F1xx) && ZEITSYNC_aktiv
#error "ZS: Zeitabgleich nur für STM32F4 (BlackPill) vorgesehen, Backup-Register 11-16 fehlen beim F1"
#endif

#if ZEITSYNC_aktiv && !defined(ARDUINO_LMIC_VERSION)
#error "ZS: Zeitabgleich braucht die MCCI LoRaWAN LMIC library"
#endif

#if ZEITSYNC_aktiv && defined(LMIC_ENABLE_DeviceTimeReq) && (LMIC_ENABLE_DeviceTimeReq == 0)
#error "ZS: LMIC_ENABLE_DeviceTimeReq ist in der MCCI-Konfiguration abgeschaltet"
#endif

#define ZS_BKP_ERSTES         11    // 11 ... 15 Daten, 16 Prüfwort
#define ZS_BKP_ANZAHL         5
#define ZS_BKP_PRUEF          16

#define ZS_MIN_SCHLAF_S       120   // mindestens 2 min bis zum nächsten Wecken
#define ZS_WECK_FRUEH_S       (6UL * 3600UL)  // Taster-Wecken bis 6 h vor dem Plan ist plausibel
#define ZS_WECK_SPAET_S       600UL           // mehr als 10 min nach dem Plan: Uhr verstellt
#define ZS_WARTE_MAX_MS       1500UL          // Warten auf die volle Sekunde, Obergrenze

static volatile uint8_t zs_antwort = 0;   // 0 = keine Abfrage/kein Callback, 1 = Zeit erhalten, 2 = ohne Zeit
static uint8_t zs_abfrage_laeuft = 0;
static lmic_time_reference_t zs_ref;


/**
  @brief zs_rtc_jetzt() - RTC-Zeit lesen, ohne veraltetes Datum
  STM32RTC 1.3.7 liest in getEpoch() erst das Datum, dann die Uhrzeit. Das Lesen der
  Uhrzeit sperrt die Datums-Schattenregister bis zum nächsten Datumslesen (STM32F4 HAL,
  HAL_RTC_GetTime). Ein späterer getEpoch() kann dann nach Mitternacht das alte Datum
  liefern. Deshalb vorher und nachher das Datum lesen (entsperren) und warten, bis die
  Schattenregister nachgeladen sind (> 2 RTCCLK = 61 us).
*/
uint32_t zs_rtc_jetzt(uint32_t *ms_teil) {
  (void)rtc_stm.getDay();
  delayMicroseconds(80);
  uint32_t t = (uint32_t)rtc_stm.getEpoch(ms_teil);
  (void)rtc_stm.getDay();
  if (t % ZS_SEK_PRO_TAG == 0) {        // Datum genau beim Tageswechsel gelesen: wiederholen
    delayMicroseconds(80);
    t = (uint32_t)rtc_stm.getEpoch(ms_teil);
    (void)rtc_stm.getDay();
  }
  return t;
}


/**
  @brief zs_netzzeit_callback() - wird von MCCI-LMIC vor EV_TXCOMPLETE aufgerufen
  Hier nur die Zeitreferenz sichern, keine Ausgaben (Funk-Timing).
*/
void zs_netzzeit_callback(void *pUserData, int flagSuccess) {
  (void)pUserData;
  if (flagSuccess == 1 && LMIC_getNetworkTimeReference(&zs_ref) == 1) {
    zs_antwort = 1;
  } else {
    zs_antwort = 2;
  }
}


#if ZEITSYNC_aktiv
/**
  @brief zs_vergangen_ms() / zs_netz_jetzt_ms() - Netzzeit "jetzt" aus der MCCI-Referenz
*/
static int32_t zs_vergangen_ms() {
  return (int32_t)osticks2ms(os_getTime() - zs_ref.tLocal);
}
static int64_t zs_netz_jetzt_ms() {
  return zs_netz_utc_ms(zs_ref.tNetwork, (uint32_t)zs_vergangen_ms());
}
#endif


/**
  @brief zs_abfrage_vorbereiten() - vor LMIC_setTxData2() aufrufen
  @return 1, wenn eine Zeitabfrage angehängt wurde
*/
uint8_t zs_abfrage_vorbereiten() {
  zs_antwort = 0;
  zs_abfrage_laeuft = 0;
#if ZEITSYNC_aktiv
  uint32_t jetzt = zs_rtc_jetzt(NULL);
  uint8_t faellig = zs_abgleich_faellig(jetzt, zs_letzter_sync, zs_letzter_versuch, zs_rtc_ist_utc,
                                        ZEITSYNC_INTERVALL_H, ZEITSYNC_WIEDERHOLUNG_MIN);
#if ZEITSYNC_TEST
  faellig = 1;
#endif
  if (faellig) {
    LMIC_requestNetworkTime(zs_netzzeit_callback, NULL);
    zs_letzter_versuch = jetzt;
    zs_abfrage_laeuft = 1;
    debugprintlnF("ZS: Zeitabfrage angehaengt");
  }
#endif
  return zs_abfrage_laeuft;
}


/**
  @brief zs_abfrage_auswerten() - nach dem Senden, vor LMIC_reset() aufrufen
  stellt die RTC auf UTC, wenn das Netz geantwortet hat
*/
void zs_abfrage_auswerten() {
#if ZEITSYNC_aktiv
  if (!zs_abfrage_laeuft) return;
  zs_abfrage_laeuft = 0;

  if (zs_antwort != 1) {
    zs_fehler_zaehlen("keine Netzzeit erhalten");
    return;
  }
  if (!zs_vergangen_ok(zs_vergangen_ms())) {
    zs_fehler_zaehlen("Zeitreferenz unplausibel");
    return;
  }

  // RTC und Netzzeit möglichst im selben Moment lesen
  uint32_t rtc_ms_teil = 0;
  uint32_t rtc_s = zs_rtc_jetzt(&rtc_ms_teil);
  int64_t netz_ms = zs_netz_jetzt_ms();
  int64_t rtc_ms = (int64_t)rtc_s * 1000 + rtc_ms_teil;
  int64_t korrektur_ms = netz_ms - rtc_ms;

  uint32_t netz_s = (uint32_t)(netz_ms / 1000);
  if (!zs_netzzeit_gueltig(netz_s)) {
    zs_fehler_zaehlen("Netzzeit ausserhalb 2024...2033");
    return;
  }

  if (!zs_korrektur_annehmen(zs_rtc_ist_utc, korrektur_ms, zs_abgelehnt > 0, zs_vorige_korr_s,
                             ZEITSYNC_MAX_SPRUNG_S)) {
    if (zs_abgelehnt < 15) zs_abgelehnt++;
    zs_vorige_korr_s = (int32_t)(korrektur_ms / 1000);
    debugprintF("ZS: grosse Korrektur, erst bei Bestaetigung uebernommen: ");
    zs_zeige_ms(korrektur_ms);
    debugprintln(" ");
    debugflush();
    return;
  }

  // auf die nächste volle Sekunde warten (max. 1 s), dann stellen
  uint32_t ziel_s = zs_naechste_volle_sekunde(netz_ms);
  int64_t ziel_ms = (int64_t)ziel_s * 1000;
  uint32_t m0 = millis();
  while (zs_netz_jetzt_ms() < ziel_ms) {
    if (millis() - m0 > ZS_WARTE_MAX_MS) {
      zs_fehler_zaehlen("Warten auf volle Sekunde abgebrochen");
      return;
    }
  }
  int64_t sprung_ms = korrektur_ms;   // tatsächlicher Sprung der RTC
#if ZEITSYNC_TEST && ZEITSYNC_TEST_VERSTELLEN_S
  rtc_stm.setEpoch(ziel_s + ZEITSYNC_TEST_VERSTELLEN_S);   // Test: absichtlich falsch stellen
  sprung_ms += (int64_t)ZEITSYNC_TEST_VERSTELLEN_S * 1000;
#else
  rtc_stm.setEpoch(ziel_s);
#endif

  // Einschaltdauer time_on (Startzeitpunkt in RTC-Sekunden) mitverschieben
  int32_t sprung_s = (int32_t)((sprung_ms >= 0 ? sprung_ms + 500 : sprung_ms - 500) / 1000);
  time_on = (uint32_t)((int32_t)time_on + sprung_s);

  // Diagnose
  float ppm = 0.0f;
  if (zs_rtc_ist_utc && zs_letzter_sync != 0 && netz_s > zs_letzter_sync) {
    ppm = zs_gang_ppm(korrektur_ms, netz_s - zs_letzter_sync);
  }
  int64_t kd = korrektur_ms / 100;
  if (kd > 32767) kd = 32767;
  if (kd < -32768) kd = -32768;
  zs_letzte_korrektur_ds = (int16_t)kd;

  zs_rtc_ist_utc = 1;
  zs_letzter_sync = ziel_s;
  zs_letzter_versuch = ziel_s;
  zs_fehler = 0;
  zs_abgelehnt = 0;
  zs_vorige_korr_s = 0;

  debugprintF("ZS: Uhr gestellt, Korrektur: ");
  zs_zeige_ms(korrektur_ms);
  debugprintF("  Gang [ppm]: ");
  debugprintln(ppm);
  (void)ppm;
  zs_zeige_zeit(ziel_s);
#endif
}


void zs_fehler_zaehlen(const char *grund) {
  (void)grund;
  if (zs_fehler < 255) zs_fehler++;
  debugprintF("ZS: ");
  debugprint(grund);
  debugprintF(", Fehler in Folge: ");
  debugprintln(zs_fehler);
  debugflush();
}


/**
  @brief zs_weckzeit() - nächste Weckzeit (RTC-Zeit) für Alarm_konfigurieren()
*/
uint32_t zs_weckzeit(uint32_t ttim, uint8_t IntervallMinuten) {
  uint32_t tt;
#if ZEITSYNC_aktiv
  tt = zs_naechste_weckzeit(ttim, IntervallMinuten, LOGGER_SLOT, SLOT_ABSTAND_S, ZS_MIN_SCHLAF_S);
#else
  tt = ttim + (uint32_t)(IntervallMinuten * 60);  // Original
  tt = tt - tt % 300;
  tt--;
#endif
  zs_geplante_weckzeit = tt;
  return tt;
}


/**
  @brief zs_ortszeit_rtc() - Ortszeit aus RTC-Zeit
  vor dem ersten Abgleich läuft die RTC auf Ortszeit (System-Check), danach in UTC
*/
uint32_t zs_ortszeit_rtc(uint32_t rtc_zeit) {
#if ZEITSYNC_aktiv
  if (zs_rtc_ist_utc) return zs_ortszeit(rtc_zeit, ZEIT_ZONE_STD_H);
#endif
  return rtc_zeit;
}


void zs_zeige_ms(int64_t ms) {   // Ausgabe "+1.234 s" ohne 64-bit-print
  (void)ms;
#if myDEBUG
  char buff[24];
  int64_t b = ms < 0 ? -ms : ms;
  snprintf(buff, sizeof(buff), "%c%lu.%03u s", ms < 0 ? '-' : '+',
           (unsigned long)(b / 1000), (unsigned)(b % 1000));
  debugprint(buff);
#endif
}


void zs_zeige_zeit(uint32_t t) {
  (void)t;
#if myDEBUG
  char buff[48];
  time_t tt = t;
  strftime(buff, sizeof(buff), "%d.%m.%Y %H:%M:%S", gmtime(&tt));
  debugprint(buff);
  if (zs_rtc_ist_utc) {
    tt = zs_ortszeit(t, ZEIT_ZONE_STD_H);
    strftime(buff, sizeof(buff), " UTC = %H:%M:%S Ortszeit", gmtime(&tt));
    debugprintln(buff);
  } else {
    debugprintlnF(" (RTC noch nicht abgeglichen)");
  }
  debugflush();
#endif
}


/**
  @brief zs_daten_sichern() / zs_daten_holen() / zs_ruecksetzen()
  Backup-Register 11-16; aufgerufen aus save_data_to_ram() / get_data_from_ram()
*/
void zs_daten_sichern() {
#if ZEITSYNC_aktiv
  uint32_t r[ZS_BKP_ANZAHL];
  r[0] = zs_letzter_sync;
  r[1] = zs_letzter_versuch;
  r[2] = (zs_rtc_ist_utc ? 1UL : 0UL)
         | ((uint32_t)(zs_abgelehnt & 0x0F) << 4)
         | ((uint32_t)zs_fehler << 8)
         | ((uint32_t)(uint16_t)zs_letzte_korrektur_ds << 16);
  r[3] = zs_geplante_weckzeit;
  r[4] = (uint32_t)zs_vorige_korr_s;
  for (uint8_t i = 0; i < ZS_BKP_ANZAHL; i++) setBackupRegister(ZS_BKP_ERSTES + i, r[i]);
  setBackupRegister(ZS_BKP_PRUEF, zs_pruefwort(r, ZS_BKP_ANZAHL));
#endif
}

void zs_daten_holen() {
#if ZEITSYNC_aktiv
  uint32_t r[ZS_BKP_ANZAHL];
  for (uint8_t i = 0; i < ZS_BKP_ANZAHL; i++) r[i] = getBackupRegister(ZS_BKP_ERSTES + i);
  if (getBackupRegister(ZS_BKP_PRUEF) != zs_pruefwort(r, ZS_BKP_ANZAHL)) {
    zs_ruecksetzen();
    zs_hinweis = 1;   // Ausgabe erst später, Serial ist hier noch nicht gestartet
    return;
  }
  zs_letzter_sync = r[0];
  zs_letzter_versuch = r[1];
  zs_rtc_ist_utc = (uint8_t)(r[2] & 0x01);
  zs_abgelehnt = (uint8_t)((r[2] >> 4) & 0x0F);
  zs_fehler = (uint8_t)((r[2] >> 8) & 0xFF);
  zs_letzte_korrektur_ds = (int16_t)(uint16_t)(r[2] >> 16);
  zs_geplante_weckzeit = r[3];
  zs_vorige_korr_s = (int32_t)r[4];

  // Wurde die Uhr seit dem Einschlafen von außen verstellt?
  if (zs_rtc_ist_utc &&
      !zs_uhr_plausibel(zs_rtc_jetzt(NULL), zs_geplante_weckzeit, ZS_WECK_FRUEH_S, ZS_WECK_SPAET_S)) {
    zs_rtc_ist_utc = 0;
    zs_hinweis = 2;
  }
#endif
}

void zs_ruecksetzen() {
  zs_letzter_sync = 0;
  zs_letzter_versuch = 0;
  zs_rtc_ist_utc = 0;
  zs_fehler = 0;
  zs_abgelehnt = 0;
  zs_letzte_korrektur_ds = 0;
  zs_geplante_weckzeit = 0;
  zs_vorige_korr_s = 0;
}

void zs_info() {
#if ZEITSYNC_aktiv
  if (zs_hinweis == 1) {
    debugprintlnF("  ZS: Backup-Daten ungueltig oder alte Version -> Zeitabgleich neu");
  }
  if (zs_hinweis == 2) {
    debugprintlnF("  ZS: Uhr passt nicht zur geplanten Weckzeit -> gilt als nicht abgeglichen");
  }
  zs_hinweis = 0;
  debugprintF("  ZS utc:"); debugprint(zs_rtc_ist_utc);
  debugprintF(" slot:"); debugprint(LOGGER_SLOT);
  debugprintF(" sync:"); debugprint(zs_letzter_sync);
  debugprintF(" err:"); debugprint(zs_fehler);
  debugprintF(" korr[ds]:"); debugprintln(zs_letzte_korrektur_ds);
  debugflush();
#endif
}

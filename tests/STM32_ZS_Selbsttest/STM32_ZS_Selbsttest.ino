/*
   STM32_ZS_Selbsttest - Test der Zeitabgleich-Logik direkt auf der BlackPill (STM32F411)

   Braucht nur die Arduino-IDE (gleiche Board-Einstellungen wie der beelogger-Sketch).
   Ausgabe: Serial1 (PA9/PA10, FTDI), 9600 Baud - wie beim beelogger.

   Teil 1: dieselben Testfälle wie am PC (tests/zs_testfaelle.h) auf dem echten Prozessor
   Teil 2: RTC-Test mit dem 32-kHz-Quarz:
           a) beginnt die RTC beim Stellen eine neue Sekunde? (bestimmt die Stell-Genauigkeit)
           b) Datum/Uhrzeit über die Sommerzeit-Umstellung, Rückrechnung UTC -> Ortszeit
           c) RTC-Alarm (MATCH_HHMMSS, wie im Sketch) kommt zur richtigen Sekunde
           d) optional: Gang der RTC gegen den 25-MHz-Quarz (GANGMESSUNG_MIN > 0)
           e) liefert getEpoch() nach Mitternacht ein veraltetes Datum (Schattenregister)?
              und: liest die Umgehung zs_rtc_jetzt() aus dem Logger-Sketch richtig?

   ACHTUNG: Der Test verstellt die RTC und löscht die ZS-Backup-Register 11-16.
   Danach wieder den beelogger-Sketch aufspielen; er stellt die Uhr beim ersten Senden neu.

   08.10.2026 ZS-Testversion
*/
#include <STM32RTC.h>
#include <backup.h>
#include "beelogger_zeitsync.h"
#include "zs_testvektoren.h"
#include "zs_testfaelle.h"

#define GANGMESSUNG_MIN 0     // z.B. 10: RTC 10 min gegen millis() vergleichen
#define AUSGABE Serial1

STM32RTC &rtc = STM32RTC::getInstance();
volatile uint32_t alarm_millis = 0;

void ausgabe(const char *s) { AUSGABE.println(s); AUSGABE.flush(); }

void alarm_cb(void *data) { (void)data; alarm_millis = millis(); }

// gleiche Funktion wie im Logger-Sketch (STM32_LORA_zeitsync.ino)
uint32_t zs_rtc_jetzt(uint32_t *ms_teil) {
  (void)rtc.getDay();
  delayMicroseconds(80);
  uint32_t t = (uint32_t)rtc.getEpoch(ms_teil);
  (void)rtc.getDay();
  if (t % ZS_SEK_PRO_TAG == 0) {
    delayMicroseconds(80);
    t = (uint32_t)rtc.getEpoch(ms_teil);
    (void)rtc.getDay();
  }
  return t;
}

// wartet auf den nächsten Sekundenwechsel der RTC, liefert millis() dabei
uint32_t auf_sekundenwechsel() {
  uint32_t s0 = rtc.getEpoch();
  while (rtc.getEpoch() == s0) { }
  return millis();
}

void setup() {
  AUSGABE.begin(9600);
  delay(1500);
  ausgabe("");
  ausgabe("=== ZS-Selbsttest beelogger (STM32) ===");

  // ---------- Teil 1 ----------
  uint32_t t0 = millis();
  int f1 = zs_tests_ausfuehren(ausgabe);
  char b[120];
  snprintf(b, sizeof(b), "Teil 1: %s (%lu ms)", f1 == 0 ? "OK" : "FEHLER", (unsigned long)(millis() - t0));
  ausgabe(b);

  // ---------- Teil 2 ----------
  rtc.setClockSource(STM32RTC::LSE_CLOCK);
  rtc.begin(false);
  enableBackupDomain();
  for (uint8_t i = 11; i <= 16; i++) setBackupRegister(i, 0);
  ausgabe("ZS-Backup-Register 11-16 geloescht");

  // a) Stellen mitten in einer Sekunde, danach Bruchteil lesen
  ausgabe("Teil 2a: RTC stellen und sofort Sekundenbruchteil lesen");
  const uint16_t versatz[] = { 100, 350, 600, 850 };
  uint8_t neustart = 0;
  for (uint8_t i = 0; i < 4; i++) {
    auf_sekundenwechsel();
    delay(versatz[i]);
    rtc.setEpoch(1791460800UL);          // 8.10.2026 12:00:00 UTC
    uint32_t ss = 0;
    rtc.getEpoch(&ss);
    uint32_t m0 = millis();
    auf_sekundenwechsel();
    uint32_t bis_naechste = millis() - m0;
    snprintf(b, sizeof(b), "  gestellt %u ms nach Sekundenwechsel: Bruchteil danach %lu ms, naechste Sekunde nach %lu ms",
             versatz[i], (unsigned long)ss, (unsigned long)bis_naechste);
    ausgabe(b);
    if (ss < 30 && bis_naechste > 950) neustart++;
  }
  ausgabe(neustart == 4 ? "  => RTC beginnt beim Stellen eine neue Sekunde: Stellgenauigkeit ca. 1 ms"
                        : "  => RTC behaelt die alte Sekundenphase: Stellfehler bis 1 s moeglich (siehe Anleitung)");

  // b) Sommerzeit-Ende 25.10.2026 01:00 UTC
  ausgabe("Teil 2b: Datum/Ortszeit ueber die Zeitumstellung");
  rtc.setEpoch(1792890000UL - 2);        // 25.10.2026 00:59:58 UTC
  delay(3500);
  uint32_t t = rtc.getEpoch();
  uint32_t ort = zs_ortszeit(t, 1);
  snprintf(b, sizeof(b), "  RTC %02u.%02u.%04u %02u:%02u:%02u UTC (erwartet 25.10.2026 01:00:01), Ortszeit %02u:%02u, Sommerzeit %u (erwartet 0)",
           rtc.getDay(), rtc.getMonth(), 2000 + rtc.getYear(), rtc.getHours(), rtc.getMinutes(), rtc.getSeconds(),
           zs_stunde(ort), (unsigned)((ort % 3600) / 60), zs_eu_sommerzeit(t));
  ausgabe(b);
  uint8_t ok_b = (t == 1792890001UL || t == 1792890002UL) && zs_stunde(ort) == 2 && !zs_eu_sommerzeit(t);
  ausgabe(ok_b ? "  => OK" : "  => FEHLER");

  // c) Alarm wie im Sketch (setAlarmEpoch, MATCH_HHMMSS)
  ausgabe("Teil 2c: RTC-Alarm");
  rtc.attachInterrupt(alarm_cb);
  auf_sekundenwechsel();
  uint32_t jetzt = rtc.getEpoch();
  uint32_t m_start = millis();
  alarm_millis = 0;
  rtc.setAlarmEpoch(jetzt + 5, rtc.MATCH_HHMMSS, 0);
  while (alarm_millis == 0 && millis() - m_start < 8000) { }
  if (alarm_millis) {
    snprintf(b, sizeof(b), "  Alarm nach %lu ms (erwartet ca. 5000)", (unsigned long)(alarm_millis - m_start));
    ausgabe(b);
    ausgabe((alarm_millis - m_start > 4900 && alarm_millis - m_start < 5100) ? "  => OK" : "  => FEHLER");
  } else {
    ausgabe("  => FEHLER: kein Alarm");
  }
  rtc.disableAlarm();
  rtc.detachInterrupt();

  // d) Gang gegen millis()
#if GANGMESSUNG_MIN > 0
  ausgabe("Teil 2d: Gangmessung laeuft ...");
  uint32_t m_a = auf_sekundenwechsel();
  uint32_t r_a = rtc.getEpoch();
  delay((uint32_t)GANGMESSUNG_MIN * 60000UL - 500);
  uint32_t m_b = auf_sekundenwechsel();
  uint32_t r_b = rtc.getEpoch();
  float ppm = ((float)(r_b - r_a) * 1000.0f - (float)(m_b - m_a)) / (float)(m_b - m_a) * 1e6f;
  snprintf(b, sizeof(b), "  RTC %lu s in %lu ms millis()", (unsigned long)(r_b - r_a), (unsigned long)(m_b - m_a));
  ausgabe(b);
  AUSGABE.print("  Gang RTC gegen 25-MHz-Quarz [ppm]: ");
  AUSGABE.println(ppm, 1);
  ausgabe("  (beide Quarze haben Toleranzen, nur grober Anhaltswert)");
#endif

  // e) Schattenregister über Mitternacht (25.10.2026 00:00:00 UTC = 1792886400)
  ausgabe("Teil 2e: Datum nach Mitternacht");
  rtc.setEpoch(1792886400UL - 3);            // 24.10.2026 23:59:57
  delay(1200);
  uint32_t e1 = rtc.getEpoch();              // vor Mitternacht, sperrt das Datum
  delay(3000);
  uint32_t e2 = rtc.getEpoch();              // nach Mitternacht, Bibliothek direkt
  delay(1000);
  rtc.getEpoch();                            // Datum wieder sperren
  delay(1000);
  uint32_t e3 = zs_rtc_jetzt(NULL);          // nach Mitternacht, mit Umgehung
  snprintf(b, sizeof(b), "  vor: %lu  getEpoch nachher: %lu  zs_rtc_jetzt: %lu  (richtig ab %lu)",
           (unsigned long)e1, (unsigned long)e2, (unsigned long)e3, 1792886400UL);
  ausgabe(b);
  ausgabe(e2 < 1792886400UL ? "  => getEpoch() liefert nach Mitternacht das alte Datum (Fehler der Bibliothek bestaetigt)"
                            : "  => getEpoch() hier ohne veraltetes Datum");
  ausgabe(e3 >= 1792886400UL && e3 < 1792886400UL + 10 ? "  => zs_rtc_jetzt() OK" : "  => zs_rtc_jetzt() FEHLER");

  ausgabe("=== Ende Selbsttest ===");
}

void loop() { }

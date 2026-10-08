# Testbericht TTN-Formatter + LoRa-Eingang — Review 2026-10-08

- **Reviewdatum:** 2026-10-08
- **Quellstand:** [f252677](https://github.com/impyer/bienen-lora-logger/commit/f2526776ee1ccfcefbc057846d6bf895b190b5b1); am Firmware-Folgecommit [d735f0f](https://github.com/impyer/bienen-lora-logger/commit/d735f0f99c7359bcabf2ad05a4c4314809afca04) keine Änderung am LoRa-Eingang festgestellt.
- **Bereich:** `formatter/formatter.js`, `formatter/ttn_formatter.min.js`, `server/lora/`, `tests/formatter/`, `tests/server/`, beelogger M.40.
- **Methode:** Statisches Schnittstellen- und Code-Review; vorhandene GitHub-Actions-Tests und Ende-zu-Ende-Testcode geprüft. **Kein Test gegen einen produktiven TTN-Webhook oder aktives BEEP.**
- **CI-Nachweis:** [Run 37789870212](https://github.com/impyer/bienen-lora-logger/actions/runs/37789870212), einschließlich Formatter unter Node.js/goja und PHP-Integration, erfolgreich.

## Architektur und positive Befunde

`Logger (FPort 1 Legacy / FPort 2 V2) → TTN-Formatter → TTN-Uplink-JSON → lora_eingang.php → beelogger_log.php (EE-Datensatz) → CSV/BEEP`.

- V2 ist versioniert und kodiert optionale Werte über 32-Bit-Maske. Legacy-Port 1 bleibt verfügbar.
- Der eigene Webhook authentifiziert über `X-Bienen-Token` und ordnet `end_device_ids.device_id` einem lokalen beelogger-Verzeichnis zu.
- Zeitwahl: gültiger Gerätemesszeitpunkt (Status `zeit_ok`, maximal 900 s alt, maximal 30 s voraus), sonst `uplink_message.received_at` in UTC.
- Zusatzdaten inklusive RSSI/SNR, FPort, Framecounter, FFT, Firmware und Status liegen getrennt in `lora_zusatz.csv`. Raw-Uplink-Log optional.
- Der unveränderte beelogger-EE-Pfad erhält Gewichtskorrektur, Anmerkungen und Weitergabe an BEEP/ThingSpeak.
- Bestehende Tests enthalten FPort 1/2, wiederholte Nachricht, fehlende Zeit, ungültiges Token, fehlerhaften Formatter und eine DST-Testreihe.

## Befunde

### SRV26-01 — P0 — Winterzeit: Datensätze im Altserver verworfen

- **Fundstellen:** `server/lora/lora_eingang.php` (`le_ortszeit_text` / `M1`-Datensatz); `server/beelogger_M40_original/beelogger1/beelogger_log.php` (`strtotime($zeit)` und monotone Zeitprüfung); `tests/server/test_lora_eingang.sh` (Winterzeitfall).
- **Nachweis:** Der vorhandene Ende-zu-Ende-Test sendet sieben Messungen am **2026-10-25** über die doppelte 02-Uhr-Stunde. Erwartete Ist-Situation: **5 von 7 gespeichert**, zwei verworfen. Der Test ist derzeit absichtlich *grün*, weil er den bekannten Fehler als Erwartung kodiert.
- **Ursache:** UTC-Zeit wird vor dem Altserver in mehrdeutigen lokalen Zeittext umgewandelt; der Altserver kann die beiden unterschiedlichen UTC-Zeitpunkte nicht mehr auseinanderhalten.
- **Akzeptanz:** Bei sieben eindeutigen, fortlaufenden UTC-Messzeitpunkten werden sieben korrekte Datensätze mit richtigem Unix-Timestamp gespeichert; Doppelmeldungen bleiben idempotent. Die Zusatzdatei allein ersetzt keine korrekte `week.csv`.
- **Status:** Reproduzierter, dokumentierter Integrationsfehler; offen, zeitkritisch vor dem 2026-10-25.

### SRV26-02 — P1 — HTTP 200 auch bei nicht gespeichertem Datensatz

- **Fundstelle:** `server/lora/lora_eingang.php`, finale Antwort `le_ende(200, 'nicht gespeichert ...')`; ebenso `kein decoded_payload`.
- **Risiko:** Ein absichtlich ignoriertes Duplikat und ein unerwarteter Speicherverlust sind für den Transport über HTTP nicht unterscheidbar. Für erwartete Duplikate ist 200 sachgerecht; bei temporärem Ausfall darf ein Erfolg nicht vorgetäuscht werden.
- **Akzeptanz:** Status-/Retry-Strategie je Fall definieren und testen: gespeichert / schon gespeichert / ungültig / vorübergehender Speicherfehler / interner Upstream-Timeout. Wiederholungen dürfen nichts doppelt speichern.
- **Status:** Rückgabeverhalten im Code belegt; konkrete Zustellverluste auf dem Produktivsystem nicht gemessen.

### SRV26-03 — P1 — Speichererfolg mit Dateigröße + letzter CSV-Zeile nicht konkurenzsicher

- **Fundstelle:** `lora_eingang.php`, `filesize(week.csv)` vor/nach HTTP-Aufruf und `le_letzter_zeitstempel`.
- **Risiko:** Parallel laufende Webhooks können Dateiänderungen gegenseitig überdecken; ein Speichervorgang kann fälschlich als fehlgeschlagen bewertet werden.
- **Akzeptanz:** Entweder eindeutige Speicherquittung/ID aus der Speicherung oder zuverlässige Zuordnung des Datensatzes, auch bei zwei gleichzeitigen Webhooks. Kein Vertrauen auf „letzte Zeile“ allein.
- **Status:** Nachvollziehbare Race Condition aus Code; noch kein Parallelitätstest.

### SRV26-04 — P1 — Haupt- und Zusatzdaten nicht atomar

- **Fundstelle:** `lora_eingang.php`, separater Append nach dem Aufruf von `beelogger_log.php`; `fopen`-Fehler wird still toleriert.
- **Risiko:** Haupt-CSV geschrieben, Zusatz-CSV fehlt oder umgekehrt. Duplikate können mehrere Zusatzzeilen produzieren.
- **Akzeptanz:** Eindeutige Event-/Mess-ID und getrennte Statusfelder; Fehler beim Anhängen protokollieren, Wiederherstellungsstrategie definieren.
- **Status:** Aus dem Code belegt; kein Fehlerfall im Live-System nachgewiesen.

### SRV26-05 — P1 — BEEP/ThingSpeak bei abgelehnten Duplikaten prüfen

- **Fundstellen:** `beelogger_log.php`, EE-Pfad: `Auswertung(1)` gefolgt von `ExternDataOut()` und `Triggeralarme()`; Speicherprüfung innerhalb `Auswertung`.
- **Risiko:** Externe Ausgabe könnte auch ohne neuen CSV-Datensatz ausgelöst werden. **Noch kein nachgewiesener Doppelversand**.
- **Akzeptanz:** Aktivierte Testintegration, mehrfacher identischer Uplink, veraltetes Paket und Ablehnung; exakt definierte Anzahl externer Aktionen.
- **Status:** Plausibles Integrationsrisiko, HiL/Server-Test ausstehend.

### SRV26-06 — P2 — Interner HTTP-Selbstaufruf und Hosting

- **Fundstelle:** `lora_eingang.php`, `curl_init` auf dieselbe beelogger-Webinstallation, 20-s-Zeitlimit.
- **Risiko:** Zu wenige PHP-Worker, TLS-/DNS-Probleme und langsame Reaktionen führen zu 502/Timeout; Rückruf muss gegen reale Webserver-Konfiguration validiert werden.
- **Akzeptanz:** Realer Deploymenttest mit mindestens zwei gleichzeitig eintreffenden Nachrichten; TLS-Prüfung aktiv.
- **Status:** Offene Betriebsannahme.

### FMT26-01 — P2 — V2-Formatinkonsistenzen hart prüfen

- **Fundstellen:** `formatter/formatter.js`, `docs/funkformat-v2.md`.
- **Risiko:** V2 erlaubt variable FFT-Bandanzahl, obwohl fachlich sechs Bänder definiert sind. Zustand `zeit_ok` und Messzeitfeld sollten hinsichtlich Konsistenz geprüft werden.
- **Akzeptanz:** Versions-/Feldregeln dokumentieren und Testvektoren für 0, 6, 12, >12 Bänder sowie Zeitstatus/Messzeit kombinieren.
- **Status:** Robustheitsvorschlag; kein reproduzierter Normalbetriebsfehler.

## Reproduktion im Repository

```bash
node tests/formatter/test_formatter.js
node tests/formatter/test_formatter.js formatter/ttn_formatter.min.js
php tests/server/test_lora_funktionen.php
bash tests/server/test_lora_eingang.sh
```

Voraussetzungen des Ende-zu-Ende-Skripts: Node, PHP mit cURL, unzip, curl. Testserver startet lokal mit vier PHP-Workern. Der **Winterzeit-Test wird erst nach Bugfix auf 7/7 umgestellt**; 5/7 ist aktuell die absichtlich dokumentierte Fehlerreferenz.

**Review-Entscheid:** Formatter für kontrollierten Feldtest geeignet. Server-Eingang im Labortest geeignet, für unbeaufsichtigten Betrieb erst Fehlerpfade und DST lösen.

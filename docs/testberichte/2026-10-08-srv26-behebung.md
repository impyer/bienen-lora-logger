# Behebung SRV26-02/03/04/05/07/08 — LoRa-Eingang und eigene Server-Fassung

- **Datum:** 2026-10-08
- **Grundlage:** Review [main 5c1b847](2026-10-08-main-5c1b847-regression.md), Abschnitt 5 „Priorisierte Übergabe“, Punkte 1–4
- **Bearbeitet von:** Claude (Cowork), Prüfung lokal im Linux-Arbeitsbereich
- **Geprüfter Stand:** Arbeitsstand vor dem Commit; die Commit-ID trägt Philipp beim Einchecken nach: `________`
- **Prüfarten:** Host-Unit-Tests (PHP), Ende-zu-Ende mit zwei PHP-Testservern und den echten beelogger-Skripten, Browser (Chromium 1194 über Playwright 1.56.1), Gegenprobe ohne Korrektur.
- **Nicht geprüft:** produktives TTN/LoRaWAN, echter BEEP-Server (api.beep.nl), Apache/PHP-FPM, GitHub-Actions-Lauf. Den CI-Lauf belegt erst der nächste Push.

## 1. Ergebnis je Befund

| ID | Ursache | Änderung | Nachweis | Status |
|---|---|---|---|---|
| **SRV26-07** | UTC-Modus hing an `beelogger_zeitzone.php` im Hauptordner, nicht am Ziel-Endpunkt | `le_utc_faehig()`: Merkmal `$BL_UTC_FAEHIG=1;` im `beelogger_log.php` **des Ziel-Loggers**. `'auto'`: Merkmal fehlt → Ortszeit, Protokoll „Mischinstallation“. `true`: Merkmal fehlt → zurückstellen (202), nicht speichern. | E2E-Matrix, 7 Fälle: alte/eigene `log.php` × Merkmal im Hauptordner ja/nein × `utc_zeit` auto/true/false; gespeicherter Zeitstempel = Messzeit in allen speichernden Fällen; zurückgestellte Nachricht nach Update nachgeholt. Unit: Merkmal in eigener Fassung vorhanden, im Original nicht. | Host/E2E reproduziert, behoben |
| **SRV26-05** | Original bereitet BEEP/ThingSpeak vor der Speicherentscheidung vor; `ExternDataOut()` sendet auch abgelehnte Datensätze. ID-Prüfung mit `OR` immer wahr. | `eigen_anpassen.py`: bei `$store=0` wird der vorbereitete Eintrag zurückgenommen; `AND` statt `OR` bei BEEP-ID und ThingSpeak-API. Zusätzlich: Duplikate erreichen beelogger gar nicht mehr (Kennung, s. SRV26-03). | BEEP-Nachbildung über den vorhandenen Einhängepunkt `BeepApiHeader.php`: neue Messung → genau 1 Übertragung (mit `key` und `time`); gleiche Zeit, anderer Inhalt → 0; identische Nachricht → 0; Platzhalter-ID → 0. **Gegenprobe:** Ohne die Korrektur schlagen 3 dieser Prüfungen fehl. | Host/E2E reproduziert, behoben (nur eigene Fassung) |
| **SRV26-03** | Speicherprüfung über Dateigröße + letzte Zeile ohne Ausschluss gleichzeitiger Aufrufe | Sperre je Logger (`flock` auf `lora_log/sperre_<verz>.lock`) um Duplikatprüfung, Aufruf, Speicherprüfung und Zusatzdatei. Kennung je Nachricht: SHA-1 aus Gerät, FPort, FCnt, `frm_payload`, `received_at`. | 4 gleiche Webhooks gleichzeitig → 1× gespeichert, 3× doppelt, je 1 Zeile in `week.csv` und `lora_zusatz.csv`. 4 verschiedene gleichzeitig → jede Antwort stimmt mit der Datei überein (Zahl „gespeichert“ = neue Zeilen). | E2E reproduziert, behoben |
| **SRV26-04** | Zusatzdatei getrennt geschrieben, Fehler still toleriert; Duplikate erzeugten mehrere Zusatzzeilen | Schreibfehler (`fopen`/`fputcsv`/`fflush`) → Protokoll `zusatz_fehler` mit der Zeile, Warnung in der Antwort. Duplikate werden vor dem Schreiben erkannt. | E2E: doppelte Nachricht → genau 1 Zusatzzeile. Schreibfehler injiziert (`lora_zusatz.csv` als Verzeichnis): Hauptdatensatz gespeichert, Warnung in der Antwort, `zusatz_fehler` mit Zeile im Protokoll. Volles Dateisystem nicht geprüft. | E2E reproduziert, behoben |
| **SRV26-02** | 200 auch bei Fehlern; keine Wiederholung | Ergebnisklassen `gespeichert`/`abgelehnt`/`doppelt`/`ignoriert` (200). Vorübergehende Fehler → Nachricht in `lora_log/nachholen/`, Antwort **202**; `lora_nachholen.php` (cron) verarbeitet nach. 5xx nur, wenn auch das Zwischenspeichern scheitert. | E2E: beelogger nicht erreichbar → 202, genau 1 Datei auch bei Wiederholung; nach Behebung `lora_nachholen.php` → gespeichert, Datei gelöscht, erneute Zustellung „doppelt“; Web-Aufruf des Nachholskripts → 403. | E2E reproduziert, behoben |
| **SRV26-08** | Playwright in der CI nicht installiert, Browserprüfung übersprungen | CI installiert `playwright@1.56.1` + Chromium; `BROWSER_PFLICHT=1` macht die Prüfung verpflichtend. | Lokal: ohne Playwright und mit Pflicht → Test schlägt fehl (67/68); mit Playwright 1.56.1 → alle bestanden. | lokal nachgewiesen, CI-Lauf offen |

### Abweichung von der Empfehlung im Review (SRV26-02)

Das Review verlangt, vorübergehende Fehler nicht als Erfolg zu melden. Umgesetzt ist **202 Accepted** mit eigenem Zwischenspeicher statt 5xx. Gründe:

1. The Things Stack wiederholt einen einzelnen Webhook nach Fehlerantwort nach meinem Stand nicht. Das ist aus dem TTS-Quelltext abgeleitet; ein Retry pro Nachricht wurde nicht gefunden.
2. Gehäufte Fehlerantworten können den Webhook abschalten. Dann gehen auch alle folgenden Nachrichten verloren.

202 meldet also ehrlich „angenommen, noch nicht gespeichert“, und die Wiederholung liegt dort, wo sie wirken kann. **[P]** Verhalten von TTS bei 4xx/5xx mit TTN prüfen.

### Hinweis zur Kennung

FCnt allein ist keine Kennung: Der Musterlogger setzt ihn bei 16384 bewusst zurück (ABP). Mit `received_at` und Nutzdaten ist eine Wiederholung derselben Nachricht eindeutig, ein neuer Uplink mit gleichem FCnt dagegen nicht. Unit-Test: gleicher FCnt, anderer Empfang → verschiedene Kennung.

## 2. Testergebnisse (lokal, Arbeitsstand)

| Prüfung | Ergebnis |
|---|---|
| `php tests/server/test_lora_funktionen.php` | 59/59 |
| `VARIANTE=eigen BROWSER_PFLICHT=1 bash tests/server/test_lora_eingang.sh` | 73/73 (Browser: Zeitachse steigend, keine JS-Fehler) |
| `VARIANTE=original bash tests/server/test_lora_eingang.sh` | 56/56 (Winterzeit absichtlich 5/7) |
| Gegenprobe SRV26-05 ohne Korrektur | die 3 BEEP-Prüfungen schlagen fehl (Lauf mit damals 70 Prüfungen: 67/70) |
| Gegenprobe SRV26-08: Pflicht ohne Playwright | 67/68 |
| `eigen_anpassen.py` aus dem Original-ZIP, Vergleich mit `server/beelogger_eigen/` | gleich |
| PHP-Syntax `server/lora/*.php`, `server/beelogger_eigen/**/*.php` | ohne Fehler |

## 3. Testumgebung: Befunde am Testaufbau

- Der eingebaute PHP-Server verteilt Verbindungen ungleichmäßig auf seine Arbeitsprozesse. Bei parallelen Webhooks landete der interne Aufruf von `beelogger_log.php` in einem Prozess, der an der Sperre wartete. Er hing dann bis zum curl-Zeitlimit (20 s). Lösung im Test: zweiter Testserver nur für `beelogger_log.php`. Auf Apache/PHP-FPM tritt das nicht auf; dort ist es aber **nicht gemessen**.
- OPcache im Testserver prüft geänderte Dateien nur alle 2 s. Der Test schreibt Konfiguration, `beelogger_ini.php` und `beelogger_log.php` während des Laufs um. Deshalb ist OPcache im Test aus.

## 4. Offen

- `SRV26-04` volles Dateisystem; eine Wiederherstellung der Zusatzzeile aus dem Protokoll ist nicht automatisiert.
- `SRV26-06` (interner HTTP-Selbstaufruf/Hosting) unverändert.
- Echter BEEP-Empfang, TTS-Verhalten bei Fehlerantworten, Webserver außerhalb von `php -S`.
- `HW26-*`, Firmware-HiL laut [Review 5c1b847](2026-10-08-main-5c1b847-regression.md).

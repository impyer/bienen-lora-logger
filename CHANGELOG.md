# Änderungen

## 2026-10-08 – LoRa-Eingang und Server nach Review 5c1b847 (SRV26-02/03/04/05/07/08)

- **SRV26-07:** Zeitbasis je Logger statt über eine Datei im Hauptordner. Der Eingang liest das Merkmal `$BL_UTC_FAEHIG=1;` im `beelogger_log.php` des Ziel-Loggers. Alte Fassung → Ortszeit (keine 2-h-Verschiebung), Meldung „Mischinstallation“. `utc_zeit=true` stellt Nachrichten an alte Endpunkte zurück.
- **SRV26-05:** eigene Fassung (eigen-utc-2) sendet BEEP/ThingSpeak nur für gespeicherte Datensätze; Prüfung der BEEP-ID/ThingSpeak-API mit `AND` statt `OR`.
- **SRV26-03/04:** Sperre je Logger; Kennung je Nachricht (Gerät, FPort, FCnt, Nutzdaten, `received_at`) → doppelte Nachrichten werden nicht erneut weitergegeben; Schreibfehler der Zusatzdatei werden protokolliert und gemeldet.
- **SRV26-02:** Ergebnisklassen `gespeichert`/`abgelehnt`/`doppelt`/`ignoriert`; vorübergehende Fehler → 202 und Zwischenspeicher, `lora_nachholen.php` (cron) verarbeitet nach.
- Aufteilung: `lora_eingang.php` (HTTP), `lora_verarbeitung.php` (Verarbeitung), `lora_nachholen.php` (Kommandozeile).
- **SRV26-08:** Playwright 1.56.1 fest in der CI; `BROWSER_PFLICHT=1` lässt den Test ohne Browser fehlschlagen.
- Tests: Ende-zu-Ende eigen 73, original 56 Prüfungen (neu: doppelt, 4 parallele Webhooks, Nachholen, Zeitbasis-Matrix, BEEP-Nachbildung, Schreibfehler Zusatzdatei); Unit-Tests 59. Gegenprobe: Ohne die SRV26-05-Korrektur schlagen 3 BEEP-Prüfungen fehl.

## 2026-10-08 – Eigene Server-Fassung mit UTC (eigen-utc-2)

- `server/beelogger_eigen/`: beelogger M.40 mit Unix-Zeitstempel (UTC) als maßgeblicher Zeit; Zeitzone wählbar in `beelogger_zeitzone.php`
  - `beelogger_log.php`: `UTC=1` beim EE-Weg (vom LoRa-Eingang gesetzt); Zeitstempel nicht mehr aus dem Ortszeit-Text zurückgerechnet
  - Grafik (`beelogger_show.php`, `beelogger_sml.php`, `beelogger_mobileWatch.php`): Zeitachse als ISO 8601 mit Versatz aus dem Zeitstempel, eindeutig auch in der doppelten Stunde; Stundenauswertung nach Zeitstempel
  - Hauptordner-Skripte (`beelogger_cron21.php`, `scraper.php`, `local_Updater.php`, `local_Split_Archivnotes.php`) setzen die Zeitzone; bisher galt die php.ini-Vorgabe
- `server/eigen_anpassen.py` erzeugt die Fassung aus dem Original-ZIP (jede Stelle muss genau einmal vorkommen); `server/eigen_utc.patch` zeigt den Unterschied
- LoRa-Eingang: `utc_zeit` (`'auto'`), Speicherprüfung über den Zeitstempel
- Tests: Ende-zu-Ende für beide Fassungen (eigen 29, original 22 Prüfungen), Grafik im Browser (Playwright); CI vergleicht die erzeugte Fassung mit dem Repo

## 2026-10-08 – Firmware 261010: Korrekturen nach Trockenprüfung (Review zu 261009)

- FFT-Spitze nur noch mit deutlichem Abstand zum Grundrauschen: `spitze_gueltig` erst ab 10 dB über dem Median der Linien 60–900 Hz (`BF_SNR_DB`). Gesamt- und Bandpegel werden weiter gesendet (`gueltig`). Vorher wurde bei Rauschen eine zufällige Linie als Spitze gemeldet.
- Spitzen, deren interpolierte Frequenz außerhalb von 60–900 Hz liegt (z. B. Ton bei 59 Hz), zählen nicht; es gilt die nächstgrößere Spitze im Bereich (Toleranz 0,5 Hz).
- ADC-Warteschleife mit Zeitgrenze (50 µs): Antwortet der ADC nicht, wird die FFT-Messung verworfen statt zu hängen.
- Unkalibrierte Waage (`Taragewicht` = 10) wird nicht mehr als 0,01 kg gesendet und nicht als Ausfall gemeldet.
- `#error` bei `FUNKFORMAT 2` mit mehr als 2 Waagen (Waage 3/4 haben im Funkformat v2 noch keine Bits).
- Mit `FUNKFORMAT 1` wird keine FFT gemessen (Ergebnis würde nicht gesendet; spart 1,25 s und 38 KB RAM).
- Tests: FFT 32 Prüfungen (neu: ±1 LSB, Rauschen ×20, Ton im Rauschen, 50/55/58/59/60/61 Hz); CI prüft zusätzlich den `#error`.

## 2026-10-08 – Firmware 261009: Funkformat v2 und FFT

- `FUNKFORMAT 2` (Vorgabe): Datensatz im Funkformat v2 auf FPort 2 (`STM32_LORA_v2.ino`, `funkformat_v2.h`)
  - 2. Innentemperatur mit Vorzeichen in 1/100 °C statt über `FeuchteIn`
  - keine CPU-Temperatur mehr als Ersatz für die Außentemperatur; Ausfälle als Zustandsbits
  - Messzeitpunkt (bei abgeglichener Uhr), Neustart-Grund, Firmware-ID nach Neustart und in jedem 96. Paket, CPU-Temperatur
- FFT des Mikrofons (`beelogger_Audio 1`): `bee_fft.h` nach `docs/fft-konzept.md`, Abtastung über ADC-Register und DWT-Takt
- Tests: C-Kodierer gegen den JavaScript-Referenz-Kodierer (303 Fälle), FFT mit künstlichen Signalen (21 Prüfungen); CI übersetzt drei Varianten
- Kommentar zur Gewichtsgröße im beelogger-Format richtiggestellt (2 Byte)

## 2026-10-08 – LoRa-Eingang am Server

- `server/lora/`: Webhook-Ziel für TTN; Messzeit aus dem Gerät bzw. `received_at`; Weitergabe über den EE-Weg an das unveränderte `beelogger_log.php`; Prüfung der Speicherung; `lora_zusatz.csv` und Protokoll
- Tests: 46 Unit-Tests (PHP), Ende-zu-Ende-Test mit den echten beelogger-Skripten M.40 und dem echten Formatter (22 Prüfungen, einschließlich Winterzeit-Nacht)

## 2026-10-08 – TTN-Formatter

- `formatter/formatter.js`: FPort 1 (beelogger, gleiche Ausgabe wie das Original) und FPort 2 (Funkformat v2)
- `docs/funkformat-v2.md`: Spezifikation 1.0
- Tests: Vergleich mit dem Original-Formatter, Goldenes Paket, Fehlerfälle, Prüfung in goja
- `formatter/ttn_formatter.min.js` (3846 Byte) zum Einfügen in TTN

## 2026-10-08 – Server-Analyse, FFT-Konzept, Verbesserungsliste

- Server-Skripte M.40 unverändert in `server/beelogger_M40_original/`
- `docs/server-analyse.md`: LoRa-Eingang geprüft (u. a. Winterzeit-Fehler, Aux2 = RSSI, Aux3 = Sketch-ID)
- `docs/fft-konzept.md`: 4-Hz-Teilung, Anti-Aliasing, dBFS, Bandpegel
- `docs/verbesserungen.md`: Liste der Notbehelfe mit Prioritäten
- Lastenheft: Mikrofon-Filter A2/A7 neu

## 2026-10-08 – Datenformat

- `docs/datenformat.md`: Daten weiter an den beelogger-Webserver, neues Funkformat auf FPort 2, Formatter liefert beelogger-Feldnamen

## 2026-10-08 – Lastenheft Platine 0.3

- Ra-01SH festgelegt (Datenblatt ausgewertet: Quarz statt TCXO, HF-Schalter über DIO2)
- neue Firmware ohne beelogger-Kompatibilität, neue Pinbelegung, USB-C
- Platine 121 × 121 mm nach Camdenboss-Zeichnung CBHUB_02 Rev. N

## 2026-10-08 – Lastenheft Platine 0.2

- Funk SX1262-Modul (E22-900M22S oder Ra-01SH), Firmware-Folgen beschrieben (RadioLib)
- Mikrofon GY-MAX4466 mit Entstörung, Akku per Kabel, Gehäuse CBHUB-02-GY mit Reserve

## 2026-10-08 – Firmware STM32_LORA_261008_ZS (Testversion, Review-Stand 2)

Grundlage: beelogger `STM32_LORA_260705`.

- MCCI LoRaWAN LMIC library statt LMIC-Arduino 1.5.0
- Zeitabgleich per LoRaWAN `DeviceTimeReq` einmal täglich, RTC läuft in UTC
- Weckraster `k × Intervall + LOGGER_SLOT × 10 s + 1 s`, Nachtfenster in Ortszeit mit EU-Sommerzeit
- 8 Kanäle, ADR aus
- RTC-Lesen ohne veraltetes Datum nach Mitternacht (STM32RTC 1.3.7, Schattenregister)
- Bei LMIC-Fehler schlafen statt Endlosschleife
- Plausibilitätsprüfung der Uhr beim Wecken; Prüfwort für die Backup-Register
- Frame-Counter beim Sendeversuch fortschalten
- Sketch-ID nur in jedem 10. Paket (Fehler im Original)
- Gerätedaten in `Config_Geraet.h` ausgelagert (nicht im Repo)

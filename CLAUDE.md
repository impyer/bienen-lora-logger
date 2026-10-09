# Hinweise für Claude / weitere Coding-Agents

**Projekt:** Autarker Bienenlogger (STM32F411/BlackPill mit RFM95 als bestehender Musterlogger; eigene SX1262-SMD-Platine erst im Entwurf). TTN → eigener PHP-LoRa-Eingang → beelogger M.40 → CSV/BEEP.

## Entwicklungsregelwerk (Version 0.1 – Diskussionsentwurf)

**Zuerst [`docs/entwicklung/README.md`](docs/entwicklung/README.md) und die fachlich betroffenen Regelabschnitte lesen.** Diese Regeln sind der vorgeschlagene Default für **Menschen und Coding-Agents**; sie wurden noch nicht formal verabschiedet und ersetzen keine dokumentierten Projektentscheidungen.

- **Sicherheit & Risiko:** Änderung D0–D3 einordnen; P0 bei Li-Ion/Lade-/Schutzschaltungen sperrt die jeweilige PCB-/Feldfreigabe. **Nie HiL simuliert als durchgeführt ausgeben**, Safety-Entscheide nicht selbst freigeben.
- **Quellwahrheit:** `hardware/kicad/*.py` führt für generierte KiCad-V0.1-Schaltpläne; `server/eigen_anpassen.py` führt für den abgeleiteten Server; `formatter/formatter.js` für den TTN-Formatter.
- **Nachweise:** Tests T0–T6 und Gates G0–G4 unterscheiden; genaue SHA, Konfiguration, Soll/Ist, Grenzen und offene Hardwaretests nennen. Bei Änderungen an Akku-/Power-Path zuvor die Gefahr- und Recovery-Analyse prüfen.
- **Open Source:** `LICENSE.md` beibehalten, Fremdurheber nennen. **GOV-01** ist offen: Python-Generatoren unter `hardware/kicad/` enthalten teilweise GPL-Header trotz Ordnerzuordnung CERN-OHL-S in `LICENSE.md`. Nicht stillschweigend re-lizenzieren.

## Bevor du Änderungen vornimmst

1. **Zuerst lesen:** [Testberichte und priorisierte Befunde](docs/testberichte/README.md), insbesondere [Schaltplan-Review V0.1 zu `fcd18fe`](docs/testberichte/2026-10-09-schaltplan-v01-review.md) und [Hardware-Review 0.4 zu `5c94e1b`](docs/testberichte/2026-10-09-hardware-04-review.md) und [früheres Review zu `5c1b847`](docs/testberichte/2026-10-08-main-5c1b847-regression.md). Konkrete Befunde: `FW26-*`, `SRV26-*`, `FMT26-*`, `ZS26-*`, `HW26-*`.
2. Lies für Firmware `firmware/README.md`, `docs/zeitabgleich.md`, `docs/funkformat-v2.md` und den genau betroffenen Quelltext.
3. **Versionsbezug beachten:** Die Reviews beziehen sich auf historische Commits, mit zusätzlichem aktuellen Review auf `5c1b847` vom 2026-10-08. Neueren Code zuerst gegenprüfen; gelöste Befunde nicht blind erneut beheben.
4. **Keine Sicherheit vortäuschen:** Reine Hosttests, SiL-/Modelltests, erfolgreiche STM32-Kompilierung, HiL und produktiver TTN-Feldtest getrennt benennen.
5. **Keine Geheimnisse committen:** `firmware/STM32_LORA_261008_ZS/Config_Geraet.h` und `server/lora/lora_config.php` bleiben lokal; keine Schlüssel/Token in Logs, Diffs oder Testvektoren.

## Projektentscheidungen beibehalten

- Bestehender Musterlogger: **MCCI-LMIC/ABP und RFM95**. Bewusst akzeptierter Frame-Counter-Reset bei 16384 mit TTN-Einstellung „Resets frame counters“; nicht eigenmächtig auf OTAA migrieren.
- RTC-Zeitabgleich per LoRaWAN DeviceTimeReq ist fachlich erwünscht; Sekundengenauigkeit genügt fürs Slotraster. RX1/RX2 auf Hardware sind als Feldtest offen.
- **FPort 1** = Legacy-Payload; **FPort 2** = neue Version mit Zustandsbits, Messzeit und FFT. Änderungen nur zusammen mit Formatter, Tests und Serververträgen.
- Server M.40 bleibt als unveränderte Referenz erhalten. Die neue generierte Server-Fassung `server/beelogger_eigen/` behebt den DST-Datenverlust im eigenen UTC-EE-Datenpfad (7/7). Eigene Änderungen **nur** in `server/eigen_anpassen.py`, der CI-Generierungsvergleich sichert den Stand. Der LoRa-Eingang prüft die UTC-Fähigkeit je Logger über das Merkmal `$BL_UTC_FAEHIG=1;` im `beelogger_log.php` (`SRV26-07`). Beim Deployment trotzdem alle Logger-Endpunkte aktualisieren (Kontrolle: `docs/server-utc.md`, Einspielen Schritt 5).
- Geplante **neue SMD-Platine SX1262/RadioLib** ist eine separate Entwicklung, nicht mit der Musterlogger-Firmware gleichsetzen. **KiCad V0.1 enthält bisher nur Akku-Platine und Hauptplatine/Versorgung, kein vollständiges Hardware-Schaltbild.** `HW26-07` … `-13` sind im Entwurf bearbeitet ([Behebung](docs/testberichte/2026-10-09-hw04-ci26-behebung.md)): Ladesperre TMP390 → CE (+5 … 42 °C), EEPROM entfällt (Sitzung im SPI-Flash), Solar-Teiler 3,3 MΩ/470 kΩ, Netzwerkkabel für BME280, 150 mA. Nachweise am Muster stehen aus; Zellen-Datenblattrevision der gekauften Zelle verbindlich prüfen. **Neuer P0 `SCH26-01`: mögliche fehlende Wiederladefähigkeit nach Schutz-FET-Abschaltung, weil TMP390 auf der geschützten Minus-Schiene hängt und CE ohne TMP390 HIGH bleibt; zuerst mit sicherem Zell-Emulator prüfen, nicht Lade-Sicherheitsfunktion umgehen.** Dazu `SCH26-02`/`SCH26-03` zur 10-MΩ-Freigabekette/Temperatur-Single-Fault und `SCH26-04` zur fehlenden ERC-CI.

## Reproduzierbare Checks

```bash
bash tests/alle_tests_linux.sh
# oder gezielt:
node tests/formatter/test_formatter.js
php tests/server/test_lora_funktionen.php
```

`tests/alle_tests_linux.sh` erzeugt Buildprodukte/`ff2_vektoren.h` lokal. Vor Commit unbeabsichtigte Artefakte prüfen. GitHub Actions auf `5c1b847` führt die neuen Firmware-Hosttests und drei Buildvarianten aus (`FW26-04` behoben). Der Playwright-Browsertest ist seit `6b83d` in CI installiert und verpflichtend (`BROWSER_PFLICHT=1`, `SRV26-08`). `CI26-01` (6/7 „gespeichert“) war uhrzeitabhängig: beelogger kürzt `week.csv` vor 08:00 Uhr Serverzeit, die alte Speichererkennung prüfte die Dateigröße. Behoben über `le_speicherung_erkannt()`; der E2E-Test läuft in der CI mit `SERVER_UHR` (libfaketime) um 05:00 und 14:00. Lokal: `SERVER_UHR="2026-10-09 05:00:00" bash tests/server/test_lora_eingang.sh` (braucht `faketime`).

## Arbeits- und Reviewprotokoll

- Behebe Findings mit Bezug zur **Befund-ID**, nachvollziehbarer Ursache und Akzeptanztest.
- Prüfe beim Änderungswunsch die Auswirkungen auf Sensorfehler, Stromverbrauch, Framecounter, Funkpaketlänge, TTN-Feldnamen, Datenzeit und Server-Antwort.
- Bei Hardwareabhängigkeit **HiL-Aufgabe konkret notieren**, keine Messwerte erfinden.
- Testbericht nach neuer Revision **als neue datierte Version** ergänzen; historische Ergebnisse und ihre Prüfbasis erhalten.

# Hinweise für Claude / weitere Coding-Agents

**Projekt:** Autarker Bienenlogger (STM32F411/BlackPill mit RFM95 als bestehender Musterlogger; eigene SX1262-SMD-Platine erst im Entwurf). TTN → eigener PHP-LoRa-Eingang → beelogger M.40 → CSV/BEEP.

## Bevor du Änderungen vornimmst

1. **Zuerst lesen:** [Testberichte und priorisierte Befunde](docs/testberichte/README.md), insbesondere [aktuelles Hardware-Review 0.4 zu `5c94e1b`](docs/testberichte/2026-10-09-hardware-04-review.md) und [früheres Review zu `5c1b847`](docs/testberichte/2026-10-08-main-5c1b847-regression.md). Konkrete Befunde: `FW26-*`, `SRV26-*`, `FMT26-*`, `ZS26-*`, `HW26-*`.
2. Lies für Firmware `firmware/README.md`, `docs/zeitabgleich.md`, `docs/funkformat-v2.md` und den genau betroffenen Quelltext.
3. **Versionsbezug beachten:** Die Reviews beziehen sich auf historische Commits, mit zusätzlichem aktuellen Review auf `5c1b847` vom 2026-10-08. Neueren Code zuerst gegenprüfen; gelöste Befunde nicht blind erneut beheben.
4. **Keine Sicherheit vortäuschen:** Reine Hosttests, SiL-/Modelltests, erfolgreiche STM32-Kompilierung, HiL und produktiver TTN-Feldtest getrennt benennen.
5. **Keine Geheimnisse committen:** `firmware/STM32_LORA_261008_ZS/Config_Geraet.h` und `server/lora/lora_config.php` bleiben lokal; keine Schlüssel/Token in Logs, Diffs oder Testvektoren.

## Projektentscheidungen beibehalten

- Bestehender Musterlogger: **MCCI-LMIC/ABP und RFM95**. Bewusst akzeptierter Frame-Counter-Reset bei 16384 mit TTN-Einstellung „Resets frame counters“; nicht eigenmächtig auf OTAA migrieren.
- RTC-Zeitabgleich per LoRaWAN DeviceTimeReq ist fachlich erwünscht; Sekundengenauigkeit genügt fürs Slotraster. RX1/RX2 auf Hardware sind als Feldtest offen.
- **FPort 1** = Legacy-Payload; **FPort 2** = neue Version mit Zustandsbits, Messzeit und FFT. Änderungen nur zusammen mit Formatter, Tests und Serververträgen.
- Server M.40 bleibt als unveränderte Referenz erhalten. Die neue generierte Server-Fassung `server/beelogger_eigen/` behebt den DST-Datenverlust im eigenen UTC-EE-Datenpfad (7/7). Eigene Änderungen **nur** in `server/eigen_anpassen.py`, der CI-Generierungsvergleich sichert den Stand. Der LoRa-Eingang prüft die UTC-Fähigkeit je Logger über das Merkmal `$BL_UTC_FAEHIG=1;` im `beelogger_log.php` (`SRV26-07`). Beim Deployment trotzdem alle Logger-Endpunkte aktualisieren (Kontrolle: `docs/server-utc.md`, Einspielen Schritt 5).
- Geplante **neue SMD-Platine SX1262/RadioLib** ist eine separate Entwicklung, nicht mit der Musterlogger-Firmware gleichsetzen. **Hardware 0.4 ist noch kein KiCad-Schaltplan.** Vor Layout die Review-Befunde `HW26-07` (Ladeübertemperatur, P0), `HW26-08` (Solar-ADC), `HW26-09` (I²C-Kapazität) und `HW26-10` (EEPROM-Atomicity) bearbeiten. Zellen-Datenblattrevision verbindlich prüfen.

## Reproduzierbare Checks

```bash
bash tests/alle_tests_linux.sh
# oder gezielt:
node tests/formatter/test_formatter.js
php tests/server/test_lora_funktionen.php
```

`tests/alle_tests_linux.sh` erzeugt Buildprodukte/`ff2_vektoren.h` lokal. Vor Commit unbeabsichtigte Artefakte prüfen. GitHub Actions auf `5c1b847` führt die neuen Firmware-Hosttests und drei Buildvarianten aus (`FW26-04` behoben). Der Playwright-Browsertest ist seit `6b83d` in CI installiert und verpflichtend (`BROWSER_PFLICHT=1`, `SRV26-08`). **Trotz bestandenem Chromium-Test ist die Gesamt-CI rot**: `CI26-01`, DST-Webhooks nur 6/7 Antworten `gespeichert`, obwohl 7/7 Zeilen in `week.csv` vorhanden sind. Den Fehler diagnostizieren, Test nicht aufweichen.

## Arbeits- und Reviewprotokoll

- Behebe Findings mit Bezug zur **Befund-ID**, nachvollziehbarer Ursache und Akzeptanztest.
- Prüfe beim Änderungswunsch die Auswirkungen auf Sensorfehler, Stromverbrauch, Framecounter, Funkpaketlänge, TTN-Feldnamen, Datenzeit und Server-Antwort.
- Bei Hardwareabhängigkeit **HiL-Aufgabe konkret notieren**, keine Messwerte erfinden.
- Testbericht nach neuer Revision **als neue datierte Version** ergänzen; historische Ergebnisse und ihre Prüfbasis erhalten.

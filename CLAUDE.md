# Hinweise für Claude / weitere Coding-Agents

**Projekt:** Autarker Bienenlogger (STM32F411/BlackPill mit RFM95 als bestehender Musterlogger; eigene SX1262-SMD-Platine erst im Entwurf). TTN → eigener PHP-LoRa-Eingang → beelogger M.40 → CSV/BEEP.

## Bevor du Änderungen vornimmst

1. **Zuerst lesen:** [Testberichte und priorisierte Befunde](docs/testberichte/README.md). Konkrete Befunde: `FW26-*`, `SRV26-*`, `FMT26-*`, `ZS26-*`, `HW26-*`.
2. Lies für Firmware `firmware/README.md`, `docs/zeitabgleich.md`, `docs/funkformat-v2.md` und den genau betroffenen Quelltext.
3. **Versionsbezug beachten:** Die Reviews beziehen sich auf historische Commits, derzeit überwiegend `d735f0f` vom 2026-10-08. Neueren Code zuerst gegenprüfen; gelöste Befunde nicht blind erneut beheben.
4. **Keine Sicherheit vortäuschen:** Reine Hosttests, SiL-/Modelltests, erfolgreiche STM32-Kompilierung, HiL und produktiver TTN-Feldtest getrennt benennen.
5. **Keine Geheimnisse committen:** `firmware/STM32_LORA_261008_ZS/Config_Geraet.h` und `server/lora/lora_config.php` bleiben lokal; keine Schlüssel/Token in Logs, Diffs oder Testvektoren.

## Projektentscheidungen beibehalten

- Bestehender Musterlogger: **MCCI-LMIC/ABP und RFM95**. Bewusst akzeptierter Frame-Counter-Reset bei 16384 mit TTN-Einstellung „Resets frame counters“; nicht eigenmächtig auf OTAA migrieren.
- RTC-Zeitabgleich per LoRaWAN DeviceTimeReq ist fachlich erwünscht; Sekundengenauigkeit genügt fürs Slotraster. RX1/RX2 auf Hardware sind als Feldtest offen.
- **FPort 1** = Legacy-Payload; **FPort 2** = neue Version mit Zustandsbits, Messzeit und FFT. Änderungen nur zusammen mit Formatter, Tests und Serververträgen.
- Server-Altcode M.40 möglichst unverändert lassen, solange ein Fix im eigenen Eingang robust möglich ist; den bekannten DST-Datenverlust nicht kaschieren.
- Geplante **neue SMD-Platine SX1262/RadioLib** ist eine separate Entwicklung, nicht mit der Musterlogger-Firmware gleichsetzen.

## Reproduzierbare Checks

```bash
bash tests/alle_tests_linux.sh
# oder gezielt:
node tests/formatter/test_formatter.js
php tests/server/test_lora_funktionen.php
```

`tests/alle_tests_linux.sh` erzeugt Buildprodukte/`ff2_vektoren.h` lokal. Vor Commit unbeabsichtigte Artefakte prüfen. GitHub Actions führt aktuell nicht jeden lokalen Firmware-Test aus (siehe `FW26-04`).

## Arbeits- und Reviewprotokoll

- Behebe Findings mit Bezug zur **Befund-ID**, nachvollziehbarer Ursache und Akzeptanztest.
- Prüfe beim Änderungswunsch die Auswirkungen auf Sensorfehler, Stromverbrauch, Framecounter, Funkpaketlänge, TTN-Feldnamen, Datenzeit und Server-Antwort.
- Bei Hardwareabhängigkeit **HiL-Aufgabe konkret notieren**, keine Messwerte erfinden.
- Testbericht nach neuer Revision **als neue datierte Version** ergänzen; historische Ergebnisse und ihre Prüfbasis erhalten.

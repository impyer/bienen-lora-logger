# Hinweise für Claude / weitere Coding-Agents

**Projekt:** Autarker Bienenlogger (STM32F411/BlackPill mit RFM95 als bestehender Musterlogger; eigene SX1262-SMD-Platine im Entwurf). TTN → eigener PHP-LoRa-Eingang → beelogger M.40 → CSV/BEEP.

## Entwicklungsregelwerk (Version 1.1 – angenommen am 09.10.2026)

**Zuerst [`docs/entwicklung/README.md`](docs/entwicklung/README.md), [`AGENTS.md`](AGENTS.md) und die fachlich betroffenen Regelabschnitte lesen.** Diese Regeln sind **verbindlicher Projektstandard für Menschen und Coding-Agents** ([ADR-0001](docs/entwicklung/entscheidungen/ADR-0001-projektregelwerk.md), [ADR-0002](docs/entwicklung/entscheidungen/ADR-0002-regelwerk-1-1.md)). Maintainer: Philipp Schnabel (`impyer`).

- **Übergabe (R-06 Nr. 2):** zuerst `git pull`, Ausgangs-SHA nennen; am Ende den Stand committen und pushen bzw. dem Maintainer zum Commit übergeben, bevor ein anderer Beteiligter arbeitet. Nur ein Beteiligter je Stand.
- **Befundstände:** **nur** im [Befundregister](docs/testberichte/befunde.md) (Statusmodell R-05a: offen / analysiert / im Entwurf behoben / nachgewiesen / geschlossen). Hier und in anderen Regeltexten keine Befundstände nennen.
- **Sicherheit & Risiko:** Änderung D0–D3 einordnen. D3 (Li-Ion, Ladefreigabe, Tiefentladeschutz): G2 nur mit Gefährdungsanalyse und sicherem Versuchsplan (Zell-Emulator, Strombegrenzung); G3/G4 nur mit T4-Messungen und unabhängigem fachkundigem Review. **Nie HiL simuliert als durchgeführt ausgeben**, Safety-Entscheide nicht selbst freigeben.
- **Quellwahrheit:** `hardware/kicad/*.py` führt für die KiCad-Schaltpläne; `server/eigen_anpassen.py` für den abgeleiteten Server; `formatter/formatter.js` für den TTN-Formatter.
- **Nachweise:** Tests T0–T6 und Gates G0–G4 unterscheiden; genaue SHA, Konfiguration, Soll/Ist, Grenzen und offene Hardwaretests nennen.
- **Lizenz (GOV-01, entschieden):** `*.py`/`*.sh` in `hardware/` und `mechanik/` unter GPL-3.0-or-later mit `SPDX-License-Identifier`; Schaltpläne, Symbole, Footprints und Exporte unter CERN-OHL-S-2.0. Fremdurheber nennen.

## Bevor du Änderungen vornimmst

1. **Zuerst lesen:** [Befundregister](docs/testberichte/befunde.md) und die dort verlinkten Prüf- und Behebungsberichte in [`docs/testberichte/`](docs/testberichte/README.md). Befundfamilien: `FW26-*`, `SRV26-*`, `FMT26-*`, `ZS26-*`, `HW26-*`, `CI26-*`, `SCH26-*`.
2. Lies für Firmware `firmware/README.md`, `docs/zeitabgleich.md`, `docs/funkformat-v2.md` und den genau betroffenen Quelltext; für Hardware `hardware/LASTENHEFT.md` (Anforderungs-IDs `LH-…`) und die Blockdokumente.
3. **Versionsbezug beachten:** Prüfberichte beziehen sich auf historische Commits. Neueren Code zuerst gegenprüfen; im Register als behoben geführte Befunde nicht blind erneut beheben.
4. **Keine Sicherheit vortäuschen:** Reine Hosttests, SiL-/Modelltests, erfolgreiche STM32-Kompilierung, KiCad-ERC/Netzprüfung, HiL und produktiver TTN-Feldtest getrennt benennen.
5. **Keine Geheimnisse committen:** `firmware/STM32_LORA_261008_ZS/Config_Geraet.h` und `server/lora/lora_config.php` bleiben lokal; keine Schlüssel/Token in Logs, Diffs oder Testvektoren.

## Projektentscheidungen beibehalten

- Bestehender Musterlogger: **MCCI-LMIC/ABP und RFM95**. Bewusst akzeptierter Frame-Counter-Reset bei 16384 mit TTN-Einstellung „Resets frame counters“; nicht eigenmächtig auf OTAA migrieren.
- RTC-Zeitabgleich per LoRaWAN DeviceTimeReq ist fachlich erwünscht; Sekundengenauigkeit genügt fürs Slotraster. RX1/RX2 auf Hardware sind als Feldtest offen.
- **FPort 1** = Legacy-Payload; **FPort 2** = neue Version mit Zustandsbits, Messzeit und FFT. Änderungen nur zusammen mit Formatter, Tests und Serververträgen.
- Server M.40 bleibt als unveränderte Referenz erhalten. Die generierte Server-Fassung `server/beelogger_eigen/` behebt den DST-Datenverlust im eigenen UTC-EE-Datenpfad. Eigene Änderungen **nur** in `server/eigen_anpassen.py`, der CI-Generierungsvergleich sichert den Stand. Der LoRa-Eingang prüft die UTC-Fähigkeit je Logger über das Merkmal `$BL_UTC_FAEHIG=1;` im `beelogger_log.php`. Beim Deployment trotzdem alle Logger-Endpunkte aktualisieren (Kontrolle: `docs/server-utc.md`, Einspielen Schritt 5). Das beelogger-Passwort im GET ist Ausnahme **EX-01**.
- Geplante **neue SMD-Platine SX1262/RadioLib** ist eine separate Entwicklung, nicht mit der Musterlogger-Firmware gleichsetzen. KiCad enthält die Hauptplatine mit allen Blättern; Zelle, Zellschutz und Ladesperre liegen seit HW-06 auf dem Blatt „Akku“ (keine eigene Akku-Platine mehr). Festgelegte Entwurfsentscheidungen stehen im Lastenheft und in `hardware/versorgung.md` (u. a. Ladesperre aus **TMP_VCC** am Ladereingang, nie aus B+/B−; EEPROM entfällt, Sitzung im SPI-Flash). Wiederanlauf und Ladesperre am Muster nur mit strombegrenztem Zell-Emulator prüfen.

## Reproduzierbare Checks

```bash
bash tests/alle_tests_linux.sh
# oder gezielt:
node tests/formatter/test_formatter.js
php tests/server/test_lora_funktionen.php
python3 hardware/energiebilanz.py; python3 hardware/i2c_leitung.py
bash hardware/kicad/pruefen.sh   # KiCad 10: Reproduzierbarkeit, ERC gegen erc_erwartet.json, netz_tests.py
```

`tests/alle_tests_linux.sh` erzeugt Buildprodukte/`ff2_vektoren.h` lokal. Vor Commit unbeabsichtigte Artefakte prüfen. Server-E2E-Tests hängen nicht von der Uhrzeit ab: `SERVER_UHR="2026-10-09 05:00:00" bash tests/server/test_lora_eingang.sh` (libfaketime; beelogger kürzt `week.csv` vor 08:00 Uhr Serverzeit). Die CI prüft 05:00 und 14:00 sowie den KiCad-Job (`git diff --exit-code` ohne PDF/Netzliste).

## Arbeits- und Reviewprotokoll

- Behebe Befunde mit Bezug zur **Befund-ID**, nachvollziehbarer Ursache und Akzeptanztest; danach den Status im Befundregister nachführen.
- Prüfe beim Änderungswunsch die Auswirkungen auf Sensorfehler, Stromverbrauch, Framecounter, Funkpaketlänge, TTN-Feldnamen, Datenzeit und Server-Antwort.
- Bei Hardwareabhängigkeit **HiL-Aufgabe konkret notieren**, keine Messwerte erfinden.
- Testbericht nach neuer Revision **als neue datierte Version** ergänzen; historische Ergebnisse und ihre Prüfbasis erhalten.
- `CHANGELOG.md` nur oben ergänzen.

## Webplattform / neue Oberfläche (ab 15.10.2026)

Für UI-, BEEP-Stockkarten-, Sensorregister-, Boden-/Umwelt- und Analysearbeiten zusätzlich **zuerst** [docs/webplattform/README.md](docs/webplattform/README.md) und [docs/webplattform/claude-arbeitsauftrag.md](docs/webplattform/claude-arbeitsauftrag.md) lesen. Das sind Arbeitsentwürfe, keine stillschweigende Abnahme neuer SQL-/API-Strukturen. Bestehende bestätigte Fachentscheidungen unter `docs/architektur/` haben Vorrang; **keine** Daten oder Gerätezuordnungen halluzinieren. Keine Produktivmigration ohne Freigabe. Änderungen isoliert auf eigener Branch und mit dokumentierten Tests an ChatGPT zur unabhängigen Review übergeben.

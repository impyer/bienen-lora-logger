# Testberichte und offene Prüfpunkte

Dieser Ordner enthält nachvollziehbare, **commitbezogene** Reviews zum Projekt Bienenlogger. Die Berichte sind Dokumentation, keine automatische Fehlerbehebung. Neue Implementierungen sollen Befund-IDs referenzieren und mit Tests gegen die angegebenen Akzeptanzkriterien abgesichert werden.

## Berichtsverzeichnis

| Bericht | Stand | Verifikation |
|---|---|---|
| **[Behebung HW26-07 … -15 und CI26-01](2026-10-09-hw04-ci26-behebung.md)** | **Arbeitsstand nach `6b83d`** (Commit-ID beim Einchecken nachtragen) | **CI26-01: Ursache reproduziert (Kürzung von week.csv vor 08:00), behoben, Gegenprobe; E2E eigen 74/74 bei 05:00 und 14:00, original 56/56, Unit 66/66; CI-Lauf offen. Hardware: Entwurfsänderungen, Rechnungen; kein KiCad/HiL** |
| **[Hardware 0.4 – unabhängiges Review, Versorgung/Pinout/PCB](2026-10-09-hardware-04-review.md)** | **Hardware-Commit `5c94e1b`, CI bis `6b83d`** | **Konzept- und numerisches SiL-Review; P0 Akku-HOT, P1 PV-ADC/I²C, CI-Regression; noch kein KiCad/HiL** |
| **[Behebung SRV26-02/03/04/05/07/08](2026-10-08-srv26-behebung.md)** | **Arbeitsstand nach `5c1b847`** (Commit-ID beim Einchecken nachtragen) | **Host-/E2E-Tests lokal (eigen 73/73, original 56/56, Unit 59/59), Gegenprobe ohne Korrektur; CI-Lauf offen; kein TTN/BEEP/HiL** |
| [main 5c1b847 — Firmware 261010, UTC-Server, Regression](2026-10-08-main-5c1b847-regression.md) | Commit `5c1b847` | 5/5 CI-Jobs erfolgreich; neuer unabhängiger UTC-Teilupdate-Spotcheck; kein HiL |
| [Firmware 261009 — Code-Review und isolierte SiL-Spotchecks](2026-10-08-firmware-261009-sil.md) | Commit `d735f0f` | Statisch + isolierter Host-Rechentest; kein MCU-/HiL-Test |
| [TTN-Formatter und LoRa-Server-Eingang](2026-10-08-ttn-formatter-server-review.md) | Commit `f252677`, nachverifiziert `d735f0f` | Code/CI/Integration; kein produktiver TTN-/BEEP-Test |
| [LoRaWAN-Zeitabgleich ZS](2026-10-08-zs-review.md) | ZS `de72645`, ZS-Logik in `d735f0f` | Host-Tests/Modellsimulation; kein HiL |
| [Hardware-Entwurf: Prüfliste](2026-10-08-hardware-architektur-review.md) | Lastenheft 0.3 in `d735f0f` | Konzeptreview; kein KiCad-/HiL-Nachweis |

## Aktuell: Behebung nach Hardware-Review 0.4 (09.10.2026)

**Maßgeblich:** [Behebung HW26-07 … -15 und CI26-01](2026-10-09-hw04-ci26-behebung.md).

- **`CI26-01` behoben (lokal):** beelogger kürzt `week.csv` vor 08:00 Uhr Serverzeit; die Speichererkennung prüft keine Dateigröße mehr. Test mit fester Serveruhr (libfaketime) um 05:00 und 14:00.
- **`HW26-07` Entwurf geändert:** Ladesperre zweistufig, TMP390 an der Zelle sperrt über CE außerhalb +5 … 42 °C, ausfallsicher bei Leitungsbruch; NTC bleibt zweite Stufe.
- **`HW26-08` … `-13` Entwurf geändert:** Solar-Teiler 3,3 MΩ/470 kΩ hinter den Dioden; Netzwerkkabel für BME280 (105–135 pF); EEPROM entfällt, Sitzung im SPI-Flash mit CRC/Generation; Ladestrom 150 mA; Flash-Aufteilung; J10 1 × 7, J11 2 × 6.
- **Offen:** `HW26-14/15`, alle Messungen am Muster, Zellvariante, CI-Lauf, KiCad.

## Hardware-Definition 0.4 (09.10.2026, Review)

Maßgebliche neue Prüfung: **[Hardware-Review 0.4](2026-10-09-hardware-04-review.md)**. Die vorigen Berichte bleiben als historische Quellen erhalten.

- **P0 `HW26-07`:** NTC/BQ25185 unterbindet die Ladung rechnerisch erst bei ca. 59,5 °C. Zellspezifikation (45 °C im Projekt vs. 55 °C auf aktueller BAK-Herstellerseite) klären und Hardware-Ladesperre sicher auslegen.
- **P1 `HW26-08`–`HW26-11`:** Überspannung Solar-ADC, I²C 440 pF Worst Case, EEPROM-Stromausfallfestigkeit, thermisches Lade-IC-Modell.
- **P2 `HW26-12`–`HW26-15`:** FFT-Rohdaten vs. 8 MiB Flash, J10/J11-Pinzahl, Ra-01SH-Chip/Schalter, STEP/Bestückung.
- **P1 `CI26-01`:** `main`-Pipeline beim Stand `6b83d` rot (4/5 Jobs). Sieben DST-Messzeitpunkte stehen korrekt in CSV, aber nur sechs Antworten als „gespeichert“ gezählt. Browserprüfung mit Playwright bestanden; Ursache der Statusabweichung offen.
- **Keine PCB-Freigabe:** Schaltplan, ERC, Layout, DRC, Gerber/BOM/CPL und Messwerte fehlen noch.

## Aktueller Stand nach Behebung SRV26 (2026-10-08)

**Maßgeblich:** [Behebung SRV26-02/03/04/05/07/08](2026-10-08-srv26-behebung.md), aufbauend auf dem Review 5c1b847.

- **Behoben, lokal nachgewiesen:**
  - `SRV26-07`: Zeitbasis je Logger über das Merkmal im Ziel-`beelogger_log.php`
  - `SRV26-05`: BEEP/ThingSpeak nur für gespeicherte Datensätze; ID-Prüfung korrigiert
  - `SRV26-03`: Sperre je Logger und Kennung je Nachricht
  - `SRV26-04`: Schreibfehler der Zusatzdatei werden gemeldet
  - `SRV26-02`: Ergebnisklassen; vorübergehende Fehler → 202, Zwischenspeicher und Nachholen
- **`SRV26-08`:** Playwright in der CI verpflichtend; wirksam erst mit dem nächsten CI-Lauf.
- **Abweichung:** Für `SRV26-02` ist 202 + eigener Zwischenspeicher statt 5xx umgesetzt. Die Begründung (TTS-Verhalten bei Fehlerantworten) steht im Bericht.
- **Weiter offen:** `SRV26-06`, `HW26-*`, Firmware-HiL, echter BEEP-/TTN-Betrieb.

## Stand nach Regression 5c1b847 (historisch)

**Maßgeblich für neue Änderungen:** [Regressionstest Firmware 261010 / UTC-Server](2026-10-08-main-5c1b847-regression.md). Der untenstehende ursprüngliche Prüfstand ist historisch und wird zur Rückverfolgung **nicht** überschrieben.

- **Behebungen nachgewiesen:** `FW26-01` (Compile-Guard), `FW26-02` (Phantomgewicht unterdrückt), `FW26-03` (ADC-Timeout im Code), `FW26-04` (CI-Tests), `FW26-05` (SiL-SNR/59 Hz), `FW26-06` (FPort-1-FFT deaktiviert).
- **`SRV26-01` nur bedingt behoben:** 7/7 über `server/beelogger_eigen`; das Original M.40 bleibt bei 5/7.
- **Neu P1 `SRV26-07`:** `utc_zeit='auto'` darf nicht wegen eines einzigen Hauptordner-Markers UTC an einen alten Logger-Endpunkt schicken (Teilupdate: 2 h Verschiebung nachgewiesen).
- **Unverändert P1:** `SRV26-02/03/04/05` (Fehlerstatus, Parallelität, CSV-Atomizität, BEEP-Duplikatrisiko).
- **Neu P2 `SRV26-08`:** Playwright-Grafiktest wurde im GitHub-CI-Lauf übersprungen.
- **Hardware `HW26-01` und weitere Entwurfs-/HiL-Punkte bleiben offen.**

## Offene Prioritäten (ursprünglicher Prüfstand vor 5c1b847, historisch)

> Diese Tabelle ist der ursprüngliche Stand. `FW26-01` bis `-06` sind mit 5c1b847 behoben, `SRV26-01` (eigene Fassung), `-02` bis `-05` und `-07` mit der SRV26-Behebung. Aktuell offen: siehe die Abschnitte oben.

| Rang | Befund | Maßnahme |
|---|---|---|
| **P0** | `SRV26-01` | Winterzeit-Datenverlust (25.10.2026): UTC-Datensätze durchgängig erhalten, Test 7/7 |
| **P0** | `HW26-01` | Hardware-Unterspannungs-/Ladeschutz vor PCB-Freigabe |
| **P1** | `FW26-02` | Phantomgewicht bei fehlender Waagenkalibrierung verhindern |
| **P1** | `FW26-03` | ADC-EOC-Polling zeitlich begrenzen |
| **P1** | `FW26-04` | FFT-/V2-Codec-Tests und Audio-Build in GitHub Actions aufnehmen |
| **P1** | `FW26-01` | Mehr als zwei Waagen bei V2 ausschließen oder Format erweitern |
| **P1** | `SRV26-02`/`SRV26-03`/`SRV26-04` | Status/Retry, parallele Webhooks, Haupt-/Zusatzdaten konsistent behandeln |
| **P1** | `SRV26-05` | BEEP/ThingSpeak bei Duplikaten prüfen |
| **P1** | `HW26-02`–`HW26-05` | Energie, Solar/Regler, Rückspeisung, Mikrofon-Kalibrierung und Anti-Aliasing |

Die Prioritäten gelten für die jeweils genannte nächste Stufe. Ein Hardware-P0 ist kein Blocker für einen rein softwarebasierten SiL-Test.

## Arbeitsweise für Claude und weitere Entwickler

1. **Vor Änderung:** Prüfobjekt und neuesten `main`-Commit prüfen. Berichte sind Snapshots; ältere Befunde können zwischenzeitlich behoben worden sein.
2. **Befund-ID aufnehmen** und in Commit-/PR-Beschreibung referenzieren, z. B. `Fixes FW26-03`; Ursache und geändertes Verhalten erläutern.
3. **Nachweis unterscheiden:** `statisch bestätigt`, `Host-/SiL reproduziert`, `CI durchgeführt`, `HiL am Gerät gemessen`, `Feldbetrieb bestätigt` oder `noch offen`. „CI grün“ ersetzt keinen speziellen Test.
4. **Regressionstest ergänzen**, möglichst im bereits existierenden `tests/`-Verzeichnis. Bei Bugfix zuerst den Test rot sehen, anschließend grün. Bestehende historische Simulationsdaten nicht als neue Messwerte ausgeben.
5. **Akzeptierte Kompromisse erhalten:** ABP mit bewusstem Framecounter-Reset, für das 10-s-Raster ausreichende RTC-Genauigkeit und geplanten RX1/RX2-HiL-Feldtest nicht ohne neue Anforderungen umdesignen; siehe [ZS-Review](2026-10-08-zs-review.md).
6. **Geheimnisse:** `Config_Geraet.h`, Netzwerkschlüssel, reale `lora_config.php`, Webhook-Token und persönliche Mess-/Standortdaten nie committen. Beispieldateien und synthetische Testvektoren sind zulässig.
7. **Nach Test:** Im Bericht oder in einem neuen datierten Bericht aktualisieren: Commit, Build-Konfiguration, reproduzierbare Befehle, Erwartung/Ergebnis, Abweichung, offene HiL-Aufgabe. Bereits veröffentlichte historische Ergebniszahlen nicht stillschweigend umschreiben.

## Test-Einstieg

- Zeitlogik/Simulation: `tests/host`, `tests/sim`, `docs/zeitabgleich.md`
- Funkformat/FFT: `tests/firmware`, `tests/formatter`, `docs/funkformat-v2.md`, `docs/fft-konzept.md`
- TTN-Server: `tests/server`, `server/lora/README.md`
- Aktuelle Buildmatrix: `.github/workflows/tests.yml`
- HiL-Vorbereitung: Abschnitt „HiL-Plan“ im [Firmware-Report](2026-10-08-firmware-261009-sil.md)

**Regel:** Geprüften Commit und Testart stets mitspeichern; „Hardware nicht vorhanden“ ist ein dokumentierter Prüfstatus, kein bestandenes Ergebnis.

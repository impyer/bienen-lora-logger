# Befundregister

**Einzige Stelle für den aktuellen Stand aller Befunde** (Regelwerk 1.1, R-05a). Prüfberichte in diesem Ordner sind historische Snapshots; der Stand hier wird bei jeder Behebung und jedem Nachweis nachgeführt.

**Stand:** 09.10.2026 (ergänzt um Audit AUD-2026-10-09-01), Zusammenführung aus den Prüf- und Behebungsberichten bis `8fc2aa4` und der Behebung SCH26 (Commit beim Einchecken nachtragen).
**Pflege:** wer einen Befund behebt oder nachweist, ändert hier Status, Nachweis und gesperrtes Gate im selben Commit.

## Statusmodell

| Status | Bedeutung |
|---|---|
| **offen** | gemeldet, nicht bewertet oder nicht bearbeitet |
| **analysiert** | technisch bewertet: *bestätigt*, *verworfen* (mit Begründung) oder *akzeptiert* (bewusst so belassen, mit Begründung) |
| **im Entwurf behoben** | Änderung umgesetzt und mit T0–T3 geprüft; **nicht** am realen Prüfling nachgewiesen |
| **nachgewiesen** | mit T4/T5 am realen Prüfling bestätigt |
| **geschlossen** | nachgewiesen bzw. sicher entfallen, vom Maintainer geschlossen |

Teststufen T0–T6 und Gates G0–G4: [tests-freigaben.md](../entwicklung/tests-freigaben.md).

## Hardware: neue Platine (Akku-Platine, Hauptplatine)

| ID | Prio | Kurzbeschreibung | Status | Höchster Nachweis | Gesperrtes Gate / nächster Schritt | Quellen |
|---|---|---|---|---|---|---|
| SCH26-01 | P0 | Ladesperre hinter dem Zellschutz → nach Tiefentladung kein Wiederanlauf | **im Entwurf behoben** (TMP_VCC am Ladereingang) | T3: KiCad-Netzprüfung inkl. Gegenprobe | G2 bis sicherer Versuchsplan; G3 bis SCH-T04 (Wiederanlauf mit Zell-Emulator) + unabhängiges Review | [Review](2026-10-09-schaltplan-v01-review.md), [Behebung](2026-10-09-sch26-behebung.md) |
| SCH26-02 | P1 | 10-MΩ-Freigabekette, Leckströme | im Entwurf behoben (100 kΩ, Pegelrechnung) | T0/T3 | G3 bis Pegelmessung über Temperatur | dto. |
| SCH26-03 | P1 | Keine Einzelfehlersicherheit ≤ 45 °C | im Entwurf behoben (2. TMP390 öffnet NTC-Kreis) | T3 | G3 bis SCH-T02/T03 | dto. |
| SCH26-04 | P1 | ERC/Footprints/Reproduzierbarkeit nicht abgesichert | im Entwurf behoben bis auf Footprints (pruefen.sh, CI-Job) | T3 lokal; CI-Lauf offen | **Fertigung** gesperrt bis Footprints BQ25185/Keystone 1043/Klemmen | dto. |
| SCH26-05 | P2 | R208 1 MΩ statt 100 kΩ | im Entwurf behoben | T3 | – | dto. |
| SCH26-06 | P2 | Akkukabel ohne Kabelplan | im Entwurf behoben (Kabelplan) | T0/T3 | G2: Kabel durchprüfen | dto. |
| SCH26-07 | P2 | Blätter MCU, Funk, Waage, Mikrofon, Anschlüsse fehlen | offen | – | G2 | dto. |
| SCH26-08 | P2 | Eingangsschutz nur nominal | im Entwurf behoben (C201 50 V); Panelmessung offen | T0 | G3 bis Panel-Voc/Isc gemessen | dto. |
| HW26-01 | P0 | Ungeschützte 18650-Zelle | im Entwurf behoben für die neue Platine (HY2111 + FS8205 an der Zelle) | T3 | G3 bis Abschalt-/Freigabeversuch mit Zell-Emulator | [Review 0.3](2026-10-08-hardware-architektur-review.md), `hardware/versorgung.md` 3.4 |
| HW26-02 | P1 | Solar-Eingang und 3,3-V-Regler | im Entwurf behoben (BQ25185, RT9080) | T0/T2 | G3 bis Messung | dto. |
| HW26-03 | P1 | Reale Energiebilanz | im Entwurf behoben (Modell `energiebilanz.py`) | T2 | G3 bis Ruhestrom-/Zyklusmessung | dto. |
| HW26-04 | P1 | Rückspeisung der geschalteten Sensorversorgung | im Entwurf behoben (Pull-ups an 3V3_SW, TPS22917 mit QOD) | T0/T3 | G3 bis SCH-T05 | dto. |
| HW26-05 | P1 | Akustik-Antialiasing und Kalibrierung | im Entwurf behoben (Analogfilter, `mikrofon_filter.py`) | T2 | G3 bis Frequenzgang-/Schallkalibrierung | dto., `hardware/mikrofon.md` |
| HW26-06 | P2 | Mechanik/RF | offen | – | G3 | [Review 0.3](2026-10-08-hardware-architektur-review.md) |
| HW26-07 | P0 | Ladesperre zu heiß (59,5 °C) | im Entwurf behoben (TMP390 42 °C, später ergänzt durch SCH26-01/03) | T3 | wie SCH26-01/03 | [Review 0.4](2026-10-09-hardware-04-review.md), [Behebung](2026-10-09-hw04-ci26-behebung.md) |
| HW26-08 | P1 | Solar-ADC-Teiler nicht bis 25 V geschützt | im Entwurf behoben (3,3 MΩ/470 kΩ) | T0/T3 | G3 bis Messung 0/6/12 V | dto. |
| HW26-09 | P1 | I²C > 400 pF | im Entwurf behoben (Netzwerkkabel) | T2 (`i2c_leitung.py`) | G3 bis Kabelkapazität und Flanken gemessen | dto. |
| HW26-10 | P1 | Sitzungs-Persistenz bei Stromausfall | im Entwurf behoben (SPI-Flash mit Generation/CRC) | T0 | G3 bis Firmware + Power-Cut-HiL | dto. |
| HW26-11 | P1 | Wärme Laderegler | im Entwurf behoben (150 mA) | T0 | G3 bis Temperaturmessung | dto. |
| HW26-12 | P2 | Flash-Kapazität FFT-Rohdaten | im Entwurf behoben (Text/Aufteilung) | T0 | – | dto. |
| HW26-13 | P2 | J10/J11-Pinzahl | im Entwurf behoben | T0 | – | dto. |
| HW26-14 | P2 | SX1262 oder LLCC68, HF-Schalter | offen | – | G2 bis Modulmuster geprüft | dto. |
| HW26-15 | P2 | Mechanik, USB, PCBA-Konfiguration | offen | – | Fertigung bis STEP/Angebot | dto. |

## Firmware Musterlogger (BlackPill + RFM95)

| ID | Prio | Kurzbeschreibung | Status | Höchster Nachweis | Gesperrtes Gate / nächster Schritt | Quellen |
|---|---|---|---|---|---|---|
| FW26-01 | P1 | Waage 3/4 in V2 nicht kodierbar | im Entwurf behoben (Compile-Guard) | T3 (CI-Negativbuild) | – | [Regression 5c1b847](2026-10-08-main-5c1b847-regression.md) |
| FW26-02 | P1 | Phantomgewicht bei unkalibrierter Waage | im Entwurf behoben | T1 | G3 bis HiL mit HX711 | dto. |
| FW26-03 | P1 | Unbegrenztes ADC-Polling | im Entwurf behoben (50-µs-Timeout) | T1/T3 | G3 bis Fehlerinjektion am MCU | dto. |
| FW26-04 | P1 | Hosttests/Buildvarianten fehlen in CI | im Entwurf behoben | T3 (CI) | – | dto. |
| FW26-05 | P2 | 50/59 Hz und Rauschen in der FFT | im Entwurf behoben (SNR-Kriterium) | T2 | G3 bis Mikrofon-HiL | dto. |
| FW26-06 | P2 | Audioaufnahme trotz FPort 1 | im Entwurf behoben | T3 | G3 bis Strommessung | dto. |
| FW26-07 | P2 | Abtastung DWT/ADC statt Timer+DMA | analysiert – akzeptiert (bewusster Prototypen-Unterschied; neue Platine getrennt) | T0 | – | dto. |
| FW26-08 | P2 | FFT-Konsistenz, SNR-Bedeutung, ADC-Timeout nur Build-abgedeckt | offen | – | G3 | dto. |
| FMT26-01 | P2 | V2-Formatinkonsistenzen hart prüfen | offen | – | G3 | [Formatter/Server](2026-10-08-ttn-formatter-server-review.md) |
| ZS26-01 | – | DeviceTimeReq/Ans im realen Funkzyklus | offen (HiL-Aufgabe) | T2 (Simulation) | G3 | [ZS-Review](2026-10-08-zs-review.md) |
| ZS26-02 | – | Zeitliche Ordnung von zehn Loggern | offen (HiL-Aufgabe) | T2 | G3 | dto. |
| ZS26-03 | – | Verhalten bei Gateway-/Downlink-Ausfall | offen (HiL-Aufgabe) | T2 | G3 | dto. |
| ZS26-04 | – | RTC-Shadow-Register am echten STM32 | offen (HiL-Aufgabe) | – | G3 | dto. |
| ZS26-05 | – | Framecounter nach Reset/Timeout | offen (HiL-Aufgabe) | T1 | G3 | dto. |
| ZS26-06 | – | Zeitabgleich und Standby-Strom | offen (HiL-Aufgabe) | – | G3 | dto. |

## Server und CI

| ID | Prio | Kurzbeschreibung | Status | Höchster Nachweis | Gesperrtes Gate / nächster Schritt | Quellen |
|---|---|---|---|---|---|---|
| SRV26-01 | P0 | Winterzeit: Datensätze verworfen | im Entwurf behoben für `beelogger_eigen` (7/7); Original M.40 bleibt fehlerhaft (Referenz) | T2 (CI) | G3 bis Betrieb über eine echte Umstellungsnacht | [Regression 5c1b847](2026-10-08-main-5c1b847-regression.md) |
| SRV26-02 | P1 | Fehlerklassen, Zwischenspeicher | im Entwurf behoben (202 + Nachholen) | T2 (CI) | G3 bis TTN-Betrieb | [Behebung SRV26](2026-10-08-srv26-behebung.md) |
| SRV26-03 | P1 | Parallelität, Duplikate | im Entwurf behoben | T2 (CI) | – | dto. |
| SRV26-04 | P1 | Schreibfehler Zusatzdatei | im Entwurf behoben | T2 (CI) | – | dto. |
| SRV26-05 | P1 | BEEP/ThingSpeak nur für gespeicherte Daten | im Entwurf behoben | T2 (CI, BEEP-Mock) | G3 bis echter BEEP-Betrieb | dto. |
| SRV26-06 | P2 | Interner HTTP-Selbstaufruf, Hosting | offen | – | G3 | [Formatter/Server](2026-10-08-ttn-formatter-server-review.md) |
| SRV26-07 | P1 | Zeitbasis je Logger (Teilupdate) | im Entwurf behoben | T2 (CI) | – | [Behebung SRV26](2026-10-08-srv26-behebung.md) |
| SRV26-08 | P2 | Browsertest in CI übersprungen | im Entwurf behoben (Playwright verpflichtend) | T3 (CI) | – | dto. |
| CI26-01 | P1 | DST-Test 6/7 je nach Uhrzeit | im Entwurf behoben (Erkennung über Zeitstempel, libfaketime 05:00/14:00) | T2 (CI) | – | [Behebung](2026-10-09-hw04-ci26-behebung.md) |

## Prozess und Regelwerk

| ID | Prio | Kurzbeschreibung | Status | Höchster Nachweis | Gesperrtes Gate / nächster Schritt | Quellen |
|---|---|---|---|---|---|---|
| REG26-01 | P0 | Behebung SCH26 lokal verworfen, `main` mit fehlerhaftem Akku-Entwurf | im Entwurf behoben (Wiederherstellung im Arbeitsverzeichnis) | T0 | G1 Akku bis Commit/Push der Wiederherstellung | [Audit](2026-10-09-regelwerk-audit.md) |
| REG26-02 | P1 | Regelwerk 1.1 nicht eingecheckt | im Entwurf behoben (mit Wiederherstellung) | T0 | G1 bis Commit/Push | dto. |
| REG26-03 | P1 | CI-Job prüft alten Entwurf mit altem `pruefen.sh` | im Entwurf behoben (mit Wiederherstellung) | T3 lokal | G1 bis grüner CI-Lauf nach Push | dto. |
| REG26-04 | P2 | Commit-Nachrichten ohne Warum/Was/IDs/Tests | analysiert – bestätigt; ab sofort Muster | T0 | – | dto. |
| REG26-05 | P2 | Berichte ohne exakten SHA | im Entwurf behoben (SRV26, HW26/CI26 nachgetragen); SCH26 offen | T0 | – | dto. |
| REG26-06 | P1 | Gefährdungsanalyse und sicherer Versuchsplan Akku fehlen | offen | – | **G2 Akku** | dto. |
| REG26-07 | P1 | Rückverfolgbarkeit D3 fehlt | offen | – | **G2 Akku** | dto. |
| REG26-08 | P2 | Pin-/Footprint-Abgleichbericht fehlt | offen | – | Layout | dto. |
| REG26-09 | P2 | PWR_FLAG-Begründungen fehlen | offen | – | – | dto. |
| REG26-10 | P2 | Board-ID/Revision, Umgebungsbedingungen | offen | – | G2 | dto. |
| REG26-11 | P2 | Kondensator-Derating, Schienentabelle | offen | – | G2 | dto. |
| REG26-12 | P1 | Zellmodell/Datenblatt unbekannt (GOV-04) | offen | – | Fertigung | dto. |

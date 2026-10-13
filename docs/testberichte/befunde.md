# Befundregister

**Einzige Stelle für den aktuellen Stand aller Befunde** (Regelwerk 1.1, R-05a). Prüfberichte in diesem Ordner sind historische Snapshots; der Stand hier wird bei jeder Behebung und jedem Nachweis nachgeführt.

**Stand:** 13.10.2026: Blatt Anschlüsse ([Bericht](2026-10-13-sch26-07-anschluesse.md), Basis `969339d`) – damit alle Schaltplanblätter im Entwurf (SCH26-07). Blatt Mikrofon im Entwurf (SCH26-07, [Bericht](2026-10-13-sch26-07-mikrofon.md), Basis main `ecf2918`). 10.10.2026 abends: Blatt Waage im Entwurf (SCH26-07, [Bericht](2026-10-10-sch26-07-waage.md), Basis main `eb9e10b`); Behebung SCH26-09/-12 ([Bericht](2026-10-10-sch26-09-12-behebung.md)), Festlegung USB (SCH26-10) und Analyse Ra-01SH nach Herstellerschaltbild (SCH26-11, [Bericht](2026-10-10-sch26-10-11-analyse.md)), auf Basis main `3ff894a`. Review-Grundlage: unabhängiges Schaltplan-T0-/GitHub-T3-Review von [`4c12b6d`](https://github.com/impyer/bienen-lora-logger/commit/4c12b6d77fdda784b83fffc3b4bdbb88e74cf614), CI [38023150749](https://github.com/impyer/bienen-lora-logger/actions/runs/38023150749) 7/7 PASS. Vorbestand und SAF-AKKU 0.1 bleiben erhalten; CI für den Behebungsstand offen.
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
| SCH26-04 | P1 | ERC/Footprints/Reproduzierbarkeit nicht abgesichert | **im Entwurf behoben bis auf Footprints**; aktueller KiCad-Generator-/ERC-/Netztest in CI **PASS** | **T3 CI `4c12b6d`**, 48/48, 0 unerwartete ERC-Warnungen | **Fertigung** gesperrt bis Footprints BQ25185/Keystone 1043/Klemmen | dto. |
| SCH26-05 | P2 | R208 1 MΩ statt 100 kΩ | im Entwurf behoben | T3 | – | dto. |
| SCH26-06 | P2 | Akkukabel ohne Kabelplan | im Entwurf behoben (Kabelplan) | T0/T3 | G2: Kabel durchprüfen | dto. |
| SCH26-07 | P2 | Blätter MCU, Funk, Waage, Mikrofon, Anschlüsse fehlen | **im Entwurf behoben** (13.10.2026): alle Blätter vorhanden – MCU, Funk + Flash (10.10.), Waage (10.10., [Bericht](2026-10-10-sch26-07-waage.md)), Mikrofon (13.10., [Bericht](2026-10-13-sch26-07-mikrofon.md)), Anschlüsse (13.10., [Bericht](2026-10-13-sch26-07-anschluesse.md)); Netzprüfung 178/178 mit Gegenproben, ERC nur Footprint-Meldung U201 | T3 | G2 | dto. |
| SCH26-08 | P2 | Eingangsschutz nur nominal | im Entwurf behoben (C201 50 V); Panelmessung offen | T0 | G3 bis Panel-Voc/Isc gemessen | dto. |
| **SCH26-09** | **P1** | J302 Debug-Pinmap widerspricht `anschluesse.md` J10: GND Pin7 vs. Pin5, UART TX Pin5 vs. Pin6 | **im Entwurf behoben**: Generator = Kabelplan (5 GND, 6 TX1, 7 RX1); `netz_tests.py` prüft je Pin und Dokument ↔ Netzliste mit Gegenprobe | **T3 lokal** (KiCad 10.0.7, 74/74, Gegenprobe gegen `4c12b6d` rot); CI auf neuem Commit offen; Durchgang am Muster (T4) offen | G2 Kabelkonfektion erst nach Durchgangsprüfung am Muster | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Issue #4](https://github.com/impyer/bienen-lora-logger/issues/4) |
| **SCH26-10** | **P1** | Selbstversorgte USB-C-Gerätefunktion ohne getrennte VBUS-/Host-Erkennung, PA9 bereits UART-TX | **im Entwurf behoben** durch Festlegung **HW-01** (Philipp 10.10.2026): USB nur Laden + ROM-DFU, Anwendung nutzt USB nie → keine VBUS-Erkennung nötig; Lastenheft K5, `mcu-funk.md` 1.3 | **T0** (ST AN4879); **T4 offen**: ROM-DFU mit 25-MHz-Quarz, Laden, Ruhestrom bei gestecktem USB | G3 bis DFU am Muster bestätigt | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Analyse 10.10](2026-10-10-sch26-10-11-analyse.md), [Issue #5](https://github.com/impyer/bienen-lora-logger/issues/5) |
| **SCH26-11** | **P1** | Ra-01SH: offene TXEN/RXEN-Lötbrücken, DIO2- und IPEX-HF-Umschaltung nicht am Liefermodul bestätigt | **analysiert** – Herstellerschaltbild (Datenblatt V1.1 S. 12): DIO2 schaltet über Q1-Inverter den SPDT, **TXEN = DIO2 (0 Ω)**, RXEN über R1 „NC“ offen, ANT ∥ IPEX, DC-DC-Spule vorgesehen; Ra-01SCH-Spec bestätigt interne Steuerung. Regel: Brücken offen, PB14/PB15 nur Eingang; `netz_tests.py` prüft die Brücken; Modell `funk_modell.py` | **T0** Hersteller, **T2** Modell, **T3** 79/79; **T4 offen** (F-1…F-7) | G3 Funk / G4 Modulfootprint bis F-1…F-7 | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Analyse 10.10](2026-10-10-sch26-10-11-analyse.md), [Issue #6](https://github.com/impyer/bienen-lora-logger/issues/6) |
| **SCH26-13** | **P2** | Klemmen-Teilenummer DEGSON 15EDGRHC-THR-3.5 (4-polig C7603445) ist zweireihig (2 × 2 Kontakte), die Platine sieht einreihige Klemmen mit eigener Polzahl vor (anschluesse.md 1) | **offen** – Belege: DEGSON-Datenblatt (Serie 15EDGKNH/15EDGRHC „double rows“, 04–48P), EasyEDA-Footprint C7603445 mit 2 × 2 Pads; JLCPCB-Teileseite nennt „1 row“ (widersprüchlich). Vorschlag: DEGSON 15EDGRC-3.5-0xP (einreihig, geschlossen) + 15EDGK-3.5; Platzhalter-Footprint Phoenix MC passt zu einreihig | T0 | G2 Stückliste, vor Bestellung | [Bericht 13.10.](2026-10-13-footprints-bienen.md) |
| **SCH26-12** | **P2** | `pruefen.sh` H1/H2 lässt neue `mcu.kicad_sch`/`funk.kicad_sch` aus, Abschluss-Git-Diff deckt sie aber ab | **im Entwurf behoben**: Dateiliste aus den Ordnern, Abdeckungsprüfung gegen Blattverweise, Modus `--gegenprobe` | **T3 lokal** (alle 6 Dateien, Gegenproben bestanden); CI auf neuem Commit offen | G1 nach grüner CI | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Issue #7](https://github.com/impyer/bienen-lora-logger/issues/7) |
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
| HW26-16 | P1 | Gemeinsamer Fehlerpunkt: beide Temperaturstufen wirken über den BQ25185; fällt der Laderegler aus, gibt es keine Temperatursperre mehr (Überladung begrenzt nur noch HY2111) | offen | T0 | G2: Entscheidung E-2 (Restrisiko oder Eingangstrennung) | [`sicherheit-akku.md`](../../hardware/sicherheit-akku.md) 4/5 |
| HW26-17 | P1 | HY2111-GB erlaubt Laden ab 0 V; eine nach der Abschaltung weiter entladene Zelle würde ungeprüft wieder geladen | offen | T0 | G2: Entscheidung E-3 | dto. |
| HW26-18 | P2 | Durchschlag des TPS70933 legt Panelspannung auf TMP_VCC; Ausfallart der TMP390 unbekannt | offen | T0 | G2: Entscheidung E-4 (Klemmung) | dto. |
| HW26-19 | P2 | Kältereserve bei Ausfall der Kaltsperre Stufe 1: NTC sperrt erst bei ca. +1,7 °C (Toleranz ca. ±1 K) | offen | T0 | G3: Toleranzrechnung, SCH-T03 | dto. |

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
| REG26-05 | P2 | Berichte ohne exakten SHA | im Entwurf behoben (SRV26 `3f2f9d6`, HW26/CI26 `cc6ba60`, SCH26 `2076c20` nachgetragen) | T0 | – | dto. |
| REG26-06 | P1 | Gefährdungsanalyse und sicherer Versuchsplan Akku fehlen | im Entwurf behoben ([`hardware/sicherheit-akku.md`](../../hardware/sicherheit-akku.md) 0.1); Gegenlesen durch zweiten Prüfweg offen | T0 | **G2 Akku** bis Gegenlesen und Entscheidungen E-1 … E-4 | dto. |
| REG26-07 | P1 | Rückverfolgbarkeit D3 fehlt | im Entwurf behoben (`sicherheit-akku.md` Abschnitt 8) | T0 | **G2 Akku** wie REG26-06 | dto. |
| REG26-08 | P2 | Pin-/Footprint-Abgleichbericht fehlt | **im Entwurf behoben** (13.10.2026): `werkzeug/pin_footprint.py` in `pruefen.sh`, Bericht [`hardware/kicad/pin_footprint.md`](../../hardware/kicad/pin_footprint.md): 161 Bauteile, 0 Abweichungen; Footprints U201 und U401 angelegt ([Bericht](2026-10-13-footprints-bienen.md)); offen: SW304, Datenblätter mit [A]/[P]; Akkuhalter 1042 entschieden (HW-02) | T0/T3 lokal | Layout erst nach Anlegen der offenen Footprints | [Bericht 13.10.](2026-10-13-reg26-08-pin-footprint.md) |
| REG26-09 | P2 | PWR_FLAG-Begründungen fehlen | im Entwurf behoben (Beschreibung je Flag im Generator, Tabelle in `hardware/kicad/README.md`) | T3 (`pruefen.sh`, ERC unverändert) | – | dto. |
| REG26-10 | P2 | Board-ID/Revision, Umgebungsbedingungen | im Entwurf behoben (PCB-AKKU-0.1/PCB-MAIN-0.1 im Titelblock, LH-M11); Umgebungswerte sind Annahmen | T0/T3 | G2: Philipp bestätigt die Umgebungswerte | dto. |
| REG26-11 | P2 | Kondensator-Derating, Schienentabelle | analysiert – bestätigt; im Entwurf teilweise behoben (`versorgung.md` 3.9; C204/C208/C209/C212 vergrößert, weil die wirksame Kapazität sonst unter dem Datenblatt-Minimum läge) | T0/T3 | **Layout** bis DC-Bias-Kurven je LCSC-Nummer eingetragen | dto. |
| REG26-12 | P1 | Zellmodell/Datenblatt unbekannt (GOV-04) | offen | – | Fertigung | dto. |
| REG26-13 | P0 | Historischer Generatorbruch auf `6dbba8d` (KiCad-CI rot), durch Nachziehen der führenden Python-Quellen und Checks behoben | **im Entwurf behoben, T3 CI aktuell PASS** | **T3 CI `4c12b6d` 7/7, KiCad 48/48** | G1 aktuell nicht mehr durch diesen Befund gesperrt; G2/G3/G4 Akku weiterhin Sicherheits-/HiL-Gates | Integrationsprüfung `2026-10-09-sch26-generator-regression.md` (nur auf Branch `review/claude-regelwerk-e1-e12`), Issue #2 |
| REG26-14 | P2 | Historische `.kicad_pro`-Quell-Divergenz auf `a0df233`; Generator erzeugt Projektdatei nur falls fehlend | **im Entwurf behoben** | **T3 CI `4c12b6d` PASS** | G1 nicht mehr wegen diesem Generatorproblem gesperrt | Audit 10.10.2026 |

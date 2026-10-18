# Befundregister

**Einzige Stelle für den aktuellen Stand aller Befunde** (Regelwerk 1.1, R-05a). Prüfberichte in diesem Ordner sind historische Snapshots; der Stand hier wird bei jeder Behebung und jedem Nachweis nachgeführt.

**Stand:** 15.10.2026: PLT26-02 R-1/R-2 im Entwurf behoben ([Bericht](2026-10-15-plt26-02-rohprotokoll.md)). Datenplattform PLT26-01 bis PLT26-10 aus Review [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11), [Bewertung](2026-10-15-plattform-review-issue11.md). 14.10.2026: HW-07 (zwei Mikrofone am Audio-ADC, HW26-05) und HW-08 (Layout extern, Platine nur Rahmen), [Bericht](2026-10-14-hw07-mikrofone.md); HW-05 (USB mit VBUS-Erkennung, SCH26-10) und HW-06 (eine Platine, SCH26-06 gegenstandslos), [Bericht](2026-10-14-hw05-hw06-schaltplan.md). 13.10.2026: Blatt Anschlüsse ([Bericht](2026-10-13-sch26-07-anschluesse.md), Basis `969339d`) – damit alle Schaltplanblätter im Entwurf (SCH26-07). Blatt Mikrofon im Entwurf (SCH26-07, [Bericht](2026-10-13-sch26-07-mikrofon.md), Basis main `ecf2918`). 10.10.2026 abends: Blatt Waage im Entwurf (SCH26-07, [Bericht](2026-10-10-sch26-07-waage.md), Basis main `eb9e10b`); Behebung SCH26-09/-12 ([Bericht](2026-10-10-sch26-09-12-behebung.md)), Festlegung USB (SCH26-10) und Analyse Ra-01SH nach Herstellerschaltbild (SCH26-11, [Bericht](2026-10-10-sch26-10-11-analyse.md)), auf Basis main `3ff894a`. Review-Grundlage: unabhängiges Schaltplan-T0-/GitHub-T3-Review von [`4c12b6d`](https://github.com/impyer/bienen-lora-logger/commit/4c12b6d77fdda784b83fffc3b4bdbb88e74cf614), CI [38023150749](https://github.com/impyer/bienen-lora-logger/actions/runs/38023150749) 7/7 PASS. Vorbestand und SAF-AKKU 0.1 bleiben erhalten; CI für den Behebungsstand offen.
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
| SCH26-06 | P2 | Akkukabel ohne Kabelplan | im Entwurf behoben; mit HW-06 (14.10.2026) gegenstandslos: Zelle auf der Hauptplatine, kein Kabel – Schließen durch den Maintainer | T0/T3 | – | dto. |
| SCH26-07 | P2 | Blätter MCU, Funk, Waage, Mikrofon, Anschlüsse fehlen | **im Entwurf behoben** (13.10.2026): alle Blätter vorhanden – MCU, Funk + Flash (10.10.), Waage (10.10., [Bericht](2026-10-10-sch26-07-waage.md)), Mikrofon (13.10., [Bericht](2026-10-13-sch26-07-mikrofon.md)), Anschlüsse (13.10., [Bericht](2026-10-13-sch26-07-anschluesse.md)); Netzprüfung 178/178 mit Gegenproben, ERC nur Footprint-Meldung U201 | T3 | G2 | dto. |
| SCH26-08 | P2 | Eingangsschutz nur nominal | im Entwurf behoben (C201 50 V); Panelmessung offen | T0 | G3 bis Panel-Voc/Isc gemessen | dto. |
| **SCH26-09** | **P1** | J302 Debug-Pinmap widerspricht `anschluesse.md` J10: GND Pin7 vs. Pin5, UART TX Pin5 vs. Pin6 | **im Entwurf behoben**: Generator = Kabelplan (5 GND, 6 TX1, 7 RX1); `netz_tests.py` prüft je Pin und Dokument ↔ Netzliste mit Gegenprobe | **T3 lokal** (KiCad 10.0.7, 74/74, Gegenprobe gegen `4c12b6d` rot); CI auf neuem Commit offen; Durchgang am Muster (T4) offen | G2 Kabelkonfektion erst nach Durchgangsprüfung am Muster | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Issue #4](https://github.com/impyer/bienen-lora-logger/issues/4) |
| **SCH26-10** | **P1** | Selbstversorgte USB-C-Gerätefunktion ohne getrennte VBUS-/Host-Erkennung, PA9 bereits UART-TX | **im Entwurf behoben** durch **HW-05** (Philipp 14.10.2026, ersetzt HW-01): USB auch für Anwendung (CDC); VBUS-Erkennung nach ST AN4879 mit Teiler R307 33 kΩ / R308 82 kΩ an PB13 (PA9 bleibt UART-TX); Netzprüfung VBUS_SENSE, T3 lokal 14.10.2026; vorher (10.10.2026) HW-01: USB nur Laden + ROM-DFU | **T0** (ST AN4879); **T4 offen**: ROM-DFU mit 25-MHz-Quarz, Laden, Ruhestrom bei gestecktem USB | G3 bis DFU am Muster bestätigt | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Analyse 10.10](2026-10-10-sch26-10-11-analyse.md), [Issue #5](https://github.com/impyer/bienen-lora-logger/issues/5) |
| **SCH26-11** | **P1** | Ra-01SH: offene TXEN/RXEN-Lötbrücken, DIO2- und IPEX-HF-Umschaltung nicht am Liefermodul bestätigt | **analysiert** – Herstellerschaltbild (Datenblatt V1.1 S. 12): DIO2 schaltet über Q1-Inverter den SPDT, **TXEN = DIO2 (0 Ω)**, RXEN über R1 „NC“ offen, ANT ∥ IPEX, DC-DC-Spule vorgesehen; Ra-01SCH-Spec bestätigt interne Steuerung. Regel: Brücken offen, PB14/PB15 nur Eingang; `netz_tests.py` prüft die Brücken; Modell `funk_modell.py` | **T0** Hersteller, **T2** Modell, **T3** 79/79; **T4 offen** (F-1…F-7) | G3 Funk / G4 Modulfootprint bis F-1…F-7 | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Analyse 10.10](2026-10-10-sch26-10-11-analyse.md), [Issue #6](https://github.com/impyer/bienen-lora-logger/issues/6) |
| **SCH26-13** | **P2** | Klemmen-Teilenummer DEGSON 15EDGRHC-THR-3.5 (4-polig C7603445) ist zweireihig (2 × 2 Kontakte), die Platine sieht einreihige Klemmen mit eigener Polzahl vor (anschluesse.md 1) | **im Entwurf behoben** (13.10.2026, Entscheidung Philipp: einreihig): DEGSON 15EDGRC-3.5-0nP, LCSC 2P C5160225, 3P C5160226, 4P C7603438, 5P C7603439, 6P C49352918 (alle lieferbar); Footprints `Bienen:DEGSON_15EDGRC-3.5-0nP` (Geometrie EasyEDA/LCSC); Stecker 15EDGK-3.5, 3- und 6-polig noch zu beschaffen | T0 (JLCPCB-Teilesuche, EasyEDA-Geometrie), T3 (ERC 0, Pin/Footprint 0 Abweichungen) | G2 Stückliste; Zeichnung DEGSON vor Bestellung [P] | [Bericht 13.10.](2026-10-13-footprints-bienen.md) |
| **SCH26-12** | **P2** | `pruefen.sh` H1/H2 lässt neue `mcu.kicad_sch`/`funk.kicad_sch` aus, Abschluss-Git-Diff deckt sie aber ab | **im Entwurf behoben**: Dateiliste aus den Ordnern, Abdeckungsprüfung gegen Blattverweise, Modus `--gegenprobe` | **T3 lokal** (alle 6 Dateien, Gegenproben bestanden); CI auf neuem Commit offen | G1 nach grüner CI | [Review 10.10](2026-10-10-main-4c12b6d-schaltplan-review.md), [Behebung 10.10](2026-10-10-sch26-09-12-behebung.md), [Issue #7](https://github.com/impyer/bienen-lora-logger/issues/7) |
| HW26-01 | P0 | Ungeschützte 18650-Zelle | im Entwurf behoben für die neue Platine (HY2111 + FS8205 an der Zelle) | T3 | G3 bis Abschalt-/Freigabeversuch mit Zell-Emulator | [Review 0.3](2026-10-08-hardware-architektur-review.md), `hardware/versorgung.md` 3.4 |
| HW26-02 | P1 | Solar-Eingang und 3,3-V-Regler | im Entwurf behoben (BQ25185, RT9080) | T0/T2 | G3 bis Messung | dto. |
| HW26-03 | P1 | Reale Energiebilanz | im Entwurf behoben (Modell `energiebilanz.py`) | T2 | G3 bis Ruhestrom-/Zyklusmessung | dto. |
| HW26-04 | P1 | Rückspeisung der geschalteten Sensorversorgung | im Entwurf behoben (Pull-ups an 3V3_SW, TPS22917 mit QOD) | T0/T3 | G3 bis SCH-T05 | dto. |
| HW26-05 | P1 | Akustik-Antialiasing und Kalibrierung | im Entwurf behoben – seit **HW-07** (14.10.2026) durch den Delta-Sigma-Audio-ADC TLV320ADC3101 (digitales Dezimationsfilter, feste Verstärkung, zwei Mikrofone zum Kanalvergleich); vorher Analogfilter. Schallkalibrierung offen | T2/T3 | G3 bis Frequenzgang-/Schallkalibrierung | dto., `hardware/mikrofon.md`, [2026-10-14-hw07-mikrofone](2026-10-14-hw07-mikrofone.md) |
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

## Datenplattform (Konzept, Schema, Eingänge)

| ID | Prio | Kurzbeschreibung | Status | Höchster Nachweis | Gesperrtes Gate / nächster Schritt | Quellen |
|---|---|---|---|---|---|---|
| PLT26-01 | P1 | 1:1 Beute–Volk ohne datierten Beschluss; BEEP-Hive→Volk nur als Heuristik | **im Entwurf behoben**: ADR-0003 (Beschluss 15.10.), Importheuristik mit Meldung | T1 (Schema-Tests HB-02/HB-03) | G1 bis Commit ADR-0003 | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-02 | P1 | Rohprotokoll: Schreibfehler in `le_log`/`we_log` werden verschluckt; Replay/Rotation/Sicherung ungetestet (vollständiges Protokoll je Uplink vor Verarbeitung ist vorhanden) | **im Entwurf behoben für R-1/R-2** (15.10.): Rückgabewert, `roh_sha256`, Warnung in der Antwort und im PHP-Fehlerprotokoll; R-4 bis R-6 mit dem Importer offen | T2 (E2E LoRa 81/81 bzw. 82/82 mit Serveruhr 05:00/14:00, original 64/64; Wetter 29/29) | G3 bis Betrieb auf der ThinkStation; R-4–R-6 | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-03 | P1 | Waage nur logisch dem Volk zugeordnet; Auszug (HB-09) nur bei Handpflege richtig | **analysiert – akzeptiert** (Maintainer 15.10., ADR-0003 Nr. 5/9): Zuordnung zum Volk bleibt; Prüfsicht `pruefung_geraet_zuordnung` meldet vergessene Zuordnungen | T1 (HB-01–HB-04, HB-09) | Prüfsicht in der Oberfläche anzeigen | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-04 | P1 | Schreibender Zugriff im Heimnetz ohne Anmeldung | **analysiert – bestätigt**; Entscheidung Maintainer 15.10. (ADR-0003 Nr. 10): Anmeldung auch im Heimnetz, Schreiben nur angemeldet, CSRF-Schutz | T0 | Umsetzung in der Lese-/Schreib-API; Endpunkttest vor Betrieb | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-05 | P2 | 12:00-Platzhalter als exakte Zeit | **im Entwurf behoben**: `zeitgenauigkeit` | T1 | – | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-06 | P2 | Sensorwechsel/Kalibrierung ohne Ablage | **im Entwurf behoben**: `kanal.kalibriert_am`, `kalibrierung`, `sensor` | T1 (Schema lädt) | – | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-07 | P2 | BEEP Base als bestätigt geführt, Inbetriebnahme nicht nachgewiesen | **im Entwurf behoben** (Kennzeichnung, Rückfallplan) | T0 | G3 je Base bis Doppelzustellung nachgewiesen | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-08 | P2 | Abgeleitete Werte ohne Berechnungsversion | **im Entwurf behoben**: Tabelle `berechnung`, Sichten mit `berechnung@version` | T1 | – | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-09 | P2 | BEEP-Import ohne autorisierten Integrationstest; 512 als feste Erwartung | **analysiert**; Wortlaut korrigiert | T0 | Integrationstest im Importer-Schritt | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |
| PLT26-10 | P2 | Bodentiefen nicht verifiziert | **analysiert** – Tiefen vom Betreiber bestätigt (15.10.): 5 cm weiß, 20 cm rot, 50 cm schwarz; Zuordnung Sondenkabel ↔ Decoderfeld an echten Daten prüfen | T0 | Kanalzuordnung beim Anschluss | [Bewertung 15.10.](2026-10-15-plattform-review-issue11.md), [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) |

## Refactoring Webplattform (R0)

Erfasst am 17.10.2026 auf `034c9e1d31612679dcc3cc15155208b9c0c82e72`.
Nachweise und Grenzen: [R0-Bericht](2026-10-17-refactoring-r0.md).
R1-Nachweise auf synthetischen Quellen: [R1-Bericht](2026-10-17-refactoring-r1.md).
**Betreiberentscheidung 17.10.2026:** Der synthetisch geprüfte R1-Entwicklungsstand
`d672d853a3af5341dc0438756266532a66258620` in PR #22 ist ausdrücklich freigegeben
([ADR-0004](../entwicklung/entscheidungen/ADR-0004-umwelt-datenstrecke.md#r1-entwicklungsstand-freigegeben)).
Echte Sensor-/LAN-Abnahme und Produktionsfreigabe bleiben offen. Diese Entscheidung
schließt die nachfolgend abgegrenzten Befunde nicht pauschal.
RF-01–RF-07 verwenden die Auftragskennungen, RF-08–RF-12 ergänzen die Analyse.

| ID | Prio | Kurzbeschreibung | Status | Höchster Nachweis | Gesperrtes Gate / nächster Schritt | Quellen |
|---|---|---|---|---|---|---|
| RF-01 | P1 | Lokale Völker/Entwürfe neben PostgreSQL-Identitäten | analysiert – bestätigt | T0, bestehende Browserprüfungen | R2/R3: kanonische Stammdaten, kontrollierter Offline-Modus | R0, `app.js:18–106` |
| RF-02 | P1 | Anmeldung/Server-Völkerwahl im separaten Stockkartenmodal | im Entwurf teilweise behoben: sichtbarer Umwelt-Login und gemeinsame Sitzung; Modal bleibt | T2: realer Browser nutzt Stockkarte ohne zweiten Login | R3: konsolidierte Navigation/kanonische Völkerliste; Betreiber-UX-Abnahme | R0/R1, `stockkarte_live.js`, `umwelt.js` |
| RF-03 | P1 | Umweltseite ohne API-Zeitreihen/ECharts, feste Boden-Einzelwerte | im Entwurf behoben: echte API-/ECharts-Strecke mit synthetischer Kennzeichnung | T2: Wetter und drei Bodentiefen, Null/Lücken, Live-Poll 29,631 bzw. 29,769 s | R1: autorisierte Echtdaten und Laptop-LAN-Abnahme | R0/R1, Umwelt-API/UI |
| RF-04 | P1 | Kein Wetter-/Boden-Dateiimport im Teststack | im Entwurf behoben: expliziter atomarer Read-only-Import, Provenienz/Revisionen und optionaler Watcher | T1/T2: Idempotenz, Fehler/Restart, zwei RO-Mounts | R1: reale Quell-/Zeit-/Sondenidentitäten bestätigen; R5 Langzeitarchive | R0/R1, `umwelt/`, Compose-Overlay |
| RF-05 | P1 | Synthetischer Beispielkatalog statt vollständiger BEEP-Taxonomie | analysiert – bestätigt | T0, sechs Kategorien in `seed_demo` | R4: autorisierte Referenz und Fachtests | R0, `stockkarte_admin.py:31–63` |
| RF-06 | P1 | Browser-API-Brücke simuliert Antworten; kein vollständiger Umwelt-Browser-E2E | im Entwurf behoben: zusätzlicher vollständiger Umwelt-E2E ohne simulierte HTTP-Antworten | T2: echte DB/API/CA-geprüftes HTTPS/CSV-Watcher/ECharts | R1: physische LAN-/Fachabnahme; bestehende Mock-Regression bleibt Zusatz | R0/R1, `tests/umwelt/e2e.py` |
| RF-07 | P1 | Destruktives Grundschema, zwei Stockkartenmodelle, kein allgemeiner Updatevertrag | im Entwurf teilweise behoben: explizite additive Migration 003 mit Prüfsumme, kein Basis-Rebuild | T2: Alt-Revision unverändert, Backup/Restore in getrennte DB | R4/R5: allgemeiner Altbestandsvertrag/Modellkonsolidierung; schema.sql nur leere Testinitialisierung | R0/R1, Migrationen 001–003 |
| RF-08 | P1 | Cookie nur Stockkartenpfad, explizite Umwelt-Standrechte fehlen | im Entwurf behoben: Cookie `/api/v1`, alte Pfadvariante gelöscht, explizite Standrechte | T2: gemeinsamer Login, CSRF, Logout, fremder Stand 404, aktiver Entzug | R1: fachliche LAN-/Rechteabnahme; R5 umfassender Betriebs-Sicherheitsnachweis | R0/R1, Session-API, Migration 003 |
| RF-09 | P1 | Messwert außerhalb `kanal.gueltig` akzeptiert und normalisiert angezeigt | im Entwurf behoben: Schreibtrigger und gefilterte Lesesicht; unzulässiger Altbestand blockiert Migration | T1/T2: SQL-Grenztest auf echter DB | Echtdatenabnahme; R2 weitere Geräte-/Zuordnungsfälle | R0/R1, Migration 003 |
| RF-10 | P1 | Faktor-/Versatzänderung verändert historische Sicht ohne Messrevision | im Entwurf behoben: Schutz benutzter Kanäle, Korrekturrevisionen, neue Kalibrierabschnitte erforderlich | T1/T2: Faktoränderung abgewiesen, Original-/Korrekturwerte erhalten | Echtdatenabnahme; R2 fachlicher Kalibrierwechsel | R0/R1, Migration 003, Importtests |
| RF-11 | P2 | Laufzeitabhängigkeiten mit Versionsbereichen, Container ohne Digest-Lock | im Entwurf teilweise behoben: Python-/ECharts-Lock und drei Image-Digests für R1 | T3: reproduzierte Browserassets, Containerbuild mit gelockten Wheels | R5: vorhandene weitere CI-Versionen vereinheitlichen, Dauer-/Updatebetrieb prüfen | R0/R1, Dockerfile/Compose/CI |
| RF-12 | P2 | Katalog-SQL/DTOs und Fachvalidierung mehrfach, kein vollständiger Konformitätskorpus | analysiert – bestätigt als Wartungsrisiko, kein pauschaler Funktionsdefekt | T0, vorhandene Teiltests PASS | R1/R4 gezielte gemeinsame Verträge; gute Bausteine erhalten | R0, API/Session/Store/native JS |

## Refactoring R1.1

Erfasst auf R1 `91284796`, Nachweise: [Bestandsaufnahme](2026-10-17-refactoring-r1-1-bestand.md)
und [R1.1-Implementierung/Tests](2026-10-17-refactoring-r1-1.md).
Die Auftragskennungen bleiben erhalten; kein tatsächlicher Feldnachweis aus synthetischen Daten.

| ID | Prio | Kurzbeschreibung | Status | Höchster Nachweis | Nächster Schritt |
|---|---|---|---|---|---|
| R1.1-01 | P1 | Langzeitdiagramm lädt keine Folgeseiten, jüngster Wert fehlt | im Entwurf behoben | T1/T2: Snapshot-/ACL-Grenzen, echter HTTPS-Browser 24 h bis Saison, jüngster Punkt/live Poll | Betreiberreview und Remote-CI; R11-A11 separat |
| R1.1-02 | P1 | Fortlaufende Monatsarchive/Rotation fehlen | im Entwurf behoben | T1/T2: Monat/Append/Rename/Backfill/Provenienz, Monatsarchiv-Browser | synthetischen Entwicklungsstand reviewen; realen Quellwechsel separat planen |
| R1.1-03 | P1 | Echte Sensor-/LAN-Dateien noch nicht abgenommen | offen | Kein T4/T5 | R11-A11 nach gesonderter Betreibererlaubnis |
| R1.1-04 | P2 | Vollscan/32-MiB-Grenze und SQL pro Messwert | im Entwurf behoben | T1/T2: Streaming/500er-Batches, 147-MB-Jahr, 48-MB-Datei/Append, Ressourcen gemessen | Prefix-Hash bleibt O(Dateigröße); Dauer-/Mehrbenutzerlast und Log-Retention planen |
| R1.1-05 | P2 | Manuelle Quell-/ID-Wechsel ohne Inventur/Diagnose | im Entwurf behoben | T1: nur lesende Inventur, wiederholbare Registrierung/harte Widerspruchsprüfung, ungültige Beispiel-IDs | lokale Betreiberprüfung tatsächlicher IDs/Zeitbasis/Quellen vor R11-A11 |
| R1.1-06 | P2 | Importer erbt breite DB-/App-Konfiguration | im Entwurf behoben | T1/T2: separate reale Login-Verbindung, negative SQL-Rechte, Container ohne App-DSN/Sitzungsschlüssel | explizite BL_IMPORT_DSN-Umstellung im freigegebenen Teststack, kein automatisches Deployment |

## R1.1-Stabilisierung 18.10.2026

Auftrag T01–T10, Ausgangsstand 974c6c4. Nachweise und Beweisgrenzen:
[Abschlussprüfung](2026-10-18-refactoring-r1-1-stabilisierung.md).

| ID | Prio | Befund | Status | Nachweis / nächster Schritt |
|---|---|---|---|---|
| R11-S01 | P1 | Konflikt-QC fehlt über Batch-/Monatsgrenzen | im Entwurf behoben | T1/T2: rote Fälle, neue Revision mit QC, Idempotenz/Backfill/Originale; unabhängige CI offen |
| R11-S02 | P1 | Gleichzeitige Snapshot-Aufbauten nicht begrenzt | im Entwurf behoben | Zwei zugelassene Verarbeitungen, reale SQL-Lock-Konkurrenz/503/Freigabe; kein globaler RSS-Nachweis |
| R11-S03 | P1 | 17 Kanäle als Standard, unnötige unverdichtbare Reihen | im Entwurf behoben | Registerbasierter Temperaturüberblick, echter 7/30-Tage-/Saisonbrowser; optionale Kanalwahl erhalten |
| R11-S04 | P1 | Zoom/Legende gehen beim regulären Poll verloren | im Entwurf behoben | Gleiche zwei ECharts-/DOM-Instanzen über drei echte Polls, Zoom/Legende/Heap geprüft |
| R11-S05 | P1 | Saison beginnt eine Stunde nach Berliner Mitternacht | im Entwurf behoben | Roter echter Request und korrekter UTC-Start für Berliner Jahresgrenze; API-Offsets geprüft |
| R11-S06 | P2 | Sichere Original→Staging-Bereitstellung noch ohne Teststrecke | im Entwurf behoben (nur synthetisch) | Reale Dateisync/CLI, atomare Kopien, Sync→PostgreSQL; neue reale Rechte/Originalpfade bleiben gesondert offen |
| R11-S08 | P1 | Gemeinsamer Session-Principal liefert bei echter DB-Verbindungsunterbrechung HTTP 500 | im Entwurf behoben | Echter roter Browserlauf; enger 503-/Retry-After-Handler ohne Daten-/Rechteänderung, Wiederaufnahme separat geprüft |
| R11-S07 | P1 | Implementierungs-PR/unabhängige CI fehlen; allgemeiner Workflow nur gegen main | im Entwurf teilweise behoben; CI/PR offen | R1-Branchfilter ergänzt, API-CONNECT 403 dokumentiert; G1/technischer Abschluss bis externem Nachweis blockiert |

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
| REG26-08 | P2 | Pin-/Footprint-Abgleichbericht fehlt | **im Entwurf behoben** (13.10.2026): `werkzeug/pin_footprint.py` in `pruefen.sh`, Bericht [`hardware/kicad/pin_footprint.md`](../../hardware/kicad/pin_footprint.md): 161 Bauteile, 0 Abweichungen; Footprints U201 und U401 angelegt ([Bericht](2026-10-13-footprints-bienen.md)); alle Footprints vorhanden (Reed MRS03-B-3, LED LTST-S220 am 13.10.); offen: Datenblätter mit [A]/[P]; Akkuhalter 1042 entschieden (HW-02) | T0/T3 lokal | Layout erst nach Anlegen der offenen Footprints | [Bericht 13.10.](2026-10-13-reg26-08-pin-footprint.md) |
| REG26-09 | P2 | PWR_FLAG-Begründungen fehlen | im Entwurf behoben (Beschreibung je Flag im Generator, Tabelle in `hardware/kicad/README.md`) | T3 (`pruefen.sh`, ERC unverändert) | – | dto. |
| REG26-10 | P2 | Board-ID/Revision, Umgebungsbedingungen | im Entwurf behoben (PCB-AKKU-0.1/PCB-MAIN-0.1 im Titelblock, LH-M11); Umgebungswerte sind Annahmen | T0/T3 | G2: Philipp bestätigt die Umgebungswerte | dto. |
| REG26-11 | P2 | Kondensator-Derating, Schienentabelle | analysiert – bestätigt; im Entwurf teilweise behoben (`versorgung.md` 3.9; C204/C208/C209/C212 vergrößert, weil die wirksame Kapazität sonst unter dem Datenblatt-Minimum läge) | T0/T3 | **Layout** bis DC-Bias-Kurven je LCSC-Nummer eingetragen | dto. |
| REG26-12 | P1 | Zellmodell/Datenblatt unbekannt (GOV-04) | offen | – | Fertigung | dto. |
| REG26-13 | P0 | Historischer Generatorbruch auf `6dbba8d` (KiCad-CI rot), durch Nachziehen der führenden Python-Quellen und Checks behoben | **im Entwurf behoben, T3 CI aktuell PASS** | **T3 CI `4c12b6d` 7/7, KiCad 48/48** | G1 aktuell nicht mehr durch diesen Befund gesperrt; G2/G3/G4 Akku weiterhin Sicherheits-/HiL-Gates | Integrationsprüfung `2026-10-09-sch26-generator-regression.md` (nur auf Branch `review/claude-regelwerk-e1-e12`), Issue #2 |
| REG26-14 | P2 | Historische `.kicad_pro`-Quell-Divergenz auf `a0df233`; Generator erzeugt Projektdatei nur falls fehlend | **im Entwurf behoben** | **T3 CI `4c12b6d` PASS** | G1 nicht mehr wegen diesem Generatorproblem gesperrt | Audit 10.10.2026 |

# Testberichte und offene Prüfpunkte

Dieser Ordner enthält nachvollziehbare, **commitbezogene** Reviews zum Projekt Bienenlogger. Die Berichte sind Dokumentation, keine automatische Fehlerbehebung. Neue Implementierungen sollen Befund-IDs referenzieren und mit Tests gegen die angegebenen Akzeptanzkriterien abgesichert werden.

**Aktueller Stand aller Befunde: [Befundregister](befunde.md)** (einzige Stelle, Regelwerk 1.1 R-05a). Die Berichte unten und die Abschnitte darunter sind historische Snapshots.

## Berichtsverzeichnis

| Bericht | Stand | Verifikation |
|---|---|---|
| **[Schaltplan-Review: Einsparungen, Pin-Kniffe, SPICE-Prüfung](2026-10-18-schaltplan-optimierung.md)** | **18.10.2026, Stand `7aa1fe5`** | **ngspice (KiCad 10) 12/12: Elektretpfad, HX711-AVDD, BLE-Lastschalter, RN4871-Reset, ADC-Teiler, Sensorschiene, 1-Wire; Vorschläge: −6 Teile ohne Funktionsverlust, 5-V-Wandler der Waage zur Entscheidung (−6, −0,5 mAh/Tag, PB10 frei), Sanftanlauf BLE, Pin-Tauschgruppen; neuer Befund HW26-21 (ADC-Teiler-Leckstrom); keine Fehler** |
| **[Pinfunktionen aller ICs und Module gegen Datenblätter](2026-10-18-pinfunktionen-review.md)** | **18.10.2026, Stand HW-10** | **STM32F411 (ST open pin data), TLV320ADC3101, BQ25185, TPS22917 (CT an VIN bestätigt), TPS61240, TMP390, HY2111, FS8205, AO3400A/AO3401A, 74LVC1G17, HX711, RN4871, Ra-01SH, ESD-Arrays: Symbol = Datenblatt, Netze plausibel; offen: S8550-Pinfolge, Flash-Typ, Keystone-Polung, RJ45-Teil, DEGSON-Zeichnung, TVS D401** |
| **[Schaltplan-Freigabe für den Layout-Auftrag](2026-10-18-layout-uebergabe.md)** | **18.10.2026, Commit `4c36898`** | **Titelblock „0.1 Layout-Stand“; pruefen.sh reproduzierbar, ERC 0, Netzprüfung 220/220, Pin/Footprint 177/0; Rahmen-DRC 0; Paket `layout-auftrag-PCB-MAIN-0.1-4c36898.zip` entpackt ERC 0 / DRC 0; Pflichtenheft issue 3; G1 vorbehaltlich CI, keine Bestellfreigabe** |
| **[HW-09: BLE-Modul RN4871 an USART6, USB-C entfällt](2026-10-18-hw09-ble-rn4871.md)** | **18.10.2026, Basis `66a3ba2`** | **RN4871 (U303) mit Lastschalter Q301 an PB13, UART über 1 kΩ, Pull-ups nur an BLE_VCC, J704 Pin 9–11; USB-C durch zwei Ladepads J301 ersetzt (Nachtrag), U302/R303/R304/R307/R308 entfernt; Footprint mit Sperrzonen nach Fig. 4-8/4-9; ERC 0, Netzprüfung 220/220, Pin/Footprint 177/0; T0/T3, kein Muster, keine BLE-Firmware** |
| **[HW-07/HW-08: zwei Mikrofone am Audio-ADC, Layout extern](2026-10-14-hw07-mikrofone.md)** | **14.10.2026, Basis `bbabcd4` + Lieferungen HW-05/HW-06 und Aufräumen** | **TLV320ADC3101 mit Elektret (analog) + IM69D127 (PDM), I²S an PB12/PA15/PB5, RJ45 für Cat7; Taktplan gegen Datenblattgrenzen gerechnet; ERC 0, Netzprüfung 187/187, Pin/Footprint 0; Platine nur Rahmen, Platzierungs-/Routing-Skripte entfernt** |
| [HW-05/HW-06: USB mit VBUS-Erkennung, Akku auf der Hauptplatine](2026-10-14-hw05-hw06-schaltplan.md) | 14.10.2026, Basis `bbabcd4` + Routing-Lieferung | Blatt Akku (Schaltung unverändert, B− ≠ GND geprüft), VBUS-Teiler an PB13; Akku-Platine entfernt; ERC 0, Netzprüfung 168/168, Pin/Footprint 0; Platine neu platziert, ohne Routing (Layouter) |
| **[Platine: Routing, Platzierung optimiert](2026-10-13-platine-routing.md)** | **13.10.2026, Basis `bbabcd4`** | **Freerouting 1.9.0 + Vorverlegung (Quarze, VCAP/VDDA, BQ25185, TPS61240) + Gitter-Router; Platzierung aus dem Routing verbessert (Kondensatoren an STM32-Ecken, J704/SW303 näher, Freiraum um U201); 6 von 202 Verbindungen offen, DRC 0, Schaltplanabgleich 0** |
| **[Platine: Fanout GND/+3V3](2026-10-13-platine-fanout.md)** | **13.10.2026, Basis `dd61bc9` + L3** | **120 Anbindungen von SMD-Pads an GND/+3V3 zu L2/L3 (Via 0,6/0,3, Abstand ≥ 0,2 mm); DRC 0, Schaltplanabgleich 0; offene Verbindungen 322 → 202** |
| **[Platine: Versorgungslage L3](2026-10-13-platine-lage-l3.md)** | **13.10.2026, Basis `dd61bc9`** | **L3: +3V3-Fläche über MCU/Funk mit Arm zu den Reglern, Rest GND-Füllung; DRC 0, Schaltplanabgleich 0; SYS/3V3_SW/5 V als Leiterbahnen beim Routing** |
| **[Platine: Feinplatzierung, Masse L2](2026-10-13-platine-feinplatzierung.md)** | **13.10.2026, Basis `751de0f`** | **34 Bauteile an STM32, Ra-01SH und TPS61240 gesetzt (Abblock-C 1,7–2,4 mm am Pin), 13 Thermal-Vias, GND-Fläche L2; DRC 0 Verstöße, Schaltplanabgleich 0; offen: Via-Füllung [P], Routing** |
| **[Gehäuse CBHUB-02: STEP-Kontrolle](2026-10-13-gehaeuse-step.md)** | **13.10.2026, Basis `4fe34a6` + Grobplatzierung** | **Lochbild 110,2 mm bestätigt, keine Kollision; Freiraum über der Platine ≥ 44,3 mm (HW-03 erfüllt), darunter ≥ 13 mm; Fund: Dombohrung Ø 2,4 mm statt 3,6 mm; Lichtleiter ca. 19,4 mm, Bohrungsmitte ca. 22,7 mm vom Boden** |
| **[Platine: Grobplatzierung](2026-10-13-platine-grobplatzierung.md)** | **13.10.2026, Basis `4fe34a6`** | **139 Bauteile per `platine_bestuecken.py` auf logger.kicad_pcb, Regeln M5/A3; Schaltplanabgleich 0, DRC ohne Kupfer-/Courtyard-Verstöße; Funde: Testpunkte/Lötbrücken nicht in Stückliste, Klemmenreihe knapp [P]** |
| **[Projektfootprints BQ25185 / Ra-01SH](2026-10-13-footprints-bienen.md)** | **13.10.2026, Basis `675f6c1`** | **Bienen.pretty: DLH0010A nach TI, Ra-01SH nach Ai-Thinker; ERC 0; Funde: Vias BQ25185, Keystone 1042 (SMD) ≠ 1043 (THT), SCH26-13 Klemmen zweireihig** |
| **[Pin-/Footprint-Abgleich](2026-10-13-reg26-08-pin-footprint.md)** | **13.10.2026, Basis `ecce931`** | **REG26-08 im Entwurf behoben: `pin_footprint.py` in `pruefen.sh`, 161 Bauteile, 0 Abweichungen; Funde: 5 fehlende Footprint-Zuordnungen, Polung TVS D401; offen: Footprints U201/U401/SW304, [A]/[P]-Datenblätter** |
| **[Schaltplanblatt Anschlüsse](2026-10-13-sch26-07-anschluesse.md)** | **13.10.2026, Basis `969339d`** | **SCH26-07 letztes Blatt: DS18B20 J701/J702, BME280 J703 (6-polig), Erweiterung J704, ESDS304, Pull-ups an 3V3_SW; T3 lokal 178/178, ERC nur Footprint U201; CI offen, kein Muster** |
| **[Schaltplanblatt Mikrofon](2026-10-13-sch26-07-mikrofon.md)** | **13.10.2026, Basis `ecf2918`** | **SCH26-07 Teil Mikrofon im Entwurf: 3V3_ANA, Hochpass 22 Hz, Sallen-Key 1179 Hz/Q 0,74 mit TLV9001IDBVR (statt LMV321TP), J601 = J5 mit ESDS304; T3 lokal 139/139, Gegenproben; CI offen, kein Muster** |
| **[Schaltplanblatt Waage](2026-10-10-sch26-07-waage.md)** | **10.10.2026, Basis `eb9e10b`** | **SCH26-07 Teil Waage im Entwurf: TPS61240, HX711 (AVDD 4,30 V), J501 = J4 mit ESD und Filter; T3 lokal 114/114, Gegenproben; CI offen, kein Muster** |
| **[Analyse USB-Rolle und Ra-01SH-HF-Schalter](2026-10-10-sch26-10-11-analyse.md)** | **10.10.2026, Basis `3ff894a`** | **SCH26-10 Festlegung HW-01 (USB nur Laden/DFU); SCH26-11 Herstellerschaltbild: TXEN = DIO2, Brücken offen, Modell `funk_modell.py`; T4 F-1…F-7 offen** |
| **[Behebung SCH26-09 bis -12](2026-10-10-sch26-09-12-behebung.md)** | **10.10.2026, Basis `4c12b6d`** | **SCH26-09/-12 im Entwurf behoben (T3 lokal, 74/74, Gegenproben); CI offen, kein HiL** |
| **[Neuestes unabhängiges Schaltplan-Review: main 4c12b6d](2026-10-10-main-4c12b6d-schaltplan-review.md)** | **10.10.2026, SHA `4c12b6d`** | **7/7 CI PASS, KiCad 48/48 Netztests, ERC 0 unerwartete; P1 Debug-Pinout, USB-VBUS, Ra-01SH-RF, P2 Doppelhash; kein HiL** |
| **[Audit Arbeitsergebnisse gegen Regelwerk 1.1](2026-10-09-regelwerk-audit.md)** | **`428d101`** + Arbeitskopie Claude | **T0/T3; REG26-01 (P0): SCH26-Behebung lokal verworfen, wiederhergestellt; 12 Befunde** |
| **[Review Entwicklungsregelwerk 1.0 (Claude)](2026-10-09-regelwerk-review.md)** | **`8fc2aa4`** | **Dokumenten-Review (T0); Entscheidungen in ADR-0002 (Regelwerk 1.1)** |
| **[Behebung SCH26-01 … -08](2026-10-09-sch26-behebung.md)** | **Arbeitsstand nach `fcd18fe`** (Commit-ID beim Einchecken nachtragen) | **SCH26-01 bestätigt und behoben (Ladesperre aus TMP_VCC am Ladereingang); SCH26-02/03/05/06/08 behoben; KiCad 10: reproduzierbar, ERC alle Schweregrade OK, 42/42 Netzprüfungen an KiCad-Netzlisten, Gegenprobe; CI-Job neu, Lauf offen; kein Muster** |
| **[Schaltplan V0.1 – Akku + Versorgung, unabhängige Netz-/Sicherheitsprüfung](2026-10-09-schaltplan-v01-review.md)** | **Commit `fcd18fe`** | **48 Komponenten und 95 Netlabels aus eingecheckten KiCad-Dateien geprüft; Herstellerabgleich/Recovery-Fallanalyse; KiCad-ERC nicht unabhängig ausgeführt, kein HiL** |
| **[Behebung HW26-07 … -15 und CI26-01](2026-10-09-hw04-ci26-behebung.md)** | **Commit `cc6ba60`** | **CI26-01: Ursache reproduziert (Kürzung von week.csv vor 08:00), behoben, Gegenprobe; E2E eigen 74/74 bei 05:00 und 14:00, original 56/56, Unit 66/66; CI-Lauf offen. Hardware: Entwurfsänderungen, Rechnungen; kein KiCad/HiL** |
| **[Hardware 0.4 – unabhängiges Review, Versorgung/Pinout/PCB](2026-10-09-hardware-04-review.md)** | **Hardware-Commit `5c94e1b`, CI bis `6b83d`** | **Konzept- und numerisches SiL-Review; P0 Akku-HOT, P1 PV-ADC/I²C, CI-Regression; noch kein KiCad/HiL** |
| **[Behebung SRV26-02/03/04/05/07/08](2026-10-08-srv26-behebung.md)** | **Commit `3f2f9d6`** | **Host-/E2E-Tests lokal (eigen 73/73, original 56/56, Unit 59/59), Gegenprobe ohne Korrektur; CI-Lauf offen; kein TTN/BEEP/HiL** |
| [main 5c1b847 — Firmware 261010, UTC-Server, Regression](2026-10-08-main-5c1b847-regression.md) | Commit `5c1b847` | 5/5 CI-Jobs erfolgreich; neuer unabhängiger UTC-Teilupdate-Spotcheck; kein HiL |
| [Firmware 261009 — Code-Review und isolierte SiL-Spotchecks](2026-10-08-firmware-261009-sil.md) | Commit `d735f0f` | Statisch + isolierter Host-Rechentest; kein MCU-/HiL-Test |
| [TTN-Formatter und LoRa-Server-Eingang](2026-10-08-ttn-formatter-server-review.md) | Commit `f252677`, nachverifiziert `d735f0f` | Code/CI/Integration; kein produktiver TTN-/BEEP-Test |
| [LoRaWAN-Zeitabgleich ZS](2026-10-08-zs-review.md) | ZS `de72645`, ZS-Logik in `d735f0f` | Host-Tests/Modellsimulation; kein HiL |
| [Hardware-Entwurf: Prüfliste](2026-10-08-hardware-architektur-review.md) | Lastenheft 0.3 in `d735f0f` | Konzeptreview; kein KiCad-/HiL-Nachweis |

## Aktuell: GitHub-main `4c12b6d` (10.10.2026)

**[Unabhängiges Hardware-Review 10.10.2026](2026-10-10-main-4c12b6d-schaltplan-review.md):** Der frühere KiCad-Generatorbruch `REG26-13` ist behoben: [CI 38023150749](https://github.com/impyer/bienen-lora-logger/actions/runs/38023150749) **7/7 Jobs PASS**, 19 Akku- und 69 Hauptplatinen-Netze, 48/48 Netzprüfungen, ERC Akku 0 und Hauptplatine 11 begründete Warnungen. Neue Blätter MCU und Funk/Flash vorhanden; Waage, Mikrofon, Anschlüsse weiterhin ausstehend.

**Neu:** `SCH26-09` P1 widersprüchliche Debug-J302/J10-Stecker-Pinfolge ([#4](https://github.com/impyer/bienen-lora-logger/issues/4)), `SCH26-10` P1 USB ohne unabhängige VBUS-Erkennung ([#5](https://github.com/impyer/bienen-lora-logger/issues/5)), `SCH26-11` P1 Ra-01SH-DIO2/TXEN/RXEN/IPEX nicht verifiziert ([#6](https://github.com/impyer/bienen-lora-logger/issues/6)), `SCH26-12` P2 doppelte Reproduzierbarkeitsprüfung ohne neue zwei Blätter ([#7](https://github.com/impyer/bienen-lora-logger/issues/7)). **D3-Akkuschutz nur im Entwurf, kein G2/G3/G4-Sign-off.** Der untenstehende Schaltplan-V0.1-Abschnitt ist historisch.

## Aktuell: Behebung Schaltplan-Review V0.1 (09.10.2026)

**Maßgeblich:** [Behebung SCH26-01 … -08](2026-10-09-sch26-behebung.md).

- **`SCH26-01` (P0) bestätigt und im Schaltplan behoben:** Ladesperre (2 × TMP390, Pull-ups) hängt an TMP_VCC aus einem LDO TPS70933 am Ladereingang; Wiederanlauf nach Tiefentladung möglich; keine Verbindung zu B+/B−. Nachweis am Muster (SCH-T04) offen.
- **`SCH26-02/03` behoben:** Pull-ups 100 kΩ (Pegel gerechnet), zweite unabhängige 42-°C-Stufe öffnet den NTC-Kreis.
- **`SCH26-04` behoben bis auf Footprints:** `pruefen.sh` mit Reproduzierbarkeit, ERC aller Schweregrade gegen `erc_erwartet.json`, `netz_tests.py`; CI-Job `kicad-schaltplan`.
- **`SCH26-05/06/08` behoben**, `SCH26-07` = nächste Blätter.

## Schaltplan V0.1 (09.10.2026, Review)

**Maßgeblich:** [Schaltplan-Review V0.1](2026-10-09-schaltplan-v01-review.md), geprüfter Commit `fcd18fe`.

- **P0 `SCH26-01`:** möglicher Lade-Recovery-Deadlock nach HY2111-Tiefentladeschutz, da TMP390 an geschütztem Akku-Minus versorgt und der BQ25185 /CE ohne TMP390 über R205 HIGH ist. Zuerst mit Schutz-FET/Body-Dioden und strombegrenztem Zell-Emulator nachweisen; *Hypothese, noch kein HiL*.
- **P1 `SCH26-02`/`SCH26-03`:** extrem hochohmige Ladefreigabe (R5/R205 jeweils 10 MΩ) und fehlende 45-°C-Einzelfehlertoleranz (Backup-NTC HOT erst ~59,5 °C).
- **P1 `SCH26-04`:** KiCad/ERC/Footprint- und Generator-Check fehlt in der CI; kritischer BQ25185-Footprint noch nicht vorhanden.
- **P2 `SCH26-05`–`SCH26-08`:** R208 1 MΩ statt dokumentierter 100 kΩ, Kabelbaum, fehlende Funktionsblätter, PV-Transientenschutz.
- **CI auf `fcd18fe`:** 6/6 Jobs erfolgreich. Das ist **keine KiCad-/Sicherheitstestfreigabe**. Insgesamt bisher nur Akku- und Versorgungsteil: kein MCU-/Funk-/Waage-/Mikrofonschaltplan.

## Behebung nach Hardware-Review 0.4 (09.10.2026)

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

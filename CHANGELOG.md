# Änderungen

## 2026-10-13 – Schaltplanblatt Anschlüsse, Schaltplan vollständig (SCH26-07)

- **Neues Blatt „Anschlüsse“** (`hauptplatine/anschluesse.kicad_sch`, Teile 7xx): DS18B20-Klemmen J701/J702 (= J6/J7) am gemeinsamen 1-Wire-Bus PA8 mit 4,7 kΩ an 3V3_SW und ESDS304; BME280-Klemme J703 (= J8, 6-polig, Pin 6 frei) mit 1,8-kΩ-Pull-ups an 3V3_SW und ESDS304; Erweiterungsleiste J704 (= J11, 2 × 6). Damit sind alle Blätter der Hauptplatine im Entwurf; SCH26-07 im Entwurf behoben.
- DBG_TX/DBG_RX sind jetzt globale Netze (Debug-Leiste und Erweiterungsleiste). `anschluesse.md`: Platinenreferenzen J701–J704.
- `netz_tests.py`: Blatt Anschlüsse (Netze, Pull-ups nur an 3V3_SW mit Gegenprobe, ESD, Polzahlen, Masse an Pin 1, J8-Pin 6 frei) und Stecker J6/J7/J8/J11 gegen `anschluesse.md`; freie Pins werden als unverbunden erwartet. 139 → 178 Prüfungen.
- ERC Hauptplatine 7 → 1 erwartete Meldung (nur der fehlende Footprint U201). Prüfung lokal mit KiCad 10.0.6: reproduzierbar, 178/178, Gegenproben bestanden. Stückliste 161 Teile. Bericht: `docs/testberichte/2026-10-13-sch26-07-anschluesse.md`.

## 2026-10-13 – Schaltplanblatt Mikrofon (SCH26-07, Teil Mikrofon)

- **Neues Blatt „Mikrofon“** auf der Hauptplatine (`hauptplatine/mikrofon.kicad_sch`, Teile 6xx): Siebung 3V3_SW → Ferrit → 47 Ω → 3V3_ANA (22 µF + 100 nF), Vorspannung 1,65 V (2 × 47 kΩ, 1 µF), Klemme J601 (= J5) mit ESDS304 direkt an OUT und VCC, 100 Ω, Hochpass 22 Hz, Sallen-Key 1179 Hz / Q 0,74 als Spannungsfolger, RC 4,8 kHz vor PA1 (MIC_ADC).
- **Operationsverstärker TLV9001IDBVR** (C398363) statt LMV321TP (C90297 laut LCSC am 13.10.2026 nicht lieferbar, TLV9001IDBVR dort 39.765 Stück; Pinfolge der 3PEAK-Variante nicht bestätigt). Pinfolge DBV nach TI-Datenblatt; TLV9001U passt nicht. ESD-Lage an die Regel „direkt hinter der Klemme“ angeglichen. `mikrofon.md` (2.1, Skizze, 7, neuer Abschnitt 8), `anschluesse.md` J5 (Platine: J601).
- Prüfwerkzeug: `netz_tests.py` prüft das Blatt Mikrofon (Siebung, VREF, ESD-Lage, Hochpass, Sallen-Key-f0/Q und RC aus den Bauteilwerten mit Gegenprobe, Spannungsfolger, J5/J601 gegen `anschluesse.md`), 114 → 139 Prüfungen.
- ERC Hauptplatine 8 → 7 erwartete Meldungen (MIC_ADC hat jetzt seine Gegenstelle). Prüfung lokal mit KiCad 10.0.6: reproduzierbar, 139/139, Gegenproben bestanden; ältere Blätter unverändert; CI und Muster offen. Stückliste 152 Teile. Bericht: `docs/testberichte/2026-10-13-sch26-07-mikrofon.md`.

## 2026-10-10 – Schaltplanblatt Waage (SCH26-07, Teil Waage)

- **Neues Blatt „Waage“** auf der Hauptplatine (`hauptplatine/waage.kicad_sch`, Teile 5xx): 5-V-Wandler TPS61240 an SYS (EN = PB10 mit 100 kΩ nach GND, 1 µH, Ferrit zu VSUP), HX711 mit AVDD 4,30 V über S8550 und 20 k/8,2 k, DVDD an 3V3_SW, je 1 kΩ zu PB8/PB9, Wägezellenklemme J501 (= J4) mit TPD4E05U06, 100 Ω, 100 nF und 2 × 10 nF C0G. Kanal B über 0 Ω an INA− [A].
- `waage.md`: Spulen- und Kondensatorwerte nach TI-Datenblatt, Kanal B, **Ferrit in E+ mit ≤ 0,1 Ω** (neue Rechnung 4.1: Temperaturgang des Leitungswiderstands), Abschnitt 9 Schaltplan, Prüfpunkte 6–8. `anschluesse.md`: J4 (Platine: J501).
- Prüfwerkzeug: `netz_tests.py` prüft das Blatt Waage (Wandler an SYS, EN-Pull-down, FB an VOUT, AVDD aus den Teilerwerten mit Gegenprobe, Zellenleitungen, J4/J501 gegen `anschluesse.md`), 79 → 114 Prüfungen. Neues Symbol TPS61240 (`symbole.py`). `kicad_gen.py`: gemeinsames GND-Symbol für verbundene GND-Pins, feste Textlage; ältere Blätter unverändert.
- ERC Hauptplatine 11 → 8 erwartete Meldungen (HX_DOUT, HX_SCK, WAAGE_EIN haben jetzt ihre Gegenstelle). Prüfung lokal mit KiCad 10.0.7: reproduzierbar, 114/114, Gegenproben bestanden; CI und Muster offen. Bericht: `docs/testberichte/2026-10-10-sch26-07-waage.md`.

## 2026-10-10 – USB-Rolle festgelegt, Ra-01SH nach Herstellerschaltbild (SCH26-10/-11)

- **SCH26-10 / HW-01:** USB-C nur zum Laden und Aufspielen (ROM-DFU); die Anwendungsfirmware nutzt USB nicht, Konsole über Serial1/SWD. Keine VBUS-Erkennung nötig. Lastenheft K5, `mcu-funk.md` 1.3, Entscheidungsregister HW-01.
- **SCH26-11:** Herstellerschaltbild des Ra-01SH (Datenblatt V1.1, S. 12) ausgewertet: DIO2 schaltet den HF-Schalter, **TXEN ist im Modul DIO2 (0 Ω)**, RXEN offen, ANT-Pad parallel zur IPEX, DC-DC-Spule vorgesehen. Regel: JP401/JP402 offen, PB14/PB15 nur Eingänge, `setDio2AsRfSwitch(true)`. Prüfplan F-1…F-7 überarbeitet (Pegelmessung an TXEN, RSSI-Vergleich bei −9 dBm, Reglerprüfung).
- Neu: `hardware/funk_modell.py` (Schaltlogik in 6 Konfigurationen, Funkstrecke 5–8 m). `netz_tests.py` prüft die offenen Lötbrücken und DIO2 (79 Prüfungen). Beschreibungen an JP401/JP402/U401 im Generator.
- Prüfung (lokal, KiCad 10.0.7): reproduzierbar, ERC unverändert, 79/79; Modell Exit 0. Bericht: `docs/testberichte/2026-10-10-sch26-10-11-analyse.md`.

## 2026-10-10 – Behebung Schaltplan-Review 4c12b6d (SCH26-09 bis -12)

- **SCH26-09:** Debug-Leiste J302 im Generator an den Kabelplan `anschluesse.md` J10 angeglichen (1 3V3, 2 SWDIO, 3 SWCLK, 4 NRST, **5 GND, 6 TX1, 7 RX1**). `anschluesse.md`: Platinenreferenzen J1/J201, J2/J202, J9/J301, J10/J302, neuer Abschnitt 1.2 Debug-Leiste. `netz_tests.py` prüft J302 je Pin und vergleicht die Stecker-Pinbelegung aus `anschluesse.md` mit der KiCad-Netzliste, mit Gegenprobe (48 → 74 Prüfungen).
- **SCH26-12:** `pruefen.sh` vergleicht alle erzeugten Blätter (Liste aus den Ordnern), prüft die Abdeckung gegen die Blattverweise der Wurzelblätter und hat den Modus `--gegenprobe` (Zufalls-UUIDs über `BIENEN_GEGENPROBE_ZUFALL` in `kicad_gen.py`).
- **SCH26-10/11:** Entscheidungsvorlage USB-Rolle/VBUS-Erkennung (`mcu-funk.md` 1.3) und Prüfplan Funkmodul F-1…F-6 (`mcu-funk.md` 6.1); Schaltplan dafür unverändert.
- Prüfung (lokal, KiCad 10.0.7): reproduzierbar, ERC Akku 0 / Hauptplatine 11 erwartete Meldungen, 74/74 Netzprüfungen; Gegenproben bestanden. Bericht: `docs/testberichte/2026-10-10-sch26-09-12-behebung.md`.

## 2026-10-10 – Blatt Funk + Flash

- Neues Blatt `hauptplatine/funk.kicad_sch` nach `mcu-funk.md` 2, 3.1, 3.2: Ra-01SH (eigenes Symbol, Pinbelegung Datenblatt V1.1 S. 11) an SPI1 mit 33-Ω-Reihenwiderständen, NSS-Pull-up 100 kΩ, Puffer 100 µF + 10 µF + 100 nF und TVS am 3,3-V-Eingang, TXEN/RXEN über offene Lötbrücken, ANT/DIO2/DIO3 offen; SPI-NOR-Flash 64 Mbit (SOIC-8 208 mil) am selben Bus mit CS-Pull-up 100 kΩ, WP/HOLD über 10 kΩ, 100 nF.
- Die 10 Funk-/Flash-Schnittstellen des Blatts MCU sind damit verbunden; `erc_erwartet.json` entsprechend gekürzt.
- Prüfung: `pruefen.sh` reproduzierbar, ERC OK (Hauptplatine 11 erwartete Meldungen), Netzvergleich 48/48. Der Netzvergleich fand beim Zeichnen einen verdrehten Pull-up an WP/HOLD; behoben vor der Lieferung.

## 2026-10-10 – Blatt MCU der Hauptplatine

- Neues Blatt `hauptplatine/mcu.kicad_sch` nach `hardware/mcu-funk.md` 1, 3.3 und 4: STM32F411CEU6 (UFQFPN-48) mit Abblockung (3 × 100 nF, 10 µF, VBAT 100 nF), VDDA über Ferrit, VCAP 4,7 µF; Reset- und BOOT-Taster, BOOT1-Pull-down; HSE 25 MHz (C9006, 2 × 18 pF) und LSE 32,768 kHz SC-32S (C97604, 2 × 8,2 pF); USB-C (C165948) mit CC-Widerständen und USBLC6-2SC6; Debug-Leiste SWD + Serial1; Magnet/Taster an PA0 (WKUP1) mit Pull-down; LED an PC13.
- 20 Schnittstellen-Netze zu den folgenden Blättern (Funk + Flash, Waage, Mikrofon, Anschlüsse) als globale Labels; in `erc_erwartet.json` begründet. VBUS hat jetzt beide Enden.
- `kicad_gen.py`: `*.kicad_pro` wird nur noch angelegt, wenn sie fehlt (REG26-14); Ausrichtung der Beschriftung bei gedrehten Teilen; Netz „NC“ nie global.
- Stückliste im KiCad-README aus den Generatoren erzeugt (87 Teile).
- Prüfung: `pruefen.sh` reproduzierbar, ERC OK (Akku 0, Hauptplatine 21 erwartete Meldungen), Netzvergleich 48/48.

## 2026-10-09 – Schaltpläne lesbar gezeichnet (Verdrahtungsmodus)

- Akku-Platine und Blatt Versorgung werden jetzt mit **echten Leitungen nach dem Stromfluss** gezeichnet statt mit Netzlabels an jedem Pin (Wunsch Philipp). Akku: Leistungspfad oben, Zellschutz im Minuspfad, darunter Ladesperre Stufe 2 und Stufe 1 mit TMP_VCC vom Stecker. Versorgung: Panels/USB → VIN_LADER → BQ25185 → SYS, Akku-Stecker mit VBAT/CE/NTC/TMP_VCC, unten SYS → 3,3 V → 3V3_SW.
- `kicad_gen.py`: Verdrahtungsmodus (`setze`, `draht`, `label`, `versorgung`), Drehung, Junctions, Teilen von Drähten an Pin-Enden, Abbruch bei Pins ohne Draht; Referenzen von `#`-Symbolen verborgen.
- `netz_tests.py`: vollständiger Netzvergleich KiCad-Netzliste ↔ Netzbeschreibung je Projekt (48 Prüfungen). Gegenproben: fehlender Draht → Abbruch, falscher Draht → 9 Prüfungen rot.
- Schaltung elektrisch unverändert (Netzvergleich identisch); ERC wie vorher (Akku 0, Hauptplatine 2 erwartete Meldungen).

## 2026-10-09 – REG26-09/10/11 vor dem Layout

- **REG26-09:** Begründung je `PWR_FLAG` als Symbolbeschreibung im Generator und als Tabelle in `hardware/kicad/README.md`.
- **REG26-10:** Board-Kennungen PCB-AKKU-0.1 / PCB-MAIN-0.1 und Auslegungsumgebung im Titelblock (neue Option `kommentare` in `kicad_gen.py`), Lastenheft M11.
- **REG26-11:** Schienentabelle und DC-Bias-Bewertung (`versorgung.md` 3.9). C204 22 µF/1206, C212 4,7 µF/0805, C208/C209 2,2 µF, weil die bisherigen Werte unter Gleichspannung voraussichtlich unter das Datenblatt-Minimum fallen. Herstellerkurven je LCSC-Nummer stehen noch aus.
- `sicherheit-akku.md` A-5 an LH-M8 (Schutzlack nach dem Test) angeglichen.
- Prüfung: `pruefen.sh` reproduzierbar, ERC unverändert (2 erwartete Warnungen), 42/42 Netzprüfungen.

## 2026-10-09 – Sicherheitsanalyse Akku (REG26-06/07)

- Neu: `hardware/sicherheit-akku.md` (SAF-AKKU 0.1): Sicherheitsziele, Gefährdungsliste, Einzelfehleranalyse der Ladesperre, Schutz- und Wiederanlaufzustände, sicherer Versuchsplan (Zell-Emulator mit Stromaufnahme, Strombegrenzung, Abbruchkriterien, SCH-T01 … T11), Rückverfolgbarkeit LH-V1/V2/V3/V7. Stufe T0, Gegenlesen offen.
- Neue Befunde HW26-16 … -19 (gemeinsamer Fehlerpunkt BQ25185, 0-V-Laden HY2111, Überspannung TMP_VCC, Kältereserve).
- SHA `2076c20` im SCH26-Bericht und im Befundregister nachgetragen (REG26-05, REG26-13).

## 2026-10-09 – Audit gegen Regelwerk 1.1, Wiederherstellung SCH26

- Audit AUD-2026-10-09-01 (`docs/testberichte/2026-10-09-regelwerk-audit.md`), Befunde REG26-01 … -12 im Befundregister.
- **REG26-01:** Die lokal verworfene Behebung SCH26 (Akku-Platine TMP_VCC, zweite Stufe, J3 5-polig, Prüfskripte, Berichte) wiederhergestellt; zusammen mit Regelwerk 1.1 (ADR-0002) eingecheckt.
- REG26-05: SHA in den Behebungsberichten SRV26 (`3f2f9d6`) und HW26/CI26 (`cc6ba60`) nachgetragen.

## 2026-10-09 – Entwicklungsregelwerk 1.1 (ADR-0002) nach Review

- Review des Regelwerks 1.0 durch Claude (`docs/testberichte/2026-10-09-regelwerk-review.md`); Entscheidungen des Maintainers in ADR-0002.
- **Befundregister** `docs/testberichte/befunde.md` als einzige Stelle für Befundstände; **Statusmodell** offen / analysiert / im Entwurf behoben / nachgewiesen / geschlossen (R-05a).
- **D3-Gates:** G2 mit Gefährdungsanalyse, Netz-/ERC-Prüfung und sicherem Versuchsplan (Zell-Emulator, Strombegrenzung); G3/G4 zusätzlich T4-Messungen und unabhängiges Review durch befreundete Hardware-Entwickler. Maintainer namentlich genannt.
- **Übergabe** zwischen Beteiligten nur über committete und gepushte Stände (R-06 Nr. 2); Lastenheft-Zeilen als Anforderungs-IDs `LH-…`; Reproduzierbarkeit ohne zeitgestempelte Exporte, KiCad-Hauptversion 10.
- **GOV-01 entschieden:** Skripte in `hardware/`/`mechanik/` GPL-3.0-or-later (SPDX ergänzt), Schaltpläne/Symbole/Footprints/Exporte CERN-OHL-S-2.0; `LICENSE.md` angepasst.
- Ausnahme **EX-01** (beelogger-Passwort im GET) eingetragen.
- Zusammenführung der parallelen Stände (Regelwerk-Commits `72e4f79`/`8fc2aa4` und lokale Behebung SCH26) in `CLAUDE.md` und `CHANGELOG.md`.

## 2026-10-09 – Entwicklungsregelwerk 1.0 angenommen

- Entwurf 0.1 als verbindlichen Standard für Menschen und Coding-Agents beschlossen; ADR-0001 und Governance-Register eingeführt.
- GOV-02 und GOV-03 angenommen; GOV-01 (Lizenzfrage) und GOV-04 (bauteilabhängige Grenzwerte) bleiben offen.
- AGENTS.md ergänzt; README, CLAUDE und CONTRIBUTING aktualisiert. **Keine Firmware-/Hardware-/Serverlogik geändert.**

## 2026-10-09 – Behebung Schaltplan-Review V0.1 (SCH26-01 … -08)

- **SCH26-01:** Ladesperre auf der Akku-Platine (2 × TMP390, Gate-Pull-ups) versorgt aus TMP_VCC = TPS70933 am Ladereingang; dadurch Wiederanlauf nach Tiefentladung (HY2111-GB gibt nur durch Laden frei) und 0 µA Ruhestrom der Sperre. J3/J203/J1 JST PH 5-polig (P−, NTC, CE_FREI, TMP_VCC, P+).
- **SCH26-02:** R5/R8/R205 100 kΩ statt 10 MΩ; Pegelrechnung in `versorgung.md` 3.3.
- **SCH26-03:** zweite unabhängige Stufe: TMP390 U3 (42 °C) öffnet mit Q3 den NTC-Kreis (TS offen → BQ25185 sperrt).
- **SCH26-04:** `pruefen.sh` prüft Reproduzierbarkeit, ERC aller Schweregrade gegen `erc_erwartet.json`, exportiert Netzlisten; `netz_tests.py` (42 Prüfungen an KiCad-Netzlisten); CI-Job `kicad-schaltplan` (KiCad 10, `git diff --exit-code`).
- **SCH26-05/06/08:** R208 100 kΩ; Kabelplan Akku ↔ Hauptplatine; C201 50 V.
- Ruhestrom 15,7 µA.

## 2026-10-09 – KiCad-10-Schaltplan, Schritt 1: Versorgung und Akku-Platine

- `hardware/kicad/`: Erzeuger für KiCad-10-Schaltpläne aus einer Netzbeschreibung (`werkzeug/kicad_gen.py`), Projektsymbole `bienen.kicad_sym` (BQ25185, TMP390, HY2111-GB, FS8205, RT9080), Prüfskript `pruefen.sh` (Erzeugen, ERC, PDF).
- Akku-Platine (eigenes Projekt): HY2111 + FS8205 nach Herstellerschaltung, Messbrücke, TMP390 mit 2,49 kΩ (42 °C) / 18,7 kΩ (+5 °C, 5 °C Hysterese) und AO3400A an CE_FREI, NTC 10 k B3435, JST PH 4. ERC 0/0.
- Hauptplatine, Blatt Versorgung: Solar mit SS34/SMAJ12A, Teiler 3,3 MΩ/470 kΩ, BQ25185 (ISET 2,0 kΩ = 150 mA, ILIM/VSET 130 kΩ = 4,1 V/500 mA), CE-Pull-up 10 MΩ, Akkuteiler, RT9080, TPS22917 (CT 1 nF nach VIN, QOD über 0 Ω an VOUT, ON mit 1 MΩ). ERC 0 Fehler.

## 2026-10-09 – Behebung Hardware-Review 0.4 (HW26-07 … -13) und CI26-01

- **CI26-01:** `lora_verarbeitung.php` erkennt „gespeichert“ über den letzten Zeitstempel vorher/nachher (`le_speicherung_erkannt`), nicht mehr über die Dateigröße. Ursache: beelogger kürzt `week.csv` vor 08:00 Uhr Serverzeit. E2E-Test mit `SERVER_UHR` (libfaketime), CI prüft 05:00 und 14:00; Protokoll je DST-Ereignis; Unit-Tests 66/66.
- **HW26-07:** Ladesperre zweistufig: TMP390 an der Zelle sperrt über CE außerhalb +5 … 42 °C (ausfallsicher bei Leitungsbruch), NTC am TS als zweite Stufe; J3 4-polig.
- **HW26-08:** Solar-Teiler 3,3 MΩ / 470 kΩ + 100 nF hinter den Dioden (25 V → 3,12 V).
- **HW26-09:** BME280 über Outdoor-Netzwerkkabel (105–135 pF); `i2c_leitung.py` mit Kabelvarianten und Fehlercode.
- **HW26-10:** EEPROM AT24C256 entfällt; LoRaWAN-Sitzung im SPI-Flash (Ringpuffer, Generation, CRC-32, Gültig-Byte).
- **HW26-11:** Ladestrom 150 mA; Wärmerechnung BQ25185.
- **HW26-12/13:** Flash-Aufteilung, FFT-Rohdaten nur als Schnappschüsse; J10 1 × 7, J11 2 × 6.
- Energiebilanz: Ruhestrom 16,6 µA, 128–452 Tage ohne Laden.

## 2026-10-08 – Lastenheft Platine 0.4: Versorgung

- `hardware/versorgung.md`: Laderegler BQ25185 (Eingang bis 18 V, Kältesperre per NTC, Ladeschluss 4,1 V), zweistufiger Tiefentladeschutz (BQ25185 3,0 V, HY2111-GB 2,9 V), Akku-Platine am Halter, LDO RT9080, Sensorschalter und Regeln gegen Rückspeisung, Regeln aus den beelogger-Erfahrungen, Montage der Panels
- 09.10.2026: J8 (BME280) 6-polig mit freiem Pin 6 als Verwechslungsschutz zu J4 (Wägezelle, E+ 4,3 V > 4,25 V BME280-Grenze); Steckerfarbe zusätzlich
- 09.10.2026: BME280-Leitung höchstens 1 m, Pull-ups 1,8 kΩ statt 1,5 kΩ (`hardware/i2c_leitung.py`: 290–440 pF, Anstiegszeit ≤ 671 ns); Bestückung komplett bei JLCPCB inkl. Durchsteckteile
- 09.10.2026: `hardware/anschluesse.md`: Klemmenbelegung J1–J11 (Masse/Schirm an Pin 1), steckbare Klemmen DEGSON 3,5 mm, ESD ESDS304 bzw. TPD4E05U06 (Wägezelle, 5,5 V, ≤ 10 nA), I²C für BME280 mit 50 kHz, alle Außenklemmen an einer Kante; Lastenheft F4, F5, F10, M4, M5 angepasst
- 09.10.2026: Wand-Lichtleiter mit Dichtung (Kandidat Bivar PLTR2, IP67); STEP-Modell des Gehäuses wird bei Camdenboss angefragt; Reedkontakt-Schaltabstand am Prototyp
- 09.10.2026: **4 Lagen** festgelegt (L2 durchgehende Masse); **Lichtleiter durch Gehäusebohrung** mit seitlich abstrahlender LED und Reedkontakt an der Platinenkante
- 09.10.2026: nur noch **ein HX711**; **SPI-Flash 64 Mbit fest** (SPI1, CS PB3, dauernd versorgt, Typ nach Bestand); Bedienung per Magnet mit **LED unter Lichtleiter** (Sofortmessung, Durchsicht ein/aus); Energiebilanz neu (≥ 128 Tage ohne Laden)
- `hardware/beep-vergleich.md`: Auswertung BEEP base v3 (Schaltplan, Stückliste); übernommen: Lastschalter TPS22917, Reedkontakt an PA0, ESD-Arrays an allen Sensorklemmen, Platz für SPI-Flash; 4 Lagen zur Entscheidung
- `hardware/mikrofon.md` und `mikrofon_filter.py`: Sallen-Key-Tiefpass 1179 Hz + RC 4,8 kHz (−36 bis −39 dB bei den Spiegelfrequenzen, ≤ 1,1 dB im Nutzband), Hochpass 22 Hz, gesiebte Versorgung, Timer + DMA, Ablaufregeln (kein Funk und kein 5-V-Wandler während der Messung)
- `hardware/waage.md`: HX711 mit 5 V aus festem Wandler TPS61240 (Lasttrennung, EN an PB10), AVDD 4,3 V, Bosche H40A 200 kg (404 Ω, 2 mV/V), Eingangsschutz der Zellenleitungen, Auflösung ca. 1,2 g je Einzelwert; Energiebilanz neu (≥ 122 Tage ohne Laden)
- `hardware/mcu-funk.md`: Beschaltung STM32F411 (VCAP 4,7 µF, LSE-Quarz 7 pF statt 12,5 pF nach ST AN4488), USB-C mit ESD und Laden über VBUS, Ra-01SH (Antenne an IPEX, TXEN/RXEN über Lötbrücken, Hinweis LLCC68 ohne SF11/12), EEPROM an der geschalteten Schiene, Pinbelegung 0.4
- `hardware/energiebilanz.py`: reproduzierbare Energiebilanz mit Quellen und Status je Wert; Ergebnis 130–510 Tage Reichweite ohne Laden, Dezemberertrag ca. 40-facher Bedarf

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

# KiCad-Projekte (KiCad 10)

Stand 09.10.2026 nach [Schaltplan-Review V0.1](../../docs/testberichte/2026-10-09-schaltplan-v01-review.md) und [Behebung SCH26](../../docs/testberichte/2026-10-09-sch26-behebung.md): **Akku-Platine** und Blatt **Versorgung** der Hauptplatine. Die Blätter MCU, Funk + Flash, Waage, Mikrofon und Anschlüsse folgen. **Entwurf, keine Fertigungsfreigabe.**

| Ordner/Datei | Inhalt |
|---|---|
| `akku-platine/` | Projekt `akku.kicad_pro`: Zelle, HY2111 + FS8205, Messbrücke, Ladesperre 2 × TMP390 (Stufe 1 → CE, Stufe 2 → NTC-Kreis), NTC, JST PH 5 |
| `hauptplatine/` | Projekt `logger.kicad_pro`: Wurzelblatt mit Blättern je Block; fertig: `versorgung.kicad_sch` |
| `bienen.kicad_sym` | Projektsymbole (BQ25185, TMP390, HY2111-GB, FS8205, RT9080, TPS70933), Pinbelegungen mit Datenblattquelle in `werkzeug/symbole.py` |
| `erc_erwartet.json` | begründete ERC-Warnungen; jede andere Meldung lässt die Prüfung scheitern |
| `pdf/`, `netzliste/` | Ausdrucke und KiCad-Netzlisten (zum Prüfen ohne KiCad; enthalten ein Datum, daher vom CI-Diff ausgenommen) |
| `werkzeug/` | Erzeuger `kicad_gen.py`, `symbole.py`, `erc_pruefen.py`, `netz_tests.py` |

## Wie die Schaltpläne entstehen

- Jeder Block ist in Python beschrieben: `akku_platine.py`, `hauptplatine.py` (Bauteil, Wert, Footprint, LCSC, Pin → Netz). **Diese Netzbeschreibung ist die Quelle der Wahrheit.**
- **Zeichnung (Verdrahtungsmodus, seit 09.10.2026):** Je Blatt legt eine Funktion `zeichne…()` Lage und Drehung jedes Bauteils fest und zieht die Leitungen nach dem Stromfluss (links Quelle, rechts Verbraucher, oben Versorgung, Masse als GND-Symbol). Netznamen stehen als Label an der Leitung; Netze zu anderen Blättern werden globale Labels.
- Absicherung der Zeichnung: Der Erzeuger bricht ab, wenn ein Pin keinen Draht hat; `netz_tests.py` vergleicht **jedes Netz** der von KiCad exportierten Netzliste mit der Netzbeschreibung (Name und Pins). Ein falsch gezogener oder vergessener Draht fällt so auf (Gegenproben 09.10.2026: fehlender Draht an R5 → Abbruch; U2-VDD an B+ → 9 Prüfungen rot).
- Danach speichert KiCad jede Datei einmal selbst neu (`kicad-cli sch upgrade --force`): exaktes KiCad-10-Format.
- **Änderungen nur im Skript.** Handänderungen in KiCad würden beim nächsten Erzeugen überschrieben.

## Prüfen

`bash hardware/kicad/pruefen.sh` (braucht KiCad 10 mit `kicad-cli`):
1. zweimal erzeugen, Prüfsummen vergleichen (reproduzierbar)
2. ERC mit **allen Schweregraden** gegen `erc_erwartet.json` (`werkzeug/erc_pruefen.py`)
3. PDF- und Netzlisten-Export
4. `werkzeug/netz_tests.py`: 48 Prüfungen **in den von KiCad exportierten Netzlisten**: vollständiger Netzvergleich Zeichnung ↔ Netzbeschreibung (je Projekt) und gezielte Prüfungen sicherheitsrelevanter Netze (Ladesperre ohne Verbindung zu B+/B−, CE- und NTC-Pfad, Kabel J1 ↔ J203, Widerstandswerte)

Die CI (Job `kicad-schaltplan`) führt das mit KiCad 10 aus der offiziellen PPA aus und verlangt danach `git diff --exit-code`.

## ERC-Stand (KiCad 10.0.6, alle Schweregrade)

| Projekt | Meldungen | Bemerkung |
|---|---|---|
| Akku-Platine | 0 | |
| Hauptplatine | 2 (erwartet) | Footprint-Bibliothek „Bienen“ fehlt noch (BQ25185 DLH 2,2 × 2 mm); `VBUS` hat erst ein Ende (USB kommt mit Blatt MCU) |

## Board-Kennung und Umgebung (REG26-10)

| Projekt | Kennung (Titelblock Kommentar 2) | Umgebung (Kommentar 3) [A] |
|---|---|---|
| Akku-Platine | PCB-AKKU-0.1 | Gehäuse −20 … +60 °C, Betauung möglich; Laden nur +5 … 42 °C |
| Hauptplatine | PCB-MAIN-0.1 | Gehäuse −20 … +60 °C, Betauung möglich; VIN ≤ 12 V dauernd, 25 V absolut |

## PWR_FLAG – Begründungen (REG26-09)

Ein `PWR_FLAG` sagt dem ERC: „Hier speist eine Quelle ein, die KiCad nicht als Treiber erkennt.“ Jedes Flag markiert eine echte Quelle; die Begründung steht auch als Beschreibung am Symbol (Generator).

| Projekt | Netz | Echte Quelle |
|---|---|---|
| Akku-Platine | B+, B− | Zelle BT1 (Halter = passive Pins) |
| Akku-Platine | P+ | Zelle über die Lötbrücke JP1 (passiv) |
| Akku-Platine | GND (P−) | Zelle über Q1 FS8205 (FET kein Treiber im ERC) |
| Akku-Platine | TMP_VCC | U204 auf der Hauptplatine über J1 Pin 4 (anderes Projekt) |
| Akku-Platine | HY_VDD | B+ über R1 100 Ω (HYCON-Anwendungsschaltung) |
| Hauptplatine | VIN_LADER | Panels J201/J202 und VBUS über D201–D203 |
| Hauptplatine | GND | Klemmen J201/J202 und Akku-Stecker J203 |
| Hauptplatine | VBAT | Akku-Platine über J203 Pin 5 (anderes Projekt) |

Ein neues `PWR_FLAG` nur mit Eintrag in dieser Tabelle; ein Flag auf einem Netz, das schon einen Ausgang hat (z. B. TMP_VCC auf der Hauptplatine), verdeckt Fehler und ist unzulässig.

## Offene Punkte [P]

- Footprints selbst anlegen: BQ25185 (DLH0010A, 2,2 × 2 mm), Akkuhalter Keystone 1043 (SMD; Platzhalter 1042).
- Klemmen: Platzhalter Phoenix MC 1,5 / 3,5 mm für DEGSON 15EDGRHC-3.5 – Maße vergleichen.
- LCSC-Nummern ergänzen (BQ25185, TMP390, TPS70933, SS34, SMAJ12A, Klemmen, JST).
- Muster: Versuchsplan SCH-T01 … T11 in [`../sicherheit-akku.md`](../sicherheit-akku.md) (Akku/Laden) und Review (übrige).
- Kondensatoren: DC-Bias-Kurven je LCSC-Nummer eintragen (`../versorgung.md` 3.9).

## Stückliste (bisher, 56 Teile)

| Ref. | Wert | Symbol | Footprint | LCSC | Blatt |
|---|---|---|---|---|---|
| BT1 | 18650 3,6 V | Device:Battery_Cell | BatteryHolder_Keystone_1042_1x18650 |  | Akku-Platine |
| C1 | 100n | Device:C | C_0603_1608Metric |  | Akku-Platine |
| C2 | 100n | Device:C | C_0603_1608Metric |  | Akku-Platine |
| C3 | 100n | Device:C | C_0603_1608Metric |  | Akku-Platine |
| J1 | JST PH 5-polig | Connector_Generic:Conn_01x05 | JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal |  | Akku-Platine |
| J2 | Strommessung (DNP) | Connector_Generic:Conn_01x02 | PinHeader_1x02_P2.54mm_Vertical |  | Akku-Platine |
| JP1 | Messbrücke B+ | Jumper:SolderJumper_2_Bridged | SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm |  | Akku-Platine |
| Q1 | FS8205 | Bienen:FS8205 | SOT-23-6 | C32254 | Akku-Platine |
| Q2 | AO3400A | Transistor_FET:AO3400A | SOT-23 |  | Akku-Platine |
| Q3 | AO3400A | Transistor_FET:AO3400A | SOT-23 |  | Akku-Platine |
| R1 | 100 | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R2 | 2k | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R3 | 2,49k 1% | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R4 | 18,7k 1% | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R5 | 100k | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R6 | 2,49k 1% | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R7 | 18,7k 1% | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R8 | 100k | Device:R | R_0603_1608Metric |  | Akku-Platine |
| TH1 | 10k B3435 | Device:Thermistor_NTC | R_0603_1608Metric |  | Akku-Platine |
| U1 | HY2111-GB | Bienen:HY2111-GB | SOT-23-6 | C82747 | Akku-Platine |
| U2 | TMP390A2DRL | Bienen:TMP390 | SOT-563 |  | Akku-Platine |
| U3 | TMP390A2DRL | Bienen:TMP390 | SOT-563 |  | Akku-Platine |
| C201 | 4,7µ 50V X7R | Device:C | C_1206_3216Metric |  | Versorgung |
| C202 | 100n 50V | Device:C | C_0603_1608Metric |  | Versorgung |
| C203 | 100n | Device:C | C_0603_1608Metric |  | Versorgung |
| C204 | 22µ 25V X5R | Device:C | C_1206_3216Metric |  | Versorgung |
| C205 | 4,7µ | Device:C | C_0805_2012Metric |  | Versorgung |
| C206 | 10n | Device:C | C_0603_1608Metric |  | Versorgung |
| C207 | 100n | Device:C | C_0603_1608Metric |  | Versorgung |
| C208 | 2,2µ 16V X7R | Device:C | C_0603_1608Metric |  | Versorgung |
| C209 | 2,2µ 16V X7R | Device:C | C_0603_1608Metric |  | Versorgung |
| C210 | 1n | Device:C | C_0603_1608Metric |  | Versorgung |
| C211 | 1µ | Device:C | C_0603_1608Metric |  | Versorgung |
| C212 | 4,7µ 16V X7R | Device:C | C_0805_2012Metric |  | Versorgung |
| D201 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D202 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D203 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D204 | SMAJ12A | Diode:SMAJ12A | D_SMA |  | Versorgung |
| J201 | Solar 1 | Connector_Generic:Conn_01x02 | PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal |  | Versorgung |
| J202 | Solar 2 | Connector_Generic:Conn_01x02 | PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal |  | Versorgung |
| J203 | Akku (JST PH 5) | Connector_Generic:Conn_01x05 | JST_PH_B5B-PH-K_1x05_P2.00mm_Vertical |  | Versorgung |
| R201 | 3,3M | Device:R | R_0603_1608Metric |  | Versorgung |
| R202 | 470k | Device:R | R_0603_1608Metric |  | Versorgung |
| R203 | 2,0k 1% | Device:R | R_0603_1608Metric |  | Versorgung |
| R204 | 130k 1% | Device:R | R_0603_1608Metric |  | Versorgung |
| R205 | 100k | Device:R | R_0603_1608Metric |  | Versorgung |
| R206 | 2,2M | Device:R | R_0603_1608Metric |  | Versorgung |
| R207 | 2,2M | Device:R | R_0603_1608Metric |  | Versorgung |
| R208 | 100k | Device:R | R_0603_1608Metric |  | Versorgung |
| R209 | 0 | Device:R | R_0603_1608Metric |  | Versorgung |
| TP201 | STAT1 | Connector:TestPoint | TestPoint_Pad_D1.0mm |  | Versorgung |
| TP202 | STAT2 | Connector:TestPoint | TestPoint_Pad_D1.0mm |  | Versorgung |
| U201 | BQ25185DLHR | Bienen:BQ25185 | WSON-10-1EP_2.2x2mm_DLH0010A |  | Versorgung |
| U202 | RT9080-33GJ5 | Bienen:RT9080-33GJ5 | TSOT-23-5 | C841192 | Versorgung |
| U203 | TPS22917DBV | Power_Management:TPS22917DBV | SOT-23-6 | C2681320 | Versorgung |
| U204 | TPS70933DBV | Bienen:TPS70933DBV | SOT-23-5 |  | Versorgung |

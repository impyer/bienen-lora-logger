# KiCad-Projekte (KiCad 10)

**Unabhängige sicherheitstechnische Prüfung von V0.1:** [Schaltplan-Review](../../docs/testberichte/2026-10-09-schaltplan-v01-review.md). **P0 SCH26-01**: möglichen Lade-Wiederanlauf-Deadlock nach HY2111-Tiefentladung klären. **P1 SCH26-02/03**: 10-MΩ-Freigabekette und fehlende Einzelfehlertoleranz des Temperaturfensters verifizieren. **Die unten genannten ERC-Werte stammen aus dem Projekt; sie wurden nicht unabhängig reproduziert und werden bislang nicht von CI geprüft.**

Stand 09.10.2026: **Akku-Platine** und Blatt **Versorgung** der Hauptplatine. Die Blätter MCU, Funk + Flash, Waage, Mikrofon und Anschlüsse folgen.

| Ordner | Inhalt |
|---|---|
| `akku-platine/` | eigenes Projekt `akku.kicad_pro`: Zelle, HY2111 + FS8205, Messbrücke, TMP390-Ladesperre, NTC, JST PH 4 |
| `hauptplatine/` | Projekt `logger.kicad_pro`: Wurzelblatt mit Blättern je Block; fertig: `versorgung.kicad_sch` |
| `bienen.kicad_sym` | Projektsymbole (BQ25185, TMP390, HY2111-GB, FS8205, RT9080), Pinbelegungen mit Datenblattquelle in `werkzeug/symbole.py` |
| `pdf/` | PDF-Ausdrucke zum Ansehen ohne KiCad |
| `werkzeug/` | Erzeuger (`kicad_gen.py`) und Symbolerzeugung |

## Wie die Schaltpläne entstehen

- Jeder Block ist in Python beschrieben: `akku_platine.py`, `hauptplatine.py` (Bauteil, Wert, Footprint, LCSC, Pin → Netz).
- Der Erzeuger setzt die Symbole und hängt an jedes Pin-Ende ein Netzlabel, ein Versorgungssymbol oder ein No-Connect. Verbindungen laufen über **Netznamen**, nicht über gezeichnete Drähte.
- Netze, die auf mehreren Blättern vorkommen, werden **globale Labels**.
- Danach speichert KiCad selbst jede Datei einmal neu (`kicad-cli sch upgrade --force`), damit das Format genau KiCad 10 entspricht.
- **Änderungen bitte im Skript machen**, nicht in KiCad: Beim nächsten Erzeugen würden Handänderungen überschrieben. Schöner zeichnen lohnt erst, wenn die Schaltung feststeht; dann wird der Stand eingefroren und von Hand weitergeführt.

Prüfen (Erzeugen + ERC + PDF): `bash hardware/kicad/pruefen.sh` (braucht KiCad 10 mit `kicad-cli`).

## ERC-Stand

| Projekt | Fehler | Warnungen | Bemerkung |
|---|---|---|---|
| Akku-Platine | 0 | 0 | |
| Hauptplatine | 0 | 2 | Footprint-Bibliothek „Bienen“ fehlt noch (BQ25185 DLH 2,2 × 2 mm); `VBUS` hat erst ein Ende (USB kommt mit Blatt MCU) |

## Offene Punkte [P]

- Footprints selbst anlegen: BQ25185 (DLH0010A, 2,2 × 2 mm), Akkuhalter Keystone 1043 (SMD; Platzhalter 1042).
- Klemmen: Platzhalter Phoenix MC 1,5 / 3,5 mm für DEGSON 15EDGRHC-3.5 – Maße vergleichen.
- LCSC-Nummern ergänzen (BQ25185, TMP390, SS34, SMAJ12A, Klemmen, JST).
- TPS22917: R209 = 0 Ω (QOD direkt an VOUT); Abfallzeit am Muster prüfen.

## Stückliste (bisher)

| Ref. | Wert | Symbol | Footprint | LCSC | Blatt |
|---|---|---|---|---|---|
| BT1 | 18650 3,6 V | Device:Battery_Cell | BatteryHolder_Keystone_1042_1x18650 |  | Akku-Platine |
| C1 | 100n | Device:C | C_0603_1608Metric |  | Akku-Platine |
| C2 | 100n | Device:C | C_0603_1608Metric |  | Akku-Platine |
| J1 | JST PH 4-polig | Connector_Generic:Conn_01x04 | JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal |  | Akku-Platine |
| J2 | Strommessung (DNP) | Connector_Generic:Conn_01x02 | PinHeader_1x02_P2.54mm_Vertical |  | Akku-Platine |
| JP1 | Messbrücke B+ | Jumper:SolderJumper_2_Bridged | SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm |  | Akku-Platine |
| Q1 | FS8205 | Bienen:FS8205 | SOT-23-6 | C32254 | Akku-Platine |
| Q2 | AO3400A | Transistor_FET:AO3400A | SOT-23 |  | Akku-Platine |
| R1 | 100 | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R2 | 2k | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R3 | 2,49k 1% | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R4 | 18,7k 1% | Device:R | R_0603_1608Metric |  | Akku-Platine |
| R5 | 10M | Device:R | R_0603_1608Metric |  | Akku-Platine |
| TH1 | 10k B3435 | Device:Thermistor_NTC | R_0603_1608Metric |  | Akku-Platine |
| U1 | HY2111-GB | Bienen:HY2111-GB | SOT-23-6 | C82747 | Akku-Platine |
| U2 | TMP390A2DRL | Bienen:TMP390 | SOT-563 |  | Akku-Platine |
| C201 | 4,7µ 25V | Device:C | C_1206_3216Metric |  | Versorgung |
| C202 | 100n 50V | Device:C | C_0603_1608Metric |  | Versorgung |
| C203 | 100n | Device:C | C_0603_1608Metric |  | Versorgung |
| C204 | 10µ | Device:C | C_0805_2012Metric |  | Versorgung |
| C205 | 4,7µ | Device:C | C_0805_2012Metric |  | Versorgung |
| C206 | 10n | Device:C | C_0603_1608Metric |  | Versorgung |
| C207 | 100n | Device:C | C_0603_1608Metric |  | Versorgung |
| C208 | 1µ | Device:C | C_0603_1608Metric |  | Versorgung |
| C209 | 1µ | Device:C | C_0603_1608Metric |  | Versorgung |
| C210 | 1n | Device:C | C_0603_1608Metric |  | Versorgung |
| C211 | 1µ | Device:C | C_0603_1608Metric |  | Versorgung |
| D201 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D202 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D203 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D204 | SMAJ12A | Diode:SMAJ12A | D_SMA |  | Versorgung |
| J201 | Solar 1 | Connector_Generic:Conn_01x02 | PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal |  | Versorgung |
| J202 | Solar 2 | Connector_Generic:Conn_01x02 | PhoenixContact_MC_1,5_2-G-3.5_1x02_P3.50mm_Horizontal |  | Versorgung |
| J203 | Akku (JST PH 4) | Connector_Generic:Conn_01x04 | JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical |  | Versorgung |
| R201 | 3,3M | Device:R | R_0603_1608Metric |  | Versorgung |
| R202 | 470k | Device:R | R_0603_1608Metric |  | Versorgung |
| R203 | 2,0k 1% | Device:R | R_0603_1608Metric |  | Versorgung |
| R204 | 130k 1% | Device:R | R_0603_1608Metric |  | Versorgung |
| R205 | 10M | Device:R | R_0603_1608Metric |  | Versorgung |
| R206 | 2,2M | Device:R | R_0603_1608Metric |  | Versorgung |
| R207 | 2,2M | Device:R | R_0603_1608Metric |  | Versorgung |
| R208 | 1M | Device:R | R_0603_1608Metric |  | Versorgung |
| R209 | 0 | Device:R | R_0603_1608Metric |  | Versorgung |
| TP201 | STAT1 | Connector:TestPoint | TestPoint_Pad_D1.0mm |  | Versorgung |
| TP202 | STAT2 | Connector:TestPoint | TestPoint_Pad_D1.0mm |  | Versorgung |
| U201 | BQ25185DLHR | Bienen:BQ25185 | WSON-10-1EP_2.2x2mm_DLH0010A |  | Versorgung |
| U202 | RT9080-33GJ5 | Bienen:RT9080-33GJ5 | TSOT-23-5 | C841192 | Versorgung |
| U203 | TPS22917DBV | Power_Management:TPS22917DBV | SOT-23-6 | C2681320 | Versorgung |

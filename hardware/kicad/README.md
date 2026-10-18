# KiCad-Projekte (KiCad 10)

Stand 14.10.2026: alle Blätter der Hauptplatine (**Versorgung**, **MCU**, **Funk + Flash**, **Waage**, **Mikrofon**, **Anschlüsse**, **Akku**) im Entwurf (SCH26-07). **Seit HW-06 gibt es nur noch eine Platine:** Zelle, Zellschutz und Ladesperre liegen auf dem Blatt „Akku“ der Hauptplatine; die frühere Akku-Platine (`akku_platine.py`, `akku-platine/`) ist entfernt und steht in der Git-Historie. Seit HW-07 zwei Mikrofone (Elektret + MEMS IM69D127) am Audio-ADC TLV320ADC3101, I²S an PB12/PA15/PB5. **Seit HW-09 (18.10.2026)** BLE-Modul Microchip RN4871 (U303) an USART6 PA11/PA12, geschaltet über PB13; USB-C-Buchse entfällt, Laden am Tisch über zwei Lötpads J301 (kein USBLC6, keine VBUS-Erkennung). **Entwurf, keine Fertigungsfreigabe.**

| Ordner/Datei | Inhalt |
|---|---|
| `hauptplatine/` | Projekt `logger.kicad_pro`: Wurzelblatt mit Blättern je Block; fertig: `versorgung.kicad_sch`, `mcu.kicad_sch`, `funk.kicad_sch`, `waage.kicad_sch`, `mikrofon.kicad_sch`, `anschluesse.kicad_sch`, `akku.kicad_sch` (Zelle, HY2111 + FS8205, Messbrücke, Ladesperre 2 × TMP390, NTC) |
| `bienen.kicad_sym` | Projektsymbole (BQ25185, TMP390, HY2111-GB, FS8205, RT9080, TPS70933, Ra-01SH, TPS61240, TLV320ADC3101, RN4871), Pinbelegungen mit Datenblattquelle in `werkzeug/symbole.py` |
| `hauptplatine/logger.kicad_pcb` | **Stand 14.10.2026: nur Rahmen** – Umriss 121 × 121 mm (Ecken R 3 [A]), 4 Löcher Ø 3,4 mm auf 110,2 mm mit Kupfersperre Ø 7 mm (Hülse 10 mm, HW-03), 4 Lagen 1,6 mm (6 Lagen nach Wahl des Layouters zulässig, M8), JLCPCB-Regeln (0,15/0,15 mm, Via 0,3/0,6 mm) [A], Hinweise auf User.1; angelegt mit `werkzeug/platine_start.py` (überschreibt nichts). **Bauteile, Platzierung, Lagenflächen und Routing macht der beauftragte Layouter** (Philipp 14.10.2026) über „Platine aus Schaltplan aktualisieren“; Vorgaben: Lastenheft M1–M10, A3, `../anschluesse.md` 4. Die eigenen Platzierungs- und Routing-Versuche vom 13./14.10.2026 (Skripte entfernt) und ihre Erkenntnisse stehen in den Prüfberichten 2026-10-13-platine-grobplatzierung und 2026-10-13-platine-routing |
| `erc_erwartet.json` | begründete ERC-Warnungen; jede andere Meldung lässt die Prüfung scheitern |
| `pdf/`, `netzliste/` | Ausdrucke und KiCad-Netzlisten (zum Prüfen ohne KiCad; enthalten ein Datum, daher vom CI-Diff ausgenommen) |
| `Bienen.pretty/` | Projektfootprints aus `werkzeug/footprints.py` (BQ25185 DLH, Ra-01SH, RN4871 mit Antennen-Sperrzonen, Klemmen, Reed, LED, Befestigung) |
| `werkzeug/` | Erzeuger `kicad_gen.py`, `symbole.py`, `footprints.py`, `erc_pruefen.py`, `netz_tests.py`, `pin_footprint.py` |

## Wie die Schaltpläne entstehen

- Jeder Block ist in Python beschrieben: `hauptplatine.py` (Bauteil, Wert, Footprint, LCSC, Pin → Netz). **Diese Netzbeschreibung ist die Quelle der Wahrheit.**
- **Zeichnung (Verdrahtungsmodus, seit 09.10.2026):** Je Blatt legt eine Funktion `zeichne…()` Lage und Drehung jedes Bauteils fest und zieht die Leitungen nach dem Stromfluss (links Quelle, rechts Verbraucher, oben Versorgung, Masse als GND-Symbol). Netznamen stehen als Label an der Leitung; Netze zu anderen Blättern werden globale Labels. Seit 10.10.2026 (Blatt Waage): Mehrere GND-Pins können mit einem Draht verbunden werden und bekommen dann ein gemeinsames GND-Symbol (`b.versorgung("GND", …)`); Referenz und Wert lassen sich mit `text=(x, y)` frei setzen. Die älteren Blätter sind davon unverändert.
- Absicherung der Zeichnung: Der Erzeuger bricht ab, wenn ein Pin keinen Draht hat; `netz_tests.py` vergleicht **jedes Netz** der von KiCad exportierten Netzliste mit der Netzbeschreibung (Name und Pins). Ein falsch gezogener oder vergessener Draht fällt so auf (Gegenproben 09.10.2026: fehlender Draht an R5 → Abbruch; U2-VDD an B+ → 9 Prüfungen rot).
- Danach speichert KiCad jede Datei einmal selbst neu (`kicad-cli sch upgrade --force`): exaktes KiCad-10-Format.
- **Änderungen nur im Skript.** Handänderungen in KiCad würden beim nächsten Erzeugen überschrieben.
- Die Projektdateien `*.kicad_pro` legt der Erzeuger nur an, wenn sie fehlen. KiCad schreibt sie beim Öffnen selbst um; das ist erlaubt und stört den CI-Vergleich nicht mehr.

## Prüfen

`bash hardware/kicad/pruefen.sh` (braucht KiCad 10 mit `kicad-cli`):
1. zweimal erzeugen, Prüfsummen **aller** erzeugten Blätter und der Symbolbibliothek vergleichen (reproduzierbar). Die Liste entsteht aus den Ordnern; jedes von einem Wurzelblatt verwiesene Blatt muss darin stehen, verwaiste `.kicad_sch` lassen die Prüfung scheitern (SCH26-12). `bash pruefen.sh --gegenprobe` erzeugt absichtlich mit Zufalls-UUIDs und zeigt, dass jede Blattdatei als abweichend erkannt wird.
2. ERC mit **allen Schweregraden** gegen `erc_erwartet.json` (`werkzeug/erc_pruefen.py`)
3. PDF- und Netzlisten-Export
4. `werkzeug/netz_tests.py`: 187 Prüfungen **in den von KiCad exportierten Netzlisten**: vollständiger Netzvergleich Zeichnung ↔ Netzbeschreibung, gezielte Prüfungen sicherheitsrelevanter Netze (Ladesperre ohne Verbindung zu B+/B−, CE- und NTC-Pfad, Zelle B− getrennt von GND (Schutz-FET im Minuspfad), Widerstandswerte; **BLE-Modul nach HW-09**: Lastschalter Q301 an PB13 mit Gate-Pull-up, BLE_VCC-Netz, USART6-Netze mit 1 kΩ, Pull-up R312 nur an BLE_VCC (Gegenprobe), Modulpins offen/GND, J704 Pin 9–12, Ladepads J301 statt USB-C, kein U302/R303/R304/R307/R308; **HW-10**: Elektret 2 an IN2R/IN3R mit MICBIAS2, gleiche Werte wie Elektret 1, D602 und J602/J12 mit Gegenprobe), Debug-Leiste J302 je Pin und **Pinbelegung der Stecker laut `hardware/anschluesse.md` gegen die Netzliste** (J1/J201, J2/J202, J9/J301, J10/J302, J12/J602) mit Gegenprobe (SCH26-09), Ra-01SH: JP401/JP402 als offene Lötbrücken, DIO2 unbeschaltet (SCH26-11); Blatt Waage: Wandler an SYS mit EN-Pull-down an PB10, FB an VOUT, HX711-DVDD an 3V3_SW, **AVDD aus den Teilerwerten 4,2–4,4 V und ≥ 0,1 V unter VSUP** (mit eingebauter Gegenprobe), Zellenleitungen nur an Klemme, ESD und Reihenwiderstand, J4/J501 gegen `anschluesse.md` (SCH26-07); Blatt Mikrofon (HW-07): Versorgungen 3V3_ANA/1V8_ADC/3V3_MEMS, Audio-ADC TLV320ADC3101 (nicht 3100) mit I²S an PB12/PA15/PB5 und I²C 0x18, Elektret-Vorspannung symmetrisch und Hochpass der Koppel-C aus den Bauteilwerten, PDM-Weg mit Takttreiber, ESD direkt an der Buchse, RJ45 J5/J601 gegen `anschluesse.md` (mit Gegenprobe vertauschter CLK/DATA); Blatt Anschlüsse: 1-Wire- und I²C-Netze, **Pull-ups nur an 3V3_SW** (HW26-04, mit Gegenprobe), ESD-Arrays, J8-Pin 6 frei, eigene Polzahl bzw. Bauform je Sensoranschluss, Masse an Pin 1, J6/J7/J8/J11 gegen `anschluesse.md` (J11 Pins 9–11 BLE-Modul)
5. `werkzeug/pin_footprint.py` (REG26-08): für jedes Bauteil Footprint vorhanden, **Symbol-Pins = Footprint-Pads** und **Symbol-Pinnamen = Pinbelegung laut Datenblatt** (Tabelle mit Quelle und Status [V]/[V*]/[A]/[P] im Skript); schreibt [`pin_footprint.md`](pin_footprint.md), Exit 1 bei Abweichung. Alle Footprints vorhanden (13.10.2026)

Die CI (Job `kicad-schaltplan`) führt das mit KiCad 10 aus der offiziellen PPA aus und verlangt danach `git diff --exit-code`.

## ERC-Stand (KiCad 10.0.6 in der CI und lokal am 13.10.2026; alle Schweregrade)

| Projekt | Meldungen | Bemerkung |
|---|---|---|
| Hauptplatine | 0 | Projektfootprints in `Bienen.pretty` (BQ25185 DLH, Ra-01SH) über `fp-lib-table`; alle globalen Netze haben ihre Gegenstelle |

## Board-Kennung und Umgebung (REG26-10)

| Projekt | Kennung (Titelblock Kommentar 2) | Umgebung (Kommentar 3) [A] |
|---|---|---|
| Hauptplatine | PCB-MAIN-0.1 | Gehäuse −20 … +60 °C, Betauung möglich; VIN ≤ 12 V dauernd, 25 V absolut; Laden nur +5 … 42 °C |

## PWR_FLAG – Begründungen (REG26-09)

Ein `PWR_FLAG` sagt dem ERC: „Hier speist eine Quelle ein, die KiCad nicht als Treiber erkennt.“ Jedes Flag markiert eine echte Quelle; die Begründung steht auch als Beschreibung am Symbol (Generator).

| Projekt | Netz | Echte Quelle |
|---|---|---|
| Hauptplatine (Blatt Akku) | B+, B− | Zelle BT801 (Halter = passive Pins) |
| Hauptplatine (Blatt Akku) | HY_VDD | B+ über R801 100 Ω (HYCON-Anwendungsschaltung) |
| Hauptplatine | VIN_LADER | Panels J201/J202 und VBUS über D201–D203 |
| Hauptplatine | GND | Klemmen J201/J202 und Zelle über Q801 FS8205 (FET kein Treiber im ERC) |
| Hauptplatine | VBAT | Zelle BT801 über die Lötbrücke JP801 (passiv) |
| Hauptplatine | VDDA | +3V3 über Ferrit FB301 (Ferrit kein Treiber im ERC) |
| Hauptplatine | VSUP_HX | 5-V-Wandler U501 über Ferrit FB501 |
| Hauptplatine | HX_AVDD | Kollektor des PNP Q501 (HX711-AVDD-Regler) |
| Hauptplatine | 3V3_ANA | 3V3_SW über Ferrit FB601 und 10 Ω R602 (passive Bauteile kein Treiber im ERC) |
| Hauptplatine | 3V3_MEMS | 3V3_SW über Ferrit FB602 (Versorgung des MEMS-Mikrofons, HW-07) |
| Hauptplatine | BLE_VCC | +3V3 über den Lastschalter Q301 AO3401A (FET kein Treiber im ERC; HW-09) |

Ein neues `PWR_FLAG` nur mit Eintrag in dieser Tabelle; ein Flag auf einem Netz, das schon einen Ausgang hat (z. B. TMP_VCC auf der Hauptplatine), verdeckt Fehler und ist unzulässig.

## Offene Punkte [P]

- Projektfootprints (`werkzeug/footprints.py` → `Bienen.pretty`, reproduzierbar, in `pruefen.sh`): BQ25185 DLH0010A nach TI 4226298/A und Ra-01SH nach Ai-Thinker-Datenblatt V1.1 S. 13 angelegt (13.10.2026). Reedkontakt MiRelay MRS03-B-3 und Side-View-LED Lite-On LTST-S220KGKT gewählt, Footprints nach Datenblatt (13.10.2026); Akkuhalter **Keystone 1042 (SMD)** festgelegt (HW-02, 13.10.2026), Footprint aus der KiCad-Bibliothek; Klemmen auf einreihige DEGSON 15EDGRC-3.5 umgestellt (SCH26-13), 5 Footprints in `Bienen.pretty`. Stand je Bauteil: [`pin_footprint.md`](pin_footprint.md).
- Datenblatt-Pinbelegung noch nicht gelesen ([A]/[P] in `pin_footprint.md`): SPI-Flash (je gewähltem Typ), AO3400A, AO3401A, S8550 (C397181), Quarz Y301, Side-View-LED, TVS D401.
- Blatt MCU, BLE-Modul (HW-09): Footprint `Bienen:Microchip_RN4871` nach DS50002489D Fig. 4-7/4-8/4-9 [V] gegen LCSC/EasyEDA C633942 gegenprüfen; Bestand (50 Stück am 18.10.2026); Prüfplan B-1 … B-6 in `../mcu-funk.md` 1.6; Entscheidung USB-C-Buchse behalten oder entfernen. HY2111, FS8205, RT9080, Ra-01SH nur aus früherer Sitzung ([V*]) – beim Footprint-Anlegen erneut lesen.
- Blatt MCU: Ferrit FB301 (LCSC-Nummer); LED-Helligkeit mit 1 kΩ und Lichtleiter am Muster prüfen; Schaltabstand Reedkontakt am Prototyp.
- Blatt Funk + Flash: Footprint Ra-01SH aus LCSC/EasyEDA C2764087 übernehmen und gegen das Datenblatt prüfen; TVS D401 (3,3 V, SOD-523) wählen; Flash-Typ nach Bestand (XT25F64B / ZD25Q64D); 100 µF C401 als MLCC 1210 oder Tantal entscheiden.
- Blatt Waage: Footprint WSON-6 2 × 2 (KiCad) mit TI DRV0006A vergleichen (U501); Spule L501 1 µH mit Isat ≥ 0,7 A wählen; Ferrite FB501 (600 Ω) und FB502 (Gleichstromwiderstand ≤ 0,1 Ω) wählen; Pinfolge des gelieferten S8550 (Q501) mit 1 B, 2 E, 3 C vergleichen; R507 (Kanal B an INA−) am Muster bewerten.
- Blatt Mikrofon (HW-07): Audio-ADC TLV320ADC3101IRGET (Footprint RGE0024B, EP 2,45 mm; Variante RGE0024F prüfen), TPS70918DBVR, 74LVC1G17 (Herstellerpinbelegung), DEGSON 15EDGRC-3.5-08P – LCSC-Nummern und Bestand; Elektretkapsel und fertige IM69D127-Platine festlegen (`../mikrofon.md` 7).
- Klemmen: DEGSON 15EDGRC-3.5 (einreihig, SCH26-13) mit Footprints `Bienen:DEGSON_15EDGRC-3.5-0nP` nach EasyEDA/LCSC-Geometrie – gegen die DEGSON-Zeichnung prüfen [P].
- Blatt Anschlüsse: LCSC-Nummer ESDS304DBVR (D701, D702); DEGSON-Teilenummern 3- und 6-polig; Kapazität des gekauften Netzwerkkabels messen (`../anschluesse.md` 3.1).
- LCSC-Nummern ergänzen (BQ25185, TMP390, TPS70933, SS34, SMAJ12A, Klemmen, Akkuhalter Keystone 1042).
- Muster: Versuchsplan SCH-T01 … T11 in [`../sicherheit-akku.md`](../sicherheit-akku.md) (Akku/Laden) und Review (übrige).
- Kondensatoren: DC-Bias-Kurven je LCSC-Nummer eintragen (`../versorgung.md` 3.9).

## Stückliste (bisher, 186 Teile; erzeugt aus dem Generator)

| Ref. | Wert | Symbol | Footprint | LCSC | Blatt |
|---|---|---|---|---|---|
| BT801 | 18650 3,6 V | Device:Battery_Cell | BatteryHolder_Keystone_1042_1x18650 |  | Akku |
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
| C301 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C302 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C303 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C304 | 10µ 10V X5R | Device:C | C_0805_2012Metric |  | MCU |
| C305 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C306 | 1µ | Device:C | C_0603_1608Metric |  | MCU |
| C307 | 4,7µ X7R | Device:C | C_0805_2012Metric |  | MCU |
| C308 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C309 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C310 | 18p C0G | Device:C | C_0603_1608Metric |  | MCU |
| C311 | 18p C0G | Device:C | C_0603_1608Metric |  | MCU |
| C312 | 8,2p C0G | Device:C | C_0603_1608Metric |  | MCU |
| C313 | 8,2p C0G | Device:C | C_0603_1608Metric |  | MCU |
| C314 | 10µ 6,3V X5R | Device:C | C_0805_2012Metric |  | MCU |
| C315 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C316 | 100n | Device:C | C_0603_1608Metric |  | MCU |
| C401 | 100µ 6,3V X5R | Device:C | C_1210_3225Metric |  | Funk + Flash |
| C402 | 10µ 10V X5R | Device:C | C_0805_2012Metric |  | Funk + Flash |
| C403 | 100n | Device:C | C_0603_1608Metric |  | Funk + Flash |
| C404 | 100n | Device:C | C_0603_1608Metric |  | Funk + Flash |
| C501 | 4,7µ 16V X5R | Device:C | C_0805_2012Metric |  | Waage |
| C502 | 10µ 10V X5R | Device:C | C_0805_2012Metric |  | Waage |
| C503 | 10µ 10V X5R | Device:C | C_0805_2012Metric |  | Waage |
| C504 | 100n | Device:C | C_0603_1608Metric |  | Waage |
| C505 | 10µ 10V X5R | Device:C | C_0805_2012Metric |  | Waage |
| C506 | 100n | Device:C | C_0603_1608Metric |  | Waage |
| C507 | 100n | Device:C | C_0603_1608Metric |  | Waage |
| C508 | 100n | Device:C | C_0603_1608Metric |  | Waage |
| C510 | 100n | Device:C | C_0603_1608Metric |  | Waage |
| C511 | 10n C0G | Device:C | C_0603_1608Metric |  | Waage |
| C512 | 10n C0G | Device:C | C_0603_1608Metric |  | Waage |
| C601 | 22µ 10V X5R | Device:C | C_0805_2012Metric |  | Mikrofon |
| C602 | 100n | Device:C | C_0603_1608Metric |  | Mikrofon |
| C609 | 1µ | Device:C | C_0603_1608Metric |  | Mikrofon |
| C610 | 4,7µ 16V X7R | Device:C | C_0805_2012Metric |  | Mikrofon |
| C611 | 1µ | Device:C | C_0603_1608Metric |  | Mikrofon |
| C612 | 100n | Device:C | C_0603_1608Metric |  | Mikrofon |
| C613 | 1µ | Device:C | C_0603_1608Metric |  | Mikrofon |
| C614 | 100n | Device:C | C_0603_1608Metric |  | Mikrofon |
| C615 | 1µ | Device:C | C_0603_1608Metric |  | Mikrofon |
| C616 | 100n | Device:C | C_0603_1608Metric |  | Mikrofon |
| C617 | 1µ | Device:C | C_0603_1608Metric |  | Mikrofon |
| C618 | 100n | Device:C | C_0603_1608Metric |  | Mikrofon |
| C619 | 1µ X7R | Device:C | C_0603_1608Metric |  | Mikrofon |
| C620 | 1µ X7R | Device:C | C_0603_1608Metric |  | Mikrofon |
| C621 | 1µ | Device:C | C_0603_1608Metric |  | Mikrofon |
| C622 | 100p C0G | Device:C | C_0603_1608Metric |  | Mikrofon |
| C623 | 100p C0G | Device:C | C_0603_1608Metric |  | Mikrofon |
| C624 | 100n | Device:C | C_0603_1608Metric |  | Mikrofon |
| C625 | 1µ X7R | Device:C | C_0603_1608Metric |  | Mikrofon |
| C626 | 1µ X7R | Device:C | C_0603_1608Metric |  | Mikrofon |
| C627 | 100p C0G | Device:C | C_0603_1608Metric |  | Mikrofon |
| C628 | 100p C0G | Device:C | C_0603_1608Metric |  | Mikrofon |
| C629 | 1µ | Device:C | C_0603_1608Metric |  | Mikrofon |
| C801 | 100n | Device:C | C_0603_1608Metric |  | Akku |
| C802 | 100n | Device:C | C_0603_1608Metric |  | Akku |
| C803 | 100n | Device:C | C_0603_1608Metric |  | Akku |
| D201 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D202 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D203 | SS34 | Diode:SS34 | D_SMA |  | Versorgung |
| D204 | SMAJ12A | Diode:SMAJ12A | D_SMA |  | Versorgung |
| D301 | LTST-S220KGKT | Device:LED | LED_Lite-On_LTST-S220_SideView | C160469 | MCU |
| D401 | TVS 3,3V | Device:D_TVS | D_SOD-523 |  | Funk + Flash |
| D501 | TPD4E05U06DQAR | Power_Protection:TPD4E05U06DQA | USON-10_2.5x1.0mm_P0.5mm | C138714 | Waage |
| D601 | ESDS304DBVR | Power_Protection:ESDS304 | SOT-23-5 |  | Mikrofon |
| D602 | ESDS304DBVR | Power_Protection:ESDS304 | SOT-23-5 |  | Mikrofon |
| D701 | ESDS304DBVR | Power_Protection:ESDS304 | SOT-23-5 |  | Anschlüsse |
| D702 | ESDS304DBVR | Power_Protection:ESDS304 | SOT-23-5 |  | Anschlüsse |
| FB301 | 600R@100MHz | Device:FerriteBead_Small | L_0603_1608Metric |  | MCU |
| FB501 | 600R@100MHz | Device:FerriteBead_Small | L_0603_1608Metric |  | Waage |
| FB502 | Ferrit ≤ 0,1 Ω | Device:FerriteBead_Small | L_0603_1608Metric |  | Waage |
| FB601 | 600R@100MHz | Device:FerriteBead_Small | L_0603_1608Metric |  | Mikrofon |
| FB602 | 600R@100MHz | Device:FerriteBead_Small | L_0603_1608Metric |  | Mikrofon |
| J201 | Solar 1 | Connector_Generic:Conn_01x02 | DEGSON_15EDGRC-3.5-02P | C5160225 | Versorgung |
| J202 | Solar 2 | Connector_Generic:Conn_01x02 | DEGSON_15EDGRC-3.5-02P | C5160225 | Versorgung |
| J301 | Laden 5 V (DNP) | Connector_Generic:Conn_01x02 | PinHeader_1x02_P2.54mm_Vertical |  | MCU |
| J302 | Debug (SWD + Serial1) | Connector_Generic:Conn_01x07 | PinHeader_1x07_P2.54mm_Vertical |  | MCU |
| J501 | Wägezelle | Connector_Generic:Conn_01x05 | DEGSON_15EDGRC-3.5-05P | C7603439 | Waage |
| J601 | Mikrofone 1 + 2 | Connector:RJ45_Shielded | RJ45_RCH_RC01937 |  | Mikrofon |
| J602 | Mikrofon 3 (Elektret) | Connector_Generic:Conn_01x04 | DEGSON_15EDGRC-3.5-04P | C7603438 | Mikrofon |
| J701 | DS18B20 Nr. 1 | Connector_Generic:Conn_01x03 | DEGSON_15EDGRC-3.5-03P | C5160226 | Anschlüsse |
| J702 | DS18B20 Nr. 2 | Connector_Generic:Conn_01x03 | DEGSON_15EDGRC-3.5-03P | C5160226 | Anschlüsse |
| J703 | BME280 | Connector_Generic:Conn_01x06 | DEGSON_15EDGRC-3.5-06P | C49352918 | Anschlüsse |
| J704 | Erweiterung | Connector_Generic:Conn_02x06_Odd_Even | PinHeader_2x06_P2.54mm_Vertical |  | Anschlüsse |
| J801 | Strommessung (DNP) | Connector_Generic:Conn_01x02 | PinHeader_1x02_P2.54mm_Vertical |  | Akku |
| JP301 | BLE dauernd (kein Bestückteil) | Jumper:SolderJumper_2_Open | SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm |  | MCU |
| JP401 | TXEN (kein Bestückteil) | Jumper:SolderJumper_2_Open | SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm |  | Funk + Flash |
| JP402 | RXEN (kein Bestückteil) | Jumper:SolderJumper_2_Open | SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm |  | Funk + Flash |
| JP801 | Messbrücke B+ (kein Bestückteil) | Jumper:SolderJumper_2_Bridged | SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm |  | Akku |
| L501 | 1µ | Device:L | L_0805_2012Metric |  | Waage |
| Q301 | AO3401A | Transistor_FET:AO3401A | SOT-23 | C15127 | MCU |
| Q501 | S8550 | Transistor_BJT:SS8550 | SOT-23 | C397181 | Waage |
| Q801 | FS8205 | Bienen:FS8205 | SOT-23-6 | C32254 | Akku |
| Q802 | AO3400A | Transistor_FET:AO3400A | SOT-23 |  | Akku |
| Q803 | AO3400A | Transistor_FET:AO3400A | SOT-23 |  | Akku |
| R201 | 3,3M | Device:R | R_0603_1608Metric |  | Versorgung |
| R202 | 470k | Device:R | R_0603_1608Metric |  | Versorgung |
| R203 | 2,0k 1% | Device:R | R_0603_1608Metric |  | Versorgung |
| R204 | 130k 1% | Device:R | R_0603_1608Metric |  | Versorgung |
| R205 | 100k | Device:R | R_0603_1608Metric |  | Versorgung |
| R206 | 2,2M | Device:R | R_0603_1608Metric |  | Versorgung |
| R207 | 2,2M | Device:R | R_0603_1608Metric |  | Versorgung |
| R208 | 100k | Device:R | R_0603_1608Metric |  | Versorgung |
| R209 | 0 | Device:R | R_0603_1608Metric |  | Versorgung |
| R301 | 10k | Device:R | R_0603_1608Metric |  | MCU |
| R302 | 10k | Device:R | R_0603_1608Metric |  | MCU |
| R305 | 100k | Device:R | R_0603_1608Metric |  | MCU |
| R306 | 1k | Device:R | R_0603_1608Metric |  | MCU |
| R309 | 100k | Device:R | R_0603_1608Metric |  | MCU |
| R310 | 1k | Device:R | R_0603_1608Metric |  | MCU |
| R311 | 1k | Device:R | R_0603_1608Metric |  | MCU |
| R312 | 10k | Device:R | R_0603_1608Metric |  | MCU |
| R401 | 33 | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R402 | 33 | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R403 | 33 | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R404 | 33 | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R405 | 100k | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R406 | 100k | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R407 | 10k | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R408 | 10k | Device:R | R_0603_1608Metric |  | Funk + Flash |
| R501 | 100k | Device:R | R_0603_1608Metric |  | Waage |
| R502 | 100k | Device:R | R_0603_1608Metric |  | Waage |
| R503 | 20k 1% | Device:R | R_0603_1608Metric |  | Waage |
| R504 | 8,2k 1% | Device:R | R_0603_1608Metric |  | Waage |
| R505 | 100 | Device:R | R_0603_1608Metric |  | Waage |
| R506 | 100 | Device:R | R_0603_1608Metric |  | Waage |
| R507 | 0 | Device:R | R_0603_1608Metric |  | Waage |
| R508 | 1k | Device:R | R_0603_1608Metric |  | Waage |
| R509 | 1k | Device:R | R_0603_1608Metric |  | Waage |
| R602 | 10 | Device:R | R_0603_1608Metric |  | Mikrofon |
| R609 | 10k | Device:R | R_0603_1608Metric |  | Mikrofon |
| R610 | 1k | Device:R | R_0603_1608Metric |  | Mikrofon |
| R611 | 1k | Device:R | R_0603_1608Metric |  | Mikrofon |
| R612 | 33 | Device:R | R_0603_1608Metric |  | Mikrofon |
| R613 | 22 | Device:R | R_0603_1608Metric |  | Mikrofon |
| R614 | 1k | Device:R | R_0603_1608Metric |  | Mikrofon |
| R615 | 1k | Device:R | R_0603_1608Metric |  | Mikrofon |
| R701 | 4,7k | Device:R | R_0603_1608Metric |  | Anschlüsse |
| R702 | 1,8k | Device:R | R_0603_1608Metric |  | Anschlüsse |
| R703 | 1,8k | Device:R | R_0603_1608Metric |  | Anschlüsse |
| R801 | 100 | Device:R | R_0603_1608Metric |  | Akku |
| R802 | 2k | Device:R | R_0603_1608Metric |  | Akku |
| R803 | 2,49k 1% | Device:R | R_0603_1608Metric |  | Akku |
| R804 | 18,7k 1% | Device:R | R_0603_1608Metric |  | Akku |
| R805 | 100k | Device:R | R_0603_1608Metric |  | Akku |
| R806 | 2,49k 1% | Device:R | R_0603_1608Metric |  | Akku |
| R807 | 18,7k 1% | Device:R | R_0603_1608Metric |  | Akku |
| R808 | 100k | Device:R | R_0603_1608Metric |  | Akku |
| SW301 | Reset | Switch:SW_Push | SW_SPST_TL3342 |  | MCU |
| SW302 | BOOT | Switch:SW_Push | SW_SPST_TL3342 |  | MCU |
| SW303 | Service | Switch:SW_Push | SW_SPST_TL3342 |  | MCU |
| SW304 | MRS03-B-3 | Switch:SW_Reed | MiRelay_MRS03_J-Lead_8.5x2.1mm | C41432613 | MCU |
| TH801 | 10k B3435 | Device:Thermistor_NTC | R_0603_1608Metric |  | Akku |
| TP201 | STAT1 (kein Bestückteil) | Connector:TestPoint | TestPoint_Pad_D1.0mm |  | Versorgung |
| TP202 | STAT2 (kein Bestückteil) | Connector:TestPoint | TestPoint_Pad_D1.0mm |  | Versorgung |
| U201 | BQ25185DLHR | Bienen:BQ25185 | WSON-10-1EP_2.2x2mm_DLH0010A |  | Versorgung |
| U202 | RT9080-33GJ5 | Bienen:RT9080-33GJ5 | TSOT-23-5 | C841192 | Versorgung |
| U203 | TPS22917DBV | Power_Management:TPS22917DBV | SOT-23-6 | C2681320 | Versorgung |
| U204 | TPS70933DBV | Bienen:TPS70933DBV | SOT-23-5 |  | Versorgung |
| U301 | STM32F411CEU6 | MCU_ST_STM32F4:STM32F411CEUx | QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm |  | MCU |
| U303 | RN4871-I/RM130 | Bienen:RN4871 | Microchip_RN4871 | C633942 | MCU |
| U401 | Ra-01SH | Bienen:Ra-01SH | Ai-Thinker_Ra-01SH | C2764087 | Funk + Flash |
| U402 | 64 Mbit SOIC-8 208 mil | Memory_Flash:W25Q32JVSS | SOIC-8_5.3x5.3mm_P1.27mm |  | Funk + Flash |
| U501 | TPS61240DRVR | Bienen:TPS61240 | WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm | C59567 | Waage |
| U502 | HX711 | Analog_ADC:HX711 | SOIC-16_3.9x9.9mm_P1.27mm | C43656 | Waage |
| U601 | TLV320ADC3101IRGET | Bienen:TLV320ADC3101 | VQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm |  | Mikrofon |
| U602 | TPS70918DBVR | Bienen:TPS70933DBV | SOT-23-5 |  | Mikrofon |
| U603 | 74LVC1G17GW | 74xGxx:74LVC1G17 | SOT-353_SC-70-5 |  | Mikrofon |
| U801 | HY2111-GB | Bienen:HY2111-GB | SOT-23-6 | C82747 | Akku |
| U802 | TMP390A2DRL | Bienen:TMP390 | SOT-563 |  | Akku |
| U803 | TMP390A2DRL | Bienen:TMP390 | SOT-563 |  | Akku |
| Y301 | 25MHz 12pF | Device:Crystal_GND24 | Crystal_SMD_3225-4Pin_3.2x2.5mm | C9006 | MCU |
| Y302 | 32,768k 7pF | Device:Crystal | Crystal_SMD_3215-2Pin_3.2x1.5mm | C97604 | MCU |

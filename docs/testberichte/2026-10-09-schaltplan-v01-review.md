# Schaltplan V0.1 – unabhängige Netz-/Sicherheitsprüfung

- **Reviewdatum:** 09.10.2026.
- **Geprüfter Commit:** [fcd18febf01b3a15fad849f12050fcc419168bb5](https://github.com/impyer/bienen-lora-logger/commit/fcd18febf01b3a15fad849f12050fcc419168bb5), „Schaltplan erstellt V0.1“.
- **Vorgängerversion:** [cc6ba60da726](https://github.com/impyer/bienen-lora-logger/commit/cc6ba60da726), Änderungen an Anforderungen und Testmodellen. [Hardware-Review 0.4](2026-10-09-hardware-04-review.md) bleibt historische Basis.
- **Umfang:** `hardware/kicad/akku-platine/akku.kicad_sch` und `hardware/kicad/hauptplatine/logger.kicad_sch` mit einzigem Unterblatt `versorgung.kicad_sch`, dazu `akku_platine.py`, `hauptplatine.py`, `werkzeug/kicad_gen.py`, `werkzeug/symbole.py`, `bienen.kicad_sym`, `pruefen.sh` und Lastenheft.
- **Methodik:** Statisches Review der Schaltungstopologie, Pins, Labels/Schienen, Grenzwerte, Sicherheits-/Recovery-Zustände und Fertigungsreife. **Die tatsächlichen eingecheckten KiCad-S-Ausdrücke** wurden mit einem unabhängigen Parser auf Instanzen, Netlabels und ausgewählte Bauteil-Pin-zu-Netz-Zuordnungen geprüft (siehe unten). Herstellerquellen TI TMP390, BQ25185, TPS22917 und HYCON HY2111 abgeglichen. Aktuelle CI-Joblogs eingesehen.
- **NICHT geleistet:** KiCad 10/`kicad-cli` lokal verfügbar, unabhängige ERC-/DRC-Ausführung, neu gerenderter Schaltplan/PDF, SPICE-, Thermal- oder EMV-Simulation, echte Bauteil-, PCB- oder Akkumessung. `hardware/kicad/README.md` **berichtet** ERC Akku 0 Fehler/0 Warnungen, Hauptplatine 0 Fehler/2 Warnungen; das ist ein Entwickler-Nachweis, **keine unabhängige Wiederholung**.
- **Entscheid:** **V0.1 für iterative Schaltplanentwicklung geeignet; NICHT für PCB/Fertigung freigegeben.** Ein kritisches Recovery-Szenario des Zellschutzes ist zuerst zu klären.

## 1. Vollständigkeit und geprüfte Netze

| Projekt | Tatsächlich eingecheckt | Komponenten ohne Power-Symbole | Nicht-versorgungsbezogene Netlabels |
|---|---|---:|---:|
| Akku-Platine | `akku.kicad_sch` | 16 | 41 |
| Hauptplatine | Root `logger.kicad_sch` + Versorgung `versorgung.kicad_sch` | 32 | 54 |
| **Summe** | **zwei Teilprojekte / ein Wurzelblatt mit einem Unterblatt** | **48** | **95** |

**Nicht Bestandteil der Revision:** MCU (STM32F411), SX1262/Ra-01SH + 64-Mbit-Flash, HX711/TPS61240, Mikrofon/Analogfilter/ADC, USB-C, I²C/OneWire, Außen-ESD-Anschlüsse und eigentliche PCB-/Gerber-/BOM-/CPL-Daten. Diese Funktionsblöcke wurden nur bezüglich vorgesehener globaler Schnittstellen geprüft, nicht als Schaltplan.

**Individuelle Pin-zu-Netz-Gegenprüfung an den eingecheckten KiCad-Instanzen:**

| Bauteil | Schlüssel-Pins / überprüfte Netze |
|---|---|
| `U1 HY2111-GB` | 1 OD → `GATE_ENTL`; 2 CS → `HY_CS`; 3 OC → `GATE_LADE`; 5 VDD → `HY_VDD`; 6 VSS → `B-` |
| `Q1 FS8205` | 1 S1 → `B-`, 3 S2 → geschütztes `GND`, 2+5 D12 → `D12`, G1/G2 getrennt zu OD/OC |
| `U2 TMP390` | 1 SETA → `SETA`, 2 SETB → `SETB`, 5 VDD → `P+`, 3 GND → geschütztes `GND`, 4 OUTB + 6 OUTA → `GATE_CE` |
| `Q2 AO3400A` | G → `GATE_CE`, S → `GND`, D → `CE_FREI` |
| `J1` ↔ `J203` | 1 GND ↔ GND; 2 NTC ↔ NTC; 3 CE_FREI ↔ CE_LADEN; 4 P+ ↔ VBAT; **logisch zueinander passend** |
| `U201 BQ25185` | 10 IN → `VIN_LADER`, 1 SYS → `SYS`, 2 BAT → `VBAT`, 4 /CE → `CE_LADEN`, 6 TS/MR → `NTC`, 7 ILIM/VSET → `ILIM`, 8 ISET → `ISET`, 5 GND und 11 EP → GND |
| `U202 RT9080` | 1 VIN, 3 EN → SYS; 5 VOUT → +3V3; 2 GND → GND |
| `U203 TPS22917` | 1 VIN → +3V3; 3 ON → SENSOR_EIN; 4 CT → SW_CT; 5 QOD → SW_QOD; 6 VOUT → 3V3_SW |

Die Custom-Symbol-Pinnummern wurden außerdem mit den aktuell hinterlegten Quellen verglichen. **Kein offensichtlicher Pinvertauschungsfehler** in diesen ausgewählten Netzen entdeckt; bei `GND` und `+3V3` liegen KiCad-Powersymbole direkt auf dem Pin und daher kein alphanumerisches Netzlabel. Eine gerenderte Schaltplan-/Netzlistenprüfung mit KiCad ersetzt dies nicht.

## 2. Bestätigte Schaltungsentscheidungen

- **Zellschutz:** HY2111-GB + FS8205 als Low-Side-Schutz mit getrenntem Entlade- und Lade-FET, CS über R2 = 2 kΩ nach geschütztem Minus, R1 = 100 Ω und C1 = 100 nF an der Zellversorgung. Das entspricht der beabsichtigten Topologie. **Schutzabschaltung und Wiederfreigabe sind ausdrücklich ungetestet.**
- **Ladetemperatur:** TMP390A2DRL, SETA über **R3 2,49 kΩ**: HOT nominal **42 °C**; SETB über **R4 18,7 kΩ**: COLD nominal **+5 °C**, Hysterese **5 °C** (TI Tabellen 7-1/7-2). Beide Open-Drain-Ausgänge verbinden sich zum gleichen Fensteralarm; TI E2E bestätigt diese Wired-OR-Anwendung.
- **BQ25185:** R203 **2,0 kΩ → ca. 150 mA** Lade-Sollstrom; R204 **130 kΩ → 4,1 V Ladeschluss / ILIM 500 mA** laut TI-Widerstandstabelle. C204 an SYS und C205 an BAT, TH1/NTC an TS/MR, /CE getrennt über Q2. **Noch keine Toleranz-/Fehler-/Thermikprüfung am Muster.**
- **Solar und USB:** SS34 D201/D202 trennen die beiden Panels; D203 trennt VBUS; D204 SMAJ12A und C201/C202 sind am gemeinsamen Eingang `VIN_LADER`. Solar-ADC teilt **3,3 MΩ/470 kΩ** und misst den Lader-Eingang: 12 V → **1,50 V**, 18 V → **2,24 V**, 25 V → **3,12 V** (ohne Störungen). Dieser frühere rechnerische Teilerfehler ist im Nennmodell korrigiert.
- **3,3-V-Schiene:** RT9080 ist dauernd an SYS; TPS22917 schaltet `3V3_SW` über `SENSOR_EIN`, C210=1 nF zwischen CT und VIN, R209=0 Ω zwischen QOD und VOUT. CT-/QOD-Polung entspricht TI-Anwendungsschaltung. Die übrigen Sensorlasten existieren noch nicht als KiCad-Schaltung.
- **Begrenztes System-CI:** [GitHub Actions Run 37876216220](https://github.com/impyer/bienen-lora-logger/actions/runs/37876216220) **6 von 6 Jobs erfolgreich**: bestehende BlackPill-Firmware, PC-/Modelltests, Server, Formatter, Windows, Hardware-Rechenmodelle. **Keiner dieser Jobs prüft KiCad-ERC oder diese neuen Schaltpläne.** Der grüne Firmware-Build gehört weiterhin zum **RFM95-Musterlogger**, nicht zur neuen SX1262-Platine.

## 3. Neue Befunde mit eindeutigen IDs

### SCH26-01 — P0, vor Bestückung zwingend — Potenzieller Lade-Wiederanlauf-Deadlock nach Zellschutz-Tiefentladung

**Konkrete Netze:** `akku_platine.py`: U2 TMP390 `VDD=P+`, `GND=GND`, Q2 `S=GND`, `D=CE_FREI`; U1 HY2111 `OD=GATE_ENTL`, Q1 FS8205 `S1=B-`, `S2=GND`. `hauptplatine.py`: U201 BQ25185 /CE=CE_LADEN, R205=10 MΩ von SYS nach CE.

**Physikalische Sequenz/Hypothese:**
1. Normalbetrieb: FS8205-Entlade-MOSFET verbindet Zell-Minus `B-` und geschütztes `GND`; TMP390 bekommt Versorgung `P+–GND` und darf über Q2 `/CE` auf LOW ziehen.
2. Unterspannung: HY2111 schaltet **Entlade-FET** ab. Der geschützte Minus-Anschluss der Akku-Platine ist dann von Zell-Minus entkoppelt. Der TMP390 ist jedoch **nicht direkt zwischen rohem B+ und B-**, sondern zwischen P+ und dem **abgeschalteten** P− verschaltet. Seine Versorgung/Referenz und damit Q2s Einschaltzustand sind bei geöffnetem FET nicht mehr garantiert.
3. Bei wieder verfügbarer Sonne oder USB wird BQ25185 SYS gespeist. **R205 zieht /CE nach HIGH = Ladung AUS**, solange Q2 nicht leitend ist. Der HY2111-GB mit Power-Down benötigt wiederum **ein Ladeereignis** zur Freigabe nach Tiefentladung. Es kann ein zirkulärer „ohne Ladefreigabe keine Recovery; ohne Recovery keine Versorgung des Ladefreigabeschalters“-Zustand entstehen.

**Kritische Einordnung:** Die Off-State-Ströme, Body-Dioden, internen Pull-ups und parasitären Pfade sind ohne vollständiges elektrothermisches Modell/Prototyp **nicht nachgewiesen**. Dies ist deshalb **ein plausibler, sicherheits- und betriebsrelevanter Sperrpfad, kein bereits gemessener Feldausfall**. HYCON dokumentiert, dass bei einer Power-Down-Variante die Recovery von Charger Detection und Zellspannung abhängt; siehe [offizielles HY2111-Datenblatt, Abschnitt 11.3.1](https://www.hycontek.com/wp-content/uploads/DS-HY2111_EN.pdf). TI dokumentiert bei BQ25185: `CE=HIGH` verhindert Ladung ([BQ25185, Datenblatt](https://www.ti.com/lit/ds/symlink/bq25185.pdf)).

**Abnahme / Vorschlag:** Sequenz mit SPICE/Schaltzustands- und Body-Dioden-Analyse nachzeichnen; **mit strombegrenztem Zell-Emulator, nicht einer absichtlich gefährlich tiefentladenen echten 18650**, HY2111 in Overdischarge versetzen; Solar/VBUS anlegen; `P+`, `B-`, `P-`, `CE_FREI`, `/CE`, TS, BAT, SYS und Ladestrom messen. Erforderlich: kontrollierte Wiederladung bei zulässiger Zelltemperatur, **ohne** ungeschützten Standby-Entladestrom im Shutdown. Eventuell temperaturüberwachte sichere Lade-Startversorgung unabhängig vom getrennten Akku-P− entwerfen; das ist **kein** Aufruf, die Temperatursperre zu überbrücken.

### SCH26-02 — P1, vor Schaltplanfreigabe — Hochohmige Freigabekette R5/R205 je 10 MΩ

- **Fundstellen:** Akku `R5=10M` an `GATE_CE`; Hauptplatine `R205=10M` an `CE_LADEN`; Sensor/Tiefentladeschutz: U2, Q2, U201.
- **Rechenpunkt:** TI spezifiziert für TMP390-Ausgänge im HIGH-Zustand einen möglichen Leckstrom von **±0,1 µA**. An **10 MΩ** ergibt das rechnerisch **1 V Pegelverschiebung**; bei 2,9 V Zellspannung könnte statt 2,9 V nur etwa 1,9 V am AO3400A-Gate liegen. Der tatsächliche Pegel hängt von Leckstromvorzeichen/-verteilung und weiteren parasitären Pfaden ab; nicht als garantierter Wert ausgeben.
- **Risiko:** Gate-/CE-Pegel sind bei hoher Temperatur, Feuchtigkeit und niedriger Zellspannung mit sehr geringer Reserve dimensioniert. Zusätzlich sind CE-Eingangsleckstrom und Widerstandstoleranzen nicht bilanziert. Der 10-nF-Kondensator C206 verlängert das Umschalten; seine Wirkung ist funktional zu prüfen.
- **Akzeptanz:** Min/typ/max-Logikpegel für Kombinationen U2-Ausgang HIGH-Z/LOW, Temperaturgrenzen, Zellspannung 2,9–4,2 V und SYS mit/ohne Eingang rechnerisch und am Muster nachweisen; Q2-VGS, CE <0,4 V bei Laden erlaubt bzw. CE >1,3 V bei gesperrt (TI-Kriterien). Resistorwerte nach Sicherheits-/Ruhestromabwägung neu bestimmen; Feuchte-/Leckpfad prüfen. **Keinen blinden Wechsel auf 10 kΩ** (wäre bei freigegebenem Laden erheblicher Ruhestrom aus dem Akku).

### SCH26-03 — P1, vor Sicherheitsfreigabe — „Zweistufig“ ist keine unabhängige 45-°C-Einzelfehlersicherheit

- **Fundstelle:** Akku U2/Q2-Hauptstufe; TH1=10k/B3435 am BQ25185 TS/MR als zweite Stufe.
- **Ist:** Bei funktionierendem TMP390 liegt die HOT-Abschaltung bei 42 °C nominal (Toleranzen nach TI ±1,5 °C bei 2,5–5,5 V im Bereich 0–70 °C), grundsätzlich konservativ unter der im Projekt bis zur Zellbeschaffung gewählten 45-°C-Grenze. NTC am BQ25185 sperrt dagegen im nominalen Modell erst **ca. 59,5 °C**.
- **Folge:** Bleibt `GATE_CE` durch defektes Q2/kurzgeschlossenen OUT / Leitungsschaden in Zustand „Laden erlaubt“, verhindert die NTC-Ersatzstufe **nicht** das Laden zwischen 45 °C und ~59,5 °C. Das ist ein **nicht abgedeckter Einzelfehler**, nicht der Nachweis eines Fehlers bei korrekt funktionierender TMP390-Stufe.
- **Akzeptanz:** Schutzanforderung explizit festlegen (normaler Betrieb vs. Single-Fault-Abdeckung). Unterbrechung/Kurzschluss von OUTA/OUTB, Q2 G/D/S, TH1 und jede der vier Akku-Leitungen simulieren und testen; die Zelloberfläche und das Sensorelement thermisch koppeln; Sensorverzug bei Erwärmung 42→45 °C messen. Falls Einzelfehlerfestigkeit verlangt ist, einen **tatsächlich in der zulässigen Grenze wirksamen** zweiten Abschaltpfad vorsehen.

### SCH26-04 — P1, vor PCB-Layout — Footprints, ERC und Generator-Reproduzierbarkeit nicht vollständig abgesichert

- **Quellen:** `hardware/kicad/README.md`, `pruefen.sh`, `hauptplatine.py`, `akku_platine.py`, `.github/workflows/tests.yml`.
- **Fakten:** Der definierte `Bienen:WSON-10-1EP_2.2x2mm_DLH0010A`-Footprint (U201 BQ25185) existiert im Repository noch **nicht**. Akkuhalter BT1 ist **1042-Footprint als Platzhalter für Keystone 1043**. J201/J202 nutzen Phoenix-Platzhalter statt endgültiger DEGSON-Footprints. Für zahlreiche weitere Teile fehlen finale Hersteller-/LCSC-IDs. Root `logger.kicad_sch` umfasst derzeit nur „Versorgung“.
- **Testabdeckung:** `pruefen.sh` ruft vor dem ERC die Python-Generatoren auf und **überschreibt die versionierten KiCad-Dateien**. Die bestehende CI führt `pruefen.sh` **nicht** aus. `kicad-cli sch erc --severity-error` berücksichtigt **Warnungen nicht** als Fehler; projektdokumentierte 0 Fehler sind kein Beweis für schaltungstechnische Fehlerfreiheit.
- **Abnahme:** KiCad-10-Version festlegen, alle Footprints geometrisch/Pin1/Pad-Größen mit Herstellerzeichnung abgleichen; **ERC inklusive Warnungsinventar** für beide Projekte, Netzlistenexport, Generierungsvergleich `git diff --exit-code` in einem sauberen CI-Checkout, BOM-/DNP-Prüfung, anschließend später DRC. Die vorhandenen PDF-Ausdrucke sind keine eigenständige elektrische Freigabe.

### SCH26-05 — P2 — Sensorschalter: R208 = 1 MΩ statt vereinbarter 100 kΩ

- **Fundstellen:** `hauptplatine.py` R208 (SENSOR_EIN → GND) und `hardware/versorgung.md` `3.7, dort **100 kΩ** als Standby-Pull-down gefordert.
- **Risiko:** Im STM32-Standby ist PB5 hochohmig. TPS22917 besitzt zusätzlich einen Smart-Pulldown, aber nur unter bestimmten Bedingungen. Der externe Faktor 10 erhöht die Anfälligkeit gegenüber Leakage/Störungen; `1 µA × 1 MΩ = 1 V` ist eine anschauliche Größenordnung, keine gemessene Pin-Leckage.
- **Akzeptanz:** Gewünschten Pull-down als verbindliche Änderung anwenden oder die Ausnahme mit Maximalleckstrom und VIH/VIL über Temperatur belegen; 3V3_SW bei Standby, MCU-Reset, ESD und hochohmigem Eingang sicher AUS.

### SCH26-06 — P2 — Akku-JST-Kabel mechanisch und gegen Fehler verdrahtungsfest machen

- **Fundstellen:** Akku J1, Hauptplatine J203, beide vierpolig PH. **Logische Reihenfolge übereinstimmend**: 1 GND, 2 NTC, 3 CE, 4 BAT+.
- **Risiko:** Zwei unabhängige KiCad-Projekte können den **wirklichen konfektionierten Kabelbaum** (Ansicht auf Stift-/Buchsenseite, Adernspiegelung, falsches Crimpgehäuse, vertikale/horizontale Orientierung) nicht ERC-prüfen. Ein Fehler kann Akkupole und Steuersignale verwechseln.
- **Akzeptanz:** Kabelbauplan mit Blickrichtung und Durchgangstabelle, Crimp-/JST-Gegenstecker-Bestellnummer, Pin-1-Markierung; Polungs-/Fehlstecktest mit **strombegrenzter Quelle**. Thermofühler-/TMP390-Platzierung am 18650 physisch bestätigen.

### SCH26-07 — P2 — Fehlende Systemblätter und Schnittstellen offen

- **Fundstelle:** `hauptplatine.py`, `SCHNITTSTELLEN = {VBUS, ADC_SOLAR, ADC_AKKU, SENSOR_EIN, 3V3_SW, SYS}`; Wurzel-Schaltplan enthält nur Versorgung.
- **Status:** Keine Beurteilung der STM32-VDD-/VCAP-/VBAT-Pins, PA0/PA1, USB-C-CC-D+/D−, Funk-RF-Switch, UART/SWD, TPS61240/HX711, SPI-Flash, Mikrofon-Anti-Aliasing, ESD-Dioden der Außenanschlüsse möglich. VBUS hat aktuell bewusst nur ein Ende.
- **Akzeptanz:** Folgende Blätter getrennt generieren, anschlussübergreifenden Netlist-/ERC-Check durchführen, insbesondere **keine Sensor-Pull-ups auf Dauerversorgung**, Rückspeisung der unversorgten Bauteile und getrennte Analog-/Power-Rückströme absichern. „Hauptplatine geprüft“ erst nach Vollständigkeit.

### SCH26-08 — P2 — Außenleitungs-/Surge-/Temperaturdimensionierung nur nominal

- **Fundstelle:** D201–D204, C201=4,7 µF/25 V, R201/R202, PV-Pinbelegung.
- **Risiken:** SMAJ12A-Schutz ist vor allem für Transienten spezifiziert; Polarität des unidirektionalen Symbols und reale Klemmspannung/Impulsenergie müssen zur Panelleitung, Schottky, BQ25185-25V-Absolutgrenze und 25V-Eingangskondensator passen. Bei 25V Dauer liegt C201 genau an seiner nominellen Spannungsgrenze; DC-Bias/Derating ist noch nicht berücksichtigt. Der ADC-Wert 3,12V bei 25V gilt nur, solange die MCU mit geeigneter Referenz versorgt ist; bei Stromausfall/VDDA=0 müssen Schutz- und Einspritzströme bewertet werden.
- **Akzeptanz:** Reale Panel-VOC/ISC messen, feste DC- und Transientengrenzen einschließlich Temperaturrand, MLCC-Derating und Reverse-/Surge-Analyse, an den Außenklemmen ESD/Transientenschutz mit Layoutleitungsweg abschließen.

## 4. Spezifische Mess- und Fehlertestmatrix für die nächste Version

| Test-ID | Umgebung / Eingriff | Abnahmepunkt |
|---|---|---|
| SCH-T01 | Normaler Akku-Emulator 3,2–4,2 V, Solar 0/6/12 V und USB 5V | SYS, BAT, +3V3, CE, Lade-/Ruhegrößen stimmen mit BQ25185-Funktion überein |
| SCH-T02 | Temperatur-Emulation 0, 4, 5, 7, 36, 37, 42, 44, 45, 55, 60 °C | CE sperrt zuverlässig außerhalb freigegebenem Fenster; Hysterese korrekt, Ladeleistung null |
| SCH-T03 | TMP390-OUTA/OUTB einzeln offen/low, Q2 offen/kurz, NTC offen/kurz, Akku-CE-Ader unterbrochen | Gewollter, dokumentierter Schutzzustand; gefährliche Single-Fault-Lücke nicht übersehen |
| SCH-T04 | **Zell-Emulator unter 2,90 V** → HY2111-Sleep → VBUS/PV wieder an | **Lade-Recovery ohne Umgehen des Temperaturschutzes**; bei Scheitern Schaltungsänderung |
| SCH-T05 | MCU PB5 high-Z, Reset/Standby, 3V3_SW belastet | Sensoren sicher aus, kein Rückspeisen, Ruhestromziel erfüllt |
| SCH-T06 | 12/18V VIN, abgeschaltete VDDA, transienter Anschluss, Strombegrenzung | Solar-ADC bleibt im erlaubten Spannungs-/Injektionsbereich |
| SCH-T07 | KiCad 10 ERC mit Warnungen; Schaltplan neu generieren und byte-/semantischen Diff prüfen | 0 echte elektrische Fehler, begründete Warnungen, kein unbeabsichtigter Export-Drift |
| SCH-T08 | Endgültige Footprints + Leiterplattenentwurf, 1:1 Ausdruck/3D-Assembly | Keine Pad-/Pinverwechslung; Akkuhalter/USB/Klemmen, Produktions- und Montagedaten stimmen |

**Keine absichtliche gefährliche Tiefentladung realer 18650-Zellen für den Test.** Zunächst strombegrenzte Zell-/Ladeemulatoren verwenden, dann mit professionellem Akkutestprotokoll die Bauteile prüfen.

## 5. Reproduktionsbefehle und Herstellerquellen

```sh
# Mit KiCad 10, in frischem Git-Checkout ausführen:
bash hardware/kicad/pruefen.sh
git diff -- hardware/kicad/
# Sichtprüfung aller gemeldeten ERC-Warnungen zusätzlich erforderlich.
# Der CLI-Check ist NICHT Teil des vorhandenen GitHub-Actions-Laufs.
```

- TI [BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf): CE-Logik, TS/MR, BATFET und Lade-Resistortabelle.
- TI [TMP390](https://www.ti.com/lit/ds/symlink/tmp390.pdf): Pins, Tabellen 7-1/7-2 und **±0,1 µA max. Open-Drain-Leckstrom**; [TI-Auskunft zur Wired-OR-Kombination](https://e2e.ti.com/support/sensors-group/sensors/f/sensors-forum/1459251/tmp390-output-configuration-and-need-for-pull-up-resistors).
- TI [TPS22917](https://www.ti.com/lit/ds/symlink/tps22917.pdf): CT an VIN, QOD an VOUT, ON-Pull-down.
- HYCON [HY2111, Abschnitte 11.3 ff.](https://www.hycontek.com/wp-content/uploads/DS-HY2111_EN.pdf): Overdischarge, Charger Detection und Recovery.
- Herstellerangaben der **konkret ausgewählten** Zell-, MOSFET-, Schottky- und Kondensatorvariante zum Fertigungsstand dokumentieren.

## Fazit für Claude

**P0 SCH26-01 zuerst prüfen:** Nach Tiefentladung muss der Zellschutz bei Solar-/USB-Ladung wieder anlaufen, auch wenn der geschützte Minuspfad zuvor getrennt wurde. Ohne Recovery-Prüfung **keine Produktionsfreigabe**. Danach **SCH26-02/03** (Freigabepegel und Single-Fault-Temperaturschutz), **SCH26-04** (KiCad-ERC-/Footprints-/Reproduktions-CI), **SCH26-05/06/08** (Pull-down, Verkabelung, PV-Surge) und die fehlenden Systemblätter (`SCH26-07`). Jede Behebung gegen die genaue Commit-/Bauteil-/Netzreferenz dokumentieren. **Keinen Produktionsfehler behaupten, wo bisher nur ein ungetesteter Schaltungszustand vorliegt.**

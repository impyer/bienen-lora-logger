# Prüfbericht: Schaltplan-Review auf Einsparungen, Pin-Kniffe und SPICE-Prüfung der Analogpfade

- **Prüfbericht-ID:** SCH-2026-10-18-OPT
- **Prüfdatum (UTC):** 18.10.2026 (abends, nach dem Layout-Stand `7aa1fe5`)
- **Anlass:** Frage des Maintainers nach weiterem Verbesserungspotenzial (Pin-Tausch, Kniffe, Bauteilreduktion) und einer Simulation
- **Geprüfter Stand:** Branch `design/hw10-layout-stand`, Kopf `7aa1fe5` (HW-09, HW-10 mit J601-Paaren, Review-Nachtrag); Generator `hardware/kicad/hauptplatine.py`, 186 Bauteile
- **Teststufe:** T0 (Durchsicht aller 7 Blätter gegen Datenblätter und Blockdokumente) und **T2 (SPICE-Modell)**: `hardware/schaltplan_spice.py` mit der ngspice-46-Bibliothek aus KiCad 10.0.7 (`ngspice.dll`), 12 Prüfungen mit Grenzen, in der CI (Job `hardware-rechnungen`, Ubuntu `libngspice0`). **Keine Messung.** Simulation ersetzt keinen Mustertest; alle Modellwerte mit [V]/[A] im Skript.
- **Ergebnis in einem Satz:** Keine Fehler gefunden; **6 Bauteile lassen sich ohne Funktionsverlust streichen**, **6 weitere mit einer Entscheidung** (5-V-Wandler der Waage), dazu zwei Kniffe (Pin-Tauschgruppen für den Layouter, Sanftanlauf des BLE-Schalters) und ein Qualitätsthema (hochohmige ADC-Teiler).

## 1. SPICE-Prüfung (`python3 hardware/schaltplan_spice.py`, 12/12 bestanden)

| Nr. | Pfad | Modell (Werte [V]/[A]) | Ergebnis | Grenze | Folge |
|---|---|---|---|---|---|
| S1 | Elektret 1/3 (Blatt Mikrofon): Kapsel 2,2 kΩ / 0,3 mA [A] an MICBIAS 2,5 V über 2 × 1 kΩ, 100 pF, 1 µF, ADC-Eingang 35 kΩ [A] | AC + Arbeitspunkt | Durchlass −6,6 dB, Hochpass **5,0 Hz**, 100-pF-Grenze 3,2 MHz; Kapselspannung **1,90 V** | ≤ 20 Hz; ≥ 100 kHz; ≥ 1,5 V | ok; die 100 pF dämpfen 3,1 MHz nur 3 dB – deshalb bleibt die Empfehlung, Mikrofon 3 ohne laufenden PDM-Takt zu messen (seit der Paarzuordnung 4/5 nicht mehr Pflicht) |
| S2 | HX711-AVDD-Regler (Blatt Waage): PNP hFE 80–300, 20 k/8,2 k ±1 %, Brücke 404 Ω [V] | .op, Eckwerte | **4,30 V**, Eckwerte 4,24–4,36 V, 12,4 mA | 4,2–4,4 V, ≥ 0,1 V unter VSUP | ok. **Variante ohne 5-V-Wandler:** VSUP 3,3 V, Teiler 14 k/10 k → AVDD 3,00 V, 8,7 mA aus 3V3_SW; Brückensignal 6,0 statt 8,6 mV, Auflösung 1,7 statt 1,2 g bei 200 kg [A] |
| S3 | BLE-Lastschalter Q301 (Blatt MCU): 10 µF + 100 nF an +3V3 (RT9080 0,2 Ω [A], Schiene 113 µF [V]) | Transient | Gate direkt: +3V3-Einbruch auf **3,06 V**, Spitzenstrom 1,2 A aus der Schiene; **Sanftanlauf** 10 kΩ + 47 nF Gate–Drain: 3,29 V, **55 mA** | ≥ 3,0 V; Vorschlag ≤ 300 mA | heutiger Stand funktioniert; Sanftanlauf empfohlen (2 Bauteile), siehe 2.3 |
| S4 | RN4871 RST_N mit internem Pull-up 34–74 kΩ [V] und C316 100 nF; Entladung über R313 | Transient | 0,7·VDD nach **4,1–8,9 ms**; BLE_VCC < 0,3 V nach **2,4 s** | 1–10 ms; ≤ 5 s | ok (Modul-Anlauf 68 ms [V]) |
| S5 | ADC-Teiler (Blatt Versorgung): Akku 2 × 2,2 MΩ, Solar 3,3 M/470 k, STM32-Eingangsleckstrom | Rechnung | 50 nA → **0,11 V** (Akku) / 0,16 V (Solar) Fehler; 1 µA (Datenblatt-Maximum [P]) → 2,2 V / 3,3 V | ≤ 0,15 V bei 50 nA | ok typisch; **Qualitätsthema HW26-21**, siehe 2.4 |
| S6 | Sensorschiene TPS22917, CT 1 nF [V] | Rechnung | Anstieg 3,9 ms, Einschaltstrom in 30 µF **25 mA** | ≤ 200 mA | ok |
| S7 | 1-Wire 4,7 kΩ, 550 pF Bus (10 m) [A] | Transient | Anstieg auf 0,7·VDD **3,1 µs** | ≤ 15 µs | ok; Reihenwiderstand nicht nötig (Text in mcu-funk.md berichtigt) |

## 2. Verbesserungspotenzial

### 2.1 Bauteile, die ohne Funktionsverlust entfallen können (Vorschlag, −6 Teile)

| Ref. | Heute | Vorschlag | Begründung | Risiko |
|---|---|---|---|---|
| R302 10 k | PB2/BOOT1 über 10 kΩ an GND | PB2 direkt an GND | BOOT1 wird nur bei BOOT0 = 1 gelesen; PB2 ist sonst unbenutzt; direkte Masse ist üblich [A] | keins (PB2 später nicht als GPIO nutzbar) |
| C308 100 n | eigener Kondensator an VBAT | entfällt | VBAT liegt fest an +3V3; die VDD-Abblockung (3 × 100 n + 10 µ) deckt den Pin mit ab; der Kondensator ist für eine Pufferzelle gedacht [A: ST AN4488] | keins |
| FB301, C306 | VDDA über Ferrit + 1 µF + 100 nF | VDDA direkt an +3V3, nur C305 100 n | Der ADC misst nur Akku- und Solarspannung über hochohmige Teiler (S5: Auflösung ohnehin durch Leckstrom begrenzt); Mikrofon läuft seit HW-07 über den Audio-ADC. ST schreibt den Ferrit nicht vor | kein PWR_FLAG #FLG301 mehr nötig; etwas mehr Rauschen am 12-Bit-ADC (unerheblich bei 2 ADC-LSB Zielgenauigkeit) |
| R407, R408 10 k | WP/HOLD des SPI-Flash über 10 kΩ an +3V3 | WP/HOLD direkt an +3V3 | Beide Funktionen werden nicht genutzt; direkte Verbindung ist Standard [A] | WP/HOLD später nicht mehr nutzbar (Quad-SPI-Modus braucht sie nicht) |

Optional, aber nicht empfohlen zu streichen: R312 10 k (P2_0 hat einen internen Pull-up 34–74 kΩ [V], der externe hält den Testmodus-Eingang an J704 Pin 11 störfest), R209 0 Ω (Platzhalter für einen QOD-Widerstand), R507 0 Ω (bis zur Messung am Muster), C402 10 µ (ESR-Ergänzung zu C401), D401 TVS (Datenblattempfehlung des Funkmoduls), C316 (Anlaufverzögerung des Moduls).

### 2.2 Entscheidung Philipp: 5-V-Wandler der Waage (−6 Teile, −50 % Waagen-Energie, +1 GPIO)

Heute: TPS61240 U501, L501, C501, C502, R501, R502 erzeugen 5 V für VSUP des HX711, damit AVDD 4,3 V möglich ist (`waage.md` 2/3). **Alternative:** HX711 direkt an 3V3_SW (VSUP 2,7–5,5 V [V]), AVDD = 3,0 V über den vorhandenen PNP-Regler mit Teiler **14 k / 10 k** (S2). Folgen laut Modell:

- Brückensignal bei 200 kg 6,0 statt 8,6 mV; Auflösung 1,7 statt 1,2 g (HX711-Rauschen 50 nV [V]) – beide weit unter dem Bedarf (Honigzunahme/Tag in 100-g-Schritten) [A].
- Strom aus der Zelle beim Wiegen 8,7 mA aus 3,3 V (≈ 8 mA an SYS über den LDO) statt 19,3 mA an SYS → **−0,5 mAh/Tag** (`energiebilanz.py`: Waage ist der größte Posten je Zyklus).
- Kein 3,5-MHz-Schaltwandler mehr neben dem Analogteil (Lastenheft A3, Pflichtenheft Regel 6 entfallen), keine Spulenauswahl, keine Burst-Mode-Frage (waage.md [P]).
- **PB10 (WAAGE_EIN) wird frei** → kann z. B. RN4871 RST_N oder UART_RX_IND (Low-Power-Modus des Moduls) bedienen.
- Gegenargumente: Gleichtaktbereich des HX711 (AGND + 1,2 V … AVDD − 1,3 V [V]) wird mit 3,0 V eng: Brückenmitte 1,5 V liegt im Fenster 1,2–1,7 V, aber mit nur 0,3 V Reserve – **vor einer Entscheidung am Steckbrett prüfen** (HX711 + H40A an 3,3 V, Gleichtakt messen) [P]. Die Entscheidung vom 09.10.2026 für 5 V bleibt bis dahin bestehen.

### 2.3 Kniffe

1. **Pin-Tauschgruppen für den Layouter** (Pflichtenheft 2.3, neue Tabelle): G1 = zehn frei tauschbare GPIOs (PA1, PA2*, PA3, PB3, PB4, PB8, PB9, PB10, PB13, PB14, PB15), G2 = I²C1 wahlweise PB6/PB7 oder PB8/PB9 (dann wandern die HX711-Leitungen). Alles andere ist durch Alternativfunktionen fest (ST open pin data, Pin-Review vom 18.10.2026). Ein Tausch ist ein Änderungsantrag, der ohne Diskussion angenommen wird; der Generator wird nachgezogen.
2. **Sanftanlauf des BLE-Lastschalters:** 10 kΩ zwischen PB13 und Gate, 47 nF Gate–Drain (Miller-Rampe). Senkt den Einschaltstromstoß von 1,2 A auf 55 mA und den Schieneneinbruch von 0,24 V auf 0,01 V (S3). Zwei 0603-Teile, keine Nachteile; empfohlen, falls der Layouter oder der Mustertest B-2 Störungen zeigt – oder gleich.
3. **J601-Paarzuordnung** (bereits umgesetzt, HW-10): jedes Mikrofon auf einem eigenen T568B-Paar; damit kein Sonderlöten am Kabel.
4. **ROM-Bootloader über USART1** statt USB-DFU (bereits umgesetzt, HW-09): BOOT0-Taster behalten, kein zusätzlicher Pin.

### 2.4 Qualitätsthema: hochohmige ADC-Teiler (neuer Befund HW26-21)

Akku- und Solarteiler sind für den Ruhestrom hochohmig (R_th 1,1 MΩ bzw. 0,41 MΩ). Der STM32-Eingangsleckstrom erzeugt daran einen Messfehler: typisch wenige 10 nA → ca. 0,1 V (akzeptabel für die 3,3/3,5-V-Schwellen), im Datenblatt-Maximum (±1 µA [P: ST DS10314]) bis 2,2 V. Optionen: (a) Firmware-Kalibrierung gegen die bekannte Ladeschlussspannung 4,1 V und VREFINT (kostenlos, empfohlen); (b) Teiler 470 k / 470 k (+1,9 µA Ruhestrom, Fehler ÷ 4,7); (c) Teiler geschaltet speisen (kein freier GPIO – würde mit 2.2 frei). Empfehlung: (a) jetzt, (b)/(c) nur wenn die Messung am Muster (SCH-T01, Akkuspannung gegen Multimeter) über 0,1 V abweicht.

### 2.5 Geprüft und in Ordnung (keine Änderung)

HSE-Quarz 25 MHz bleibt trotz Wegfall von USB (HSI ±1 % bei 25 °C, bis ±4 % über Temperatur: zu ungenau für 115 200 Bd an BLE und Serial1; Lastenheft K2). Zwei TMP390 (Sicherheitsstufen D3). 33-Ω-Reihenwiderstände am Funkmodul (Datenblatt). 100 kΩ Pull-ups an NSS/CS (Standby hochohmig). TPS70918 für DVDD 1,8 V (Pflicht). Schmitt-Puffer 74LVC1G17 (Flankensteilheit ≤ 13 ns am Mikrofon). ESD-Arrays an allen Außenanschlüssen. Ladepads J301 mit D203 (Verpolung). RT9080 (SYS 4,4 V ist kein Ersatz für 3,3 V).

## 3. Durchführung

```sh
python3 hardware/schaltplan_spice.py --zeige   # ngspice aus KiCad 10 (Windows) oder libngspice0 (Ubuntu, CI)
bash hardware/kicad/pruefen.sh                 # unverändert grün: ERC 0, 231/231, 186 Bauteile
```

## 4. Einschränkungen

- T2-Modelle mit Annahmen (Kapsel 2,2 kΩ/0,3 mA, ADC-Eingang 35 kΩ, LDO 0,2 Ω, STM32-Leckstrom); Grenzen teils selbst gesetzt [A]. Kein Ersatz für die Mustermessungen (SCH-T01, B-1 … B-6, Waage-Gleichtakt).
- Die Vorschläge 2.1–2.3 sind **nicht umgesetzt** (Layout-Stand eingefroren); sie ändern Stückliste und Pflichtenheft und gehören in eine Entscheidung HW-11 vor dem Start des Layouters oder in Revision 0.2.

## 5. Freigabeentscheidung

- **Betroffenes Gate:** G1 – der geprüfte Stand bleibt freigegeben; die Vorschläge sind Optionen.
- **Entscheidung:** keine Fehler; Umsetzung von 2.1/2.3 (−6 Teile, Sanftanlauf, Pin-Tauschtabelle) wird empfohlen, 2.2 braucht einen Steckbretttest, 2.4 eine Firmware-Kalibrierung.
- **Verantwortlich:** Maintainer (HW-11, falls gewünscht).

# Block Anschlüsse und Schutz nach außen (Lastenheft 0.4, M4/M5/F10 – Entwurf, 09.10.2026)

Kennzeichnung:
- **[V]** im Datenblatt bzw. auf der Händlerseite gelesen
- **[A]** Annahme oder Rechnung
- **[P]** vor dem Schaltplan bzw. am Muster prüfen

Bezug:
- `versorgung.md`, `mcu-funk.md`, `waage.md`, `mikrofon.md`
- `beep-vergleich.md` 3.2 (ESD-Arrays wie bei der BEEP base v3)
- `i2c_leitung.py` (Rechnung BME280-Leitung)

## 1. Übersicht

| Nr. | Anschluss | Bauform | Pins (Reihenfolge 1 → n) | Schutz | Leitung |
|---|---|---|---|---|---|
| J1 | Solarpanel 1 | steckbare Klemme 3,5 mm, 2-polig | 1 GND, 2 +PV | Schottky je Panel, TVS SMAJ12A gemeinsam (versorgung.md 3.1) | Panelkabel |
| J2 | Solarpanel 2 | wie J1 | 1 GND, 2 +PV | wie J1 | Panelkabel |
| J3 | Akku-Platine | **JST PH 3-polig, kodiert** (Platine–Platine-Kabel im Gehäuse) | 1 BAT−, 2 NTC, 3 BAT+ | Schutz-IC auf der Akku-Platine (versorgung.md 3.4) | kurz, im Gehäuse |
| J4 | Wägezelle H40A | steckbare Klemme 3,5 mm, 5-polig | 1 Schirm, 2 E−, 3 S−, 4 S+, 5 E+ | **TPD4E05U06** an E+, S+, S− (E− ist Masse); 100 Ω in S±, 100 nF S+/S−, 10 nF je S nach Masse (waage.md 4) | Originalkabel 1,8 m |
| J5 | Mikrofon | steckbare Klemme 3,5 mm, 4-polig | 1 Schirm, 2 GND, 3 OUT, 4 VCC (3V3_ANA) | **ESDS304** an OUT und VCC; 100 Ω in OUT (mikrofon.md 2) | LiYCY 3 × 0,14, ≤ 2 m |
| J6 | DS18B20 Nr. 1 (TempIn) | steckbare Klemme 3,5 mm, 3-polig | 1 GND, 2 DQ, 3 3V3_SW | **ESDS304** (ein Array für J6 + J7) | Fühlerkabel |
| J7 | DS18B20 Nr. 2 (TempIn2) | wie J6, am selben 1-Wire-Bus | 1 GND, 2 DQ, 3 3V3_SW | wie J6 | Fühlerkabel |
| J8 | BME280 (Strahlungsschutz) | steckbare Klemme 3,5 mm, **6-polig** | 1 Schirm, 2 GND, 3 SDA, 4 SCL, 5 3V3_SW, 6 frei (nur Verwechslungsschutz) | **ESDS304** an SDA, SCL, 3V3_SW | LiYCY 4 × 0,14, **≤ 1 m** (siehe 3) |
| J9 | USB-C | Buchse 16-polig (mcu-funk.md 1.3) | – | USBLC6-2SC6 | nur am Tisch |
| J10 | Debug | Stiftleiste 2,54 mm, 1 × 6 | 1 3V3, 2 SWDIO, 3 SWCLK, 4 NRST, 5 GND, 6 TX/RX (Serial1, 2 Pins bei 1 × 7) **[P]** | – | innen |
| J11 | Erweiterung | Stiftleiste 2,54 mm, 2 × 5 | 3V3, 3V3_SW, GND, GND, SDA, SCL, TX, RX, PA15, PB12, PB13 **[P]** auf 2 × 6 erweitern | – | innen |
| – | Antenne | IPEX am Funkmodul | – | – | FPC-Antenne innen (mcu-funk.md 2.3) |

Die Klemmen-Pinbelegung folgt drei Regeln:
- **Masse bzw. Schirm immer an Pin 1**, die Versorgung immer am anderen Ende. Ein um einen Pin versetzter Stecker legt so keine Versorgung auf einen Signaleingang.
- **Jede Klemme hat eine andere Polzahl oder Kodierung**, wo Verwechslungen schaden würden. Wägezelle und BME280 hatten zuerst beide 5 Pole. **Festlegung (Philipp, 09.10.2026): J8 wird 6-polig (Pin 6 frei)**, zusätzlich Farbe als Hinweis. Damit hat jede Sensorklemme eine eigene Polzahl: Solar 2, DS18B20 3, Mikrofon 4, Wägezelle 5, BME280 6.
  - Gefährlicher Fall ausgeschlossen: Der 6-polige BME280-Stecker passt mechanisch nicht in J4. Sonst läge seine Versorgung an E+ = 4,3 V; der BME280 verträgt höchstens **4,25 V** [V: Bosch-Datenblatt, Tabelle 5].
  - Ein **kleinerer** Stecker lässt sich weiter in eine größere Buchse stecken, um eine Stelle versetzt [A]. Nachgerechnet für die Belegung oben:
    - Wägezelle in J8: Die Brücke hängt an 3V3_SW bzw. an SDA/SCL. Der I²C-Bus fällt aus; Spannungen über 3,3 V entstehen nicht.
    - Mikrofon in J4, versetzt: Das Modul bekommt bis 4,3 V (MAX4466 verträgt bis 6 V [V: ADI-Datenblatt]); seine Leitungen landen über 100 Ω an den HX711-Eingängen. Die Messung ist gestört, ein Schaden ist unwahrscheinlich [A].
    Die Farbe bleibt deshalb als Hinweis.
- Die Belegung steht im **Bestückungsdruck an jeder Klemme**: Klemmenname und Pin-Bezeichnungen.

## 2. Bauteile

| Teil | Wahl | Quelle | Status |
|---|---|---|---|
| Klemme Platine | **DEGSON 15EDGRHC-3.5**, steckbar, gewinkelt, Durchsteckmontage, 3,5 mm, 8 A / 150 V, −30 … +120 °C; 4-polig = JLCPCB C7603445 (Extended) | JLCPCB-Teileseite | [V]; 2-, 3-, 5- und 6-polig **[P]** Teilenummern |
| Gegenstecker | DEGSON 15EDGK-3.5 (Schraubstecker) passend zur Polzahl | – | [A] Bezeichnung prüfen; Stecker werden lose mitbestellt |
| ESD 3,6 V | **TI ESDS304DBVR**, 4 Kanäle, SOT-23-5. VRWM 3,6 V, ±30 kV, **Leckstrom 3 nA typ., 50 nA max.** bei 3,6 V und 25 °C, 2,3 pF | TI-Datenblatt | [V]; LCSC-Nummer **[P]** |
| ESD 5,5 V (Wägezelle) | **TI TPD4E05U06DQAR**, 4 Kanäle, USON-10. VRWM 5,5 V, **Leckstrom 0,01 nA typ., 10 nA max.** (bei 2,5 V), 0,5 pF, ±12 kV Kontakt | TI-Datenblatt; LCSC/JLCPCB **C138714** (Extended) | [V] |
| Akku-Stecker | JST PH 3-polig, gewinkelt (S3B-PH-K-S) bzw. stehend (B3B-PH-K-S) | – | **[P]** LCSC-Nummern (2-polig gewinkelt ist C265016) |

Warum zwei ESD-Typen:
- An der Wägezelle liegt E+ bei 4,3 V. Das ist über der Arbeitsspannung des ESDS304 (3,6 V). Der TPD4E05U06 hält 5,5 V.
- Er hat zudem 5-mal weniger Leckstrom: 10 nA × 100 Ω = 1 µV, das sind etwa 0,02 kg im ungünstigsten Fall [A]. Mit dem ESDS304 (50 nA) wären es etwa 0,1 kg.

## 3. Lange Leitungen: Rechnung und Grenzen

| Leitung | Problem | Festlegung |
|---|---|---|
| BME280 über I²C | Höchstens 400 pF Buskapazität (I²C-Spezifikation; BME280-Datenblatt „Cb max 400 pF“) [V]. Leitung **höchstens 1 m** (Festlegung Philipp 09.10.2026). | Siehe 3.1: Pull-ups **1,8 kΩ** an der geschalteten Schiene, Takt **50 kHz**. |
| DS18B20 (1-Wire) | 1-Wire verträgt mit 4,7 kΩ einige Meter bis zehn Meter Sternleitung [A, Maxim-Anwendungshinweise nicht gelesen] | 4,7 kΩ an der geschalteten Schiene, 3-adrig (nicht parasitär) |
| Mikrofon | Kabelkapazität am MAX4466 | 1 kΩ Trennwiderstand am Modul (mikrofon.md 2.1) |
| Wägezelle | Leckströme und Störungen | kleine Leckströme, Filter, Schirm nur an der Platine (waage.md 4) |
| Panels | Überspannung, Verpolung | Schottky je Panel, TVS (versorgung.md 3.1) |

### 3.1 Rechnung BME280-Leitung (`i2c_leitung.py`)

Eingaben:
- Kabel LiYCY 4 × 0,14: Lapp nennt ca. 120 pF/m Ader/Ader und 160 pF/m Ader/Schirm [V]. Die Ader SDA sieht gegen alle anderen Adern und den Schirm **0,25–0,40 nF/m** [A].
- Platine, Stecker, ESD-Array, STM32, EEPROM und BME280-Modul: zusammen ca. **40 pF** [A].
- BME280: Low-Pegel ≤ 20 % VDDIO bei **3 mA** [V: Bosch-Datenblatt, Tabelle der elektrischen Daten].
- Standard-Mode: Anstiegszeit (30 → 70 %) höchstens **1000 ns** [V: I²C-Spezifikation].

Ergebnis bei 1 m: Buskapazität **290–440 pF**.

| Pull-up | Strom Low | Anstiegszeit (290 / 440 pF) | Bewertung |
|---|---|---|---|
| 1,5 kΩ | 1,9 mA | 369 / 559 ns | ok, 44 % Reserve |
| **1,8 kΩ (gewählt)** | 1,6 mA | 442 / 671 ns | **ok, 33 % Reserve** |
| 2,2 kΩ | 1,3 mA | 541 / 820 ns | ok, 18 % Reserve |
| 3,3 kΩ | 0,9 mA | 811 / 1230 ns | zu langsam im ungünstigen Fall |
| 4,7 kΩ (BEEP) | 0,6 mA | 1155 / 1752 ns | zu langsam |

Bewertung:
- **1,8 kΩ** ist der schwächste Wert mit deutlicher Reserve. Der Strom bleibt weit unter 3 mA. Energie zählt nicht: Die Schiene ist nur während der Messung an.
- Mit 50 kHz statt 100 kHz ist auch die Low-/High-Zeit doppelt so lang. Das gibt zusätzliche Reserve gegen Übersprechen zwischen SDA und SCL im selben Kabel [A].
- **Ehrlich:** Im ungünstigen Fall (440 pF) liegen wir **leicht über der 400-pF-Grenze** des Datenblatts. Die Anstiegszeit hält trotzdem. **[P]** Am Muster die Anstiegszeit mit dem Oszilloskop am BME280-Ende messen. Wird es knapp, die Leitung kürzen oder ein Kabel mit kleinerer Kapazität nehmen.
- Firmware der neuen Platine: I²C-Takt auf 50 kHz setzen (z. B. `Wire.setClock(50000)`).

Der EEPROM sitzt am selben I²C-Bus. Er läuft mit den stärkeren Pull-ups und dem langsameren Takt problemlos [A].

## 4. Anordnung auf der Platine (Lastenheft M5)

- **Alle Außenklemmen an eine Platinenkante**, zu den späteren Kabeldurchführungen hin. Bei einem an der Wand hängenden Gehäuse ist das die Unterseite [A].
- Reihenfolge an der Kante, von links: J1/J2 Solar – J8 BME280 – J6/J7 DS18B20 – J5 Mikrofon – J4 Wägezelle.
  - Die Wägezelle sitzt am Rand neben dem HX711.
  - Das Mikrofon sitzt neben dem Filter vor PA1.
  - Beide liegen weit weg vom 5-V-Wandler und vom Funkmodul (A3).
- **Der ESD-Schutz sitzt direkt hinter der Klemme**, vor allen anderen Bauteilen. Der Masseanschluss geht auf kürzestem Weg mit mehreren Durchkontaktierungen auf die Massefläche (L2).
- Das Funkmodul mit der IPEX-Buchse sitzt an der **gegenüberliegenden** Kante, die Antenne an der Wand daneben.
- Der Akkustecker J3 und USB J9 sitzen innen, gut erreichbar beim Öffnen.
- **Lichtleiter-LED und Reedkontakt** sitzen an einer Seitenkante (mcu-funk.md 3.3).

## 5. Fertigung

- **Festlegung (Philipp, 09.10.2026): JLCPCB lötet alles ein**, auch die Durchsteckteile (Klemmen, Stiftleisten, JST-Buchse, Befestigungsstifte der USB-Buchse).
  - Durchsteckstellen auf der Platine: ca. 25 Klemmenpins, 3 JST, 16–18 Stiftleiste, 4 USB-Befestigung, also **rund 50** [A, nach Tabelle 1].
  - Preis laut einer Übersicht von 04/2024: ca. 0,0135 $ je Durchsteckpin plus Grundgebühr je Auftrag [A, nicht von JLCPCB bestätigt]. Das wären unter 1 $ je Platine. **[P]** Im Angebot prüfen.
  - **[P]** Ob „Economic PCBA“ Durchsteckteile erlaubt oder „Standard PCBA“ nötig ist, habe ich nicht sicher gefunden. Das Funkmodul Ra-01SH könnte ohnehin „Standard only“ sein. Beides im Bestellformular prüfen.
  - Die **Gegenstecker** (DEGSON 15EDGK) werden nicht gelötet. Sie werden bei LCSC mitbestellt.
- Laut M2 dürfen unten keine Bauteile sitzen. Die Lötstellen der Durchsteckteile liegen unten; in den zwei Feldern mit wenig Freiraum kurz abschneiden. Die Klemmen liegen am Rand, außerhalb dieser Felder **[P]** mit dem STEP-Modell prüfen.
- Schutzlack nach dem Test; Klemmen, Stiftleisten, USB, IPEX und Lichtleiter-LED abdecken (M8).

## 6. Offene Prüfpunkte

1. LCSC-Nummern: ESDS304DBVR, DEGSON 15EDGRHC-3.5 in 2-, 3-, 5- und 6-polig, Gegenstecker, JST PH 3-polig
2. ~~Kodierung J4/J8~~: J8 6-polig plus Farbe (09.10.2026); Farbvariante bei LCSC suchen
3. ~~Länge der BME280-Leitung~~: höchstens 1 m (09.10.2026); Anstiegszeit am Muster messen
4. Debug- und Erweiterungsleiste endgültig festlegen (Pinzahl)
5. ~~THT-Bestückung~~: JLCPCB (09.10.2026); Economic oder Standard PCBA im Bestellformular klären

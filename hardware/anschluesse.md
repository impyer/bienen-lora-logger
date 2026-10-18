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
| J1 (Platine: J201) | Solarpanel 1 | steckbare Klemme 3,5 mm, 2-polig | 1 GND, 2 +PV | Schottky je Panel, TVS SMAJ12A gemeinsam (versorgung.md 3.1) | Panelkabel |
| J2 (Platine: J202) | Solarpanel 2 | wie J1 | 1 GND, 2 +PV | wie J1 | Panelkabel |
| ~~J3 (Platine: J203)~~ | ~~Akku-Platine~~ | **entfällt (HW-06, 14.10.2026):** Zelle, Zellschutz und Ladesperre liegen auf der Hauptplatine (Blatt „Akku“, BT801) | – | – | Halter Keystone 1042 innen auf der Hauptplatine |
| J4 (Platine: J501) | Wägezelle H40A | steckbare Klemme 3,5 mm, 5-polig | 1 Schirm, 2 E−, 3 S−, 4 S+, 5 E+ | **TPD4E05U06** an E+, S+, S− (E− ist Masse); Ferrit ≤ 0,1 Ω in E+; 100 Ω in S±, 100 nF S+/S−, 10 nF je S nach Masse (waage.md 4) | Originalkabel 1,8 m |
| J5 (Platine: J601) | Mikrofone (Elektret + MEMS, HW-07) | **RJ45 geschirmt, ohne Übertrager** (Teil wählt der Layouter) | 1 GND, 2 CLK (PDM-Takt), 3 DATA (PDM), 4 VDD (3V3_MEMS), 5 GND, 6 GND, 7 MIC+, 8 MIC−, SH Schirm | **ESDS304** an CLK, DATA, MIC+, MIC−; Takttreiber + 33 Ω, 22 Ω in DATA (mikrofon.md 2) | Cat7 S/FTP mit geschirmtem RJ45-Stecker, fest verlegt, 0,5–1 m (länger nur mit Treiber im Mikrofonkopf); Paare nach T568B: 1/2 CLK, 3/6 DATA, 4/5 VDD, 7/8 MIC |
| J6 (Platine: J701) | DS18B20 Nr. 1 (TempIn) | steckbare Klemme 3,5 mm, 3-polig | 1 GND, 2 DQ, 3 3V3_SW | **ESDS304** (ein Array für J6 + J7) | Fühlerkabel |
| J7 (Platine: J702) | DS18B20 Nr. 2 (TempIn2) | wie J6, am selben 1-Wire-Bus | 1 GND, 2 DQ, 3 3V3_SW | wie J6 | Fühlerkabel |
| J8 (Platine: J703) | BME280 (Strahlungsschutz) | steckbare Klemme 3,5 mm, **6-polig** | 1 Schirm, 2 GND, 3 SDA, 4 SCL, 5 3V3_SW, 6 frei (nur Verwechslungsschutz) | **ESDS304** an SDA, SCL, 3V3_SW | **Outdoor-Netzwerkkabel** (Cat 5e/6, PE-Mantel), Paare SDA+GND, SCL+GND, 3V3+GND, Schirm falls vorhanden an Pin 1; **≤ 1 m** (siehe 3.1, HW26-09) |
| J9 (Platine: J301) | Laden 5 V | **zwei Lötpads** 2,54 mm (Stiftleiste nicht bestückt), mcu-funk.md 1.3 | 1 GND, 2 +5V | Schottky D203 (sperrt Verpolung), TVS D204 (versorgung.md 3.1) | am Tisch: Laden aus einem 5-V-Netzteil (HW-09, 18.10.2026; USB-C-Buchse entfällt; Aufspielen über SWD/Serial1, Kommunikation über BLE, mcu-funk.md 1.6) |
| J10 (Platine: J302) | Debug | Stiftleiste 2,54 mm, **1 × 7** (HW26-13) | 1 3V3, 2 SWDIO, 3 SWCLK, 4 NRST, 5 GND, 6 TX1, 7 RX1 (Serial1) | – | innen; Pinfolge siehe 1.2 (SCH26-09) |
| J11 (Platine: J704) | Erweiterung | Stiftleiste 2,54 mm, **2 × 6** (HW26-13) | 1 3V3, 2 3V3_SW, 3 GND, 4 GND, 5 SDA, 6 SCL, 7 TX1, 8 RX1, 9 BLE_RXD, 10 BLE_TXD, 11 BLE_MODE, 12 GND | – | innen; I²C-Geräte hier zählen zur Buskapazität (3.1); Pins 9–11 seit **HW-09** (18.10.2026): UART-Eingang und -Ausgang des BLE-Moduls (hinter 1 kΩ zum STM32) und P2_0 (Modus) für das Firmware-Update des Moduls (Brücke 11–12 = Testmodus, mcu-funk.md 1.6); keine freien GPIOs mehr (PB13 Lastschalter BLE, PA15/PB12 I²S seit HW-07) |
| – | Antenne | IPEX am Funkmodul | – | – | FPC-Antenne innen (mcu-funk.md 2.3) |
| – | BLE-Antenne | Chip-Antenne auf dem Modul U303 (RN4871, HW-09) | – | – | keine Buchse; Modul an der Platinenkante, Antenne nach außen, Metall ≥ 30 mm (mcu-funk.md 1.6) |

Die Nummern J1–J11 sind die Anschlussnummern dieses Dokuments; in Klammern steht die Referenz im KiCad-Schaltplan. Steht ein Stecker schon auf einem Schaltplanblatt, vergleicht `hardware/kicad/werkzeug/netz_tests.py` die Spalte „Pins“ mit der KiCad-Netzliste (SCH26-09). Eine Änderung der Pinfolge gehört deshalb immer in diese Tabelle **und** in den Generator.

### 1.1 ~~Kabelplan Akku-Platine ↔ Hauptplatine (SCH26-06)~~

Entfällt mit HW-06 (14.10.2026): Die Zelle sitzt im Halter Keystone 1042 auf der Hauptplatine, Zellschutz und Ladesperre direkt daneben (Blatt „Akku“). Es gibt kein Akkukabel mehr; der frühere Kabelplan J203 ↔ J1 steht in der Git-Historie. Erstinbetriebnahme weiter mit **strombegrenztem Netzteil** (z. B. 4,0 V, 50 mA) statt Zelle an B+/B− des Halters (sicherheit-akku.md).

Die Klemmen-Pinbelegung folgt drei Regeln:
- **Masse bzw. Schirm immer an Pin 1**, die Versorgung immer am anderen Ende. Ein um einen Pin versetzter Stecker legt so keine Versorgung auf einen Signaleingang.
- **Jede Klemme hat eine andere Polzahl oder Kodierung**, wo Verwechslungen schaden würden. Wägezelle und BME280 hatten zuerst beide 5 Pole. **Festlegung (Philipp, 09.10.2026): J8 wird 6-polig (Pin 6 frei)**, zusätzlich Farbe als Hinweis. Damit hat jede Sensorklemme eine eigene Polzahl: Solar 2, DS18B20 3, Wägezelle 5, BME280 6. Die Mikrofone haben seit HW-07 eine **RJ45-Buchse** (andere Bauform, vorher Klemme 4-polig).
  - Gefährlicher Fall ausgeschlossen: Der 6-polige BME280-Stecker passt mechanisch nicht in J4. Sonst läge seine Versorgung an E+ = 4,3 V; der BME280 verträgt höchstens **4,25 V** [V: Bosch-Datenblatt, Tabelle 5].
  - Ein **kleinerer** Stecker lässt sich weiter in eine größere Buchse stecken, um eine Stelle versetzt [A]. Nachgerechnet für die Belegung oben:
    - Wägezelle in J8: Die Brücke hängt an 3V3_SW bzw. an SDA/SCL. Der I²C-Bus fällt aus; Spannungen über 3,3 V entstehen nicht.
    - Die RJ45-Buchse J5 nimmt keinen Klemmenstecker auf und umgekehrt. **Gefahr:** ein Netzwerkkabel von einem PoE-Gerät (bis ca. 57 V auf den Paaren 4/5 und 7/8 [A]) würde 3V3_MEMS und den Elektreteingang zerstören. Darum Beschriftung „Mikrofon – kein Netzwerk“ an Buchse und Kabel; das Kabel ist fest mit dem Mikrofonkopf verbunden.
    Die Farbe bleibt deshalb als Hinweis.
- Die Belegung steht im **Bestückungsdruck an jeder Klemme**: Klemmenname und Pin-Bezeichnungen.

### 1.2 Debug-Leiste J10 / J302 (SCH26-09)

| Pin | Signal | MCU | Gegenstelle |
|---|---|---|---|
| 1 | 3V3 | – | SWD-Adapter VTref (nur Referenz, **nicht** aus dem Adapter speisen) |
| 2 | SWDIO | PA13 | SWD-Adapter SWDIO |
| 3 | SWCLK | PA14 | SWD-Adapter SWCLK |
| 4 | NRST | NRST | SWD-Adapter NRST/RST |
| 5 | GND | – | SWD-Adapter GND **und** USB-Seriell-Adapter GND |
| 6 | TX1 | PA9 (Ausgang) | RX des USB-Seriell-Adapters |
| 7 | RX1 | PA10 (Eingang) | TX des USB-Seriell-Adapters |

- Begründung der Reihenfolge [A]: Mit GND an Pin 5 liegen SWD (Pin 1–5) und Serial1 (Pin 5–7) jeweils am Stück. Ein dreipoliger Seriell-Stecker (GND, RX, TX) passt direkt auf Pin 5–7.
- Ein Kabel nach dieser Tabelle zuerst **stromlos mit dem Durchgangsprüfer** gegen den Bestückungsdruck prüfen. Pin 1 ist im Bestückungsdruck markiert.
- Seriell-Adapter nur mit **3,3-V-Pegel** verwenden.

## 2. Bauteile

| Teil | Wahl | Quelle | Status |
|---|---|---|---|
| Klemme Platine | **DEGSON 15EDGRC-3.5-0nP-14-00A(H)**, steckbar, **einreihig**, geschlossen, gewinkelt, Durchsteckmontage, Raster 3,5 mm (Entscheidung Philipp 13.10.2026, SCH26-13). JLCPCB/LCSC (Extended), Bestand am 13.10.2026: **2-polig C5160225** (4604), **3-polig C5160226** (3961), **4-polig C7603438** (8720), **5-polig C7603439** (1234), **6-polig C49352918** (1003). Vorher gewählt 15EDGRHC: zweireihig, passte nicht | JLCPCB-Teilesuche 13.10.2026 [V]; Footprint `Bienen:DEGSON_15EDGRC-3.5-0nP` nach EasyEDA/LCSC-Geometrie (Bohrung 1,4 mm) [A] | Zeichnung des Herstellers prüfen [P]; Bohrung laut LCSC je Polzahl 1,3–1,4 mm |
| Gegenstecker | **DEGSON 15EDGK-3.5-0nP-14-00A(H)** (Schraubstecker) passend zur Polzahl: 2-polig C5632692 (3771), 3-polig C7603431 (**0**), 4-polig C7603432 (890), 5-polig C7603433 (800), 6-polig bei JLCPCB nicht gefunden | JLCPCB-Teilesuche 13.10.2026 [V] | Stecker werden lose bestellt (nicht bestückt); 3- und 6-polig bei LCSC/Mouser beschaffen [P] |
| ESD 3,6 V | **TI ESDS304DBVR**, 4 Kanäle, SOT-23-5. VRWM 3,6 V, ±30 kV, **Leckstrom 3 nA typ., 50 nA max.** bei 3,6 V und 25 °C, 2,3 pF | TI-Datenblatt | [V]; LCSC-Nummer **[P]** |
| ESD 5,5 V (Wägezelle) | **TI TPD4E05U06DQAR**, 4 Kanäle, USON-10. VRWM 5,5 V, **Leckstrom 0,01 nA typ., 10 nA max.** (bei 2,5 V), 0,5 pF, ±12 kV Kontakt | TI-Datenblatt; LCSC/JLCPCB **C138714** (Extended) | [V] |
| ~~Akku-Stecker~~ | entfällt (HW-06) | – | – |

Warum zwei ESD-Typen:
- An der Wägezelle liegt E+ bei 4,3 V. Das ist über der Arbeitsspannung des ESDS304 (3,6 V). Der TPD4E05U06 hält 5,5 V.
- Er hat zudem 5-mal weniger Leckstrom: 10 nA × 100 Ω = 1 µV, das sind etwa 0,02 kg im ungünstigsten Fall [A]. Mit dem ESDS304 (50 nA) wären es etwa 0,1 kg.

## 3. Lange Leitungen: Rechnung und Grenzen

| Leitung | Problem | Festlegung |
|---|---|---|
| BME280 über I²C | Höchstens 400 pF Buskapazität (I²C-Spezifikation; BME280-Datenblatt „Cb max 400 pF“) [V]. Leitung **höchstens 1 m** (Festlegung Philipp 09.10.2026). | Siehe 3.1: Outdoor-Netzwerkkabel, Ziel **≤ 340 pF**, Pull-ups **1,8 kΩ**, Takt **50 kHz**. |
| DS18B20 (1-Wire) | 1-Wire verträgt mit 4,7 kΩ einige Meter bis zehn Meter Sternleitung [A, Maxim-Anwendungshinweise nicht gelesen] | 4,7 kΩ an der geschalteten Schiene, 3-adrig (nicht parasitär) |
| Mikrofone (HW-07) | PDM-Takt/-Daten über das Kabel: DATA ≤ 200 pF, Taktflanke ≤ 13 ns [V Infineon] | Cat7 S/FTP, 0,5–1 m; Takt über Schmitt-Puffer + 33 Ω; länger nur mit Treiber im Mikrofonkopf (mikrofon.md 5) |
| Wägezelle | Leckströme und Störungen | kleine Leckströme, Filter, Schirm nur an der Platine (waage.md 4) |
| Panels | Überspannung, Verpolung | Schottky je Panel, TVS (versorgung.md 3.1) |

### 3.1 Rechnung BME280-Leitung (`i2c_leitung.py`, geändert 09.10.2026 nach HW26-09)

Eingaben:
- Grenze **400 pF** [V: I²C-Spezifikation, BME280-Datenblatt]. **Ziel 340 pF** (15 % Reserve) [A].
- Kabel, SDA gegen alle anderen Adern:
  - LiYCY 4 × 0,14 geschirmt: Lapp nennt ca. 120 pF/m Ader/Ader und 160 pF/m Ader/Schirm [V]; zusammen **250–400 pF/m** [A].
  - **Outdoor-Netzwerkkabel** mit verdrillten Paaren (Entscheidung Philipp 09.10.2026): je Paar ca. 50 pF/m [A, übliche Normgrenze 5,6 nF/100 m], mit Kopplung zu den anderen Paaren **70–100 pF/m** [A].
- Platine, Stecker, ESD-Array, STM32, BME280-Modul: ca. **35 pF** [A]. Der EEPROM entfällt (HW26-10).
- BME280: Low-Pegel ≤ 20 % VDDIO bei **3 mA** [V: Bosch-Datenblatt].
- Standard-Mode: Anstiegszeit (30 → 70 %) höchstens **1000 ns** [V: I²C-Spezifikation].

Ergebnis bei 1 m:

| Kabel | Buskapazität | Ziel 340 pF | Anstiegszeit mit 1,8 kΩ |
|---|---|---|---|
| LiYCY geschirmt | 285–435 pF | **nicht eingehalten** | 435–663 ns |
| **Netzwerkkabel (gewählt)** | **105–135 pF** | **eingehalten** | 160–206 ns (79 % Reserve) |

Bewertung:
- Mit dem Netzwerkkabel liegt der Bus weit unter der Grenze (Review HW26-09 damit erledigt, sofern das echte Kabel die Annahme trifft).
- **1,8 kΩ** bleiben: Sie halten auch mit LiYCY die Anstiegszeit ein, falls jemand das falsche Kabel nimmt. Der Strom bleibt weit unter 3 mA; die Schiene ist nur während der Messung an.
- 50 kHz geben zusätzliche Reserve gegen Übersprechen [A].
- Ein Gerät am Erweiterungsstecker J11 zählt mit. Summe aus Kabel, Gerät und 35 pF muss unter 340 pF bleiben.
- **[P]** Kapazität des gekauften Kabels messen (Ader gegen alle anderen, 1 m; Multimeter mit nF-Bereich reicht) und Anstiegszeit am BME280-Ende mit dem Oszilloskop prüfen; ACK und Wiederholungen bei Kälte und Nässe protokollieren.
- Firmware der neuen Platine: I²C-Takt 50 kHz (z. B. `Wire.setClock(50000)`).
- Das Skript endet mit Fehlercode, wenn das gewählte Kabel das Ziel verfehlt; die CI führt es aus.

## 4. Anordnung auf der Platine (Lastenheft M5)

**Die Lage legt der beauftragte Layouter fest** (Philipp 14.10.2026); hier stehen die Randbedingungen und ein Vorschlag.

- Außenanschlüsse möglichst an **einer** Kante zu den späteren Kabeldurchführungen hin (bei einem an der Wand hängenden Gehäuse die Unterseite [A]); zwei Kanten sind zulässig. Breite zum Vergleich: zwischen den Sperrflächen der unteren Befestigungslöcher sind ca. 102 mm frei; die Klemmen J1/J2, J8, J6/J7, J4 brauchen zusammen ca. 86 mm, dazu die RJ45-Buchse J5 (ca. 16 mm) [A].
- Vorschlag Reihenfolge: J1/J2 Solar – J8 BME280 – J6/J7 DS18B20 – J5 Mikrofone (neben dem Audio-ADC) – J4 Wägezelle (neben dem HX711); Mikrofon- und Waagenzweig weit weg vom 5-V-Wandler und vom Funkmodul (A3).
- **Der ESD-Schutz sitzt direkt hinter jedem Anschluss**, vor allen anderen Bauteilen. Der Masseanschluss geht auf kürzestem Weg mit mehreren Durchkontaktierungen auf die Massefläche (L2).
- Das Funkmodul mit der IPEX-Buchse sitzt an der Kante gegenüber, die Antenne an der Wand daneben.
- Ladepads J9, Debug J10, Erweiterung J11, BOOT und Reset innen, gut erreichbar beim Öffnen. Akkuhalter auf der Hauptplatine (HW-06), Zellwechsel nach dem Öffnen; TMP390/NTC unter der Zelle.
- **Lichtleiter-LED und Reedkontakt** an einer Seitenkante (mcu-funk.md 3.3; Bohrungsmitte des Lichtleiters ca. 22,7 mm über dem Gehäuseboden).
- **[P]** Mit gesteckten 15EDGK-Steckern am Muster prüfen, ob die Klemmen nebeneinander passen und sich lösen lassen.

## 5. Fertigung

- **Festlegung (Philipp, 09.10.2026): JLCPCB lötet alles ein**, auch die Durchsteckteile (Klemmen, Stiftleisten).
  - Durchsteckstellen auf der Platine: ca. 25 Klemmenpins, 19 Stiftleiste (1 × 7 + 2 × 6), also **rund 45** [A, nach Tabelle 1]; JST (seit HW-06) und USB-Buchse (seit HW-09) entfallen, die Ladepads J9 werden nicht bestückt.
  - Preis laut einer Übersicht von 04/2024: ca. 0,0135 $ je Durchsteckpin plus Grundgebühr je Auftrag [A, nicht von JLCPCB bestätigt]. Das wären unter 1 $ je Platine. **[P]** Im Angebot prüfen.
  - **[P]** Ob „Economic PCBA“ Durchsteckteile erlaubt oder „Standard PCBA“ nötig ist, habe ich nicht sicher gefunden. Das Funkmodul Ra-01SH könnte ohnehin „Standard only“ sein. Beides im Bestellformular prüfen.
  - Die **Gegenstecker** (DEGSON 15EDGK) werden nicht gelötet. Sie werden bei LCSC mitbestellt.
- Laut M2 dürfen unten keine Bauteile sitzen. Die Lötstellen der Durchsteckteile liegen unten; in den zwei Feldern mit wenig Freiraum kurz abschneiden. Die Klemmen liegen am Rand, außerhalb dieser Felder **[P]** mit dem STEP-Modell prüfen.
- Schutzlack nach dem Test; Klemmen, Stiftleisten, Ladepads, IPEX, BLE-Modul und Lichtleiter-LED abdecken (M8).

## 6. Offene Prüfpunkte

1. LCSC-Nummern: ESDS304DBVR, ~~Klemmen~~ (13.10.2026, Abschnitt 2), Gegenstecker 3- und 6-polig, JST PH 5-polig, TMP390A2DRL, AO3400A, TPS70933DBVR
2. ~~Kodierung J4/J8~~: J8 6-polig plus Farbe (09.10.2026); Farbvariante bei LCSC suchen
3. ~~Länge der BME280-Leitung~~: höchstens 1 m (09.10.2026); Anstiegszeit am Muster messen
4. ~~Debug- und Erweiterungsleiste~~: J10 1 × 7, J11 2 × 6 (09.10.2026, HW26-13)
5. ~~THT-Bestückung~~: JLCPCB (09.10.2026); Economic oder Standard PCBA im Bestellformular klären

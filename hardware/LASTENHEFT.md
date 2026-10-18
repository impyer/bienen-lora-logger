# Lastenheft: eigene Logger-Platine (Entwurf 0.4, 08.10.2026)

Ziel ist eine offene SMD-Platine, die JLCPCB weitgehend fertig bestückt.
Funkmodul ist das **Ai-Thinker Ra-01SH (SX1262)**. Die Firmware wird **neu aufgesetzt**; Kompatibilität zur
beelogger-Firmware und zur beelogger-Pinbelegung ist **nicht** gefordert.

Kennzeichnung: **[M]** Muss, **[S]** Soll, **[K]** Kann, **[P]** offener Prüfpunkt.

Änderungen gegen 0.3:
- Abschnitt 3 Versorgung neu ausgearbeitet: [`versorgung.md`](versorgung.md) mit Energiebilanz [`energiebilanz.py`](energiebilanz.py)
- Laderegler BQ25185 statt CN3065; Tiefentladeschutz zweistufig in Hardware; Zelle, Schutz und NTC auf der Hauptplatine (HW-06, 14.10.2026; vorher eigene Akku-Platine)
- RT9080 als 3,3-V-Regler; Regeln gegen Rückspeisung; Erfahrungen aus dem beelogger
- Vergleich mit BEEP base v3: [`beep-vergleich.md`](beep-vergleich.md) (Übernahmen: TPS22917, Reedkontakt, ESD-Arrays, 4 Lagen zur Entscheidung)
- Block Mikrofon: [`mikrofon.md`](mikrofon.md); seit **HW-07 (14.10.2026)** zwei Mikrofone verschiedener Bauart (Elektret analog + MEMS IM69D127 digital) am Audio-ADC TLV320ADC3101 statt GY-MAX4466 mit Analogfilter
- Block Waage: [`waage.md`](waage.md) (5 V über TPS61240, H40A 404 Ω, Auflösung, Energie)
- Block Mikrocontroller und Funk: [`mcu-funk.md`](mcu-funk.md) (Beschaltung, Quarz 7 pF, Ladepads, Antenne an IPEX, LLCC68-Hinweis, Pinbelegung)
- **HW-09 (18.10.2026):** Bluetooth-Low-Energy-Modul **RN4871** an USART6 (PA11/PA12) als Service-Schnittstelle ohne Öffnen; USB-C-Buchse entfällt, Laden am Tisch über zwei Pads (K5, K6, F9; [`mcu-funk.md`](mcu-funk.md) 1.3 und 1.6)

Änderungen gegen 0.2:
- Ra-01SH festgelegt.
- Neue Firmware ohne beelogger-Kompatibilität, Pinbelegung neu.
- Gehäusemaße aus der Herstellerzeichnung übernommen.
- Kabeldurchführungen zurückgestellt.

## 1. Grundlagen

| Nr. | Anforderung |
|---|---|
| K1 [M] | Mikrocontroller **STM32F411CEU6** (UFQFPN-48, LCSC C60420). |
| K2 [S] | **25-MHz-Quarz (HSE)** wie bei der BlackPill. So bleibt die fertige Arduino-Variante „BlackPill F411CE“ nutzbar, und eine gekaufte BlackPill mit Ra-01SH-Adapter dient als Entwicklungsplattform, bevor die Platine da ist. |
| K3 [M] | **32,768-kHz-Quarz (LSE)** an PC14/PC15 für die RTC. |
| K4 [M] | ~~EEPROM AT24C256~~ entfällt (09.10.2026, HW26-10): LoRaWAN-Sitzung und Messwerte im dauernd versorgten SPI-Flash (F11), Sitzung mit Generationszähler und CRC. `mcu-funk.md` 3.1. |
| K5 [S] | **Kein USB** (HW-09, Philipp 18.10.2026; ersetzt HW-05 „USB-C: Laden, Aufspielen und Kommunikation“): PA11/PA12 sind USART6 für K6. **Laden am Tisch über zwei Lötpads J9/J301** (1 GND, 2 +5 V → Schottky D203 → Ladereingang; Verpolung sperrt die Diode). Aufspielen über SWD oder den ROM-Bootloader an USART1 (J10, BOOT0-Taster); Kommunikation über BLE (K6) oder Serial1. `mcu-funk.md` 1.3. |
| K6 [S] | **Bluetooth Low Energy** (HW-09, 18.10.2026): Modul **Microchip RN4871-I/RM130** (Chip-Antenne, −40 … +85 °C, LCSC C633942) an **USART6** (PA11 TX, PA12 RX) als Transparent-UART-Konsole; Versorgung über Lastschalter an **PB13** (im Standby aus, Ruhestrom ≈ 0); nur auf Anforderung (Magnet, F7) für begrenzte Zeit ein; Modul-UART und Modus auch an J11 Pin 9–11 (Firmware-Update des Moduls). Modul an der Platinenkante, Antenne nach außen, **Metall ≥ 30 mm** (Zelle!). Rückfall bei Lieferproblemen: Ai-Thinker PB-03F (anderer Footprint). `mcu-funk.md` 1.6. |

### Pinbelegung

Stand 0.4 mit Beschaltung, Quarzen, Ladepads, BLE und Debug: **[`mcu-funk.md`](mcu-funk.md), Abschnitt 4.** Änderungen gegen 0.3:
- Ra-01SH TXEN/RXEN über Lötbrücken an PB14/PB15
- Erweiterung: keine freien GPIOs mehr am Erweiterungsstecker (PB13 seit HW-09 Lastschalter des BLE-Moduls, vorher VBUS-Erkennung; PA15/PB12 seit HW-07 I²S zum Audio-ADC, dazu PB5 als I²S-Daten und die Sensorschiene von PB5 auf PA1; PB10 schaltet den 5-V-Wandler der Waage, PB3 ist CS des SPI-Flashs; nur noch ein HX711); J11 Pin 9–11 seit HW-09 Modul-UART und Modus des BLE-Moduls
- PA15 nicht mehr für den Regensensor
- (EEPROM entfällt, Sitzung im SPI-Flash)

## 2. Funktionen

| Nr. | Anforderung |
|---|---|
| F1 [M] | **Funk: Ai-Thinker Ra-01SH** (LCSC C2764087). Werte laut Datenblatt V1.1 vom 18.08.2020: 17 × 16 × 3,2 mm, 16 Stempellöcher im Raster 2 mm, −40 bis +85 °C. Einzelheiten in 2.1. |
| F2 [M] | **Antenne** (Entscheidung 08.10.2026): FPC-Antenne 868 MHz an der **IPEX-Buchse des Moduls**, innen an eine Seitenwand geklebt. Pin ANT ohne Leiterbahn. Einzelheiten `mcu-funk.md` 2.3. |
| F3 [M] | **Waage** (Entscheidungen 08./09.10.2026): **1 × HX711** mit **VSUP 5 V aus festem Aufwärtswandler TPS61240** (Lasttrennung, nur beim Wiegen an), AVDD 4,3 V, **eine** Bosche H40A 200 kg. Anschluss 5-polig steckbar (E±, S±, Schirm). Einzelheiten [`waage.md`](waage.md). |
| F4 [M] | **Temperatur**: 1-Wire für mindestens 2 × DS18B20, zwei 3-polige Klemmen J6/J7 am gleichen Bus (GND, DQ, 3V3_SW), 4,7 kΩ an der geschalteten Schiene, ESDS304. [`anschluesse.md`](anschluesse.md). |
| F5 [M] | **I²C außen**: BME280 im Strahlungsschutz an J8 (6-polig mit Schirm, Pin 6 frei), ESDS304; wegen der Kabelkapazität Pull-ups **1,8 kΩ** und Takt **50 kHz**, Leitung **≤ 1 m** (Festlegung 09.10.2026), **Outdoor-Netzwerkkabel mit verdrillten Paaren** (SDA/GND, SCL/GND, 3V3/GND); Buskapazität gesamt **≤ 340 pF** (400 pF minus 15 % Reserve, HW26-09). [`anschluesse.md`](anschluesse.md) 3.1. |
| F6 [M] | **Zwei Mikrofone verschiedener Bauart** (HW-07, 14.10.2026; ersetzt GY-MAX4466): Elektretkapsel (analog) und MEMS **Infineon IM69D127** (PDM, IP57, fertige Platine) in einem Mikrofonkopf auf dem Gitterboden, beide am **Audio-ADC TI TLV320ADC3101** (links analog, rechts digital, I²S an den STM32). Zweck: Plausibilisierung (Ausfall, Verkleben, Drift) durch Vergleich der Kanäle. Ausgearbeitet in [`mikrofon.md`](mikrofon.md) (2.2). |
| F7 [M] | **Bedienung ohne Öffnen** (Entscheidung 09.10.2026): Reedkontakt parallel zum Service-Taster an PA0 (Magnet von außen); **seitlich abstrahlende LED** an PC13 am Platinenrand, **fertiger Wand-Lichtleiter mit Dichtung durch eine Bohrung in der Gehäusewand** (Kandidat Bivar PLTR2, IP67), außen Markierung „Magnet hier“. Lichtsignale: `mcu-funk.md` 3.3. Reset- und BOOT0-Taster innen. |
| F8 [K] | Regensensor über den Erweiterungsstecker (F9). |
| F9 [S] | **Reserve**: Erweiterungsstecker J11 **2 × 6**, 2,54 mm: 3,3 V (geschaltet und dauernd), 3 × GND, I²C, Serial1; Pins 9–11 seit HW-09 Modul-UART und Modus des BLE-Moduls (vorher frei; keine freien GPIOs: PB13 Lastschalter BLE, PA15/PB12 seit HW-07 I²S). Ein dort angeschlossenes I²C-Gerät zählt zur Buskapazität von F5 (HW26-13). |
| F11 [M] | **SPI-Flash 64 Mbit** für Messwerte (fest, Entscheidung 09.10.2026): SOIC-8 208 mil, Typ nach Bestand bei der Bestellung, SPI1 mit CS an PB3, dauernd versorgt im Deep Power-down. `mcu-funk.md` 3.2. |
| F10 [M] | **ESD-Schutz** an allen Sensorklemmen mit 4-fach-ESD-Arrays (wie BEEP base v3). An der Wägezelle mit kleinem Leckstrom; für E± Sperrspannung ≥ 5 V. Gewählt (09.10.2026): **TI ESDS304** (3,6 V, ≤ 50 nA) an DS18B20, BME280 und Mikrofon; **TI TPD4E05U06** (5,5 V, ≤ 10 nA, C138714) an der Wägezelle. Siehe [`anschluesse.md`](anschluesse.md) 2 und [`beep-vergleich.md`](beep-vergleich.md) 3.2. |

### 2.1 Ra-01SH – Befunde aus Datenblatt V1.1

| Punkt | Befund | Folge |
|---|---|---|
| Takt | **Quarz** (32 MHz) im Schaltbild, **kein TCXO**; DIO3 bleibt frei | In der Firmware TCXO aus. Bei niedrigem Spreizfaktor (Gateway 5–8 m entfernt) sehe ich kein Problem. Bei SF11/SF12 in strenger Kälte **[P]** Frequenzdrift im Wintertest beobachten. |
| HF-Umschalter | Im Schaltbild steuert **DIO2** über 0 Ω den TX_EN-Zweig („DIO2 = 1 → TX“) | In der Firmware DIO2 als HF-Schalter einstellen. TXEN/RXEN brauchen dann keine MCU-Pins. **[P]** am ersten Modul nachmessen, ob TXEN intern wirklich an DIO2 hängt. |
| Versorgung | 3,3 V, Spitzenstrom > 200 mA empfohlen, LDO empfohlen, ESD am 3,3-V-Eingang | LDO für mindestens 250 mA Spitze, Pufferkondensator nahe am Modul |
| Pegel | 3,3 V | passt zum STM32 |
| CE | Ai-Thinker verlinkt ein CE-RED-Zertifikat für das Modul | **[P]** Zertifikat herunterladen und ablegen |
| Lager | LCSC 1.791 Stück am 08.10.2026, ca. 3,96 $ ab 10 Stück | **[P]** Bestand bei JLCPCB vor der Bestellung |

### 2.2 Mikrofone und Audio-ADC (HW-07, 14.10.2026; ersetzt GY-MAX4466 mit Analogfilter)

| Nr. | Maßnahme |
|---|---|
| A1 [M] | Versorgung: AVDD aus eigener Schiene 3V3_ANA (Ferrit + 10 Ω + 22 µF hinter dem Sensorschalter), DVDD 1,8 V aus TPS70918, IOVDD = 3V3_SW (wie die I²C-Pull-ups), MEMS-Versorgung 3V3_MEMS über eigenen Ferrit. |
| A2 [M] | **Anti-Aliasing im Audio-ADC:** Delta-Sigma-Wandler mit digitalem Dezimationsfilter (Filter A: −73 dB ab 0,55 fS [V, TI SLAS553B]), Abtastung **fS = 24 576 Hz, AOSR 128** → PDM-Takt 3,146 MHz (Bedingung 2,8–6,2 MHz [V], IM69D127-Band 2,9–3,3 MHz [V]). Der STM32 dezimiert weiter auf 2048 Hz (Faktor 12) und wertet 60–900 Hz aus (`docs/fft-konzept.md`). Hochpass durch die Koppelkondensatoren (1 µF an ca. 35 kΩ ≈ 4,5 Hz). |
| A3 [M] | Durchgehende Massefläche; ADC nahe der Mikrofonbuchse J5, weg von Funkmodul, SPI und 5-V-Wandler; PDM-Takt über Schmitt-Puffer (Flanke ≤ 13 ns am Mikrofon [V]). |
| A4 [M] | Kabel **Cat7 S/FTP** mit geschirmtem **RJ45** (Buchse J5 ohne Übertrager, Paare T568B), fest verlegt, **0,5–1 m** (länger nur mit Treiber für DATA im Mikrofonkopf: Last ≤ 200 pF und Taktflanke ≤ 13 ns, `mikrofon_filter.py`); je Signal ein Paar mit GND, Elektret auf eigenem Paar (pseudo-differenziell); Gesamtschirm nur am Logger an Masse. |
| A5 [M] | Messung nie während einer Funkübertragung und nie bei laufendem 5-V-Wandler; Reihenfolge Waage → Mikrofon → Senden. |
| A6 [S] | Feste Verstärkung (AGC aus), damit die Pegel beider Kanäle und aller Logger vergleichbar bleiben; Welch-Mittelung, Pegel in dBFS und Bandpegel (`docs/fft-konzept.md`); zusätzlich eine **Kanalvergleichs-Kennzahl** (Pegelverhältnis, Kohärenz) als Qualitätsmerkmal, 1 Byte im Funkformat [A]. |
| A7 [M] | Daten über **I2S3** des STM32 (PB12 CK, PA15 WS, PB5 SD; STM32 Master, Empfang mit DMA); ADC-Takt aus BCLK über die interne PLL (kein MCLK); Einstellung über I²C (0x18). Sind 3V3_SW und der ADC aus, bleiben die I²S-Pins hochohmig. **[P]** PLL-/Teilerwerte am Muster bestätigen. |

## 3. Versorgung

Ausgearbeitet in **[`versorgung.md`](versorgung.md)**, dort mit Quellen, Rechnung und offenen Prüfpunkten. Kurzfassung:

| Nr. | Anforderung |
|---|---|
| V1 [M] | Li-Ion 18650 im Halter **Keystone 1042 (SMD)** (HW-02) **auf der Hauptplatine** (HW-06, 14.10.2026; vorher eigene Akku-Platine mit Kabel). Direkt am Halter: Zellschutz, NTC, **2 × TMP390 mit N-FETs für die Ladesperre** (V3), Messbrücke. Stecker J3 JST PH **5-polig** (P−, NTC, CE_FREI, TMP_VCC, P+), Kabel 1:1 nach Kabelplan `anschluesse.md`. |
| V2 [M] | **Tiefentladeschutz in Hardware, zweistufig:** BQ25185 trennt SYS bei 3,0 V; HY2111-GB + 8205 trennt die Zelle bei 2,9 V (0,1 µA). Freigabe nur durch Laden. Dazu Firmware-Stufen ab 3,5 V. |
| V3 [M] | Laderegler **BQ25185**: Eingang bis 18 V (Panels kalt bis ca. 10 V), Eingangsspannungsregelung, Ladeschluss **4,1 V**, **150 mA** (HW26-11, Wärme `versorgung.md` 3.2a). **Ladesperre zweistufig, beide ≤ 45 °C (HW26-07, SCH26-01/03, 09.10.2026):** 1. **TMP390 U2 an der Zelle** sperrt über CE außerhalb **+5 … 42 °C**; 2. **zweiter TMP390 U3** öffnet über 42 °C den NTC-Kreis (TS offen), NTC zusätzlich +1,7 / 59,5 °C. Versorgung beider Stufen aus **TMP_VCC (TPS70933 am Ladereingang)**, damit der Wiederanlauf nach Tiefentladung funktioniert und nachts kein Strom fließt; ausfallsicher bei Leitungsbruch. Auslegung auf 45 °C, bis die Zellvariante feststeht. Je Panel eine Schottky-Diode, TVS am Eingang; Messung der Eingangsspannung 3,3 MΩ / 470 kΩ hinter den Dioden (HW26-08). `versorgung.md` 3.1–3.3. |
| V4 [M] | LDO **RT9080-33**: 600 mA, 2 µA Ruhestrom |
| V5 [M] | Lastschalter **TPS22917** für die Sensorschiene (Anstiegszeit über CT, aktive Ausgangsentladung, wie BEEP base v3); Rückfall AO3401A mit Gate-RC und Entladewiderstand. **Alle Pull-ups an der geschalteten Schiene** (Rückspeisung, HW26-04). |
| V6 [S] | RTC über VBAT an 3,3 V, **keine Knopfzelle**. Bei Abschaltung durch den Schutz holt die Firmware die Zeit per DeviceTimeReq neu. |
| V7 [S] | Ruhestrom **unter 20 µA bei 25 °C** (gerechnet 15,7 µA, `energiebilanz.py`); bei 70 °C bis ca. 25 µA. **[P]** nachmessen. |
| V8 [S] | Panels steil (60–70° Süd) montieren, Unterkante frei (Schnee) |

## 4. Gehäuse und Mechanik

Grundlage: **Camdenboss-Zeichnung CBHUB_02, Revision N vom 14.10.2025** („Sales GA drawing for Hub size 2“, 6 Blätter, Maße in mm).
Die PDF liegt wegen des Herstellercopyrights nicht im Repo, sondern lokal unter `Bienen\Datenblaetter\`.

### 4.1 Maße aus der Zeichnung

| Maß | Wert | Blatt |
|---|---|---|
| Außen (B × T × H) | 162,5 × 162,5 × 81,5 mm | 1 |
| Innenhöhe Unterteil | 58,9 mm (Boden 3 mm) | 4 |
| Werkstoff | PC, UL 94 V0 | Schriftfeld |
| **Platine im Unterteil**: größte Kontur | 152,5 × 152,5 mm, kreuzförmig: Mitte 152,5 breit auf 121 mm Höhe, Laschen 121 breit; Ecken frei mit R 5 | 5 |
| Befestigungsdome Unterteil | 4 × Ø 6 mm (Dom), Bohrung in der Platine Ø 3,4 mm, **Lochabstand 110,2 × 110,2 mm** | 5 |
| Führungsschlitze am Rand | 2 mm breit, bis auf 138 mm Breite, bei 0 und ± 40 mm (80 mm Abstand) | 5 |
| Eingeschränkte Bauhöhe **unter** der Platine | 2 Felder je 50,5 mm breit, mittig, von ± 28 mm (Abstand 56 mm) bis zum Rand; an ihrer Innenkante je eine Rundung Ø 6,5 mm bis ± 26,75 mm (Abstand 53,5 mm). Vermutlich die Wandhalter-Aufnahmen. | 5 |
| **Platine im Deckel** (Alternative) | bis 146,8 × 146,8 mm, Lochabstand 108 × 108 mm, Ø 3,4 mm, Dom Ø 6 mm; Kerbe 7 mm für den Angusspunkt | 6 |
| Dombohrung Unterteil | **Ø 2,4 mm**, 10,1 mm tief (STEP: 2,4 → 2,3 mm konisch); früher hier fälschlich Ø 3,6 mm gelesen (Ø 3,6 steht auf Blatt 3) | 4, STEP |

### 4.1a Maße aus dem STEP-Modell (CBHUB_02 -01.1, Camdenboss, erhalten 13.10.2026)

Ausgewertet mit OpenCascade (Strahlschnitte im 1-mm-Raster und Einzelschnitte); Bericht `docs/testberichte/2026-10-13-gehaeuse-step.md`. Das STEP-Modell liegt nur lokal (Herstellerdatei, nicht im Repo).

| Maß | Wert |
|---|---|
| Referenzplatine Unterteil im STEP | 152,5 × 152,5 × 1,6 mm, Löcher Ø 3,4 mm auf **110,2 × 110,2 mm**, Auflage Ø 6 mm – bestätigt M1 |
| Dom | Außen-Ø 5,9 mm, Spitze **9,1 mm über dem Innenboden**; Boden 2,5 mm |
| Innenwand auf Platinenhöhe (HW-03) | ± 76,7 mm von der Mitte (Formschräge ca. 1°), Wand 2,5 mm → **16,2 mm** von der Platinenkante zur Innenwand |
| Freiraum unter der Platine (HW-03) | Unterseite 19,1 mm über dem Innenboden; mindestens **13,0 mm** über den erhöhten Feldern (Wandhalter-Aufnahmen) |
| Freiraum über der Platinenoberseite | **53,8 mm** bis zur Deckel-Innenfläche; **45,8 mm** unter den Deckeldomen (Ø 6, 108 mm, direkt neben unseren Löchern); **44,3 mm** unter den Deckelpfosten an den Platinenecken |
| Ecksäulen (Deckelschrauben) | Abstand zur Platinenecke ca. 3–4 mm (Raster 1 mm) |
| Kollision Gehäuse ↔ Platine 121 × 121 mm | keine |

### 4.2 Anforderungen

| Nr. | Anforderung |
|---|---|
| M1 [M] | **Hauptplatine 121 × 121 mm**, quadratisch, Ecken gerundet, 4 Bohrungen Ø 3,4 mm auf **110,2 × 110,2 mm** (mittig). Sie liegt ganz innerhalb der erlaubten Kontur und lässt am Rand Platz für die Kabel. |
| M2 [M] | Auf der **Unterseite** keine Bauteile. **Platine auf glatten Distanzhülsen 10 mm über den Domen** (HW-03, 13.10.2026), selbstformende Schrauben durch Platine und Hülse in die Dombohrung Ø 2,4 mm (Blatt 4, STEP; Schraube Ø 3 mm für Kunststoff); damit genug Freiraum unter der Platine auch in den eingeschränkten Feldern, THT-Lötstellen müssen nicht gekürzt werden [A]. **Bauhöhe über der Platine höchstens 40 mm** (inkl. gesteckter Klemmen- und RJ45-Stecker und Zelle im Halter, M3). Höhe der Lichtleiter-Bohrung (F7) aus dem STEP berechnet (4.1a, `mcu-funk.md` 3.3), am ersten Muster bestätigen. **STEP-Kontrolle (13.10.2026): bestanden**, mindestens 4,3 mm Reserve über den 40 mm. |
| M3 [S] | **Akkuhalter** Keystone 1042 (88 × 22 mm Courtyard) **auf der Hauptplatine** (HW-06). Bauhöhe 18650 im Halter ca. 21 mm [A], unter den 40 mm über der Platine (M2/HW-03) und unter dem STEP-Freiraum ≥ 44,3 mm (4.1a). Nicht an der Funkkante; TMP390/NTC unter der Zelle. Halterung bei Erschütterung am Muster prüfen [P]. |
| M4 [M] | Innen **steckbare Schraubklemmen**, Raster **3,5 mm** (Mikrofone seit HW-07 über eine geschirmte **RJ45-Buchse**) (**DEGSON 15EDGRC-3.5**, einreihig; Teilenummern je Polzahl in `anschluesse.md` 2; SCH26-13), damit jeder Sensor ohne Löten getauscht werden kann. Masse/Schirm immer Pin 1; Aufdruck an jeder Klemme; Jede Sensorklemme eigene Polzahl: **J8 (BME280) 6-polig**, J4 (Wägezelle) 5-polig, dazu Steckerfarbe (09.10.2026). Belegung J1–J11: [`anschluesse.md`](anschluesse.md). |
| M5 [S] | **Lage der Außenanschlüsse legt der Layouter fest** (Philipp 14.10.2026): möglichst an einer Kante zu den Kabeldurchführungen hin, zwei Kanten zulässig; ESD direkt hinter jedem Anschluss; Funkmodul mit IPEX an der Kante gegenüber; **BLE-Modul U303 an einer Platinenkante, Antenne nach außen, Sperrzonen des Footprints frei, Metall (Zelle, Klemmen, Buchsen) ≥ 30 mm** (HW-09, mcu-funk.md 1.6); Ladepads, Debug, Erweiterung, BOOT/Reset innen gut erreichbar; Lichtleiter-LED und Reedkontakt an einer Seitenkante (mcu-funk.md 3.3). Vorschläge und Gründe in [`anschluesse.md`](anschluesse.md) 4. |
| M6 [K] | Kabeldurchführungen: zurückgestellt, Festlegung später. |
| M7 [M] | Bestückung **komplett bei JLCPCB, auch die Durchsteckteile** (Festlegung 09.10.2026; anschluesse.md 5). SMD einseitig, möglichst JLCPCB-„Basic Parts“; „Extended Parts“ (STM32, HX711, CN3065, Ra-01SH …) nur wo nötig. |
| M8 [M] | **4 oder 6 Lagen nach Wahl des Layouters** (Philipp 14.10.2026, Preise geprüft; vorher 4 Lagen, 09.10.2026), 1,6 mm, Aufbau nach JLCPCB-Standard. Pflicht: **Lage unter L1 durchgehende Masse**, jede Signallage mit Masse-Nachbarlage. 4 Lagen: L1 Signal/Bauteile, L2 Masse, L3 Versorgung (3,3 V, SYS, 5 V) mit Masse-Füllung, L4 Signal; 6 Lagen (Vorschlag): L1 Signal, L2 Masse, L3 Signal, L4 Versorgung, L5 Masse, L6 Signal. Masselage nicht auftrennen; Masse-Durchkontaktierungen entlang der Platinenkante und um Funkmodul, Wandler und Waagen-/Mikrofonzweig. HASL bleifrei oder ENIG; Schutzlack nach dem Test; Klemmen, Ladepads, Antennenanschluss und das BLE-Modul (Chip-Antenne, Schirm nicht waschen) abdecken. |
| M9 [S] | Testpunkte für 3,3 V, Akku, Solar, GND, PDM-Takt und I²S (HW-07). |
| M10 [M] | Temperaturbereich: alle Bauteile mindestens −20 bis +70 °C. |
| M11 [M] | **Board-Kennung und Umgebung** im Titelblock jedes Schaltplans und später im Bestückungsdruck: **PCB-AKKU-0.1**, **PCB-MAIN-0.1** (REG26-10). Auslegungsumgebung [A]: Gehäuse innen −20 … +60 °C, Betauung möglich (Bienenstock); Laden nur +5 … 42 °C (`sicherheit-akku.md`); Solar-Eingang ≤ 12 V dauernd, 25 V absolut. Jede Änderung von Schaltung oder Leiterplatte erhöht die Kennung. |

## 5. Fertigung bei JLCPCB (Ablauf)

1. Entwurf in **KiCad**, Fertigungsdaten z. B. mit dem Plugin „Fabrication Toolkit“.
2. Diese Daten erzeugen:
   - Gerber + Bohrdaten (ZIP)
   - BOM mit LCSC-Nummern
   - CPL (Bestückungsdaten)
3. Hochladen, „PCB Assembly“ wählen, Vorschau prüfen, in den Warenkorb legen.
4. **[P]** Kurz vor der Bestellung prüfen:
   - Lagerstand bei JLCPCB
   - Kosten
   - Versand und Einfuhrumsatzsteuer

## 6. Neue Firmware (Eckpunkte)

| Nr. | Punkt |
|---|---|
| S1 | **Stack:** RadioLib, Stand 7.8.1 vom 03.10.2026 geprüft. Unterstützt werden SX1262, ABP, EU868 und DeviceTimeReq (`getMacDeviceTimeAns`, rechnet die Zeit seit Sendeende selbst ein). |
| S2 | **Sitzung speichern:** Sitzungspuffer 302 Byte, Nonce-Puffer 14 Byte. Ablage im **SPI-Flash** nach jedem Senden als Ringpuffer mit Generationszähler, CRC-32 und Gültig-Byte; beim Wiederherstellen Frame-Zähler mit Sicherheitsabstand (`mcu-funk.md` 3.1, HW26-10). |
| S3 | **Übernommen wird** die eigene Zeitlogik aus `beelogger_zeitsync.h`: Weckraster, Plausibilität, Sommerzeit. Ebenso die PC-Tests und die Simulation. |
| S4 | **Nutzlast und Decoder:** Entschieden (08.10.2026): Die Daten gehen weiter an den **eigenen beelogger-Webserver**. Die neue Firmware bekommt ein eigenes Funkformat auf FPort 2. Der TTN-Formatter übersetzt es in die beelogger-Feldnamen. Einzelheiten in `docs/datenformat.md`. |
| S5 | **Lizenz:** Ohne beelogger-Code ist die Lizenz der neuen Firmware frei wählbar. Vorschlag: bei GPL-3.0-or-later bleiben, das passt zum restlichen Repo. |
| S6 | Die Musterlogger mit beelogger-Platine und RFM95 laufen weiter mit `STM32_LORA_261008_ZS`. |

## 7. Entschieden und offen

Entschieden (08.10.2026):

- Funkmodul Ai-Thinker Ra-01SH
- Neue Firmware ohne beelogger-Kompatibilität
- Mikrofon GY-MAX4466 mit Entstörung (ersetzt durch HW-07: zwei Mikrofone am Audio-ADC)
- Akku per Kabel
- Gehäuse CBHUB-02-GY, Hauptplatine im Unterteil
- Daten weiter an den eigenen beelogger-Webserver
- Durchführungen später
- BLE-Modul RN4871 statt USB; USB-C-Buchse entfällt, Laden über zwei Pads (HW-09, 18.10.2026; `mcu-funk.md` 1.3/1.6)

Offen:

- RN4871: Footprint-Abgleich mit C633942, Bestand, Prüfplan B-1 … B-6 (HW26-20)

- Webserver-Skripte prüfen: Felder für Mikrofon und Deckeltemperatur (S4, `docs/datenformat.md`)
- Prüfpunkte der Versorgung, `versorgung.md` Abschnitt 7 (u. a. Panel-Messung, BQ25185-Eingangsbereich, HY2111-Variante)
- ~~Domhöhe und Freiraum (STEP-Modell)~~ (13.10.2026, 4.1a); Lage des Akkuhalters (M2, M3)

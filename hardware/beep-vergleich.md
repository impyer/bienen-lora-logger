# Vergleich mit der BEEP base v3 (Stand 09.10.2026)

Quelle: BEEP measurement system v3 bzw. BEEP base v3. Platine von Ideetron, Schaltplan ID190222-02 vom 08.10.2019, Stückliste vom 10.10.2019, Lizenz CC BY-SA.
- https://www.openhardware.io/view/739/BEEP-base-v3
- https://github.com/beepnl/measurement-system-v3

Gelesen habe ich den Schaltplan (2 Blätter), die Stückliste und die Leiterplatten-Spezifikation. Übernommen werden nur **Ideen**, keine Konstruktionsdaten.

## 1. Was die BEEP base v3 ist

| Bereich | BEEP base v3 |
|---|---|
| Mikrocontroller / Funk | nRF52840-Modul (Rigado BMD-340, Bluetooth) + RFM95 (LoRa), U.FL-Buchse auf der Platine |
| Versorgung | **2 × AAA Lithium (Primärzellen, kein Solar)** → Schottky CRS08 → Aufwärtswandler TPS61291 mit Bypass, 3,0 V |
| Sensorschiene | **Lastschalter TPS22917** (3,3Vx): Anstiegszeit über CT = 100 pF, **aktive Entladung des Ausgangs (QOD)** |
| Waage | 1 × HX711 **an der 3,0-V-Schiene**, AVDD = 1,25 V × (10k + 8,2k) / 8,2k = **2,77 V** (PNP MMBT4403). Zweite Zelle an **Kanal B (Verstärkung 32)**. Jede Signalleitung mit 100 Ω in Reihe, 100 nF zwischen den Signalleitungen, ESD-Array an allen Leitungen |
| Temperatur | DS18B20 (1-Wire), **Pull-up 4,7 kΩ an der geschalteten Schiene**, ESD-Array, 3-polige Klemme |
| BME280 | I²C extern, **Pull-ups 4,7 kΩ an der geschalteten Schiene**, ESD-Array |
| Audio | **Audio-ADC TLV320ADC3100** (Delta-Sigma, I²S an den nRF), eigener 1,8-V-LDO. Elektret-Mikrofon direkt über **3,5-mm-Klinke**; Vorspannung über 2,2 kΩ, 470 nF Koppelkondensatoren, ESD-Array |
| Bedienung | **Reedkontakt** (Magnet von außen) und **Neigungsschalter** (ohne Ruhestrom) als Weckquellen, Summer |
| Speicher / Sicherheit | 64-Mbit-SPI-Flash für Messwerte, Krypto-Chip ATECC608A |
| Leiterplatte | **4 Lagen**, 1,6 mm, viele SMD-Testpunkte |
| 32-kHz-Quarz | NX3215SA mit **6 pF** und 2 × 6 pF |

## 2. Abgleich mit unserer Planung

| Thema | BEEP | Wir | Bewertung |
|---|---|---|---|
| Pull-ups an der geschalteten Schiene | ja | ja (versorgung.md 3.7) | **bestätigt** |
| ESD-Schutz an jedem Außenanschluss, auch an den Signalleitungen der Wägezelle | 4-fach-ESD-Arrays ESDS304 | geplant, Teil offen | **übernehmen**: gleicher Ansatz, Teil siehe 3.2 |
| 100 Ω in den Signalleitungen der Wägezelle + Kondensator zwischen S+/S− | ja | ja (waage.md 4) | **bestätigt** |
| Lastschalter mit Anstiegssteuerung und Ausgangsentladung | TPS22917 | P-MOSFET AO3401A | **übernehmen** (siehe 3.1) |
| Weckquelle von außen ohne Gehäuseöffnung | Reedkontakt | Taster an PA0 | **übernehmen** (siehe 3.3) |
| Testpunkte | viele | M9 | **bestätigt**, großzügig vorsehen |
| 32-kHz-Quarz mit kleiner Lastkapazität | 6 pF | 7 pF (C97604) | **bestätigt** |
| Leiterplatte | 4 Lagen | 4 Lagen (09.10.2026) | **übernommen** (siehe 3.4) |
| HX711-Speisung | 3,0 V, AVDD 2,77 V, 2. Zelle an Kanal B (Verstärkung 32) | 5 V, AVDD 4,3 V, 2 × HX711 je Kanal A (128) | Wir haben **ca. 1,55-fach mehr Signal** und für die zweite Zelle die **4-fache Verstärkung**. Unsere Entscheidung bleibt. |
| Audio | eigener Audio-ADC mit eingebauter digitaler Filterung | GY-MAX4466 + Analogfilter + STM32-ADC → seit HW-07 TLV320ADC3101 mit Elektret + MEMS | **übernommen (HW-07)**, siehe 3.5 |
| Versorgung | Primärzellen ohne Solar | 18650 + Solar | anderes Konzept, nichts zu übernehmen |
| Krypto-Chip, Bluetooth, Summer | ja | nein | nicht übernehmen (ABP-Schlüssel in der Firmware; Summer kostet Strom und stört womöglich die Bienen [A]) |
| Flash für Messwerte | 64 Mbit | 64 Mbit, fest (09.10.2026) | **übernommen** (siehe 3.6) |

## 3. Übernahmen im Einzelnen

### 3.1 Lastschalter TPS22917 statt P-MOSFET

Was er bringt [V: TI TPS22917; Beschaltung wie BEEP]:
- **Anstiegszeit über CT** einstellbar. An der Sensorschiene hängen 22 µF (Mikrofon) und 10 µF (HX711). Ein harter Einschaltstoß könnte die 3,3-V-Schiene kurz einbrechen lassen.
- **Ausgangsentladung (QOD):** Im Aus-Zustand wird die Schiene aktiv auf 0 V gezogen. Kein halb versorgter Sensor über Restladung.
- **Rückstromsperre**, 0,5 µA eingeschaltet, 10 nA Leckstrom aus [V].

Kosten: Extended-Teil statt Basic (LCSC C2681320 [V, Nummer aus Recherche]). **[P]** Bestand prüfen.

Rückfall: AO3401A mit Gate-RC und 10-kΩ-Entladewiderstand an der Schiene. Der Widerstand zieht eingeschaltet 0,33 mA; das ist nur während der Messung.

### 3.2 ESD-Schutz an den Klemmen

BEEP nutzt ESDS304 (TI, 4 Kanäle, 3,6 V, SOT-23-5) an allen Außenanschlüssen, auch an den Signalleitungen der Wägezelle. Für unsere Platine:

| Klemme | Schutz |
|---|---|
| DS18B20, BME280, Mikrofon | 4-fach-ESD-Array (3,6 V) |
| Wägezelle S±, E± | 4-fach-ESD-Array **mit kleinem Leckstrom**. **[P]** Leckstrom des ESDS304 bei 25 °C und 60 °C im Datenblatt prüfen: 100 nA durch 100 Ω ergeben 10 µV, das sind etwa 0,2 kg. |
| E± bei 5 V | Array mit Sperrspannung ≥ 5 V nötig, nicht 3,6 V. Die Erregung liegt bei 4,3 V. |
| Panel, USB | wie versorgung.md / mcu-funk.md (TVS bzw. USBLC6) |

### 3.3 Reedkontakt als Service-Weckquelle

- Reedkontakt (SMD, wie RI-80SMD bei BEEP) **parallel zum Service-Taster an PA0** (WKUP1, steigende Flanke).
- Wirkung: Mit einem Magneten außen am Gehäuse wird der Logger geweckt, z. B. für eine Sofort-Messung oder einen Testsendung. Das Gehäuse bleibt dicht, es braucht keine Taster-Durchführung.
- Strom: Nur solange der Magnet anliegt, fließen 33 µA durch den 100-kΩ-Pull-down. Im Ruhezustand ist der Kontakt offen und braucht nichts.
- Der Taster bleibt für den Tisch.

Den **Neigungsschalter** übernehme ich nicht: Das Öffnen des Stocks sieht man schon am Gewichtssprung [A]. Wer ihn möchte, kann ihn über den Erweiterungsstecker anschließen.

### 3.4 Vier Lagen statt zwei (entschieden 09.10.2026: 4 Lagen)

BEEP hat 4 Lagen mit durchgehender Masse auf den Innenlagen. Bei uns liegen auf einer Platine:
- ein Funkmodul mit bis zu 140 mA Sendestrom
- ein 5-V-Wandler mit 3,5 MHz
- ein 24-Bit-Wägezellen-ADC
- ein Mikrofoneingang

Eine durchgehende Massefläche unter allem macht das Layout deutlich sicherer gegen gegenseitige Störungen.

- **Vorteil:** einfachere Führung von Masse und Versorgung; entschärft A3 und HW26-04.
- **Nachteil:** höherer Preis je Platine. **[P]** Preis für 121 × 121 mm, 4 Lagen, 10 Stück bei JLCPCB im Angebot prüfen; ich habe ihn nicht abgefragt.
- **Entschieden:** 4 Lagen (Signal / Masse / Versorgung / Signal), siehe Lastenheft M8.

### 3.5 Audio: Alternative eigener Audio-ADC (nur zur Information)

BEEP setzt einen Audio-ADC TLV320ADC3100 ein. Ein Delta-Sigma-Audio-ADC filtert intern digital gegen Spiegelfrequenzen. Das Problem aus `mikrofon.md` Abschnitt 1 gibt es damit praktisch nicht.

| | Vorteil | Nachteil |
|---|---|---|
| Audio-ADC (BEEP-Weg) | kein Analogfilter nötig; **Verstärkung per Software**, also bei allen Loggern gleich (hilft bei HW26-05) | Elektret direkt über 2 m Kabel: Millivolt-Signal mit hoher Impedanz, störanfälliger [A]; **4–5 zusätzliche Pins** (I²S, MCLK, Reset), die wir nicht mehr frei haben; neue Firmware für I²S; Extended-Teil |
| Unser Weg (GY-MAX4466 + Filter) | Modul verstärkt im Stock, kräftiges Signal auf dem Kabel; nur ein Pin; einfach | Analogfilter nötig; Verstärkung am Poti, bei jedem Logger etwas anders |

~~**Keine Änderung**, die Entscheidung für den GY-MAX4466 steht.~~ **Überholt durch HW-07 (14.10.2026):** Audio-ADC übernommen, aber als **TLV320ADC3101** (mit Digitalmikrofon-Eingang) für zwei Mikrofone verschiedener Bauart; Elektret pseudo-differenziell über Cat7 0,5–1 m statt 2 m, Takt aus BCLK (kein MCLK), Reset per RC, damit genügen 3 I²S-Pins (mikrofon.md).

### 3.6 Flash für Messwerte (Kann)

Optional einen SOIC-8-Platz für SPI-Flash (z. B. 64 Mbit) an SPI1 neben dem Funkmodul. Er braucht einen eigenen Chip-Select (PB3, frei).

Nutzen:
- Messwerte bei Funkausfall vorhalten
- später über USB auslesen

Unbestückt lassen, bis die Firmware das nutzt.

## 4. Änderungen am Lastenheft (0.4)

- V5: TPS22917 statt AO3401A (AO3401A als Rückfall)
- F7: Reedkontakt parallel zum Service-Taster an PA0
- Neu F10: ESD-Arrays an allen Sensorklemmen; an der Wägezelle mit kleinem Leckstrom, für E± ≥ 5 V Sperrspannung
- M8: **4 Lagen** (entschieden 09.10.2026)
- F11: SPI-Flash 64 Mbit **fest bestückt** (Entscheidung 09.10.2026), CS an PB3

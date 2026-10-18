# Prüfbericht: Pinfunktionen aller ICs und Module gegen die Datenblätter

- **Prüfbericht-ID:** SCH-2026-10-18-PINS
- **Prüfdatum (UTC):** 18.10.2026
- **Anlass:** Rückmeldung des Maintainers („viele falsche Verbindungen im Schaltplan“) ohne Nennung einzelner Stellen; Regelwerk H-04 (Pin-Multiplex gegen Firmware-Pinmatrix), H-06 Nr. 4 (Symbol-Pin-/Footprint-Abgleich gegen Hersteller-Pinzeichnung)
- **Geprüfter Stand:** Branch `design/hw10-mikrofon3-layout` (HW-09 + HW-10, Layout-Stand 18.10.2026); Generator `hardware/kicad/hauptplatine.py`, Symbole `werkzeug/symbole.py`
- **Teststufe:** T0 (Datenblätter, ST-Pindaten) und T3 (`pin_footprint.py`, `netz_tests.py`). Keine Messung.
- **Methode:** Für jedes aktive Bauteil die Pinnummer → Pinname des Symbols gegen das Herstellerdokument gelesen (PDF als Text oder als Bild gerendert) und die Netzzuordnung auf Plausibilität geprüft (Richtung, Versorgung, Pegel). Die Tabelle `DATENBLATT` in `werkzeug/pin_footprint.py` wurde entsprechend auf [V] gehoben; `pruefen.sh` prüft daraus weiter automatisch Symbol = Datenblatt und Symbol-Pins = Footprint-Pads.

## Ergebnis je Bauteil

| Bauteil | Quelle (18.10.2026 gelesen) | Pinfolge Symbol = Datenblatt | Netzprüfung (Richtung/Versorgung) | Ergebnis |
|---|---|---|---|---|
| **U301 STM32F411CEU6** | ST open pin data `STM32F411C(C-E)Ux.xml` (UFQFPN48) | ST-Bibliothekssymbol; Pinnummern 2 PC13, 3/4 PC14/PC15, 10 PA0, 11–17 PA1–PA7, 18/19 PB0/PB1, 20 PB2, 21 PB10, 25–28 PB12–PB15, 29–33 PA8–PA12, 34 PA13, 37 PA14, 38 PA15, 39–46 PB3–PB9 bestätigt | **PA11 = USART6_TX, PA12 = USART6_RX** (BLE); **PB12 = I2S3_CK, PA15 = I2S3_WS, PB5 = I2S3_SD** (Audio-ADC); PA4–PA7 SPI1 (NSS/SCK/MISO/MOSI); PB6/PB7 I2C1 SCL/SDA; PA9/PA10 USART1 TX/RX; PB0/PB1 ADC1_IN8/IN9; PA0 SYS_WKUP; PA13/PA14 SWDIO/SWCLK; PC14/PC15 OSC32; PA2/PA3, PB3, PB4, PB8–PB10, PB13–PB15, PC13 als GPIO | **ok** |
| **U601 TLV320ADC3101** | TI SLAS553B Abschnitt 7 (bereits [V]); vom Maintainer bestätigt | 25 Pins (EP = AVSS) | links IN2L(P)/IN3L(M), rechts IN2R(P)/IN3R(M) (HW-10) und DMDIN/DMCLK; MICBIAS1/2; BCLK/WCLK/DOUT ↔ I2S3; SCL/SDA; I2C_ADR0/1 an GND = 0x18; MCLK an GND (PLL aus BCLK) | **ok** |
| **U201 BQ25185** | TI SLUSF65B Tab. 4-1 (bereits [V]) | 10 + Pad | IN ← VIN_LADER, SYS → Regler, BAT ↔ VBAT, CE/TS von der Ladesperre, ISET/ILIM-Widerstände, STAT1/2 Testpunkte | **ok** |
| **U203 TPS22917** | TI SLVSDW8 Tab. 6-1 | 1 VIN, 2 GND, 3 ON, 4 CT, 5 QOD, 6 VOUT | **CT-Kondensator an VIN** – Datenblatt: „Connect capacitor from this pin to VIN“ (anders als bei TPS22918!) – so gezeichnet; QOD über R209 an VOUT (Datenblatt erlaubt Widerstand oder direkt) | **ok** |
| **U202 RT9080-33** | Richtek DS9080 (frühere Sitzung [V*], Download heute 404) | 1 VIN, 2 GND, 3 EN, 4 NC, 5 VOUT | EN an VIN | ok (Quelle nicht erneut geöffnet) |
| **U204 TPS70933, U602 TPS70918** | TI SBVS186 Tab. 5-1 DBV (bereits [V]) | 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT | U204 EN offen (erlaubt), U602 EN an IN | **ok** |
| **U501 TPS61240** | TI SLVS806D Pin Functions, WSON | 1 GND, 2 VOUT, 3 FB, 4 EN, 5 L, 6 VIN, 7 Pad | FB an VOUT (feste 5 V), EN ← PB10 mit Pull-down, VIN an SYS, Pad an GND | **ok** |
| **U502 HX711** | AVIA HX711 Tab. 1 | 1 VSUP, 2 BASE, 3 AVDD, 4 VFB, 5 AGND, 6 VBG, 7 INNA, 8 INPA, 9 INNB, 10 INPB, 11 PD_SCK, 12 DOUT, 13 XO, 14 XI, 15 RATE, 16 DVDD | INA+ = Pin 8 ← S+, INA− = Pin 7 ← S−; RATE an GND (10 SPS), XI an GND (interner Takt), XO offen; AVDD aus PNP-Regler mit VFB-Teiler | **ok** |
| **U802/U803 TMP390** | TI SBOS904 Pin Functions, DRL | 1 SETA, 2 SETB, 3 GND, 4 OUTB, 5 VDD, 6 OUTA | SETA/SETB-Widerstände nach GND; OUTA/OUTB Open-Drain mit Pull-up an TMP_VCC; U803 OUTB offen (Datenblatt: erlaubt) | **ok** |
| **U801 HY2111-GB** | HYCON DS-HY2111-V17 Abschnitt 7 | 1 OD, 2 CS, 3 OC, 4 NC, 5 VDD, 6 VSS | VDD über 100 Ω von B+, VSS = B−, CS über 2 kΩ an P− (GND), OD → Gate M1 (Entladen, Source B−), OC → Gate M2 (Laden, Source P−) = HYCON-Anwendungsschaltung | **ok** |
| **Q801 FS8205** | Fortune FS8205 Rev. 1.7 Abschnitt 4 | 1 S1, 2 D12, 3 S2, 4 G2, 5 D12, 6 G1 (D1/D2 gemeinsam) | S1 = B−, S2 = GND (P−), G1 ← OD, G2 ← OC, D12 verbunden | **ok** |
| **Q802/Q803 AO3400A, Q301 AO3401A** | AOS AO3400A Rev. 3.1 / AO3401A Rev. 3.1, Pinbild SOT-23 | 1 G, 2 S, 3 D | Q802/Q803: S an GND, D an CE_LADEN bzw. NTC_FUSS, G vom TMP390 mit Pull-up; Q301: S an +3V3, D = BLE_VCC, G ← PB13 mit Pull-up (P-Kanal high-side) | **ok** |
| **U603 74LVC1G17** | TI SN74LVC1G17 Pin Functions, DCK | 1 NC, 2 A, 3 GND, 4 Y, 5 VCC | A ← DMCLK des ADC, Y → 33 Ω → Klemme, VCC = 3V3_SW | **ok** (Nexperia GW gleich belegt [A]) |
| **U303 RN4871** | Microchip DS50002489D Tab. 1-2, Fig. 5-4 | 16 Pins (siehe HW-09-Bericht) | UART_RX ← PA11 (TX), UART_TX → PA12 (RX), VBAT = BLE_VCC, P2_0 Pull-up an BLE_VCC, RST_N intern hochgezogen | **ok** |
| **U401 Ra-01SH** | Ai-Thinker Spec V1.1 S. 11 (bereits [V]) | 16 Pads | NSS/SCK/MOSI/MISO ↔ SPI1 über 33 Ω, BUSY → PA3, DIO1 → PA2, RESET ← PB4, ANT offen, TXEN/RXEN über offene Brücken | **ok** |
| **U402 SPI-Flash** | Standard-Pinbelegung 25er-Reihe (KiCad W25Q32JVSS) | 1 CS, 2 DO, 3 WP, 4 GND, 5 DI, 6 CLK, 7 HOLD, 8 VCC | DI ← SPI_MOSI, DO → SPI_MISO, CS ← PB3 mit Pull-up, WP/HOLD Pull-ups | ok; **Teil (XT25F64B/ZD25Q64D) bei der Bestellung gegen diese Belegung prüfen [P]** |
| **D501 TPD4E05U06, D601/D602/D701/D702 ESDS304** | TI Tab. 4-2 (bereits [V]) | 10 bzw. 5 Pins | GND-Pin an GND, Kanäle an die Klemmensignale | **ok** |
| **Q501 S8550 (C397181, AnBon)** | AnBon S8550 Datenblatt: **kein Pinbild** (nur Gehäusemaße) | KiCad-Symbol SS8550 (Fairchild): 1 B, 2 E, 3 C | B ← HX711 BASE, E ← VSUP_HX, C → HX_AVDD | **offen [P]:** Pinfolge des bestellten Herstellers prüfen; je nach Hersteller 1 E/2 B/3 C – Layouter nennt das Teil, Symbol ggf. anpassen |
| Passive, Klemmen, Stiftleisten, Quarze, LED, Reed, Akkuhalter | `pin_footprint.md` | – | Y301 1/3 Quarz, 2/4 Gehäuse [A]; LTST-S220 Pad 1 = Kathode [V]; Keystone 1042 Pad 1 = Plus laut KiCad-Footprint [A] | **offen [P]:** Keystone-Polung und Quarz-Pads am Footprint prüfen; DEGSON-Zeichnung; RJ45-Teil |

## Automatische Prüfungen auf diesem Stand

- `pruefen.sh` (KiCad 10.0.7): reproduzierbar, **ERC 0**, **Netzprüfung 236/236** (Modell ↔ KiCad-Netzliste vollständig, dazu gezielte Prüfungen je Blatt mit Gegenproben), **Pin-/Footprint-Abgleich 186 Bauteile, 0 Abweichungen**.
- `pin_footprint.md` enthält jetzt für STM32, AO3400A, AO3401A, HY2111, FS8205 und 74LVC1G17 die Quelle mit Datum.

## Bewertung

Im geprüften Stand wurde **keine falsche Pinzuordnung und keine unplausible Netzverbindung** gefunden. Sollten im PDF einzelne Verbindungen falsch wirken, bitte Blatt und Bauteil nennen: Mögliche Ursachen sind die Darstellung (Netznamen statt gezeichneter Leitungen zwischen den Blättern; an einem Pin endende Leitung mit Netzname; Versorgungssymbole an gedrehten Bauteilen) oder eine Absicht, die hier dokumentiert ist (z. B. CT an VIN beim TPS22917, MCLK an GND beim Audio-ADC, XI/RATE an GND beim HX711, B− ≠ GND beim Zellschutz, offene Lötbrücken TXEN/RXEN).

## Offen

S8550-Pinfolge je Hersteller (Q501), Flash-Typ (U402), Keystone-1042-Polung, Quarz-Pad-Zuordnung Y301, RJ45-Teil (J601), DEGSON-Zeichnung, TVS D401 – alle bereits in `pin_footprint.md` bzw. Pflichtenheft 7 als [P] geführt; keine Änderung am Schaltplan nötig, solange der Layouter Teile mit passender Pinfolge vorschlägt.

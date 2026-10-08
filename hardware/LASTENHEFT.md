# Lastenheft: eigene Logger-Platine (Entwurf 0.1, 08.10.2026)

Ziel ist eine offene SMD-Platine, die JLCPCB weitgehend fertig bestückt und auf der die
beelogger-STM32-Firmware (`firmware/`) **ohne Änderung** läuft. Board-Einstellung bleibt „BlackPill F411CE“.
Die Platine ist eine Neuentwicklung; von beelogger übernommen wird nur die Pinbelegung, die im GPL-Quelltext steht.

Kennzeichnung: **[M]** Muss, **[S]** Soll, **[K]** Kann, **[P]** offener Prüfpunkt.

## 1. Kompatibilität zur Firmware

| Nr. | Anforderung |
|---|---|
| K1 [M] | Mikrocontroller **STM32F411CEU6** (UFQFPN-48) direkt auf der Platine. |
| K2 [M] | **25-MHz-Quarz (HSE)**: Die Arduino-Variante BLACKPILL_F411CE rechnet fest mit 25 MHz (PLLM = 25, im STM32-Core 2.6.0 geprüft). Ein anderer Takt ergibt falsche Zeiten, Baudraten und LoRa-Timings. |
| K3 [M] | **32,768-kHz-Quarz (LSE)** an PC14/PC15 für die RTC. Lastkapazitäten nach Datenblatt des Quarzes; LSE-Treiberstärke bedenken. |
| K4 [M] | Pinbelegung wie in der Tabelle unten. |
| K5 [M] | EEPROM **AT24C256** am I²C-Bus, Adresse 0x57 (A0–A2 auf High). |

### Pinbelegung (aus `STM32_beelogger.h` und `STM32_LORA.ino`)

| Pin | Funktion | Bemerkung |
|---|---|---|
| PA0 | Service-Taster / Wakeup | Pull-down extern (laut Sketch zusätzlich empfohlen) |
| PA1 | Mikrofon (analog) | Eingang für GY-MAX4466 oder eigene Verstärkerstufe |
| PA2 / PA3 | RFM95 DIO0 / DIO1 | |
| PA4 / PA5 / PA6 / PA7 | RFM95 NSS / SCK / MISO / MOSI (SPI1) | |
| PA8 | 1-Wire DS18B20 | Pull-up 4,7 kΩ |
| PA9 / PA10 | Serial1 TX / RX | Programmier- und Debug-Anschluss (FTDI) |
| PA13 / PA14 | SWD | zusätzlich zum Seriell-Bootloader |
| PA15 | Regensensor | optional |
| PB0 / PB1 | Spannungsmessung Akku / Solar | Teiler hochohmig, möglichst abschaltbar |
| PB2 / PB10 | HX711 Nr. 2 DT / SCK | PB2 ist zugleich BOOT1: Pegel beim Start beachten |
| PB4 | frei (beim Original ESP-Reset / SIM-Power) | |
| PB5 | Power_Pin: Peripherie ein/aus | High-Side-Schalter |
| PB6 / PB7 | I²C SCL / SDA | EEPROM, BME280 (extern), Pull-ups |
| PB8 / PB9 | HX711 Nr. 1 DT / SCK | |
| PB12 / PB13 | DHT (optional) | |
| PC13 | LED | |
| PC14 / PC15 | LSE 32,768 kHz | |

## 2. Funktionen

| Nr. | Anforderung |
|---|---|
| F1 [M] | **LoRa**: Footprint für RFM95W-868 (16 × 16 mm, SMD). **[P]** Bei LCSC war das Modul (RFM95-868S2, C22371063) am 08.10.2026 nicht vorrätig → von Hand bestücken oder als beigestelltes Teil einplanen. Alternative mit anderem Funkchip (SX1262) hieße Firmware-Änderung. |
| F2 [M] | **Antenne**: Lötpad für λ/4-Draht (86 mm) **und** optional u.FL/SMA. 50-Ω-Leitung kurz halten; Masseflächen nach Modul-Datenblatt. |
| F3 [M] | **Waage**: 2 × HX711 (SOP-16) mit eigener Analogversorgung nach Referenzschaltung. Abgeschirmte Zuleitung; Anschluss je Wägezelle 4- oder 6-polig (Sense optional). |
| F4 [M] | **Temperatur**: 1-Wire-Anschluss für mindestens 2 × DS18B20 (Brut, Deckel), Schraub- oder Steckklemme. |
| F5 [M] | **I²C außen**: Anschluss für BME280 im Strahlungsschutz (3,3 V, GND, SCL, SDA), ESD-Schutz. |
| F6 [S] | **Mikrofon**: Anschluss für GY-MAX4466 mit RC-Siebung (68 Ω, 100 Ω, 470 µF wie in der Stückliste) **oder** eigene Verstärkerstufe auf der Platine. |
| F7 [S] | **Service**: Taster an PA0, LED an PC13, Reset-Taster, BOOT0-Taster oder -Jumper. |
| F8 [K] | Regensensor (PA15), DHT (PB12/PB13), zweiter I²C-Anschluss. |

## 3. Versorgung

| Nr. | Anforderung |
|---|---|
| V1 [M] | Li-Ion 18650 (3,0–4,2 V), Halter auf der Platine oder Anschluss; Verpolschutz. |
| V2 [M] | **Solarladeregler** auf der Platine (CN3065 oder gleichwertig, Eingang für 2 Panels 6 V parallel), Schottky-Diode im Solarpfad (SMD-Bauform statt 1N5818). |
| V3 [M] | LDO 3,3 V mit sehr kleinem Ruhestrom (MCP1700/1702, ca. 1,6 µA, oder TPS7A02, ca. 25 nA). |
| V4 [M] | High-Side-Schalter (P-MOSFET) für Sensoren, HX711, Mikrofon an PB5. |
| V5 [S] | **RTC-Pufferung über VBAT** (CR2032 oder Kondensator mit Diode): Die Uhr läuft beim Akkutausch weiter. Das vermeidet den Neustart bei Power-On-Reset. |
| V6 [S] | Ziel-Ruhestrom der ganzen Platine **unter 20 µA** im Standby (STM32 mit RTC, LDO, EEPROM, HX711 power-down, RFM95 sleep, Teiler abgeschaltet). **[P]** Nachmessen. |

## 4. Mechanik und Fertigung

| Nr. | Anforderung |
|---|---|
| M1 [M] | Abmessungen und Bohrungen passend zum Spelsberg-Gehäuse. **[P]** Gehäusetyp festlegen. |
| M2 [M] | SMD-Bauteile einseitig, möglichst JLCPCB-„Basic Parts“; „Extended Parts“ (STM32, HX711, CN3065 …) nur wo nötig. |
| M3 [M] | Steckverbinder und Klemmen in Durchsteckmontage: JLCPCB-THT-Bestückung oder von Hand. |
| M4 [S] | 2-lagig, 1,6 mm, HASL bleifrei oder ENIG; Schutzlack nach dem Test (Feuchte im Bienenstand). |
| M5 [S] | Testpunkte für 3,3 V, Akku, Solar, GND; Aufdruck aller Anschlüsse. |
| M6 [M] | Temperaturbereich: Bauteile für mindestens −20 bis +70 °C. Das RFM95-Modul ist laut LCSC-Datenblattangabe für −20 bis +70 °C spezifiziert. **[P]** Winterbetrieb prüfen. |

## 5. Fertigung bei JLCPCB (Ablauf)

1. Entwurf in **KiCad**; für die Fertigungsdaten z. B. das Plugin „Fabrication Toolkit“.
2. Fertigungsdaten:
   - Gerber + Bohrdaten (ZIP)
   - **BOM** (Comment, Designator, Footprint, LCSC-Teilenummer)
   - **CPL** (Designator, Mid X, Mid Y, Layer, Rotation)
3. Bei jlcpcb.com hochladen, „PCB Assembly“ wählen, Bauteile und Platzierung in der Vorschau prüfen, in den Warenkorb legen.
4. **[P]** Kurz vor der Bestellung prüfen: Lagerstand der Teile, Mindestmengen für die Bestückung, Kosten (Einrichtung, Extended-Parts-Gebühr, Schablone), Versand und Einfuhrumsatzsteuer nach Deutschland.

## 6. Offene Entscheidungen

- RFM95W von Hand bestücken oder Funkmodul mit Lagerbestand bei LCSC (Firmware-Folgen)
- Mikrofonstufe auf der Platine oder Modul
- Akkuhalter auf der Platine oder Kabel
- Gehäusetyp und Steckverbinder (Schraubklemmen, JST-XH, M8-Rundstecker durch die Gehäusewand)

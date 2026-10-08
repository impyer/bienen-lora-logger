# Lastenheft: eigene Logger-Platine (Entwurf 0.2, 08.10.2026)

Ziel ist eine offene SMD-Platine, die JLCPCB weitgehend fertig bestückt.
Sie trägt den gleichen Mikrocontroller wie die BlackPill (Board-Einstellung bleibt „BlackPill F411CE“).
Der Funkteil wechselt auf **SX1262**. Dafür braucht die Firmware einen anderen LoRaWAN-Stack (Abschnitt 6).
Die Platine ist eine Neuentwicklung; von beelogger übernommen wird nur die Pinbelegung, die im GPL-Quelltext steht.

Kennzeichnung: **[M]** Muss, **[S]** Soll, **[K]** Kann, **[P]** offener Prüfpunkt.

Änderungen gegen 0.1: Entscheidungen vom 08.10.2026 eingearbeitet (Funkmodul SX1262, Mikrofon GY-MAX4466 mit
Entstörung, Akku per Kabel, Gehäuse CBHUB-02 mit Reserve).

## 1. Kompatibilität

| Nr. | Anforderung |
|---|---|
| K1 [M] | Mikrocontroller **STM32F411CEU6** (UFQFPN-48, LCSC C60420) direkt auf der Platine. |
| K2 [M] | **25-MHz-Quarz (HSE)**: Die Arduino-Variante BLACKPILL_F411CE rechnet fest mit 25 MHz (PLLM = 25, im STM32-Core 2.6.0 geprüft). Ein anderer Takt ergibt falsche Zeiten, Baudraten und LoRa-Timings. |
| K3 [M] | **32,768-kHz-Quarz (LSE)** an PC14/PC15 für die RTC. Lastkapazitäten nach Datenblatt des Quarzes. |
| K4 [M] | Pinbelegung wie in der Tabelle unten. Sensoren und Peripherie bleiben auf den beelogger-Pins; nur der Funkteil ändert sich. |
| K5 [M] | EEPROM **AT24C256** am I²C-Bus, Adresse 0x57 (A0–A2 auf High). Es speichert zusätzlich die LoRaWAN-Sitzung (siehe 6). |

### Pinbelegung

| Pin | Funktion | Bemerkung |
|---|---|---|
| PA0 | Service-Taster / Wakeup | Pull-down extern |
| PA1 | Mikrofon (analog) | GY-MAX4466, Entstörung siehe F6 |
| PA2 | **SX1262 DIO1** (Interrupt) | beim RFM95 DIO0 |
| PA3 | **SX1262 BUSY** | beim RFM95 DIO1 |
| PA4 / PA5 / PA6 / PA7 | SX1262 NSS / SCK / MISO / MOSI (SPI1) | wie bisher |
| PA8 | 1-Wire DS18B20 | Pull-up 4,7 kΩ |
| PA9 / PA10 | Serial1 TX / RX | Programmier- und Debug-Anschluss (FTDI) |
| PA13 / PA14 | SWD | zusätzlich zum Seriell-Bootloader |
| PA15 | Regensensor | optional |
| PB0 / PB1 | Spannungsmessung Akku / Solar | Teiler hochohmig, möglichst abschaltbar |
| PB2 / PB10 | HX711 Nr. 2 DT / SCK | PB2 ist zugleich BOOT1: Pegel beim Start beachten |
| PB4 | **SX1262 NRESET** | beim Original frei (ESP-Reset / SIM-Power) |
| PB14 | **RXEN des Funkmoduls** (nur E22) | beim Original frei. **[P]** nach Moduldatenblatt |
| PB5 | Power_Pin: Peripherie ein/aus | High-Side-Schalter |
| PB6 / PB7 | I²C SCL / SDA | EEPROM, BME280 (extern), Pull-ups |
| PB8 / PB9 | HX711 Nr. 1 DT / SCK | |
| PB12 / PB13 | DHT (optional) | |
| PC13 | LED | |
| PC14 / PC15 | LSE 32,768 kHz | |
| PB3, PB15 | frei | auf Erweiterungsstecker führen (F9) |

## 2. Funktionen

| Nr. | Anforderung |
|---|---|
| F1 [M] | **Funk: SX1262-Modul** (fertiges Modul, kein Chip-down). Kandidaten siehe 2.1. Der Footprint wird für **ein** Modul festgelegt. |
| F2 [M] | **Antenne**: Lötpad für λ/4-Draht (ca. 86 mm) **und** u.FL (falls das Modul es hat) oder SMA-Footprint. 50-Ω-Leitung kurz halten; Masseflächen nach Modul-Datenblatt. |
| F3 [M] | **Waage**: 2 × HX711 (SOP-16) mit eigener Analogversorgung nach Referenzschaltung. Anschluss je Wägezelle 4- oder 6-polig (Sense optional). |
| F4 [M] | **Temperatur**: 1-Wire-Anschluss für mindestens 2 × DS18B20 (Brut, Deckel), zwei getrennte Klemmen am gleichen Bus. |
| F5 [M] | **I²C außen**: Anschluss für BME280 im Strahlungsschutz (3,3 V, GND, SCL, SDA), ESD-Schutz. |
| F6 [M] | **Mikrofon GY-MAX4466** als Modul, mit Entstörung auf der Platine (Abschnitt 2.2). |
| F7 [S] | **Service**: Taster an PA0, LED an PC13, Reset-Taster, BOOT0-Taster oder -Jumper. |
| F8 [K] | Regensensor (PA15), DHT (PB12/PB13). |
| F9 [S] | **Reserve**: Erweiterungsstecker (Stiftleiste 2,54 mm) mit 3,3 V geschaltet und ungeschaltet, GND, I²C, Serial1, PB3, PB15. Zweiter I²C-Anschluss als Klemme. |

### 2.1 Funkmodul-Kandidaten (Stand 08.10.2026, Lagerstand bei LCSC)

| Modul | LCSC | Lager LCSC | Preis ab 10 St. | Temperatur | Bemerkung |
|---|---|---|---|---|---|
| Ebyte **E22-900M22S** | C411293 | 37 | ca. 5,67 $ | −40 bis +85 °C | 20 × 14 mm, bis 22 dBm, u.FL und Stempelloch-Antenne. Externe RF-Umschaltung über TXEN/RXEN. Ich glaube, es hat einen TCXO (so in Händlerangaben); **[P]** im Datenblatt prüfen. |
| Ai-Thinker **Ra-01SH** | C2764087 | 1.791 | ca. 3,96 $ | −40 bis +85 °C | SMD-16P, 803–930 MHz. **[P]** Antennenanschluss, TCXO und RF-Umschaltung im Datenblatt prüfen. |
| (Chip-down) SX1262IMLTRT | C191341 | 2.132 | ca. 2,77 $ | – | Nur als Option: braucht HF-Anpassung, TCXO und sauberes Layout. Wegen des HF-Risikos nicht empfohlen. |

- Beide Module sind für −40 °C angegeben. Das RFM95 ist laut LCSC-Angabe nur für −20 °C angegeben; für den Winterbetrieb ist das ein Vorteil.
- **[P]** Die JLCPCB-Bestückung nutzt das eigene JLCPCB-Lager, nicht das LCSC-Lager. Den Bestand dort kurz vor der Bestellung prüfen.
- **[P]** CE-/RED-Unterlagen des gewählten Moduls anfordern bzw. prüfen. Ob für reinen Eigengebrauch eine Konformitätserklärung nötig ist, kann ich nicht sicher beurteilen.
- EU868 erlaubt 14 dBm ERP (wie bisher in der Firmware). Die 22 dBm der Module werden nicht genutzt.

### 2.2 Mikrofon-Entstörung (GY-MAX4466)

Das Modul gibt das Signal um VCC/2 aus. Jedes Rauschen auf der Versorgung erscheint deshalb direkt im Signal.

| Nr. | Maßnahme |
|---|---|
| A1 [M] | Eigene Versorgung für das Mikrofon: RC- oder LC-Siebung hinter dem Power_Pin (bisher 68 Ω / 100 Ω / 470 µF aus der Stückliste), zusätzlich Ferrit. **[K]** eigener rauscharmer LDO für den Analogteil. |
| A2 [M] | Tiefpass vor dem ADC-Eingang PA1 (Anti-Aliasing). Grenzfrequenz grob 2–3 kHz: Das Bienensummen liegt nach meinem Wissen überwiegend unter 1 kHz. **[P]** Werte mit der ADC-Abtastrate der Firmware abstimmen. |
| A3 [M] | Analogmasse sternförmig an einem Punkt mit der Digitalmasse verbunden. Leitungen von Funkmodul und SPI fern von PA1 und der Mikrofonklemme. |
| A4 [M] | Abgeschirmtes Kabel (LiYCY 3 × 0,14, vorhanden). Schirm einseitig auf der Platine an Analogmasse. |
| A5 [S] | Messung nie während einer Funkübertragung. Die Firmware misst ohnehin vor dem Senden; **[P]** im Musterbau mit dem Oszilloskop prüfen. |
| A6 [S] | Verstärkung am Poti des Moduls so einstellen, dass das Signal nicht übersteuert. Rauschen lässt sich in der Firmware zusätzlich durch Mittelung mehrerer Messungen senken. |

## 3. Versorgung

| Nr. | Anforderung |
|---|---|
| V1 [M] | Li-Ion 18650 (3,0–4,2 V) **per Kabel**. Halter Keystone 1043 ist bereits bestellt und sitzt getrennt im Gehäuse. Steckbarer Anschluss auf der Platine mit **Verpolschutz** (P-MOSFET statt Diode, wegen des Spannungsabfalls). |
| V2 [M] | Akku **ohne Schutzschaltung** (BAK N18650CP, bestellt): Tiefentladeschutz auf der Platine (Unterspannungsabschaltung) oder sichere Abschaltung durch die Firmware. **[P]** Lösung festlegen. |
| V3 [M] | **Solarladeregler** auf der Platine (CN3065 oder gleichwertig, Eingang für 2 Panels 6 V parallel), Schottky-Diode im Solarpfad (SMD-Bauform statt 1N5818). |
| V4 [M] | LDO 3,3 V mit sehr kleinem Ruhestrom (MCP1700/1702, ca. 1,6 µA, oder TPS7A02, ca. 25 nA). Spitzenstrom beim Senden beachten (SX1262 bei 14 dBm deutlich unter 100 mA; **[P]** Datenblatt). |
| V5 [M] | High-Side-Schalter (P-MOSFET) für Sensoren, HX711, Mikrofon an PB5. |
| V6 [S] | **RTC-Pufferung über VBAT** (CR2032 oder Kondensator mit Diode): Die Uhr läuft beim Akkutausch weiter. |
| V7 [S] | Ziel-Ruhestrom der ganzen Platine **unter 20 µA** im Standby (STM32 mit RTC, LDO, EEPROM, HX711 power-down, SX1262 sleep, Teiler abgeschaltet). **[P]** Nachmessen. |

## 4. Mechanik, Gehäuse und Steckverbinder

| Nr. | Anforderung |
|---|---|
| M1 [M] | Gehäuse **Camdenboss CBHUB-02-GY**, IP66/67, innen ca. 152 × 152 × 57 mm (10 Stück bereits gekauft). **[P]** Lage und Abstand der Befestigungsdome am Mustergehäuse ausmessen; danach Platinenumriss festlegen. |
| M2 [M] | **Platz einteilen**: Platine, Akkuhalter, Kippschalter und Druckausgleichselement (M12) getrennt anordnen. Rund ein Drittel der Fläche bleibt frei für spätere Erweiterungen. |
| M3 [M] | **Kabeleinführung mit Kabelverschraubungen** (vorhanden, 6 je Gehäuse). Innen **steckbare Schraubklemmen** (Raster 3,5 oder 5,08 mm), damit jeder Sensor ohne Löten getauscht werden kann. Rundsteckverbinder (M8/M12) durch die Gehäusewand sind dichter und bequemer, kosten aber deutlich mehr; nur für die Waage als Option **[K]**. |
| M4 [M] | **Reserve bei den Durchführungen**: Waage, 2 × DS18B20, BME280, Mikrofon und Solar belegen bereits alle 6 Verschraubungen. Mindestens 1–2 zusätzliche Bohrungen mit Blindstopfen vorsehen oder beide DS18B20 durch eine Mehrfach-Dichteinsatz-Verschraubung führen. |
| M5 [M] | SMD-Bauteile einseitig, möglichst JLCPCB-„Basic Parts“; „Extended Parts“ (STM32, HX711, CN3065, Funkmodul …) nur wo nötig. |
| M6 [M] | Klemmen und Steckverbinder in Durchsteckmontage: JLCPCB-THT-Bestückung oder von Hand. Aufdruck an jeder Klemme. |
| M7 [S] | 2-lagig, 1,6 mm, HASL bleifrei oder ENIG; Schutzlack nach dem Test (Feuchte im Bienenstand), Klemmen und Antennenanschluss abdecken. |
| M8 [S] | Testpunkte für 3,3 V, Akku, Solar, GND, Mikrofon-Ausgang. |
| M9 [M] | Temperaturbereich: alle Bauteile mindestens −20 bis +70 °C, Funkmodul möglichst −40 °C. |

## 5. Fertigung bei JLCPCB (Ablauf)

1. Entwurf in **KiCad**; für die Fertigungsdaten z. B. das Plugin „Fabrication Toolkit“.
2. Fertigungsdaten:
   - Gerber + Bohrdaten (ZIP)
   - **BOM** (Comment, Designator, Footprint, LCSC-Teilenummer)
   - **CPL** (Designator, Mid X, Mid Y, Layer, Rotation)
3. Bei jlcpcb.com hochladen, „PCB Assembly“ wählen, Bauteile und Platzierung in der Vorschau prüfen, in den Warenkorb legen.
4. **[P]** Kurz vor der Bestellung prüfen: Lagerstand der Teile bei JLCPCB, Mindestmengen für die Bestückung, Kosten (Einrichtung, Extended-Parts-Gebühr, Schablone), Versand und Einfuhrumsatzsteuer nach Deutschland.

## 6. Folgen für die Firmware

| Nr. | Punkt |
|---|---|
| S1 | **MCCI LMIC unterstützt nur SX127x**, nicht SX1262. Neuer Stack: **RadioLib** (Version 7.8.1 vom 03.10.2026 geprüft). Sie unterstützt ABP (`beginABP`), EU868 und DeviceTimeReq (`getMacDeviceTimeAns`). |
| S2 | RadioLib rechnet beim DeviceTimeAns die Zeit zwischen Sendeende und Auswertung selbst ein, ähnlich wie die bisherige Lösung. Die Zeitlogik in `beelogger_zeitsync.h` (Weckraster, Plausibilität) bleibt nutzbar; nur die Anbindung an den Stack ändert sich. |
| S3 | RadioLib verlangt für LoRaWAN 1.0.4 eine **gespeicherte Sitzung**: Sitzungspuffer 302 Byte, Nonce-Puffer 14 Byte (aus dem Quelltext 7.8.1 berechnet). Das passt nicht in die 80 Byte der Backup-Register. Ablage im **AT24C256** nach jedem Senden. Bei einer Aufzeichnung alle 15 Minuten sind das rund 35.000 Schreibvorgänge im Jahr; das EEPROM ist nach Datenblatt für etwa 1 Mio. Zyklen ausgelegt. **[P]** Datenblatt und Speicherbereich festlegen, ggf. Speicherorte wechseln. |
| S4 | Die Firmware erhält eine Funk-Abstraktion, damit Musterlogger mit RFM95 (MCCI) und neue Platinen (SX1262, RadioLib) aus einem Quelltext übersetzt werden. Eigener Schalter, z. B. `FUNK_SX1262`. |
| S5 | TTN-Einstellungen (MAC-Version 1.0.x, Factory presets, Statusabfragen) **[P]** für RadioLib neu prüfen; RadioLib kann die LoRaWAN-Version beim ABP-Start wählen. |

## 7. Entschieden und offen

Entschieden (08.10.2026):

- Funk: SX1262-Modul; Firmware wird angepasst.
- Mikrofon: GY-MAX4466 als Modul, Entstörung auf der Platine.
- Akku: per Kabel, Halter getrennt.
- Gehäuse: CBHUB-02-GY (vorhanden), Kabelverschraubungen und steckbare Klemmen, Reserve an Platz und Durchführungen.

Offen:

- Modul E22-900M22S oder Ra-01SH (nach Datenblattprüfung; Lager bei JLCPCB).
- Tiefentladeschutz in Hardware oder Firmware (V2).
- Platinenumriss nach Ausmessen der Befestigungsdome (M1).
- Rundsteckverbinder für die Waage ja/nein (M3).

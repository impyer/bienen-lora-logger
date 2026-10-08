# Lastenheft: eigene Logger-Platine (Entwurf 0.3, 08.10.2026)

Ziel ist eine offene SMD-Platine, die JLCPCB weitgehend fertig bestückt.
Funkmodul ist das **Ai-Thinker Ra-01SH (SX1262)**. Die Firmware wird **neu aufgesetzt**; Kompatibilität zur
beelogger-Firmware und zur beelogger-Pinbelegung ist **nicht** gefordert.

Kennzeichnung: **[M]** Muss, **[S]** Soll, **[K]** Kann, **[P]** offener Prüfpunkt.

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
| K4 [M] | EEPROM **AT24C256** am I²C-Bus (Messwertpuffer und LoRaWAN-Sitzung). |
| K5 [S] | **USB-C** an PA11/PA12: Aufspielen über den eingebauten USB-DFU-Bootloader des STM32 und Service-Konsole, ohne FTDI-Adapter. Dazu ein BOOT0-Taster. Seriell (PA9/PA10) und SWD bleiben als Stiftleiste. |

### Pinbelegung (Vorschlag)

| Pin | Funktion | Bemerkung |
|---|---|---|
| PA0 | Service-Taster / Wakeup (WKUP1) | Pull-down extern |
| PA1 | Mikrofon (ADC1_IN1) | Entstörung siehe 2.2 |
| PA2 | Ra-01SH DIO1 (Interrupt) | |
| PA3 | Ra-01SH BUSY | |
| PA4 / PA5 / PA6 / PA7 | Ra-01SH NSS / SCK / MISO / MOSI (SPI1) | Serienwiderstände 22–100 Ω laut Moduldatenblatt |
| PA8 | 1-Wire DS18B20 | Pull-up 4,7 kΩ |
| PA9 / PA10 | Serial1 TX / RX | Stiftleiste Debug |
| PA11 / PA12 | USB D− / D+ | USB-C, ESD-Schutz |
| PA13 / PA14 | SWD | Stiftleiste |
| PA15 | Regensensor | optional |
| PB0 / PB1 | Spannung Akku / Solar (ADC1_IN8 / IN9) | Teiler hochohmig, abschaltbar |
| PB2 | BOOT1 | fest über Widerstand auf GND, nicht belegen |
| PB4 | Ra-01SH RESET | |
| PB5 | Peripherie ein/aus | High-Side-Schalter |
| PB6 / PB7 | I²C SCL / SDA | EEPROM, BME280 (extern), Pull-ups |
| PB8 / PB9 | HX711 Nr. 1 DT / SCK | |
| PB12 / PB13 | HX711 Nr. 2 DT / SCK | nicht mehr auf PB2 (BOOT1) |
| PC13 | LED | |
| PC14 / PC15 | LSE 32,768 kHz | |
| PB3, PB10, PB14, PB15 | frei | Erweiterungsstecker (F9) |

## 2. Funktionen

| Nr. | Anforderung |
|---|---|
| F1 [M] | **Funk: Ai-Thinker Ra-01SH** (LCSC C2764087). Werte laut Datenblatt V1.1 vom 18.08.2020: 17 × 16 × 3,2 mm, 16 Stempellöcher im Raster 2 mm, −40 bis +85 °C. Einzelheiten in 2.1. |
| F2 [M] | **Antenne**: Lötpad für λ/4-Draht (ca. 86 mm) am Pin ANT, kurze 50-Ω-Leitung, Masseflächen. Das Modul hat zusätzlich eine IPEX-Buchse auf der Oberseite. Antenne fern von Metallteilen (Datenblatt). |
| F3 [M] | **Waage**: 2 × HX711 (SOP-16) mit eigener Analogversorgung nach Referenzschaltung. Anschluss je Wägezelle 4- oder 6-polig. |
| F4 [M] | **Temperatur**: 1-Wire für mindestens 2 × DS18B20, zwei Klemmen am gleichen Bus. |
| F5 [M] | **I²C außen**: Anschluss für BME280 im Strahlungsschutz, ESD-Schutz. |
| F6 [M] | **Mikrofon GY-MAX4466** als Modul, Entstörung auf der Platine (2.2). |
| F7 [S] | **Service**: Taster PA0, LED PC13, Reset-Taster, BOOT0-Taster. |
| F8 [K] | Regensensor (PA15). |
| F9 [S] | **Reserve**: Erweiterungsstecker 2,54 mm mit 3,3 V (geschaltet und dauernd), GND, I²C, Serial1, PB3, PB10, PB14, PB15. |

### 2.1 Ra-01SH – Befunde aus Datenblatt V1.1

| Punkt | Befund | Folge |
|---|---|---|
| Takt | **Quarz** (32 MHz) im Schaltbild, **kein TCXO**; DIO3 bleibt frei | In der Firmware TCXO aus. Bei niedrigem Spreizfaktor (Gateway 5–8 m entfernt) sehe ich kein Problem. Bei SF11/SF12 in strenger Kälte **[P]** Frequenzdrift im Wintertest beobachten. |
| HF-Umschalter | Im Schaltbild steuert **DIO2** über 0 Ω den TX_EN-Zweig („DIO2 = 1 → TX“) | In der Firmware DIO2 als HF-Schalter einstellen. TXEN/RXEN brauchen dann keine MCU-Pins. **[P]** am ersten Modul nachmessen, ob TXEN intern wirklich an DIO2 hängt. |
| Versorgung | 3,3 V, Spitzenstrom > 200 mA empfohlen, LDO empfohlen, ESD am 3,3-V-Eingang | LDO für mindestens 250 mA Spitze, Pufferkondensator nahe am Modul |
| Pegel | 3,3 V | passt zum STM32 |
| CE | Ai-Thinker verlinkt ein CE-RED-Zertifikat für das Modul | **[P]** Zertifikat herunterladen und ablegen |
| Lager | LCSC 1.791 Stück am 08.10.2026, ca. 3,96 $ ab 10 Stück | **[P]** Bestand bei JLCPCB vor der Bestellung |

### 2.2 Mikrofon-Entstörung (GY-MAX4466)

| Nr. | Maßnahme |
|---|---|
| A1 [M] | Eigene, gesiebte Versorgung: RC- oder LC-Glied hinter dem Peripherieschalter, Ferrit. **[K]** eigener rauscharmer LDO für den Analogteil. |
| A2 [M] | **Anti-Aliasing-Tiefpass 2. Ordnung** vor PA1, Grenzfrequenz ca. 1 kHz (passiv zweistufig oder mit stromsparendem OPV). Er ist auf 8192 Hz ADC-Takt mit digitaler Dezimierung auf 2048 Hz ausgelegt; siehe `docs/fft-konzept.md`. Zusätzlich ein flacher Hochpass bei 20–30 Hz gegen Gleichanteil und Rumpeln. Die Grenze bei 55,5/60 Hz setzt die Firmware, nicht die Platine. |
| A3 [M] | Analogmasse sternförmig an einem Punkt mit Digitalmasse. Funkmodul und SPI fern von PA1. |
| A4 [M] | Abgeschirmtes Kabel (LiYCY 3 × 0,14). Schirm einseitig auf Analogmasse. |
| A5 [M] | Messung nie während einer Funkübertragung; das legt die neue Firmware fest. |
| A6 [S] | Verstärkung am Poti so einstellen, dass nichts übersteuert. In der Firmware Welch-Mittelung, Pegel in dBFS und Bandpegel (`docs/fft-konzept.md`). |
| A7 [M] | ADC an PA1 timergesteuert mit DMA (8192 Hz). PA1 = ADC1_IN1 und Timer-Trigger beim STM32F411 **[P]** im Referenzhandbuch bestätigen. |

## 3. Versorgung

| Nr. | Anforderung |
|---|---|
| V1 [M] | Li-Ion 18650 **per Kabel**. Halter Keystone 1043 (bestellt) sitzt getrennt. Steckbarer Anschluss mit Verpolschutz (P-MOSFET). |
| V2 [M] | Akku **ohne Schutzschaltung** (BAK N18650CP): Tiefentladeschutz in Hardware (Unterspannungsabschaltung) oder sicher in der Firmware. **[P]** festlegen. |
| V3 [M] | Solarladeregler (CN3065 oder gleichwertig), Eingang für 2 Panels 6 V parallel, SMD-Schottky im Solarpfad. |
| V4 [M] | LDO 3,3 V mit sehr kleinem Ruhestrom **und** mindestens 250 mA Spitzenstrom (Ra-01SH). **[P]** Kandidaten prüfen; MCP1700 schafft nur 250 mA und ist damit knapp. |
| V5 [M] | High-Side-Schalter (P-MOSFET) für Sensoren, HX711, Mikrofon an PB5. |
| V6 [S] | RTC-Pufferung über VBAT (CR2032 oder Kondensator mit Diode). |
| V7 [S] | Ruhestrom der ganzen Platine **unter 20 µA**. **[P]** nachmessen. |

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
| Dombohrung Unterteil | Ø 3,6 mm (vermutlich für selbstformende Schrauben) | 4 |

### 4.2 Anforderungen

| Nr. | Anforderung |
|---|---|
| M1 [M] | **Hauptplatine 121 × 121 mm**, quadratisch, Ecken gerundet, 4 Bohrungen Ø 3,4 mm auf **110,2 × 110,2 mm** (mittig). Sie liegt ganz innerhalb der erlaubten Kontur und lässt am Rand Platz für die Kabel. |
| M2 [M] | Auf der **Unterseite** keine Bauteile; THT-Lötstellen in den zwei eingeschränkten Feldern kurz abschneiden. **[P]** Freiraum unter der Platine und Domhöhe aus dem STEP-Modell (bei Camdenboss anfragen) oder am Muster messen. |
| M3 [S] | **Akkuhalter** auf einer Trägerplatte an den Deckeldomen (108 × 108 mm) oder seitlich neben der Hauptplatine. **[P]** Bauhöhe 18650 im Halter gegen den Freiraum zwischen Hauptplatine und Deckel prüfen. |
| M4 [M] | Innen **steckbare Schraubklemmen** (Raster 3,5 oder 5,08 mm), damit jeder Sensor ohne Löten getauscht werden kann. Aufdruck an jeder Klemme. |
| M5 [S] | Klemmen an den Platinenrändern zu den späteren Durchführungen hin. Rund ein Drittel der Fläche frei für Erweiterungen. |
| M6 [K] | Kabeldurchführungen: zurückgestellt, Festlegung später. |
| M7 [M] | SMD einseitig, möglichst JLCPCB-„Basic Parts“; „Extended Parts“ (STM32, HX711, CN3065, Ra-01SH …) nur wo nötig. |
| M8 [S] | 2-lagig, 1,6 mm, HASL bleifrei oder ENIG; Schutzlack nach dem Test; Klemmen, USB und Antennenanschluss abdecken. |
| M9 [S] | Testpunkte für 3,3 V, Akku, Solar, GND, Mikrofon-Ausgang. |
| M10 [M] | Temperaturbereich: alle Bauteile mindestens −20 bis +70 °C. |

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
| S2 | **Sitzung speichern:** Sitzungspuffer 302 Byte, Nonce-Puffer 14 Byte. Ablage im AT24C256 nach jedem Senden, Speicherorte möglichst wechseln. |
| S3 | **Übernommen wird** die eigene Zeitlogik aus `beelogger_zeitsync.h`: Weckraster, Plausibilität, Sommerzeit. Ebenso die PC-Tests und die Simulation. |
| S4 | **Nutzlast und Decoder:** Entschieden (08.10.2026): Die Daten gehen weiter an den **eigenen beelogger-Webserver**. Die neue Firmware bekommt ein eigenes Funkformat auf FPort 2. Der TTN-Formatter übersetzt es in die beelogger-Feldnamen. Einzelheiten in `docs/datenformat.md`. |
| S5 | **Lizenz:** Ohne beelogger-Code ist die Lizenz der neuen Firmware frei wählbar. Vorschlag: bei GPL-3.0-or-later bleiben, das passt zum restlichen Repo. |
| S6 | Die Musterlogger mit beelogger-Platine und RFM95 laufen weiter mit `STM32_LORA_261008_ZS`. |

## 7. Entschieden und offen

Entschieden (08.10.2026):

- Funkmodul Ai-Thinker Ra-01SH
- Neue Firmware ohne beelogger-Kompatibilität
- Mikrofon GY-MAX4466 mit Entstörung
- Akku per Kabel
- Gehäuse CBHUB-02-GY, Hauptplatine im Unterteil
- Daten weiter an den eigenen beelogger-Webserver
- Durchführungen später

Offen:

- Webserver-Skripte prüfen: Felder für Mikrofon und Deckeltemperatur (S4, `docs/datenformat.md`)
- Tiefentladeschutz in Hardware oder Firmware (V2)
- LDO-Typ mit 250 mA Spitzenstrom und kleinem Ruhestrom (V4)
- Domhöhe und Freiraum (STEP-Modell), Lage des Akkuhalters (M2, M3)

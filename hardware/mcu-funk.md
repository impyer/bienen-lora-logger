# Block Mikrocontroller und Funk (Lastenheft 0.4, Abschnitt 1 und 2.1 – Entwurf, 08.10.2026)

Kennzeichnung:
- **[V]** im Datenblatt gelesen
- **[A]** Annahme oder Rechnung
- **[P]** vor dem Schaltplan bzw. am Muster prüfen

Bezug: `versorgung.md` (Schienen 3,3 V dauernd / 3,3 V geschaltet), Entscheidung Antenne (Philipp, 08.10.2026): **kleine Antenne an der IPEX-Buchse des Moduls**, im Gehäuse.

## 1. Mikrocontroller STM32F411CEU6 (UFQFPN-48)

### 1.1 Versorgung und Grundbeschaltung [V: ST AN4488 Abschnitt 2.2, 3.1, 4.5; DS10314 Abschnitt 3.14–3.16]

| Pin | Beschaltung |
|---|---|
| VDD (24, 36, 48) | je 100 nF direkt am Pin, dazu 1 × 10 µF in der Nähe (ST: mind. 4,7 µF) |
| VDDA/VREF+ (9) | 100 nF + 1 µF; über Ferrit (z. B. 600 Ω bei 100 MHz) an 3,3 V [A]. Gut für die Mikrofonmessung an PA1, ST schreibt den Ferrit nicht vor. |
| VSSA (8), VSS (23, 35, 47), Thermal-Pad | an die Massefläche; Thermal-Pad mit Durchkontaktierungen |
| VCAP_1 (22) | **4,7 µF keramisch, ESR < 1 Ω**, sehr nah. Der UFQFPN-48 hat nur diesen einen VCAP-Pin. |
| VBAT (1) | an 3,3 V (dauernd) + 100 nF; **keine Knopfzelle** (versorgung.md, V6). Nie an den Akku: nur 1,65–3,6 V zulässig. |
| NRST (7) | 100 nF nach GND (interner Pull-up), Reset-Taster nach GND |
| BOOT0 (44) | 10 kΩ nach GND [A, üblicher Wert], Taster nach 3,3 V für den USB-Bootloader |
| PB2/BOOT1 (20) | 10 kΩ nach GND, sonst frei. Wirkt nur bei BOOT0 = 1. |

### 1.2 Takt

| Quarz | Teil | Begründung |
|---|---|---|
| HSE 25 MHz | YXC X322525MOB4SI, 3225, CL 12 pF (LCSC **C9006, Basic** [V]) | wie die BlackPill; USB braucht einen Quarz |
| Lastkondensatoren HSE | 2 × 18 pF C0G [A]: C = 2 · (CL − Cstray), Cstray 3–5 pF angenommen | **[P]** am Muster Frequenz messen |
| LSE 32,768 kHz | **Seiko SC-32S, 7 pF**, 3215 (LCSC **C97604**, 152.555 Stück am 08.10.2026 [V]) | ST AN4488: für STM32F4 „strongly recommended CL ≤ 7 pF“ und „Never use a resonator with CL 12.5 pF“ [V]. Die üblichen 12,5-pF-Basic-Quarze (z. B. C32346) scheiden damit aus. |
| Lastkondensatoren LSE | 2 × 8,2 pF C0G [A]: 2 · (7 − ca. 3 pF) | **[P]** Anschwingen bei −20 °C und Gangabweichung der RTC prüfen. Die Firmware gleicht die Zeit zwar täglich ab, das Weckraster braucht trotzdem einen stabilen Quarz. |

Layout: Quarze direkt am Gehäuse, Masse darunter, keine Signale zwischen Quarz und Pin. PC14/PC15 nicht anderweitig nutzen [V: AN2867, AN4488].

### 1.3 USB-C (Aufspielen und Konsole)

- Buchse 16-polig, z. B. TYPE-C-31-M-12 (LCSC C165948, Extended [V]); eine Basic-Buchse ist nicht bekannt.
- CC1 und CC2 je 5,1 kΩ nach GND (USB-2.0-Gerät) [A, Type-C-Spezifikation].
- **ESD-Schutz USBLC6-2SC6** (LCSC C7519, Extended) an D+/D− (PA12/PA11).
- **VBUS → Schottky → Eingang des BQ25185**, parallel zu den Panels. So lädt der Logger am Tisch über USB, und USB speist nie zurück ins Panel [A].
- Bootloader: BOOT0-Taster gedrückt halten, Reset → DFU über USB. Ob der Bootloader des F411 mit 25-MHz-Quarz zuverlässig startet, ist in AN2606 für F411 nicht gelesen. Ein ST-Forumsbeitrag berichtet Probleme [V, Forum]. Die BlackPill macht es aber serienmäßig. **[P]** am Muster prüfen. **SWD bleibt der sichere Weg.**

### 1.4 Debug

- SWD-Stiftleiste 1,27 mm oder 2,54 mm: 3,3 V, SWDIO (PA13), SWCLK (PA14), NRST, GND
- Serial1 (PA9/PA10) auf derselben Leiste
- Firmware stellt auf „nur SWD“: Dann sind PA15, PB3, PB4 als normale Pins frei [A].

## 2. Funk Ai-Thinker Ra-01SH

### 2.1 Pinbelegung des Moduls [V: Ai-Thinker Ra-01SH Specification 2020-08-18, S. 11]

| Pin | Name | Anschluss |
|---|---|---|
| 1 | ANT | **offen lassen**, keine Leiterbahn (Antenne über IPEX, siehe 2.3) |
| 2, 9, 16 | GND | Massefläche |
| 3 | 3.3V | 3,3 V dauernd, mit Pufferung (2.2) |
| 4 | RESET | PB4 |
| 5 | TXEN | über Lötbrücke an PB14 (offen bestückt) |
| 6 | DIO1 | PA2 (Interrupt) |
| 7 | DIO2 | offen (steuert intern den HF-Schalter) |
| 8 | DIO3 | offen (kein TCXO) |
| 10 | BUSY | PA3 |
| 11 | RXEN | über Lötbrücke an PB15 (offen bestückt) |
| 12–15 | SCK / MISO / MOSI / NSS | PA5 / PA6 / PA7 / PA4 (SPI1), je **33 Ω** in Reihe (Datenblatt: 10–100 Ω) |

**TXEN/RXEN:** Ai-Thinker nennt sie nur „RF control port“. Nach einer Drittquelle (Bibliothek nopnop2002) schaltet beim Ra-01SH **DIO2** den HF-Schalter; TXEN/RXEN bleiben dort unbeschaltet [V, Drittquelle]. Weil das nicht vom Hersteller belegt ist, gehen beide über offene Lötbrücken an freie Pins. Funktioniert das Senden ohne sie nicht, werden die Brücken geschlossen und die Firmware steuert die Pins. Kein Umbau der Platine nötig.

### 2.2 Versorgung des Moduls

- 3,3 V dauernd (das Modul schläft mit 0,6 µA; ein Abschalten bringt fast nichts und kostet die Sitzungsdaten im Funkchip).
- **100 µF + 10 µF + 100 nF** direkt am Pin 3 [A]; Datenblatt: Spitzenstrom > 200 mA, Platz für Stützkondensator [V].
- ESD-Schutzdiode am 3,3-V-Eingang des Moduls (Datenblatt-Empfehlung [V]), z. B. eine 3,3-V-TVS in SOD-523 **[P] Teil wählen**.
- Das Modul arbeitet laut Drittquelle nur mit dem internen LDO, eine DC-DC-Spule ist nicht bestückt [V, Drittquelle; Herstellerschaltbild nicht lesbar]. Folge für die Energiebilanz: RX 8,8 mA, so bereits gerechnet.

### 2.3 Antenne (Entscheidung: IPEX im Gehäuse)

- Modul mit IPEX-Buchse, Stecker IPEX-1 (U.FL-kompatibel) [A, üblich; Datenblatt nennt nur „IPEX“].
- Ob ANT-Pad und IPEX parallel liegen, ist im Datenblatt-Text nicht beschrieben. Deshalb **Pin 1 ohne Leiterbahn** lassen: Ein offenes Leitungsstück an Pin 1 würde sonst die Antenne verstimmen [A].
- Antenne: **FPC-Klebeantenne 868 MHz mit 100 mm Kabel**. Beispiel Taoglas FXP280.07.0100A: 75 × 45 mm, 1,8 dBi, 52 % Wirkungsgrad, IPEX MHF1 [V, Taoglas-Datenblatt]. Kleinere generische FPC-Antennen sind möglich, haben aber meist weniger Gewinn [A].
- **Einbau** [V: Taoglas APN-14-8-001, Antenova]:
  - innen an eine **Seitenwand** des Gehäuses kleben, nicht über die Platine
  - mindestens 10 mm Abstand zur Massefläche, mindestens 15 mm zu Metall
  - weg vom Akku
  - Kabel nicht scharf knicken
- **Metalldach der Beute:** Metall in der Nähe verstimmt jede Antenne und kostet typisch 3–10 dB [V: Antenova]. Liegt der Logger unter einem Blechdeckel, schirmt dieser nach oben ab. **[P]** RSSI am Stand vergleichen, mit und ohne Deckel. Bei 5–8 m zum Gateway ist trotzdem Reserve da [A].

### 2.4 Funkchip SX1262 oder LLCC68

Ein RadioLib-Fall berichtet ein Ra-01SH, auf dessen Chip „LLCC68“ steht [V: RadioLib Issue #1405]. Der LLCC68 ist zum SX1262 weitgehend gleich, kann aber **kein SF11/SF12** (bei 125 kHz) [A, Semtech-Produktunterschied]. Für unseren Fall ist das unkritisch:
- Das Gateway steht 5–8 m entfernt; wir senden mit SF7.
- Der Zeitabgleich (DeviceTimeReq) läuft über normale Uplinks.

Folge für die Firmware: Chip beim Start abfragen und melden. **Nicht auf SF12 als Rückfall bauen.** **[P]** an den gelieferten Modulen den Chipaufdruck ansehen.

Einstellungen für RadioLib [A, aus der RadioLib-API; am Steckbrett bestätigen]:
- TCXO-Spannung 0 (Quarz statt TCXO)
- Regler LDO
- `setDio2AsRfSwitch(true)`
- Sendeleistung zunächst +14 dBm, später so niedrig wie möglich (ADR aus, fest einstellen)

## 3. Speicher

### 3.1 EEPROM für die LoRaWAN-Sitzung

| Punkt | Festlegung |
|---|---|
| Baustein | AT24C256C-SSHL-T, SOIC-8 (LCSC C6482, 62.566 Stück [V]) |
| Versorgung | **an der geschalteten Sensorschiene**. Die Daten bleiben ohne Strom erhalten; gelesen und geschrieben wird nur bei eingeschalteter Schiene. Damit gibt es auf dem I²C-Bus keinen Teilnehmer, der dauernd versorgt ist, während andere aus sind (Rückspeisung, versorgung.md 3.7). |
| Bus | I²C1 (PB6/PB7), Pull-ups **1,8 kΩ** an der geschalteten Schiene, Takt **50 kHz** wegen der BME280-Leitung (≤ 1 m, anschluesse.md 3.1); gemeinsam mit dem BME280 |
| Schreiblast | 96 Sitzungsstände pro Tag × 316 Byte. Die Firmware wechselt die Speicherplätze (versorgung.md, S2). **[P]** Schreibzyklen im Datenblatt (typ. 1 Mio.) gegen die Lebensdauer rechnen. |
| Nicht gewählt | FRAM MB85RC256V: 6- bis 12-mal teurer und „Not recommended for new designs“ [V: LCSC/JLCPCB] |

Backup-Register des STM32 (20 × 32 Bit) reichen für die Sitzung nicht. Backup-SRAM hat der F411 nicht [A].

### 3.2 Flash für Messwerte (fest eingeplant, Entscheidung 09.10.2026)

| Punkt | Festlegung |
|---|---|
| Zweck | alle Messwerte lokal speichern: Lücken bei Funkausfall schließen (später per USB auslesen oder nachsenden), Rohdaten der FFT für Auswertungen |
| Bauart | serieller NOR-Flash, **SOIC-8 208 mil**, Standard-Pinbelegung der 25er-Reihe (CS, DO, WP, GND / DI, CLK, HOLD, VCC), 2,7–3,6 V, JEDEC-Befehlssatz |
| Größe | **64 Mbit (8 MB)**. Ein Datensatz von 64 Byte alle 15 min sind etwa 6 KB pro Tag; 8 MB reichen für etwa 3,5 Jahre [A]. Ein Ringpuffer überschreibt danach die ältesten Werte. |
| Teil | **Wird bei der Bestellung nach Bestand gewählt.** Am 09.10.2026 waren bei LCSC **nicht lieferbar**: Winbond W25Q64JVSSIQ (C179171, C83140), W25Q128JVSIQ (C97521), Macronix MX25R6435F (C2802846). Gelistet: XTX XT25F64BSSIGU-S (C2890984, ab 0,52 $; Bestand nicht angezeigt) und Zetta ZD25Q64DSIGT (C55199021, 7.700 Stück) [V: LCSC-Seiten]. Alle haben dasselbe Gehäuse und dieselbe Pinbelegung; die Firmware erkennt den Typ an der JEDEC-ID. |
| Bus | **SPI1 gemeinsam mit dem Funkmodul**, eigener Chip-Select an **PB3** |
| Versorgung | **3,3 V dauernd**, im Ruhezustand im Deep Power-down. Grund: Der Bus ist mit dem Funkmodul gemeinsam. Ein unversorgter Flash würde über SCK/MOSI mitgespeist (Rückspeisung). Ruhestrom: Winbond 1 µA laut LCSC, Zetta 3 µA typ. [V]; gerechnet mit 1 µA. |
| CS-Pull-up | **100 kΩ nach 3,3 V an PB3**: Im Standby ist PB3 hochohmig, der Flash darf dann nicht ausgewählt sein [A]. Das gilt genauso für NSS des Funkmoduls (PA4). |
| WP, HOLD | über 10 kΩ an 3,3 V (nicht genutzt) |
| Haltbarkeit | ≥ 100.000 Lösch-/Schreibzyklen je Sektor, 20 Jahre Datenerhalt (Macronix-Datenblatt; übliche Werte der Reihe) [V/A] |

Das EEPROM für die LoRaWAN-Sitzung (3.1) bleibt. Es lässt sich byteweise schreiben, das ist für die Sitzungsdaten einfacher. Später kann die Sitzung auch in den Flash wandern; dann entfällt das EEPROM.

### 3.3 Bedienung ohne Öffnen: Magnet und Lichtsignal

Ohne Summer zeigt eine **LED** an, was der Logger tut. Entscheidung (Philipp, 09.10.2026): **Lichtleiter durch eine Bohrung in der Gehäusewand.**

Anordnung:
- Die Platine liegt waagerecht im Unterteil, die Wand steht senkrecht. Deshalb eine **seitlich abstrahlende SMD-LED** (Side-View, z. B. 0603/1206) direkt an der Platinenkante, Lichtaustritt zur Wand [A].
- **Lichtleiter waagerecht** von der LED durch die Bohrung nach außen.
- **Fertiger Wand-Lichtleiter mit Dichtung** (Entscheidung 09.10.2026). Kandidat: **Bivar PLTR2** (Linse 3 mm), starr, gerade, **IP67 mit Dichtung** (schwarz oder weiß), von außen eingepresst mit Gewinde-Halterung, Polycarbonat UL94 V-0, Längen 6,4–72 mm [V: Mouser-Seite „BIVAR PLTR IP67-Rated Rigid Light Pipes“]. Alternativ PLTR5 (Linse 5 mm, heller sichtbar).
  - Länge: Wand 3 mm + Abstand Wand bis Platinenkante ca. 15 mm (Platine 121 mm im Innenraum 152 mm) ≈ **18–20 mm** [A]; genau nach dem STEP-Modell.
  - **[P]** im Datenblatt PLTR2-XXX-PRX: Bohrungsdurchmesser, zulässige Wanddicke (wir haben ca. 3 mm PC), Temperaturbereich, UV-Beständigkeit; Bezug (Mouser/DigiKey), Preis.
  - Nicht gewählt: Mentor 1292/1282/1293 (IP68). Diese sind nur für 1 mm Frontplatte und −20 bis +50 °C angegeben [V: Mentor-Datenblatt].
- Kein Durchsteck-Lichtleiter mit Klebefuß auf der Platine: Die Platine ist verschraubt und die Toleranzen zur Wand sind zu groß [A].
- **Reedkontakt** auf derselben Kante, 10–20 mm neben der LED; außen eine Markierung „Magnet hier“.
- Schaltabstand Reedkontakt durch die Wand: **wird am Prototyp getestet** (Entscheidung 09.10.2026).
- **Höhe der Bohrung** = Domhöhe + 1,6 mm Platine + halbe LED-Höhe. Die Domhöhe kommt aus dem **STEP-Modell**. Camdenboss gibt es nur auf Anfrage heraus („STEP drawing request“ auf der Produktseite, Formular mit Kontaktdaten und Captcha; Philipp stellt die Anfrage).

| Vorgang | Lichtsignal (Vorschlag) |
|---|---|
| Magnet erkannt | LED leuchtet, solange der Magnet anliegt (Kontakt geschlossen) |
| **kurz** (unter 3 s) anlegen, dann wegnehmen | **Sofortmessung**: 1 × kurz beim Start; nach dem Senden 2 × kurz = gesendet, 1 × lang = Fehler |
| **lang** (über 5 s) anlegen | **Durchsicht ein/aus**. Beim beelogger heißt das „Service“: Gewichtssprünge in dieser Zeit sind Eingriffe des Imkers, kein Honig. |
| Durchsicht eingeschaltet | 3 × langsam als Bestätigung, dann alle 10 s ein kurzer Blitz, solange die Durchsicht läuft |
| Durchsicht ausgeschaltet | 1 × lang. Automatisch aus nach 2 h, falls man das Ausschalten vergisst [A]. |

Strom: Ein Blitz von 2 mA für 20 ms alle 10 s sind im Mittel 4 µA, nur während der Durchsicht [A]. Sonst bleibt die LED aus.

Rückmeldung zusätzlich über Funk: Die Sofortmessung und der Wechsel der Durchsicht gehen sofort als Datensatz raus. Sie sind dann in der beelogger-Ansicht bzw. in BEEP zu sehen.

## 4. Pinbelegung (Stand 0.4, ersetzt die Tabelle in LASTENHEFT.md)

| Pin | Funktion | Bemerkung |
|---|---|---|
| PA0 | Service-Taster und Reedkontakt parallel, Wecken (WKUP1) | Pull-down extern 100 kΩ |
| PA1 | Mikrofon (ADC1_IN1) | Abtastung per TIM2/TIM3-TRGO und DMA2 [V: ST HAL, F4-Familie; RM0383 Tab. 42 noch prüfen] |
| PA2 | Ra-01SH DIO1 | Interrupt |
| PA3 | Ra-01SH BUSY | |
| PA4–PA7 | Ra-01SH NSS, SCK, MISO, MOSI (SPI1, gemeinsam mit dem Flash) | je 33 Ω; NSS Pull-up 100 kΩ |
| PA8 | 1-Wire DS18B20 | Pull-up 4,7 kΩ an geschalteter Schiene, 1 kΩ in Reihe |
| PA9 / PA10 | Serial1 TX / RX | Debug-Leiste |
| PA11 / PA12 | USB D− / D+ | USBLC6 |
| PA13 / PA14 | SWDIO / SWCLK | Debug-Leiste |
| PA15 | frei (Erweiterung) | nach „nur SWD“ |
| PB0 | Akkuspannung (ADC1_IN8) | Teiler 2 × 2,2 MΩ + 100 nF |
| PB1 | Solarspannung (ADC1_IN9) | Teiler 3,3 MΩ / 1 MΩ |
| PB2 | BOOT1 | 10 kΩ nach GND |
| PB3 | Chip-Select SPI-Flash | Pull-up 100 kΩ; nach „nur SWD“ (3.2) |
| PB4 | Ra-01SH RESET | |
| PB5 | Sensorschiene ein (high = ein) | ON des TPS22917, Pull-down 100 kΩ (beim Rückfall AO3401A: low = ein, Pull-up 1 MΩ) |
| PB6 / PB7 | I²C1 SCL / SDA | EEPROM, BME280 (außen), Pull-ups an geschalteter Schiene |
| PB8 / PB9 | HX711 Nr. 1 DOUT / SCK | 1 kΩ in Reihe |
| PB10 | 5-V-Wandler der Waage ein (high = ein) | Pull-down 100 kΩ; siehe waage.md |
| PB12 / PB13 | frei (Erweiterung) | nur noch ein HX711 (09.10.2026) |
| PB14 / PB15 | Ra-01SH TXEN / RXEN | über offene Lötbrücken |
| PC13 | LED (low = an), am Platinenrand unter dem Lichtleiter | Signale siehe 3.3; Vorwiderstand ≥ 1 kΩ |
| PC14 / PC15 | LSE 32,768 kHz | |
| PH0 / PH1 | HSE 25 MHz | |

Frei für den Erweiterungsstecker (F9): PA15, PB12, PB13. PB11 gibt es beim UFQFPN-48 nicht [V].

## 5. Regeln für den Block

1. Jeder VDD-Pin bekommt seinen 100-nF-Kondensator direkt am Pin; VCAP_1 4,7 µF mit kleinem ESR.
2. LSE-Quarz mit **höchstens 7 pF** Lastkapazität.
3. Funkmodul an den Platinenrand, IPEX-Buchse zur Gehäusewand hin, **keine Leiterbahn an ANT**. Unter dem Modul durchgehende Masse; laut Datenblatt dürfen die Pads größer sein als die Modulpads [V].
4. Mikrofoneingang PA1 und VDDA weit weg von Funkmodul und SPI (Lastenheft A3).
5. Ungewisse Modulpins (TXEN/RXEN) über Lötbrücken an freie Pins führen, statt sich festzulegen.
6. Alles, was am I²C-Bus hängt, an derselben (geschalteten) Schiene.
7. SWD immer zugänglich, auch wenn USB-DFU vorgesehen ist.

## 6. Offene Prüfpunkte

1. Ra-01SH: Maßzeichnung (S. 10) und Pad-Layout (S. 13) liegen im Datenblatt nur als Bild vor. Footprint aus der LCSC/EasyEDA-Bibliothek (C2764087) nehmen und dagegen prüfen. Rastermaß vermutlich 2,0 mm.
2. Ra-01SH: Liegen IPEX und ANT-Pad parallel? (Foto oder Schaltbild am gelieferten Modul)
3. Ra-01SH: Chipaufdruck SX1262 oder LLCC68
4. RM0383: Tab. 42 (ADC-Auslöser) und Tab. 28 (DMA2) für den F411 bestätigen
5. AN2606: USB-Bootloader des F411 mit 25-MHz-Quarz
6. Lastkondensatoren HSE/LSE am Muster prüfen (Frequenz, Anschwingen in der Kälte)
7. TVS für den 3,3-V-Eingang des Moduls auswählen
8. FPC-Antenne: passende Größe für die Gehäusewand wählen (CBHUB-02: Innenhöhe 58,9 mm)

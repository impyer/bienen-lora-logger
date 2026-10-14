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
| VDDA/VREF+ (9) | 100 nF + 1 µF; über Ferrit (z. B. 600 Ω bei 100 MHz) an 3,3 V [A]. Ursprünglich für die Mikrofonmessung an PA1 (seit HW-07 Audio-ADC per I²S); für die Akku- und Solar-ADC-Messung weiter sinnvoll. ST schreibt den Ferrit nicht vor. |
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

### 1.3 USB-C (Aufspielen und Laden)

- Buchse 16-polig, z. B. TYPE-C-31-M-12 (LCSC C165948, Extended [V]); eine Basic-Buchse ist nicht bekannt.
- CC1 und CC2 je 5,1 kΩ nach GND (USB-2.0-Gerät) [A, Type-C-Spezifikation].
- **ESD-Schutz USBLC6-2SC6** (LCSC C7519, Extended) an D+/D− (PA12/PA11).
- **VBUS → Schottky → Eingang des BQ25185**, parallel zu den Panels. So lädt der Logger am Tisch über USB, und USB speist nie zurück ins Panel [A].
- Bootloader: BOOT0-Taster gedrückt halten, Reset → DFU über USB. Ob der Bootloader des F411 mit 25-MHz-Quarz zuverlässig startet, ist in AN2606 für F411 nicht gelesen. Ein ST-Forumsbeitrag berichtet Probleme [V, Forum]. Die BlackPill macht es aber serienmäßig. **[P]** am Muster prüfen. **SWD bleibt der sichere Weg.**

**USB-Rolle (SCH26-10) – entschieden: Laden, Aufspielen und Kommunikation (Philipp, 14.10.2026, HW-05; ersetzt Variante A „nur Laden und Aufspielen“ vom 10.10.2026, HW-01):**
- USB lädt (VBUS → D203 → BQ25185), dient zum **Aufspielen** (ROM-DFU über BOOT0 + Reset oder aus der Anwendung) und zur **Kommunikation** (USB-CDC als Service-Konsole, Auslesen des Flashs).
- **VBUS-Erkennung** nach ST AN4879 [V: AN4879, „VBUS sensing detection“]: Teiler **R307 33 kΩ / R308 82 kΩ** von VBUS an **PB13** (5-V-tolerant) → 5,0 V ergeben 3,57 V am Pin, 43 µA nur bei gestecktem Kabel [A, gerechnet]. Die Firmware schaltet USB-Peripherie und D+-Pull-up nur bei erkannter VBUS ein; ohne Kabel bleibt USB aus (Ruhestrom unverändert, USB-Spezifikation: kein Pull-up ohne VBUS).
- **Takt:** 48 MHz für USB aus der PLL (25 MHz HSE, z. B. PLLM 25, PLLN 192, PLLQ 4 → 48 MHz; SYSCLK 96 MHz mit PLLP 2) [A, nach RM0383 zu bestätigen].
- Folge: PB13 steht nicht mehr am Erweiterungsstecker zur Verfügung (J11/J704 Pin 11 frei).
- Service-Konsole über **Serial1 an J10/J302** und SWD bleiben als Rückfall.
- Prüfung am Muster (T4): Erkennung beim Stecken/Ziehen, CDC-Enumeration am PC, ROM-DFU mit 25-MHz-Quarz, Laden über USB, gesteckter USB ohne Einfluss auf den Ruhestrom nach dem Ziehen.

### 1.4 Debug

- Stiftleiste 2,54 mm 1 × 7 (J10, im Schaltplan J302): 1 3V3, 2 SWDIO (PA13), 3 SWCLK (PA14), 4 NRST, 5 GND, 6 TX1 (PA9), 7 RX1 (PA10). Führend ist die Tabelle in `anschluesse.md` 1.2; die Netzprüfung vergleicht sie mit dem Schaltplan (SCH26-09).
- Firmware stellt auf „nur SWD“: Dann sind PA15, PB3, PB4 als normale Pins frei [A]. **Pflicht seit HW-07:** PA15 ist I2S3_WS.

### 1.5 Auswahlprüfung: Alternativen, FPGA, externer RAM (13.10.2026, Entscheidung HW-04)

Anlass: Frage von Philipp, ob ein günstiger FPGA oder ein Mikrocontroller mit besserem Preis-Leistungs-Verhältnis sinnvoll wäre. Ergebnis: **STM32F411CEU6 bleibt, kein FPGA, kein externer RAM.**

**Bedarf** (aus `docs/fft-konzept.md`, `hardware/energiebilanz.py`): ADC 8192 Hz, FFT N = 512 mit Welch-Mittelung, ca. 41 KB RAM mit Mikrofon; dazu LoRaWAN-Stack (RadioLib), HX711, 1-Wire, I²C, SPI-Flash, USB-DFU und USB-CDC (HW-05), RTC mit LSE. Genauen RAM-/Flash-Bedarf des Gesamtprogramms nach dem ersten Build der Platinenfirmware nachtragen [P].

Preise JLCPCB/LCSC am 13.10.2026, 10 Stück, in US-Dollar [V: JLCPCB-Teilesuche]:

| MCU | Preis | Lager | Flash / RAM | Bewertung |
|---|---|---|---|---|
| **STM32F411CEU6 (gewählt)** | 4,96 | 474 | 512 K / 128 K | gleicher Chip wie BlackPill (Firmware dort entwickelbar), RAM-Reserve ca. 3 × |
| STM32L433CCU6 | 4,81 | 1619 | 256 K / 64 K | Standby mit RTC 280 nA [V: ST-Datenblatt], USB ohne HSE-Quarz; aber anderes Pinout, RAM knapp. **Ausweichoption bei Lieferproblemen** |
| STM32F401CCU6 | 7,39 | 1644 | 256 K / 64 K | teurer und schwächer |
| APM32F411CEU6 (Geehy) | 2,03 | 0 | 512 K / 128 K | als F411-Ersatz beworben, nicht lieferbar |
| AT32F403ACGU7 (Artery) | 2,68 | 1923 | 1 M / 224 K | andere Peripherie, schwächere Arduino-Unterstützung |
| GD32F303CCT6, CH32V203C8T6 | 1,22 / 0,72 | viel | ≤ 256 K / ≤ 48 K | DFU-Bootloader und Ruhestrom ungeprüft |
| STM32WLE5 (z. B. Wio-E5-Modul) | 7,58 | 6 | 256 K / 64 K | ersetzt MCU + Ra-01SH (zusammen ca. 8,90), aber **kein USB** (HW-05 entfiele), nach unserem Wissen ohne FPU [A], Neuentwurf → frühestens Version 2 |

- **Energie:** Der L433 spart im Ruhezustand ca. 2,3 µA ≈ 0,055 mAh/Tag, das sind 2 % der Last (2,81 mAh/Tag, Szenario B; seit HW-07 3,02 mAh/Tag) und wenig gegenüber der Selbstentladung (2,2–5,6 mAh/Tag). Kein Grund zum Wechsel.
- **FPGA:** Keine Aufgabe braucht hohe Datenraten oder parallele Kanäle; die FFT läuft auf dem M4F in Bruchteilen einer Sekunde. Günstigster Kandidat iCE40UP5K-SG48I 9,38 $ (doppelt so teuer wie die MCU) plus 1,2-V-Versorgung, Konfigurationsspeicher, zweite Toolchain und zusätzlicher Ruhestrom. Sinnvoll erst bei z. B. 4–8 synchron abgetasteten Mikrofonen (Schallortung), nicht im Lastenheft.
- **Externer RAM (SPI-PSRAM):** Der F411 im 48-Pin-Gehäuse hat kein QSPI/FSMC [A], PSRAM wäre nur per SPI-Befehlen nutzbar, zu langsam für die FFT und flüchtig (im Ruhezustand abschalten = Daten weg). Dauerhafte Daten liegen bereits im SPI-Flash U402 (8 MB). Wird RAM knapp, zuerst in der Firmware sparen: FFT in q15 statt float (halbe Puffer), blockweise Welch-Mittelung per DMA, ggf. N = 256.
- **Beschaffung:** F411 bei der JLCPCB-Bestellung reservieren (Lager 474).

## 2. Funk Ai-Thinker Ra-01SH

### 2.1 Pinbelegung des Moduls [V: Ai-Thinker Ra-01SH Specification 2020-08-18, S. 11]

| Pin | Name | Anschluss |
|---|---|---|
| 1 | ANT | **offen lassen**, keine Leiterbahn (Antenne über IPEX, siehe 2.3) |
| 2, 9, 16 | GND | Massefläche |
| 3 | 3.3V | 3,3 V dauernd, mit Pufferung (2.2) |
| 4 | RESET | PB4 |
| 5 | TXEN | im Modul **dasselbe Netz wie DIO2** (R8 0 Ω, Herstellerschaltbild); über offene Lötbrücke JP401 an PB14. PB14 **nie als Ausgang** (SCH26-11) |
| 6 | DIO1 | PA2 (Interrupt) |
| 7 | DIO2 | offen; steuert im Modul den HF-Schalter (Herstellerschaltbild), Firmware `setDio2AsRfSwitch(true)` |
| 8 | DIO3 | offen (kein TCXO) |
| 10 | BUSY | PA3 |
| 11 | RXEN | im Modul über R1 „NC/10K“ an /CTRL, in der Grundbestückung **nicht verbunden**; über offene Lötbrücke JP402 an PB15. PB15 nie als Ausgang |
| 12–15 | SCK / MISO / MOSI / NSS | PA5 / PA6 / PA7 / PA4 (SPI1), je **33 Ω** in Reihe (Datenblatt: 10–100 Ω) |

**HF-Schalter laut Herstellerschaltbild (SCH26-11, Stand 10.10.2026):** Das Datenblatt V1.1 enthält auf S. 12 das Schaltbild des Moduls als eingebettetes Bild. In voller Auflösung ist es lesbar [V: Ai-Thinker Ra-01SH Specification V1.1, Kap. 5]:
- **DIO2 → R8 0 Ω → TX_EN = Modulpin 5 (TXEN).** TXEN ist also kein Eingang, sondern derselbe Knoten wie DIO2.
- TX_EN → R6 10 kΩ → CTRL des Schalters U2 (SC70-6); TX_EN → R5 1 kΩ → NPN Q1, dessen Kollektor /CTRL treibt (R7 1 MΩ nach 3,3 V). Ein DIO2-Signal erzeugt beide Steuerpegel.
- Vermerk im Schaltbild: „DIO2 = 1 → RFC an RF1 (Senden); DIO2 = 0 → RFC an RF2 (Empfangen)“.
- **RXEN (Pin 11) → R1 „NC/10K“ → /CTRL**: in der Grundbestückung offen.
- Das Schwestermodul Ra-01SCH (LLCC68) beschreibt dasselbe im Text: Der HF-Schalter wird **standardmäßig von der Modulschaltung gesteuert**; für Steuerung durch einen externen Mikrocontroller ist eine **andere Bestückung** beim Hersteller anzufragen [V: Ai-Thinker Ra-01SCH 规格书 V1.1.0, 6.6].
- Drittquelle passt dazu: nopnop2002/esp-idf-sx126x (TXEN/RXEN „N/C“, DIO2 schaltet einen SC70-6-Schalter) [V, Drittquelle].
- Einschränkung: Das Schaltbild trägt beim Funkchip die Aufschrift „SX1268/X“; es ist offenbar dasselbe Blatt wie beim Ra-01S (433 MHz). Bauteilwerte der HF-Filter gelten daher nicht 1:1; die Schalterlogik ist für die Familie dieselbe [A]. Am gelieferten Modul mit Prüfplan 6.1 bestätigen.

**Folgen für unseren Schaltplan und die Firmware** (Modell `funk_modell.py`):
- JP401/JP402 **offen lassen** (Grundbestückung). RadioLib: `setDio2AsRfSwitch(true)`, **kein** `setRfSwitchPins`.
- Wird JP401 geschlossen, darf PB14 nur **Eingang** sein (zeigt dann „Senden aktiv“ an). Als Ausgang treibt PB14 gegen DIO2 (Modell: ca. 20 mA Querstrom [A]) – Gefahr für beide Pins.
- JP402/PB15 hat bei der Grundbestückung keine Wirkung. Bei einem Modul mit R1 = 10 kΩ würde ein PB15 low den Empfangsweg in einen undefinierten Zustand ziehen.
- Wird DIO2 in der Firmware nicht als HF-Schalter konfiguriert, bleibt der Schalter auf Empfang; gesendet wird dann nur über die Isolation des Schalters. Das Modell zeigt: Bei 5–8 m reicht das wahrscheinlich trotzdem für eine Verbindung – ein Fehler würde im Betrieb leicht übersehen.

### 2.2 Versorgung des Moduls

- 3,3 V dauernd (das Modul schläft mit 0,6 µA; ein Abschalten bringt fast nichts und kostet die Sitzungsdaten im Funkchip).
- **100 µF + 10 µF + 100 nF** direkt am Pin 3 [A]; Datenblatt: Spitzenstrom > 200 mA, Platz für Stützkondensator [V].
- ESD-Schutzdiode am 3,3-V-Eingang des Moduls (Datenblatt-Empfehlung [V]), z. B. eine 3,3-V-TVS in SOD-523 **[P] Teil wählen**.
- **Regler:** Das Herstellerschaltbild zeigt **L6 15 µH zwischen DCC_SW und VREG** und 470 nF an VREG – die Beschaltung für den DC-DC-Regler des SX126x; L7 (Brücke VDD_IN → VREG) ist „NC“ [V: Schaltbild V1.1]. Das Datenblatt nennt „minimum receiving current 4.2 mA“, was zum DC-DC-Betrieb passt [V]. Die frühere Drittquellen-Aussage „nur LDO“ ist damit widersprochen. Ob die Spule auf dem gelieferten Modul sitzt, prüft F-7 (6.1). Bis dahin rechnet die Energiebilanz weiter mit LDO (RX 8,8 mA, ungünstiger Fall); RadioLib zuerst mit LDO, nach F-7 auf DC-DC umstellen.

### 2.3 Antenne (Entscheidung: IPEX im Gehäuse)

- Modul mit IPEX-Buchse, Stecker IPEX-1 (U.FL-kompatibel) [A, üblich; Datenblatt nennt nur „IPEX“].
- **ANT-Pad und IPEX liegen parallel** am selben Netz RF_OUT hinter dem Ausgangsfilter [V: Herstellerschaltbild V1.1]. Deshalb **Pin 1 ohne Leiterbahn** lassen: Ein offenes Leitungsstück an Pin 1 wäre eine Stichleitung parallel zur Antenne und würde sie verstimmen [A]. Am Modul mit F-2 bestätigen.
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

Folge für die Firmware: Chip beim Start abfragen und melden. **Nicht auf SF12 als Rückfall bauen.** ADR so begrenzen, dass kein SF11/SF12 angefordert wird. Die SF12-Zeile in `energiebilanz.py` ist nur ein ungünstiger Vergleichsfall; mit einem LLCC68 gibt es diese Betriebsart nicht (HW26-14). **[P]** an den gelieferten Modulen den Chipaufdruck ansehen.

Einstellungen für RadioLib [A, aus der RadioLib-API; am Steckbrett bestätigen]:
- TCXO-Spannung 0 (Quarz statt TCXO)
- Regler zunächst LDO; nach F-7 DC-DC (2.2)
- `setDio2AsRfSwitch(true)`
- Sendeleistung zunächst +14 dBm, später so niedrig wie möglich (ADR aus, fest einstellen)

## 3. Speicher

### 3.1 LoRaWAN-Sitzung im SPI-Flash (HW26-10, Entscheidung Philipp 09.10.2026)

**Der EEPROM AT24C256 entfällt.** Er hing an der geschalteten Sensorschiene und am äußeren I²C-Bus. Ein Abschalten der Schiene oder ein Spannungseinbruch während des Schreibens hätte einen halben Sitzungsstand hinterlassen können (Review HW26-10). Der SPI-Flash (3.2) ist **dauernd versorgt** und hängt nicht am Außenbus.

| Punkt | Festlegung |
|---|---|
| Bereich | eigener Bereich von **64 KB (16 Sektoren zu 4 KB)** am Anfang des Flash, getrennt von den Messwerten |
| Datensatz | 512 Byte (2 Seiten): Kennung, **Generationszähler (32 Bit)**, Länge, Sitzung 302 Byte + Nonces 14 Byte, **CRC-32**, zuletzt ein **Gültig-Byte** |
| Schreibfolge | 1. Daten beider Seiten schreiben, 2. CRC zurücklesen und prüfen, 3. erst dann das Gültig-Byte von 0xFF auf 0x00 setzen (NOR darf Bits nachträglich von 1 auf 0 schreiben) [A] |
| Start | alle Datensätze lesen; der mit der **höchsten Generation, gültiger CRC und gesetztem Gültig-Byte** gilt. Ein unterbrochener Schreibvorgang fällt so auf den vorigen Stand zurück. |
| Ringpuffer | 8 Datensätze je Sektor. Gelöscht wird immer der Sektor **vor** dem Schreibzeiger; er enthält nur alte Stände. Der zuletzt gültige Stand liegt nie im gerade gelöschten Sektor. |
| Verschleiß | 96 Stände/Tag, 128 Plätze → jeder Sektor wird etwa alle 1,3 Tage gelöscht → 100.000 Zyklen reichen rechnerisch für über 300 Jahre [A, aus 100.000 Zyklen je Sektor] |
| Frame-Zähler | Fällt der Start auf einen älteren Stand zurück, wäre der Uplink-Zähler einmal doppelt. Deshalb **den Zähler beim Wiederherstellen um einen Sicherheitsabstand erhöhen** (z. B. +16). Bei ABP mit „Resets frame counters“ sind Sprünge nach vorn unkritisch [A]. **[P]** in der neuen Firmware umsetzen und testen. |
| Spannung | Geschrieben wird nur, wenn der Akku über 3,3 V liegt (Firmware-Stufen, versorgung.md 6). Eine Seite braucht etwa 1 ms; der 3,3-V-Regler hängt am Akku, nicht an der geschalteten Schiene [A]. |
| Prüfung am Muster **[P]** | Stromunterbrechung gezielt in jedem Schreibschritt (HiL): Danach muss der letzte vollständige Stand geladen werden, ohne Zählerverlust. |

Backup-Register des STM32 (20 × 32 Bit) reichen für die Sitzung nicht. Backup-SRAM hat der F411 nicht [A].

### 3.2 Flash für Messwerte (fest eingeplant, Entscheidung 09.10.2026)

| Punkt | Festlegung |
|---|---|
| Zweck | 1. **LoRaWAN-Sitzung** (3.1, 64 KB). 2. **Messwerte** als Ringpuffer: Lücken bei Funkausfall schließen, später über Serial1/SWD auslesen oder per Funk nachsenden (USB nur Laden/Aufspielen, 1.3). 3. **FFT-Rohdaten nur als einzelne Schnappschüsse** (auf Befehl oder bei Auffälligkeiten), nicht bei jeder Messung (HW26-12). |
| Bauart | serieller NOR-Flash, **SOIC-8 208 mil**, Standard-Pinbelegung der 25er-Reihe (CS, DO, WP, GND / DI, CLK, HOLD, VCC), 2,7–3,6 V, JEDEC-Befehlssatz |
| Größe | **64 Mbit (8 MB)**. Aufteilung [A]: 64 KB Sitzung, ca. 6 MB Messwerte, ca. 2 MB Rohdaten-Schnappschüsse. |
| Reichweite (HW26-12) | **Messwerte:** 64 Byte alle 15 min = 6 KB/Tag → 6 MB reichen für etwa **2,7 Jahre** [A]. **FFT-Rohdaten:** ein Schnappschuss sind 9.342 Werte × 2 Byte ≈ 18,7 KB. Bei jeder Messung wären das 1,8 MB/Tag, der ganze Flash wäre nach **4,7 Tagen** voll (Rechnung Review HW26-12, nachgeprüft). Deshalb nur Schnappschüsse: 2 MB fassen etwa **110**. Beide Bereiche sind Ringpuffer; die ältesten Daten werden überschrieben. |
| Teil | **Wird bei der Bestellung nach Bestand gewählt.** Am 09.10.2026 waren bei LCSC **nicht lieferbar**: Winbond W25Q64JVSSIQ (C179171, C83140), W25Q128JVSIQ (C97521), Macronix MX25R6435F (C2802846). Gelistet: XTX XT25F64BSSIGU-S (C2890984, ab 0,52 $; Bestand nicht angezeigt) und Zetta ZD25Q64DSIGT (C55199021, 7.700 Stück) [V: LCSC-Seiten]. Alle haben dasselbe Gehäuse und dieselbe Pinbelegung; die Firmware erkennt den Typ an der JEDEC-ID. |
| Bus | **SPI1 gemeinsam mit dem Funkmodul**, eigener Chip-Select an **PB3** |
| Versorgung | **3,3 V dauernd**, im Ruhezustand im Deep Power-down. Grund: Der Bus ist mit dem Funkmodul gemeinsam. Ein unversorgter Flash würde über SCK/MOSI mitgespeist (Rückspeisung). Ruhestrom: Winbond 1 µA laut LCSC, Zetta 3 µA typ. [V]; gerechnet mit 1 µA. |
| CS-Pull-up | **100 kΩ nach 3,3 V an PB3**: Im Standby ist PB3 hochohmig, der Flash darf dann nicht ausgewählt sein [A]. Das gilt genauso für NSS des Funkmoduls (PA4). |
| WP, HOLD | über 10 kΩ an 3,3 V (nicht genutzt) |
| Haltbarkeit | ≥ 100.000 Lösch-/Schreibzyklen je Sektor, 20 Jahre Datenerhalt (Macronix-Datenblatt; übliche Werte der Reihe) [V/A] |

Seit 09.10.2026 liegt auch die LoRaWAN-Sitzung im Flash (3.1); der EEPROM entfällt.

### 3.3 Bedienung ohne Öffnen: Magnet und Lichtsignal

Ohne Summer zeigt eine **LED** an, was der Logger tut. Entscheidung (Philipp, 09.10.2026): **Lichtleiter durch eine Bohrung in der Gehäusewand.**

Anordnung:
- Die Platine liegt waagerecht im Unterteil, die Wand steht senkrecht. Deshalb eine **seitlich abstrahlende SMD-LED** direkt an der Platinenkante, Lichtaustritt zur Wand [A]. **Gewählt (13.10.2026): Lite-On LTST-S220KGKT** (grün, AlInGaP, 2,15 × 1,0 mm, LCSC C160469, Bestand 39.801) [V: Lite-On DS22-2000-075]; mit 1 kΩ ca. 1,3 mA – Sichtbarkeit durch den Lichtleiter am Muster prüfen, ggf. kleineren Widerstand [P].
- **Lichtleiter waagerecht** von der LED durch die Bohrung nach außen.
- **Fertiger Wand-Lichtleiter mit Dichtung** (Entscheidung 09.10.2026). Kandidat: **Bivar PLTR2** (Linse 3 mm), starr, gerade, **IP67 mit Dichtung** (schwarz oder weiß), von außen eingepresst mit Gewinde-Halterung, Polycarbonat UL94 V-0, Längen 6,4–72 mm [V: Mouser-Seite „BIVAR PLTR IP67-Rated Rigid Light Pipes“]. Alternativ PLTR5 (Linse 5 mm, heller sichtbar).
  - Länge aus dem STEP (13.10.2026): LED-Front ca. 0,7 mm innerhalb der Platinenkante + 16,2 mm bis zur Innenwand + Wand 2,5 mm ≈ **19,4 mm** von der LED bis zur Außenfläche [V: STEP + Layout]; passende PLTR-Länge wählen [P].
  - **[P]** im Datenblatt PLTR2-XXX-PRX: Bohrungsdurchmesser, zulässige Wanddicke (laut STEP 2,5 mm PC), Temperaturbereich, UV-Beständigkeit; Bezug (Mouser/DigiKey), Preis.
  - Nicht gewählt: Mentor 1292/1282/1293 (IP68). Diese sind nur für 1 mm Frontplatte und −20 bis +50 °C angegeben [V: Mentor-Datenblatt].
- Kein Durchsteck-Lichtleiter mit Klebefuß auf der Platine: Die Platine ist verschraubt und die Toleranzen zur Wand sind zu groß [A].
- **Reedkontakt** auf derselben Kante, 10–20 mm neben der LED; außen eine Markierung „Magnet hier“. **Gewählt (13.10.2026): MiRelay MRS03-B-3** (vergossen, SMD mit J-Anschlüssen, 8,5 × 2,1 × 2,4 mm, Empfindlichkeit 10–15 AT, LCSC C41432613, Bestand 2051) [V: MiRelay-Datenblatt]; Längsachse parallel zur Kante, Magnet längs der Kante führen. Lötprofil laut Datenblatt max. 260 °C / 5 s.
- Schaltabstand Reedkontakt durch die Wand: **wird am Prototyp getestet** (Entscheidung 09.10.2026).
- **Höhe der Bohrung** (STEP, 13.10.2026): Platinenoberseite 23,2 mm unter der Außenfläche des Bodens (Dom 9,1 + Hülse 10 + Platine 1,6 + Boden 2,5 mm). Mit der Lichtmitte der LED ca. 0,5 mm über der Platine [A] liegt die **Bohrungsmitte ca. 22,7 mm von der Außenfläche des Bodens** (bzw. ca. 44,6 mm von der offenen Kante des Unterteils). Seitlich: LED 8 mm links der Wandmitte, Reedkontakt 8 mm rechts davon (Grobplatzierung). Am ersten Muster bestätigen [P].

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
| PA1 | Sensorschiene ein (high = ein) | ON des TPS22917, Pull-down 100 kΩ (HW-07, vorher PB5; Mikrofon-ADC entfällt) |
| PA2 | Ra-01SH DIO1 | Interrupt |
| PA3 | Ra-01SH BUSY | |
| PA4–PA7 | Ra-01SH NSS, SCK, MISO, MOSI (SPI1, gemeinsam mit dem Flash) | je 33 Ω; NSS Pull-up 100 kΩ |
| PA8 | 1-Wire DS18B20 | Pull-up 4,7 kΩ an geschalteter Schiene, 1 kΩ in Reihe |
| PA9 / PA10 | Serial1 TX / RX | Debug-Leiste |
| PA11 / PA12 | USB D− / D+ | USBLC6 |
| PA13 / PA14 | SWDIO / SWCLK | Debug-Leiste |
| PA15 | I2S3_WS zum Audio-ADC U601 (HW-07) | nach „nur SWD“; AF laut ST-Pindaten [V] |
| PB0 | Akkuspannung (ADC1_IN8) | Teiler 2 × 2,2 MΩ + 100 nF |
| PB1 | Eingangsspannung Lader (ADC1_IN9) | Teiler 3,3 MΩ / 470 kΩ + 100 nF hinter den Schottky-Dioden (versorgung.md 3.1, HW26-08) |
| PB2 | BOOT1 | 10 kΩ nach GND |
| PB3 | Chip-Select SPI-Flash | Pull-up 100 kΩ; nach „nur SWD“ (3.2) |
| PB4 | Ra-01SH RESET | |
| PB5 | I2S3_SD vom Audio-ADC U601 (HW-07) | Empfang mit DMA; vorher Sensorschiene (jetzt PA1) |
| PB6 / PB7 | I²C1 SCL / SDA | BME280 (außen) und Erweiterungsstecker, Pull-ups 1,8 kΩ an geschalteter Schiene, 50 kHz |
| PB8 / PB9 | HX711 Nr. 1 DOUT / SCK | 1 kΩ in Reihe |
| PB10 | 5-V-Wandler der Waage ein (high = ein) | Pull-down 100 kΩ; siehe waage.md |
| PB12 | I2S3_CK zum Audio-ADC U601 (HW-07) | STM32 ist I²S-Master; AF laut ST-Pindaten [V] |
| PB13 | VBUS-Erkennung (HW-05) | Teiler 33 kΩ / 82 kΩ von VBUS (AN4879) |
| PB14 / PB15 | Ra-01SH TXEN / RXEN | über offene Lötbrücken |
| PC13 | LED (low = an), am Platinenrand unter dem Lichtleiter | Signale siehe 3.3; Vorwiderstand ≥ 1 kΩ |
| PC14 / PC15 | LSE 32,768 kHz | |
| PH0 / PH1 | HSE 25 MHz | |

Frei für den Erweiterungsstecker (F9): keine GPIOs mehr (PB13 seit HW-05 VBUS-Erkennung, PA15/PB12 seit HW-07 I²S). PB11 gibt es beim UFQFPN-48 nicht [V]. Rückfall der Sensorschiene auf AO3401A: dann PA1 low = ein, Pull-up 1 MΩ.

## 5. Regeln für den Block

1. Jeder VDD-Pin bekommt seinen 100-nF-Kondensator direkt am Pin; VCAP_1 4,7 µF mit kleinem ESR.
2. LSE-Quarz mit **höchstens 7 pF** Lastkapazität.
3. Funkmodul an den Platinenrand, IPEX-Buchse zur Gehäusewand hin, **keine Leiterbahn an ANT**. Grobplatzierung: Oberkante mittig, Pin-1-Seite (ANT) zur Kante; dass die IPEX-Buchse nahe Pin 1 sitzt, ist angenommen **[A]**, am gelieferten Modul prüfen. Unter dem Modul durchgehende Masse; laut Datenblatt dürfen die Pads größer sein als die Modulpads [V].
4. Audio-ADC U601 und I²S-Leitungen weit weg von Funkmodul und SPI (Lastenheft A3).
5. Ungewisse Modulpins (TXEN/RXEN) über Lötbrücken an freie Pins führen, statt sich festzulegen. Die zugehörigen MCU-Pins (PB14/PB15) bleiben in der Firmware **Eingänge** (2.1).
6. Alles, was am I²C-Bus hängt, an derselben (geschalteten) Schiene.
7. SWD immer zugänglich, auch wenn USB-DFU vorgesehen ist.

## 6. Offene Prüfpunkte

1. Ra-01SH: Maßzeichnung (S. 10) und Pad-Layout (S. 13) liegen im Datenblatt nur als Bild vor. Footprint aus der LCSC/EasyEDA-Bibliothek (C2764087) nehmen und dagegen prüfen. Rastermaß vermutlich 2,0 mm.
2. ~~Ra-01SH: Liegen IPEX und ANT-Pad parallel?~~ Laut Herstellerschaltbild ja (2.3); am Modul mit F-2 bestätigen
3. Ra-01SH: Chipaufdruck SX1262 oder LLCC68
4. RM0383: Tab. 42 (ADC-Auslöser) und Tab. 28 (DMA2) für den F411 bestätigen
5. AN2606: USB-Bootloader des F411 mit 25-MHz-Quarz
6. Lastkondensatoren HSE/LSE am Muster prüfen (Frequenz, Anschwingen in der Kälte)
7. TVS für den 3,3-V-Eingang des Moduls auswählen
8. FPC-Antenne: passende Größe für die Gehäusewand wählen (CBHUB-02: Innenhöhe 58,9 mm)

### 6.1 Prüfplan Funkmodul am Steckbrett (SCH26-11, T4, durch Philipp)

Aufbau: BlackPill + Ra-01SH aus der Lieferung für die Platine, FPC-Antenne an IPEX, 3,3 V aus Labornetzteil mit Strombegrenzung 300 mA, Gateway RAK7268V2 in 5–8 m. Ergebnisse als Prüfbericht mit Fotos und Messwerten eintragen; nichts als gemessen eintragen, was nicht gemessen wurde. Erwartungswerte aus dem Herstellerschaltbild (2.1) und dem Modell `funk_modell.py`.

| Test | Durchführung | Erwartung nach Schaltbild | Entscheidung |
|---|---|---|---|
| F-1 Chip | Aufdruck/Händlerangabe, Foto; Firmware liest das Chip-Register (RadioLib meldet SX1262 oder LLCC68) | SX1262 (Ra-01SH) | bei LLCC68: kein SF11/12 (2.4) |
| F-2 stromlos | Widerstand messen: TXEN↔DIO2, RXEN↔DIO2, RXEN↔GND, ANT-Pad↔IPEX-Innenleiter | TXEN↔DIO2 ≈ 0 Ω; RXEN ohne Verbindung (oder ca. 10 kΩ-Variante); ANT↔IPEX ≈ 0 Ω | Abweichung = andere Modulvariante → Schaltplan prüfen |
| F-3 Pegel | RadioLib `setDio2AsRfSwitch(true)`, JP offen: Spannung an TXEN messen bei Dauerträger (`transmitDirect`) und bei Empfang (`startReceive`) | Senden ≈ 3,3 V, Empfang ≈ 0 V | Hauptnachweis der Schalterlogik |
| F-4 Senden | Uplinks bei **−9 dBm** (kleinste Leistung, damit der Unterschied sichtbar wird), RSSI/SNR in TTN gegen den RFM95-Musterlogger am selben Platz mit gleicher Leistung (RFM95: kleinste einstellbare Leistung, Unterschied notieren); einmal mit `setDio2AsRfSwitch(false)` als Gegenprobe, **nur wenige kurze Pakete** | richtig: RSSI im Bereich des Musterloggers; Gegenprobe deutlich schwächer (Modell: 20–35 dB [A]) | „Verbindung geht“ allein reicht nicht (Modell Teil 2) |
| F-5 Empfangen | Downlink bzw. DeviceTimeAns (RX1/RX2) | Antwort kommt an | – |
| F-6 nur bei Fehlschlag | Ursache mit F-2/F-3 eingrenzen. **PB14/PB15 nicht als Ausgang** schalten, solange TXEN = DIO2 (Querstrom, `funk_modell.py` K4) | – | Hersteller fragen / andere Modulbestückung |
| F-7 Regler | Empfangsstrom am Netzteil: RadioLib mit LDO, dann mit DC-DC (`setRegulatorDCDC`), je `startReceive` | DC-DC deutlich unter LDO (Datenblatt: RX min 4,2 mA) | DC-DC in der Firmware nutzen; Energiebilanz anpassen |

Hinweise: Senden mit falsch stehendem Schalter gibt die Leistung auf einen nicht angeschlossenen Schalterzweig; die Gegenprobe in F-4 deshalb nur kurz und mit kleiner Leistung [A]. Entscheidung danach im Befundregister (SCH26-11).

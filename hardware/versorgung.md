# Versorgung der Logger-Platine (Lastenheft 0.4, Abschnitt 3 – Entwurf, 08.10.2026)

Bezug: Befunde HW26-01 bis HW26-04 (`docs/testberichte/2026-10-08-hardware-architektur-review.md`).

Kennzeichnung:
- **[V]** = im Datenblatt gelesen
- **[A]** = Annahme oder Rechnung
- **[P]** = vor dem Schaltplan bzw. am Muster prüfen

Die Rechnung zur Energiebilanz ist reproduzierbar: `python3 hardware/energiebilanz.py`.

## 1. Ergebnis in Kürze

| Frage | Ergebnis |
|---|---|
| Reicht die Energie im Winter? | **Ja, mit großer Reserve.** Bedarf rund 5–18 mAh/Tag (eine 5-V-Waage). Reichweite ohne jedes Laden 128–454 Tage, je nach Firmware, Funk und Selbstentladung. Der Dezemberertrag der Panels liegt bei grob dem 38-Fachen des Bedarfs. |
| Was ist kritisch? | 1. Laden **unter 0 °C** muss gesperrt sein. 2. **Tiefentladeschutz** in Hardware. 3. **Leerlaufspannung** der Panels bei Kälte (bis etwa 9–10 V). 4. Ein Kurzschluss im **Akkukabel**. |
| Laderegler | **BQ25185** (TI) statt CN3065. Der CN3065 verträgt nur 6,5 V am Eingang und hat nur eine Temperaturschwelle; bei LCSC ist er zurzeit nicht lieferbar. |
| Tiefentladeschutz | **zweistufig in Hardware**, dazu Stufen in der Firmware (Abschnitt 4) |
| 3,3 V | **RT9080-33**: 600 mA, 2 µA Ruhestrom |
| Größte Verbraucher | **aktive Zeit des Mikrocontrollers** und die **Waage** (5-V-Wandler mit 404-Ω-Brücke, ca. 35 mAs je Messung), danach die Selbstentladung der Zelle. Funk und übrige Sensoren sind klein. |

## 2. Blockschaltbild

```
 Panel 1 ─┬─ Schottky ─┐
 Panel 2 ─┴─ Schottky ─┴─┬─ TVS 12 V ─┬─ Teiler 3,3 MΩ/470 kΩ + 100 nF → ADC PB1 (Eingangsspannung Lader)
                          │            │
                          └─► BQ25185 IN
                                 │ SYS (bei Sonne 4,5 V, sonst = Akku) ──┬─► RT9080 3,3 V ──┬─► STM32, Ra-01SH, SPI-Flash
                                 │ BAT                                   │                  └─► TPS22917 ─► Sensorschiene 3,3 V
                                 │                                       │                       (HX711-DVDD, DS18B20, BME280,
                                 │                                       │                        Mikrofon, Pull-ups)
     Zelle + Schutz (Blatt Akku) │                                       └─► TPS61240 5 V (EN = PB10, nur beim Wiegen)
                                 │                                            └─► Filter ─► HX711 VSUP → AVDD 4,3 V → H40A
       ┌─────────────────────────┴───┐
       │ Stecker ─ HY2111 + 8205 ─ Zelle 18650 │    NTC 10 k an der Zelle → TS des BQ25185 (2. Stufe)
       │ 2 × TMP390 + N-FET an der Zelle ──────│──► CE_FREI → CE (Stufe 1) / NTC-Fuß (Stufe 2), versorgt aus TMP_VCC
       VIN_LADER → TPS70933 → TMP_VCC 3,3 V (nur bei Sonne/USB) ──► Ladesperre (Blatt Akku)
       │ (Verpolschutz, Strommessbrücke)       │
       └───────────────────────────────┘
 Akkuspannung: Teiler 2 × 2,2 MΩ + 100 nF → ADC; VREFINT zur Korrektur
```

## 3. Bauteile

### 3.1 Solar-Eingang

| Punkt | Festlegung | Begründung |
|---|---|---|
| Panels | 2 × „6 V“, parallel, Typ Spacnana (Hilitand7fhbtxkcwg). **Elektrische Daten unbekannt**; Messung ist zurzeit nicht möglich (Philipp, 08.10.2026). | Messung später nachholen; die Auslegung kommt ohne sie aus. |
| Leerlaufspannung kalt | **Auslegung auf bis 12 V Dauer** [A] | Voc steigt um etwa 0,34 %/K. Ein Panel mit 7,2–8,7 V bei 25 °C hat bei −20 °C 8,3–10 V; 12 V lässt Reserve für unbekannte Panels mit mehr Zellen. Der BQ25185 arbeitet bis 18 V. |
| Je Panel eine Schottky-Diode | z. B. SS34 [P] (LCSC/Basic prüfen) | Kein Rückstrom von einem Panel ins andere; Verpolschutz am Panel |
| Eingangskondensator | C201 4,7 µF **50 V** X7R 1206 (SCH26-08): 25 V Absolutgrenze plus DC-Bias-Reserve | wirksam bleiben bei 12 V noch deutlich über 1 µF [A, Hersteller-Kurve prüfen] |
| TVS-Diode am Eingang | SMAJ12A (Sperrspannung 12 V) [P] | Begrenzt Störungen auf dem langen Panelkabel unter die 25 V Absolutgrenze des BQ25185 |
| Messung Solarspannung (HW26-08, geändert 09.10.2026) | Teiler **3,3 MΩ / 470 kΩ** + 100 nF am ADC-Knoten, **hinter** den Schottky-Dioden am Eingang IN des BQ25185 | Faktor 0,1247: 12 V → 1,50 V, 18 V → 2,24 V, **25 V (Absolutgrenze BQ25185) → 3,12 V**, also immer unter 3,3 V; der ADC-Pin braucht keine Klemmdiode. Gemessen wird die **Eingangsspannung des Laders**: das stärkere Panel minus Diodenspannung, bei angestecktem USB die VBUS-Spannung minus Diode (Firmware erkennt USB am VBUS-Teiler, mcu-funk.md 1.3). Nachts 0 V. Der Teiler belastet nur die Quelle (3,2 µA bei 12 V), nicht den Akku. Der 100-nF-Kondensator liefert die Ladung für die Abtastung; Abtastzeit lang wählen (480 Takte) [A]. Unversorgter ADC (SCH26-08): kommt praktisch nicht vor, weil +3V3 über SYS aus VIN versorgt wird, sobald dort Spannung liegt; selbst dann begrenzt 3,3 MΩ den Strom bei 25 V auf unter 8 µA (STM32 erlaubt ±5 mA Einspeisung [A, ST-Datenblatt prüfen]). **[P]** am Muster bei 0, 6, 12 V prüfen. |

### 3.2 Laderegler BQ25185 (LCSC C19725033, Extended) [V: TI-Datenblatt]

| Merkmal | Wert | Bedeutung für uns |
|---|---|---|
| Eingang | Betrieb 3,0–18 V, Absolutgrenze 25 V, Überspannungsabschaltung bei 18,5 V | Panelspannung bis 10 V ist unkritisch; keine Z-Diode nötig wie beim beelogger |
| Schwache Quelle | VINDPM: Ladestrom wird reduziert, damit der Eingang nicht unter Akku + 0,33 V fällt | Das Panel bricht nicht zusammen. Es ist **kein MPPT**; das Panel arbeitet bei etwa 4,4 V statt etwa 6 V. Der Verlust (grob 25 %) ist bei 40-facher Reserve ohne Bedeutung. |
| Ladeschluss | per Widerstand: u. a. 4,05 / 4,1 / 4,2 V | **4,1 V wählen** [A]: Die Zelle steht dauernd voll und warm im Sommer; das schont sie. Kostet grob 10 % Kapazität. |
| Ladestrom (HW26-11, geändert 09.10.2026) | ICHG = 300 AΩ ÷ RISET, 5–1000 mA | **150 mA** mit RISET = 2,0 kΩ. Begründung Wärme siehe 3.2a. Der Bedarf liegt bei 2,4–5,5 mAh je Tag; schon eine Stunde mit 150 mA bringt das 30-Fache. |
| Systemausgang SYS | bei Sonne 4,5 V geregelt; ohne Sonne über den Akkuschalter (115 mΩ) = Akkuspannung | Der LDO hängt an SYS. Bei Sonne versorgt das Panel den Logger direkt. |
| **Akku-Unterspannung** | BUVLO 3,0 V fallend, Hysterese 0,11–0,19 V: trennt den Akku von SYS | **Erste Hardware-Stufe des Tiefentladeschutzes** |
| Überstrom Akku | 3,13 A, Hiccup | zusätzlicher Schutz |
| Temperatur (TS) | für 10-kΩ-NTC, B = 3435 K. Kalt: 1,0075 V steigend, Heiß: 0,115 V fallend. Laden außerhalb gesperrt. **TS/MR ist zugleich Reset-Eingang:** länger auf Low gezogen, geht der Baustein in den Werksmodus („factory mode“, Akku getrennt) [V: TI-Datenblatt, Pinbeschreibung]. TS also nie aktiv auf Masse ziehen. | siehe 3.3 |
| Laden ein/aus (CE) | **CE aktiv Low**: Low = Laden erlaubt, High = gesperrt; VIH 1,3 V, VIL 0,4 V [V] | Eingang für die externe Temperatursperre (3.3) |
| Ruhestrom aus dem Akku | 4 µA typ., 5 µA max. (ohne Eingang) | in der Bilanz enthalten |
| Gehäuse | WSON-10, 2,2 × 2 mm, Thermal-Pad | JLCPCB bestückt das; Handlöten ist schwer |

### 3.2a Wärme im Laderegler (HW26-11)

Der BQ25185 ist ein **Linearregler**: Die Differenz zwischen Eingang und Akku wird im IC zu Wärme.

- P ≈ (V_IN − V_BAT) × I_CHG + (V_IN − V_SYS) × I_SYS. Die Systemlast ist klein (ca. 1 mA im Mittel) und hier vernachlässigt.
- RθJA = **68,3 K/W** nach JEDEC-Platine [V: TI-Datenblatt]. Unsere 4-Lagen-Platine mit Massefläche unter dem Pad ist eher besser [A].
- **Thermische Regelung bei 100 °C** Sperrschicht (TREG typ.) [V]: Wird es heißer, senkt der IC den Ladestrom selbst. Das ist kein Sicherheitsproblem, kostet aber Ladung.

| Fall | V_IN − V_BAT | 300 mA | **150 mA (gewählt)** |
|---|---|---|---|
| „6-V“-Panel unter Last, Akku 3,5 V | 6,5 − 3,5 = 3,0 V | 0,90 W → +61 K | 0,45 W → +31 K |
| Panel mit 12 V unter Last (Auslegungsgrenze, unbekanntes Panel) | 12 − 3,5 = 8,5 V | 2,55 W → TREG greift | 1,28 W → +87 K, TREG greift |
| Rechenfall aus dem Review (10 V, 4,1 V) | 5,9 V | 1,77 W | 0,89 W → +60 K |

Bei **50 °C im Gehäuse** und 150 mA bleibt das „6-V“-Panel bei etwa 81 °C Sperrschicht, unter TREG. Mit 300 mA würde der IC schon heute regeln. Die Leerlaufspannung (bis 12 V) tritt nur ohne Strom auf und erzeugt keine Wärme [A].

Regeln:
- Ladestrom 150 mA.
- Der Laderegler sitzt **nicht** neben der Zelle (seit HW-06 liegt die Zelle auf der Hauptplatine: Abstand halten), Thermal-Pad mit Durchkontaktierungen auf L2: Das Pad misst nur 0,9 × 1,5 mm; TI zeigt im Layoutbeispiel 2 Vias Ø 0,2 mm, verfüllt oder abgedeckt (DLH0010A, 4226298/A). Die früher genannten 6–9 Vias passen nicht auf das Pad (REG26-08, 13.10.2026). Bei 150 mA Ladestrom reicht das [A]; Via-in-Pad bei JLCPCB im Angebot prüfen [P].
- **[P]** Am Muster bei Sonne die Gehäusetemperatur am IC messen.

**Eingangsbereich geklärt:** Die TI-Produktseite nennt „3.0V to 18V input voltage operating range“, „25V tolerant input voltage“ und „solar input support“ [V, ti.com/product/BQ25185, 08.10.2026]. Die abweichende Zeile „2,7–5,5 V“ in der Empfehlungstabelle des Datenblatts widerspricht dem. Ich halte sie für einen Fehler im Datenblatt, belegt ist das nicht. Maßgeblich für uns sind die Betriebsdaten 3,6–18 V und die Produktseite.

**Ersatz, falls der BQ25185 ausscheidet:**
- BQ25170: hat einen NTC-Eingang mit 0 °C und 45 °C, aber eine Überspannungsabschaltung bei 6,75 V. Er bräuchte also eine Eingangsbegrenzung.
- CN3791: echtes MPPT bis 28 V, aber kein NTC-Eingang. Die Kältesperre müsste man extern bauen.

### 3.3 Temperatursperre beim Laden (HW26-07, neu 09.10.2026)

**Grenzen der Zelle:**
- Händlerangabe für die BAK N18650CP: Laden **0 bis +45 °C** [V: keeppower.com.cn].
- BAK-Datenblatt N18650CP-34E: Laden **0 bis 55 °C**, Zelloberfläche [V: bakpower.com, Datenblatt 34E].
- Welche Variante gekauft ist, steht noch nicht fest (Philipp, 09.10.2026). **Auslegung daher auf 45 °C.**

**Problem mit dem BQ25185 allein:** Seine TS-Schwellen sind fest [V: TI-Datenblatt]. Mit einem 10-kΩ-NTC (B 3435) und dem Messstrom 38 µA ergeben sich die Werte unten.

| Schwelle | Spannung | NTC-Widerstand | Temperatur |
|---|---|---|---|
| Kalt (Laden aus) | 1,0075 V | 26,5 kΩ | ca. +1,7 °C |
| Kalt (Laden wieder ein) | 0,820 V | 21,6 kΩ | ca. +6,3 °C |
| Heiß (Laden aus) | 0,115 V | 3,0 kΩ | **ca. +59,5 °C** |
| Heiß (Laden wieder ein) | 0,135 V | 3,6 kΩ | ca. +54,4 °C |

- Die Heißsperre liegt **über beiden Zellgrenzen** (45 bzw. 55 °C).
- Mit Vor- oder Parallelwiderständen lässt sie sich nicht auf 45 °C bringen, ohne die Kältesperre zu verlieren. TI bestätigt das im E2E-Forum: dafür bräuchte es einen NTC mit unrealistisch großem B-Wert [V: TI E2E 1472003]. Eigene Rechnung dazu: Ein Fenster 0–45 °C verlangt ein Widerstandsverhältnis von 8,75; der NTC liefert nur 5,9 [A].

**Lösung (Entscheidungen Philipp, 09.10.2026): zweistufige Sperre, beide Stufen ≤ 45 °C**

Versorgung der Sperre (geändert nach Schaltplan-Review SCH26-01):
- Beide Temperaturschalter, alle Gate-Pull-ups und der CE-Pull-up hängen an **TMP_VCC = 3,3 V aus einem LDO TPS70933 am Ladereingang** (VIN_LADER, 2,7–30 V, 1 µA) [V: TI SBVS186H].
- TMP_VCC gibt es nur bei Sonne oder USB, also genau dann, wenn geladen werden kann.
- Grund: In der ersten Fassung hing der TMP390 an P+/P− hinter dem Zellschutz. Nach einer Tiefentladung trennt der HY2111 den Entlade-FET; P− ist dann von der Zelle getrennt, der TMP390 ohne Versorgung, Q2 sperrt, CE bleibt High. Der HY2111-GB gibt die Zelle aber **nur durch einen Ladevorgang** wieder frei [V: HYCON-Datenblatt 11.3.1]. Ergebnis wäre ein Stillstand gewesen: ohne Laden keine Freigabe, ohne Freigabe kein Laden. ChatGPT hat das gefunden; die Rechnung bestätigt es.
- Nebeneffekt: Nachts zieht die Sperre **keinen Strom aus der Zelle** (vorher 0,9 µA).
- Es gibt keine Verbindung der Sperre zu B+/B−. Ein Pfad am Zellschutz vorbei ist ausgeschlossen; die Netzprüfung (`hardware/kicad/werkzeug/netz_tests.py`) prüft das.

1. **Stufe 1, TMP390 U2 → CE des BQ25185**
   - TMP390 (TI): zwei Schwellen über je einen Widerstand; heiß 30–124 °C in 2-°C-Schritten (OUTA), kalt −50 … +25 °C in 5-°C-Schritten (OUTB); Ausgänge **Open-Drain, aktiv Low**, Leckstrom ±0,1 µA; 0,5 µA; Genauigkeit A2 ±1,5 °C von 0 bis 70 °C bei 2,5–5,5 V [V: TI SBOS904A].
   - **Heiß 42 °C (R3 = 2,49 kΩ), kalt +5 °C, Hysterese 5 °C (R4 = 18,7 kΩ)** [V: Tab. 7-1/7-2]. Mit Toleranz: Sperre spätestens bei 43,5 °C, frühestens unter 6,5 °C.
   - Schaltung (Blatt Akku, seit HW-06 auf der Hauptplatine; Bauteile 8xx): OUTA und OUTB verbunden am Gate von Q802 (früher Q2, AO3400A), Gate-Pull-up **100 kΩ** nach TMP_VCC. Q802 zieht **CE_LADEN** (früher Leitung CE_FREI über das Kabel) auf Low. Dort zieht **R205 = 100 kΩ** CE nach SYS.
   - Temperatur im Fenster → Q2 leitet → CE Low → Laden erlaubt. Außerhalb → TMP390 zieht das Gate auf Low → CE High → gesperrt.
2. **Stufe 2, zweiter TMP390 U3 → NTC-Kreis (SCH26-03)**
   - U3 mit **42 °C (R6 = 2,49 kΩ)**, Hysterese 5 °C; nur Kanal A, OUTB offen (laut Datenblatt erlaubt).
   - U3 schaltet Q3 (AO3400A) im Fuß des NTC. Zu heiß → Q3 sperrt → **TS-Pin offen** → Spannung über VCOLD → BQ25185 unterbricht das Laden [V: TI-Datenblatt, Schwellen; TI E2E: TS offen = kein Laden].
   - Die Stufe wirkt unabhängig von Q2, R205 und der Leitung CE_FREI. Ein Einzelfehler in Stufe 1 lässt das Laden damit nicht über ca. 43,5 °C zu.
   - Der NTC bleibt Teil der Stufe 2 und sperrt zusätzlich unter ca. +1,7 °C (Kaltreserve, falls U2 ausfällt) und über ca. 59,5 °C.
   - TS **nie** auf Masse ziehen (Werksmodus). Stufe 2 öffnet deshalb den Kreis, statt kurzzuschließen.

**Pegel (SCH26-02), Rechnung mit Datenblattwerten:**

| Größe | Wert | Bewertung |
|---|---|---|
| Gate Q2/Q3 bei „Laden erlaubt“ | TMP_VCC − 0,1 µA × 100 kΩ ≈ 3,29 V | AO3400A VGS(th) ≤ 1,45 V [A, Datenblatt beim Bestellen prüfen]: sicher leitend |
| CE bei „gesperrt“ | SYS − I_leck(Q2) × 100 kΩ; mit 5 µA (Annahme heiß): 4,5 − 0,5 = 4,0 V | > 1,3 V (VIH): sicher gesperrt |
| CE bei „erlaubt“ | Q2 leitet, < 0,05 V | < 0,4 V (VIL) |
| Strom der Pull-ups | 45 µA (R205) + 33 µA (R5/R8, nur bei gesperrt) | nur bei Sonne, kommt aus dem Panel |
| RC an CE | 100 kΩ × 10 nF = 1 ms | unkritisch |

**Fehlerfälle:**

| Fehler | Folge |
|---|---|
| Zellschutz hat nach Tiefentladung getrennt, Sonne kommt | TMP_VCC da → U2 prüft die Temperatur → Q2 leitet → BQ25185 lädt mit Vorladestrom (20 % = 30 mA) über die Body-Diode → HY2111 erkennt das Ladegerät und gibt ab 2,9 V frei [V: HYCON 11.3.1] |
| U2 oder Q2 fällt so aus, dass CE Low bleibt | Stufe 2 (U3/Q3) sperrt über 42 °C, NTC unter +1,7 °C |
| U3 oder Q3 fällt aus | Stufe 1 sperrt weiter |
| Leitung CE_FREI unterbrochen, J3 abgezogen | CE über R205 High → gesperrt |
| Leitung TMP_VCC unterbrochen oder LDO defekt | beide TMP390 ohne Versorgung, Gates Low → Q2 sperrt (CE High) und Q3 öffnet den NTC → gesperrt |
| NTC-Leitung offen | TS offen → gesperrt |
| NTC-Leitung kurzgeschlossen | TS auf Masse → **Werksmodus**, Akku getrennt, bis wieder eine Quelle anliegt [V]; Stufe 1 sperrt bei falscher Temperatur trotzdem |

**Wärmekopplung:** U802, U803 und TH801 (früher U2, U3, NTC der Akku-Platine) sitzen **direkt unter der Zelle**, mit Wärmeleitpad, nicht neben dem Laderegler. **[P]** Verzug der Erwärmung 42 → 45 °C am Muster messen.

**Prüfung am Muster [P]** (Versuchsplan, Einzelfehleranalyse und Grenzen der Unabhängigkeit: [`sicherheit-akku.md`](sicherheit-akku.md)): Temperaturen 0/4/5/7/36/37/42/44/45/55/60 °C; jeden Fehlerfall der Tabelle einzeln; Wiederanlauf nach Tiefentladung **nur mit strombegrenztem Zell-Emulator, nicht mit einer absichtlich tiefentladenen 18650**.

Die Kältesperre steigt damit von +1,7 °C auf +5 °C. Im Winter lädt der Logger seltener. Bei 128 Tagen Reichweite ohne Laden ist das unkritisch [A].

### 3.4 Zelle und Zellschutz am Halter (bis 14.10.2026: eigene Akku-Platine)

> **HW-06 (Philipp, 14.10.2026): eine Platine.** Die unten beschriebene Schaltung (Halter, HY2111 + FS8205, NTC, 2 × TMP390, Messbrücke) liegt jetzt auf dem Blatt „Akku“ der Hauptplatine (Bauteile 8xx: BT801, U801, Q801, U802, U803, TH801 …). Kabel und JST-Stecker entfallen; damit auch das ungeschützte Kabel aus der Beobachtung unten. Layoutregeln: B− nur als kleine Insel zwischen Halter, U801 und Q801 (GND = P−); TH801/U802/U803 unter der Zelle; Halter nicht an der Funkkante. Der folgende Text beschreibt den Stand bis HW-06 und gilt für die Schaltung unverändert.

**Beobachtung:** Der Akku hängt per Kabel an der Hauptplatine. Liegt der Schutz auf der Hauptplatine, ist das Kabel zwischen Zelle und Schutz **ungeschützt**. Ein Kurzschluss im Kabel wird dann aus einer ungeschützten Zelle gespeist. Der beelogger umgeht das, indem er Zellen mit eingebauter Schutzschaltung vorschreibt.

**Vorschlag:** eine kleine zweite Platine (im selben JLCPCB-Auftrag als Nutzen) mit:
- Halter **Keystone 1042** (SMD, Entscheidung HW-02 am 13.10.2026; die 1043 wäre die Durchsteck-Ausführung)
- **HY2111-GB + Doppel-MOSFET 8205** direkt an der Zelle
- NTC 10 k und **2 × TMP390** unter der Zelle (thermisch angekoppelt, 3.3)
- Stecker JST PH **5-polig** zur Hauptplatine (P−, NTC, CE_FREI, TMP_VCC, P+), siehe anschluesse.md
- Lötbrücke bzw. Stiftleiste in BAT+ zum **Strommessen** (beelogger-Erfahrung, Abschnitt 5)

| Schutz-IC HY2111-GB (LCSC C82747, SOT-23-6, 1.900 Stück am 08.10.2026) | Wert [V: HYCON-Datenblatt über LCSC, Produkttabelle Abschnitt 6 und Kennwerte Abschnitt 9] |
|---|---|
| Überladung | 4,28 V aus, 4,08 V wieder ein |
| Tiefentladung | **2,90 V aus**, 3,00 V wieder ein |
| Freigabe nach Tiefentladung | **nur durch Ladegerät** (Variante mit Ruhezustand) |
| Laden einer Zelle mit 0 V | erlaubt |
| Ruhestrom | 3,0 µA typ., 6,0 µA max. bei 3,9 V; **0,1 µA max. im Ruhezustand** (2,0 V) |
| Überstrom | 150 mV am Doppel-FET; bei 8205 mit etwa 2 × 25 mΩ ergibt das grob 3 A [A] |

Warum 2,9 V statt der üblichen 2,4 V des DW01A: Die Zelle hängt monatelang ohne Aufsicht draußen. Nach der Abschaltung soll sie nicht unter die Entladegrenze von 2,5 V absinken [A].

**[P] am Muster:** Nach Abschaltung durch den HY2111 muss der BQ25185 bei Sonne über die Body-Diode des Entlade-FETs wieder laden und den Schutz freigeben.

### 3.5 Verpolschutz Akku

Der Steckverbinder ist verpolsicher kodiert. Zusätzlich P-MOSFET (AO3401A) in BAT+ zur Hauptplatine; er leitet in beide Richtungen, also auch beim Laden [A]. **[P]** Prüfen, ob er hinter dem Schutz-IC überhaupt noch nötig ist. Ein Kodierstecker allein ist einfacher.

### 3.6 3,3-V-Regler RT9080-33GJ5 (LCSC C841192, Extended) [V: Richtek DS9080]

| Merkmal | Wert |
|---|---|
| Strom | 600 mA (Funkmodul braucht laut Ai-Thinker bis 140 mA) |
| Ruhestrom | 2 µA typ., 4 µA max. |
| Spannungsabfall | 0,31 V typ. bei 600 mA; bei 120 mA geschätzt 60 mV [A] |
| Kondensatoren | Keramik ≥ 1 µF; dazu 100 µF + 10 µF nahe am Funkmodul [A] |
| Eingangsspannung | Betrieb 1,2–5,5 V, Absolutgrenze 6,5 V [V]. SYS liefert bei Sonne 4,5 V: passt. |
| Strombegrenzung | min. 610 mA, typ. 1,1 A [V] |
| EN | an VIN legen; darf nicht offen bleiben [V] |
| Temperatur | Sperrschicht −40 bis +125 °C [V] |

**Ersatz:** MCP1700-3302 (250 mA, ca. 1,6 µA; knapp beim Funk).

**Kein Abwärtswandler:** Er spart bei Akku über 3,3 V nur wenige Prozent der aktiven Ladung. Dafür bringt er Spule, Welligkeit neben dem Funk und ein Extended-Teil mehr [A].

**Untere Grenze:** Unter etwa 3,35 V Akku regelt der LDO nicht mehr; der Ausgang folgt dem Akku. Der DS18B20 braucht mindestens 3,0 V [V]. Alle anderen Teile laufen tiefer.

### 3.7 Geschaltete Sensorschiene

| Punkt | Festlegung |
|---|---|
| Schalter | **TPS22917** (LCSC C2681320, Extended) im 3,3-V-Zweig, ON an PB5 (high = ein), Pull-down 100 kΩ an ON; CT für die Anstiegszeit, QOD für die aktive Entladung (Übernahme aus BEEP base v3, beep-vergleich.md 3.1). Rückfall: AO3401A (C15127, Basic) mit Gate direkt am GPIO (low = ein). |
| Sicher aus im Standby | **Pflicht:** Die GPIOs sind im Standby hochohmig. TPS22917: Pull-down 100 kΩ an ON. Rückfall AO3401A: Gate-Pull-up 1 MΩ nach 3,3 V. |
| Einschaltstrom | An der Schiene hängen u. a. 22 µF (Mikrofon) und 10 µF (HX711). TPS22917: CT ≥ 1 nF für eine Anstiegszeit im ms-Bereich [A, Datenblatt-Gleichung prüfen]. Rückfall: Gate-RC 100 kΩ / 10 nF. |
| An der Schiene | HX711 (nur DVDD; Brücke und Analogteil am 5-V-Wandler, waage.md), DS18B20, BME280, Mikrofon, **alle Pull-ups**. (Der EEPROM entfällt seit 09.10.2026, HW26-10; die Sitzung liegt im SPI-Flash, mcu-funk.md 3.2.) **Nicht** an der Schiene: SPI-Flash (dauernd versorgt, Bus mit dem Funk geteilt, mcu-funk.md 3.2). |
| Ruhestrom | TPS22917 eingeschaltet 0,5 µA, aus 10 nA Leckstrom [V]; in der Bilanz wie der FET mit 0,1 µA gerechnet |

**Regeln gegen Rückspeisung (HW26-04):**
1. Alle Pull-ups (I²C, 1-Wire) hängen an der **geschalteten** Schiene, nie an der Dauerversorgung.
2. Vor dem Abschalten stellt die Firmware alle Sensor-Pins auf Analog bzw. hochohmig. Beim Einschalten zuerst die Schiene, dann die Pins.
3. Serienwiderstände 1 kΩ in HX711-SCK/DOUT und 1-Wire. 10 kΩ vor PA1 (Mikrofon) gehört ohnehin zum Filter.
4. **[P] am Muster:** mit abgeschalteter Schiene und Standby den Ruhestrom messen; der Wert muss zur Tabelle in Abschnitt 4 passen.

### 3.8 Akkuspannung messen

- Fester Teiler 2 × 2,2 MΩ an SYS bzw. BAT, 100 nF am ADC-Knoten. Er zieht 0,9 µA; ein abschaltbarer Teiler lohnt den Aufwand nicht.
- VREFINT messen und damit VDDA korrigieren, falls der LDO schon nicht mehr regelt.
- **Den VBAT-Pin des STM32 nie an den Akku legen** (nur bis 3,6 V) [V: ST-Datenblatt]. VBAT an 3,3 V; Knopfzelle entfällt (siehe 5, Regel 10).

### 3.9 Schienen und Kondensatoren (REG26-11, 09.10.2026)

**Schienen** (Werte aus den Datenblättern der Bauteile in 3.2–3.7; Welligkeit und Abfall am Muster messen [P]):

| Schiene | Quelle | Bereich | Toleranz / Grenze | Ein- und Ausschalten | Last |
|---|---|---|---|---|---|
| VIN_LADER | Panels über D201/D202, USB über D203 | 0–12 V dauernd, Störung bis 25 V | BQ25185 abs. 25 V, OVP 18,5 V; TVS 12 V [V] | folgt der Sonne | Lader, TPS70933, Teiler 3,2 µA |
| TMP_VCC | U204 TPS70933 aus VIN_LADER | 3,3 V, sobald VIN > ca. 3,5 V [A] | Ausgangsgenauigkeit laut Datenblatt prüfen [P] | **nur bei Sonne/USB**; nachts aus | Ladesperre, max. ca. 80 µA (Pull-ups) |
| VBAT | Zelle über Zellschutz (Blatt Akku) | 3,0 (BUVLO) … 4,1 V | HY2111 2,9 / 4,28 V | dauernd | Lader-Ruhestrom, Teiler 0,9 µA |
| SYS | BQ25185: bei Quelle 4,5 V geregelt, sonst VBAT über 115 mΩ | 3,0–4,5 V | – | dauernd, solange VBAT > BUVLO oder Quelle da | RT9080, 5-V-Wandler der Waage |
| +3V3 | U202 RT9080 aus SYS, EN an SYS | 3,3 V bei SYS ≥ ca. 3,4 V; darunter folgt sie SYS | Abfall 0,31 V bei 600 mA [V] | folgt SYS (kein eigener Startablauf) | MCU, Funk (bis 140 mA), SPI-Flash |
| 3V3_SW | U203 TPS22917 aus +3V3 | wie +3V3 | Anstieg ca. 1,7 ms (CT 1 nF), aktive Entladung über QOD | **nur auf Befehl der MCU** (PB5); Standby aus | Sensoren und alle Pull-ups |

Reihenfolge beim Start: Quelle oder Zelle → SYS → +3V3 → MCU → (Firmware) 3V3_SW → Sensor-Pins. Beim Abschalten umgekehrt; vor 3V3_SW aus stellt die Firmware alle Sensor-Pins hochohmig (3.7, Regel 2). Brownout-Schwelle der MCU und Verhalten bei langsam fallender SYS sind Firmware-Festlegungen auf Blatt MCU und am Muster zu prüfen [P].

**Kondensatoren mit DC-Bias:** Keramikkondensatoren (X5R/X7R) verlieren unter Gleichspannung Kapazität, umso mehr, je kleiner die Bauform und je niedriger die Nennspannung. Mindestwerte aus den Datenblättern gelten für die **wirksame** Kapazität.

| Bauteil | Anforderung | Gewählt (V0.1) | Wirksam bei Betriebsspannung [A] | Bewertung |
|---|---|---|---|---|
| C201 VIN_LADER | ≥ 1 µF (BQ25185) | 4,7 µF 50 V X7R 1206 | bei 12 V grob 3–4 µF | ausreichend |
| C204 SYS | ≥ 10 µF (BQ25185) | **22 µF 25 V X5R 1206** (vorher 10 µF 0805) | bei 4,5 V grob 13–18 µF; 10 µF/0805 läge bei grob 5–7 µF und damit unter der Anforderung | geändert |
| C205 VBAT | ≥ 1 µF | 4,7 µF 0805 | bei 4,1 V grob 2,5–3,5 µF | ausreichend |
| C212 TMP_VCC | ≥ 2,2 µF (TPS70933) | **4,7 µF 16 V X7R 0805** (vorher 2,2 µF 0603) | bei 3,3 V grob 3–4 µF; 2,2 µF/0603 läge bei grob 1,3–1,8 µF | geändert |
| C208 SYS am RT9080 | ≥ 1 µF | **2,2 µF 16 V X7R 0603** (vorher 1 µF) | bei 4,5 V grob 1,2–1,6 µF | geändert |
| C209 +3V3 | ≥ 1 µF | **2,2 µF 16 V X7R 0603** (vorher 1 µF) | bei 3,3 V grob 1,4–1,8 µF | geändert |
| C211 3V3_SW | keine Vorgabe | 1 µF 0603 | – | unverändert |

Die Spannen „grob“ sind Erfahrungswerte für übliche MLCC-Familien [A], **keine** Herstellerdaten. Beim Festlegen der LCSC-Nummern (vor dem Layout) für jeden Kondensator dieser Tabelle die DC-Bias-Kurve des Herstellers prüfen und den Wert hier eintragen; erst dann gilt REG26-11 als erledigt. Temperatur: X7R −55 … +125 °C ±15 %, X5R −55 … +85 °C ±15 % [V: EIA-Klassen]; bei +60 °C Gehäuse reicht X5R.

## 4. Energiebilanz (Auszug aus `energiebilanz.py`)

### Ruhestrom bei 25 °C

| Teil | µA | Status |
|---|---|---|
| BQ25185 (ohne Eingang) | 4,0 | V |
| HY2111-GB | 3,0 | V |
| RT9080 | 2,0 | V |
| STM32F411 Standby mit RTC | 2,6 | A (aus 2,4 / 2,8 µA bei 1,7 / 3,6 V) |
| SX1262 Sleep | 0,6 | V |
| Akkuteiler | 0,9 | A |
| Lastschalter | 0,1 | A |
| 5-V-Wandler TPS61240 aus | 1,5 | V |
| SPI-Flash Deep Power-down | 1,0 | A (Typ bei Bestellung) |
| Ladesperre (3.3) | 0 | V/A: hängt an TMP_VCC, nur bei Sonne |
| **Summe** | **15,7 µA ≈ 0,38 mAh/Tag** | |

Bei 70 °C im Gehäuse steigt allein der STM32 auf bis 14 µA (max.); die Summe liegt dann bei grob 25 µA. Das Ziel „unter 20 µA“ gilt also bei Raumtemperatur.

### Messzyklus alle 15 min

| Szenario | je Zyklus | pro Tag | größter Posten |
|---|---|---|---|
| A: Ablauf wie die heutige ZS-Firmware (MCU durchgehend 96 MHz, 8 s) | 207 mAs | 5,5 mAh | MCU 156 mAs (75 %), Waage 35 mAs |
| B: neue Firmware (16 MHz beim Warten, 96 MHz nur für die FFT, Stop in den RX-Pausen) | 91 mAs | 2,4 mAh | MCU 47 mAs, Waage 35 mAs |
| Zusatz bei schlechter Verbindung (SF12 jedes Mal) | +201 mAs | +5,4 mAh | Sendezeit 2,8 s |

### Reichweite ohne Laden (Frostperiode, Ladung gesperrt)

Nutzbare Kapazität: 3350 mAh × 0,9 (Ladeschluss 4,1 V) × 0,95 (bis 3,3 V) × 0,8 (Kälte) ≈ **2290 mAh** [A].

| Szenario | Selbstentladung 2 %/Monat | 5 %/Monat | SF12 + 5 %/Monat |
|---|---|---|---|
| A | 282 Tage | 200 Tage | 128 Tage |
| B | 454 Tage | 273 Tage | 155 Tage |

**Die Selbstentladung der Zelle ist so groß wie der ganze Logger.** Werte für 2–5 %/Monat sind eine Spanne [A]. Battery University nennt für volle Zellen bei 25 °C deutlich mehr. In der Kälte ist sie kleiner. **[P]** Leerlaufspannung einer Zelle über einige Wochen beobachten.

### Ertrag im Dezember

- 0,55 kWh/m²/Tag horizontal (DWD-Mittel für Deutschland) [V]
- × 1,5 für 65° Neigung nach Süden [A]
- × 200 cm² Panelfläche [A, messen]
- × 10 % Gesamtwirkungsgrad [A]
- ≈ **1,6 Wh/Tag ≈ 430 mAh/Tag**, das sind grob **38 : 1** zum Bedarf

**[P]** PVGIS für 51,1° N / 13,9° O, 65° Süd selbst abrufen (re.jrc.ec.europa.eu, „Monthly radiation“). Das automatische Abrufen sperrt die Seite.

**Folgerung:** Die Panels sind auch an trüben Tagen und mit Teilabschattung mehr als ausreichend. Die Reichweite ohne Laden deckt jede realistische Frostperiode ab. Für die Firmware heißt das: Spielraum für FFT und Sensoren ist da, Sparen beim Mikrocontroller bringt am meisten.

## 5. Erfahrungen aus dem beelogger → Regeln

| Nr. | beelogger macht es so | Quelle | Regel für unsere Platine |
|---|---|---|---|
| 1 | Kein Schutz auf der Platine; **Zelle mit Schutzschaltung „zwingend erforderlich“** | beelogger.de, Bauteile STM32 / Akku-Shield | Schutz in Hardware, und zwar **an der Zelle** (3.4; seit HW-06 auf der Hauptplatine direkt am Halter, kein Kabel mehr), damit auch das Kabel geschützt ist |
| 2 | CN3065-Modul, davor Schottky 1N5818, **Z-Diode 5,6 V** und 1,5–2,2 Ω | beelogger.de, Beschaltung und Aufbau | Den Eingang nicht mit einer Z-Diode begrenzen (verheizt Leistung, schützt nur knapp). Laderegler mit **Eingangsreserve über der kalten Leerlaufspannung** wählen. |
| 3 | Früher SPV1040 (MPPT), ab V1.3 entfernt; empfindlich gegen Panelspannung und Ladeschluss | beelogger.de, Platinenversionen | MPPT nur, wenn nötig. Bei 40-facher Reserve genügt Eingangsspannungsregelung. |
| 4 | LDO MCP1702-3302, ca. 2 µA | beelogger.de, Schaltung | LDO mit Ruhestrom im niedrigen µA-Bereich, aber **mit Reserve für den Funk** (MCP1702: 250 mA) |
| 5 | BlackPill: Vorwiderstand der Power-LED und Bordregler entfernen | beelogger.de, Bauteile STM32 | **Keine dauernd leuchtende LED, kein zweiter Regler.** LED nur über GPIO. |
| 6 | 5-V-Aufwärtswandler MT3608 für HX711; **unjustiert zerstört er die Platine**; Layoutfehler bei der HX711-Versorgung in V1.3 | beelogger.de, Beschaltung, Versionen | 5 V für die HX711 ja (Entscheidung Philipp; Bosche empfiehlt 5–12 V), aber **nur mit festem Wandler-IC mit Lasttrennung**, kein einstellbares Modul (waage.md) |
| 7 | P-MOSFET mit Transistorstufe schaltet die Sensoren | beelogger.de, Bauteile | P-MOSFET mit Logikpegel direkt am GPIO, **Gate-Pull-up**, Pull-ups auf der geschalteten Seite |
| 8 | Lötbrücke neben Akku-Plus zum Trennen; Strommessung mit Multimeter in der Plusleitung | beelogger.de, Beschaltung / Stromaufnahme | **Messbrücke in BAT+** und Testpunkte vorsehen |
| 9 | Ab V1.4 Masse der Solarzelle getrennt geführt | beelogger.de, Platinenversionen | Solarstrom und Messmasse sauber führen. Solarteiler auf der Panelseite. |
| 10 | Ruhestrom „unter 20 µA“; Ursachen bei Abweichung: Lötbrücken, Flussmittel, ESD-geschädigte Controller oder MOSFETs | beelogger.de, Stromaufnahme | Ziel beibehalten, aber **temperaturabhängig** angeben (Abschnitt 4). Schutzlack erst nach der Messung. ESD-Schutz an allen Außenanschlüssen. |
| 11 | Software: Sendewiederholungen begrenzt (2020), Zeitsteuerung bei leerem Akku überarbeitet (2023) | beelogger.de, News | Firmware-Stufen bei niedriger Spannung (siehe unten), Sendewiederholungen begrenzen |
| 12 | Kondenswasser: Öffnungen mit diffusionsoffenem Material | beelogger.de, Inbetriebnahme | Druckausgleichselement im Gehäuse vorsehen (bei den Durchführungen) |
| 13 | Panel 5–6 V, 2–10 W, Leerlauf bis 7,5 V | beelogger.de, Bauteile STM32 | Eingang auf **10 V Dauer** und 25 V Spitze auslegen |

Aus dem beelogger-Forum (communityserver) ließ sich nichts automatisch lesen. Erfahrungen zu Winterbetrieb und Frost von dort fehlen also noch. **[P]** Bei Gelegenheit im Browser nachlesen.

**Stufen bei niedriger Akkuspannung** (Firmware, Werte zur Diskussion [A]):

| Akku | Verhalten |
|---|---|
| ≥ 3,50 V | normal |
| < 3,50 V | FFT aus, Messintervall 30 min |
| < 3,40 V | nur noch eine Zustandsmeldung alle 6 h |
| < 3,30 V | kein Senden mehr, Standby, Wecken alle 6 h zum Prüfen |
| < 3,0 V | BQ25185 trennt SYS vom Akku (Hardware) |
| < 2,9 V | HY2111 trennt die Zelle (Hardware, 0,1 µA) |

## 6. Montage der Panels

- **Steil montieren, etwa 60–70° nach Süden.** Schnee rutscht ab etwa 30–40° [V: ingenieur.de], und im Winter ist der Ertrag bei steilem Winkel am höchsten.
- Unterkante frei lassen, damit sich der Schnee nicht staut.
- Panels nicht flach auf den Deckel legen.
- Die Reserve aus Abschnitt 4 überbrückt auch mehrere Wochen unter Schnee.

## 7. Offene Prüfpunkte

Erledigt am 08.10.2026:
- BQ25185-Eingangsbereich (Produktseite: 3,0–18 V)
- HY2111-GB = 2,90/3,00 V mit Ruhezustand
- RT9080-Eingang bis 5,5 V

Offen:
1. **Panels messen** (Voc, Isc, Maße, Zellzahl, Laminat), sobald möglich. Bis dahin gilt die Auslegung auf 12 V.
2. BQ25185: Bezug zwischen TS-Strom (38 µA) und NTC sowie Verhalten von SYS bei TS-Fehler. Im Datenblatt nicht beschrieben. Am Muster prüfen oder TI E2E fragen.
3. RT9080: Spannungsabfall bei 120–300 mA (Datenblatt nur Tabellenwert bei 600 mA: 0,31 V typ., 0,53 V max.)
4. JLCPCB-Bestand und Basic/Extended aller Teile kurz vor der Bestellung
5. Original-Datenblatt BAK N18650CP: Ladetemperatur, Entladegrenze, Innenwiderstand in der Kälte, Selbstentladung
6. **Am Steckbrett:** Ruhestrom gesamt, Ladung je Zyklus, Strom des Mikrofonmoduls, Ra-01SH mit oder ohne DC-DC-Spule (RX 4,6 oder 8,8 mA)
7. Gehäusetemperatur im Sommer; Ladesperre bei 42 °C (TMP390) und 59,5 °C (NTC) am Muster prüfen

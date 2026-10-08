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
 Panel 2 ─┴─ Schottky ─┴─┬─ TVS 12 V ─┬─ Teiler 3,3 MΩ/1 MΩ → ADC (Solar)
                          │            │
                          └─► BQ25185 IN
                                 │ SYS (bei Sonne 4,5 V, sonst = Akku) ──┬─► RT9080 3,3 V ──┬─► STM32, Ra-01SH, SPI-Flash
                                 │ BAT                                   │                  └─► TPS22917 ─► Sensorschiene 3,3 V
                                 │                                       │                       (HX711-DVDD, DS18B20, BME280,
                                 │                                       │                        EEPROM, Mikrofon, Pull-ups)
          Akku-Platine am Halter │                                       └─► TPS61240 5 V (EN = PB10, nur beim Wiegen)
                                 │                                            └─► Filter ─► HX711 VSUP → AVDD 4,3 V → H40A
       ┌─────────────────────────┴───┐
       │ Stecker ─ HY2111 + 8205 ─ Zelle 18650 │    NTC 10 k an der Zelle → TS des BQ25185
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
| TVS-Diode am Eingang | SMAJ12A (Sperrspannung 12 V) [P] | Begrenzt Störungen auf dem langen Panelkabel unter die 25 V Absolutgrenze des BQ25185 |
| Messung Solarspannung | Teiler 3,3 MΩ / 1 MΩ **vor** den Dioden auf der Panelseite [A] | 12 V ergeben 2,8 V am ADC (Messbereich bis 14 V). Der Teiler belastet nur das Panel, nicht den Akku. |

### 3.2 Laderegler BQ25185 (LCSC C19725033, Extended) [V: TI-Datenblatt]

| Merkmal | Wert | Bedeutung für uns |
|---|---|---|
| Eingang | Betrieb 3,0–18 V, Absolutgrenze 25 V, Überspannungsabschaltung bei 18,5 V | Panelspannung bis 10 V ist unkritisch; keine Z-Diode nötig wie beim beelogger |
| Schwache Quelle | VINDPM: Ladestrom wird reduziert, damit der Eingang nicht unter Akku + 0,33 V fällt | Das Panel bricht nicht zusammen. Es ist **kein MPPT**; das Panel arbeitet bei etwa 4,4 V statt etwa 6 V. Der Verlust (grob 25 %) ist bei 40-facher Reserve ohne Bedeutung. |
| Ladeschluss | per Widerstand: u. a. 4,05 / 4,1 / 4,2 V | **4,1 V wählen** [A]: Die Zelle steht dauernd voll und warm im Sommer; das schont sie. Kostet grob 10 % Kapazität. |
| Ladestrom | ICHG = 300 AΩ ÷ RISET, 5–1000 mA | **300 mA** mit RISET = 1 kΩ. Die Panels liefern ohnehin weniger; VINDPM regelt. |
| Systemausgang SYS | bei Sonne 4,5 V geregelt; ohne Sonne über den Akkuschalter (115 mΩ) = Akkuspannung | Der LDO hängt an SYS. Bei Sonne versorgt das Panel den Logger direkt. |
| **Akku-Unterspannung** | BUVLO 3,0 V fallend, Hysterese 0,11–0,19 V: trennt den Akku von SYS | **Erste Hardware-Stufe des Tiefentladeschutzes** |
| Überstrom Akku | 3,13 A, Hiccup | zusätzlicher Schutz |
| Temperatur (TS) | für 10-kΩ-NTC, B = 3435 K. Kalt: 1,0075 V steigend, Heiß: 0,115 V fallend. Laden außerhalb gesperrt. | siehe 3.3 |
| Ruhestrom aus dem Akku | 4 µA typ., 5 µA max. (ohne Eingang) | in der Bilanz enthalten |
| Gehäuse | WSON-10, 2,2 × 2 mm, Thermal-Pad | JLCPCB bestückt das; Handlöten ist schwer |

**Eingangsbereich geklärt:** Die TI-Produktseite nennt „3.0V to 18V input voltage operating range“, „25V tolerant input voltage“ und „solar input support“ [V, ti.com/product/BQ25185, 08.10.2026]. Die abweichende Zeile „2,7–5,5 V“ in der Empfehlungstabelle des Datenblatts widerspricht dem. Ich halte sie für einen Fehler im Datenblatt, belegt ist das nicht. Maßgeblich für uns sind die Betriebsdaten 3,6–18 V und die Produktseite.

**Ersatz, falls der BQ25185 ausscheidet:**
- BQ25170: hat einen NTC-Eingang mit 0 °C und 45 °C, aber eine Überspannungsabschaltung bei 6,75 V. Er bräuchte also eine Eingangsbegrenzung.
- CN3791: echtes MPPT bis 28 V, aber kein NTC-Eingang. Die Kältesperre müsste man extern bauen.

### 3.3 Temperatursperre beim Laden

Die Zelle (BAK N18650CP) darf laut Händlerangaben bei **0 bis +45 °C** geladen werden [V: keeppower.com.cn]. Das Original-Datenblatt von BAK ist noch zu lesen [P].

Rechnung für einen 10-kΩ-NTC mit B = 3435 K am TS-Pin [A]. Annahme: Der TS-Pin speist den NTC mit dem Strom ITSMR = 38 µA. Das Datenblatt nennt den Wert, ordnet ihn aber nicht ausdrücklich dem NTC zu [P]:

| Schwelle | Spannung | NTC-Widerstand | Temperatur |
|---|---|---|---|
| Kalt (Laden aus) | 1,0075 V | 26,5 kΩ | **ca. +1,7 °C** |
| Kalt (Laden wieder ein) | 0,820 V | 21,6 kΩ | ca. +6,3 °C |
| Heiß (Laden aus) | 0,115 V | 3,0 kΩ | **ca. +59,5 °C** |
| Heiß (Laden wieder ein) | 0,135 V | 3,6 kΩ | ca. +54,4 °C |

- **Die Kältesperre passt.** Zwischen +1,7 °C und 10 °C wird mit vollem Strom geladen (BQ25185 hat keine JEITA-Stufen). Bei 300 mA sind das unter 0,1 C. Das Risiko einer Lithium-Abscheidung schätze ich bei so kleinem Strom als gering ein [A].
- **Die Heißsperre liegt bei 60 °C statt 45 °C.** Sie lässt sich mit einem Parallelwiderstand auf 45 °C verschieben, aber dann wirkt die Kältesperre nicht mehr. Ausgleich:
  - Ladeschluss 4,1 V
  - kleiner Strom
  - Gehäuse hell und möglichst im Schatten
  - **[P]** Gehäusetemperatur im Sommer messen; die Firmware meldet sie ohnehin (CPU-Temperatur).
- **Der NTC muss an der Zelle sitzen**, nicht auf der Hauptplatine (siehe 3.4).

### 3.4 Akku-Platine am Halter (neu)

**Beobachtung:** Der Akku hängt per Kabel an der Hauptplatine. Liegt der Schutz auf der Hauptplatine, ist das Kabel zwischen Zelle und Schutz **ungeschützt**. Ein Kurzschluss im Kabel wird dann aus einer ungeschützten Zelle gespeist. Der beelogger umgeht das, indem er Zellen mit eingebauter Schutzschaltung vorschreibt.

**Vorschlag:** eine kleine zweite Platine (im selben JLCPCB-Auftrag als Nutzen) mit:
- Halter Keystone 1043 (für Leiterplattenmontage)
- **HY2111-GB + Doppel-MOSFET 8205** direkt an der Zelle
- NTC 10 k unter der Zelle (thermisch angekoppelt)
- Stecker mit Kodierung zur Hauptplatine (BAT+, BAT−, NTC, GND)
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
| An der Schiene | HX711 (nur DVDD; Brücke und Analogteil am 5-V-Wandler, waage.md), DS18B20, BME280, Mikrofon, **alle Pull-ups**, EEPROM (mcu-funk.md 3.1). **Nicht** an der Schiene: SPI-Flash (dauernd versorgt, Bus mit dem Funk geteilt, mcu-funk.md 3.2). |
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
| 1 | Kein Schutz auf der Platine; **Zelle mit Schutzschaltung „zwingend erforderlich“** | beelogger.de, Bauteile STM32 / Akku-Shield | Schutz in Hardware, und zwar **an der Zelle** (Akku-Platine 3.4), damit auch das Kabel geschützt ist |
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
7. Gehäusetemperatur im Sommer (Heißsperre 59,5 °C)

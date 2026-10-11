# Block Waage (Lastenheft 0.4, F3 – Entwurf, 08.10.2026, geändert 10.10.2026)

Kennzeichnung:
- **[V]** im Datenblatt gelesen
- **[A]** Annahme oder Rechnung
- **[P]** vor dem Schaltplan bzw. am Muster prüfen

Entscheidungen (Philipp, 08.10.2026):
- **HX711 mit 5 V aus einem Aufwärtswandler**
- Wägezelle **Bosche H40A, 200 kg**
- **Nur ein HX711 und eine Wägezelle je Logger** (09.10.2026)

## 1. Wägezelle Bosche H40A 200 kg [V: Bosche-Datenblatt „Single point load cell H40A“]

| Größe | Wert | Folge |
|---|---|---|
| Nennkennwert | 2,0 ± 0,2 mV/V | Signal bei 200 kg und 4,3 V Speisung: 8,6 mV |
| Eingangswiderstand | **404 ± 10 Ω** | Brückenstrom bei 4,3 V: **10,6 mA je Zelle** |
| Ausgangswiderstand | 350 ± 3 Ω | |
| Empfohlene Speisespannung | **5–12 V**, max. 15 V | Mit 3,3 V lägen wir unter der Empfehlung. Auch mit dem HX711 an 5 V speist er die Brücke nur mit AVDD ≈ 4,3 V. Das ist knapp unter 5 V, aber üblich (HX711-Referenzschaltung). |
| Genauigkeitsklasse | C3, 3000 Teilungen | |
| Nenntemperaturbereich | **−10 … +40 °C** | Darunter gelten die Herstellerangaben nicht. Im Winter ist mit größerem Temperaturgang zu rechnen. Der Server rechnet das Gewicht schon heute nach der Temperatur um (Wägezellentemperatur); die Firmware sendet TempOut mit. **[P]** Kälteverhalten der eigenen Zellen im Winter beobachten. |
| Schutzart, Kabel | IP65, 1,8 m | lange Leitung: Schutz und Filter am Eingang (Abschnitt 4) |

## 2. 5-V-Versorgung

| Punkt | Festlegung |
|---|---|
| Wandler | **TPS61240DRVR** (TI), fest 5,0 V ±2 %, Eingang 2,3–5,5 V, 250 mA ab 3,2 V [V: TI-Datenblatt S. 3–5]. LCSC C59567, Bestand 601 am 08.10.2026 [V]. |
| Warum dieser | fest 5 V ohne Teiler und ohne Einstellpoti; echte **Lasttrennung** im Aus-Zustand [V, S. 11]; 3,5 MHz Taktfrequenz, leicht zu filtern |
| Ersatz | **MCP1640B** (Microchip, SOT-23-6, LCSC C478087, 4.022 Stück [V]): Lasttrennung, **nur PWM** (kein Burst-Betrieb), 500 kHz, ca. 300 mA aus Li-Ion [V: DS20002234E]. Wenn der TPS61240 bei unserer Last (ca. 25 mA) in den Burst-Betrieb wechselt und das die Messung stört, wechseln wir auf diesen. |
| Ausgeschlossen | MT3608, SX1308, ME2108: Diese Wandler haben keine Lasttrennung. Im Aus-Zustand liegt am Ausgang Akku minus Diodenspannung (ca. 3,7 V), und die Waage würde dauernd mitversorgt [A]. Dazu kommt beim beelogger das einstellbare MT3608-Modul, das unjustiert die Platine zerstört [V: beelogger.de]. |
| Eingang | an **SYS** (Akku bzw. 4,5 V vom Laderegler), nicht an 3,3 V. So belasten die 40 mA den 3,3-V-Regler nicht. |
| Ein/Aus | EN an **PB10** (neu belegt), Pull-down 100 kΩ: Im Standby ist der Wandler sicher aus. Das Datenblatt nennt keinen internen Pull-down an EN; Eingangsstrom ≤ 1 µA, VIH 1,0 V, VIL 0,4 V [V, Abschnitt 7.5]. |
| Ruhestrom aus | 1,5 µA typ. [V, S. 5; das Kurzblatt nennt „< 1 µA“]. In der Energiebilanz enthalten (Ruhestrom gesamt 13,2 → 14,7 µA). |
| Spule, Kondensatoren | **1,0 µH** (TI empfiehlt 1,0 µH; Schaltstrombegrenzung 500–600 mA, Spule mit Isat ≥ 0,7 A wählen) [V, Abschnitt 7.5 und 10.2.2.2]; TI-Liste u. a. TOKO MDT2012-CH1R0AN (0805). Eingang **4,7 µF/0805** (TI: mindestens 2,2 µF; Reserve für DC-Bias bei 4,5 V) [V/A]. Ausgang **10 µF/0805** (TI: 1–20 µF, Abschnitt 7.3) [V]; hinter dem Ferrit noch einmal 10 µF, zusammen 20 µF Nennwert, bei 5 V wirksam etwa die Hälfte [A]. |
| Filter | Wandler → Ferrit (ca. 600 Ω bei 100 MHz) → 10 µF + 100 nF → VSUP des HX711 [A] |
| Entladewiderstand | 100 kΩ am 5-V-Ausgang, damit die HX711 beim nächsten Einschalten sicher neu starten [A] |
| **[P]** am Muster | Welligkeit an VSUP messen; Strom bei Akku 3,0 V (Datenblatt nennt 200 bzw. 250 mA, widersprüchlich) |

## 3. HX711 (1 Stück, Kanal A mit Verstärkung 128)

| Punkt | Festlegung | Quelle |
|---|---|---|
| Baustein | HX711, SOP-16, LCSC C43656 (7.344 Stück, Extended) | [V] |
| VSUP | 5 V vom Wandler | [V] Bereich 2,7–5,5 V |
| AVDD | **4,30 V**: AVDD = 1,25 V × (1 + 20 kΩ / 8,2 kΩ) über externen PNP S8550 | [V] Formel und S8550 aus Datenblatt Fig. 1; Werte 20k/8,2k aus SparkFun-Forum, nachgerechnet |
| Abstand zu VSUP | ≥ 100 mV (5,0 − 4,3 = 0,7 V) | [V] |
| PNP | S8550, SOT-23 (LCSC C397181 oder C111271, Extended) | [V] |
| DVDD | **3,3 V geschaltete Sensorschiene**; damit passen die Logikpegel zum STM32 | [V] DVDD 2,6–5,5 V, unabhängig von VSUP |
| Takt | XI an GND (interner Oszillator), XO offen | [V] |
| RATE | an GND: **10 Werte/s** (geringeres Rauschen, 50 nV) | [V] |
| Entkopplung | 100 nF an VBG; 10 µF + 100 nF an AVDD; 100 nF an DVDD und VSUP | [V/A] |
| Pins zum STM32 | SCK und DOUT je 1 kΩ in Reihe; DOUT an PB8, SCK an PB9 | mcu-funk.md |
| Kanal B | nicht genutzt: INB+ und INB− verbunden und über **0 Ω (R507) an INA−**, also auf den Gleichtakt der Brücke (ca. AVDD/2) [A]. Falls das die Messung am Muster stört, R507 auslöten [P]. | |

**Zustand bei ausgeschaltetem 5-V-Wandler:** DVDD liegt dann noch an, VSUP/AVDD nicht. Das Datenblatt beschreibt diesen Zustand nicht. Die Firmware hält SCK low und schaltet die Sensorschiene nach der Messung ab. **[P]** Strom in diesem Zustand am Muster messen.

## 4. Anschluss der Wägezelle (Kabel 1,8 m)

| Leitung | Beschaltung [A] |
|---|---|
| E+ / E− (Speisung) | E+ aus AVDD über einen Ferrit mit **Gleichstromwiderstand ≤ 0,1 Ω** (Abschnitt 4.1), E− an Masse; ESD-Schutz TPD4E05U06 (5,5 V) |
| S+ / S− (Signal) | je 100 Ω in Reihe, 100 nF zwischen S+ und S−, je 10 nF nach Masse. Keine TVS mit Leckstrom über ca. 100 nA (100 nA × 100 Ω = 10 µV, das sind etwa 0,2 kg). |
| Schirm | nur auf der Platinenseite an Masse, an der Zelle offen |
| Klemme | steckbare Schraubklemme 5-polig (E+, E−, S+, S−, Schirm), Raster 3,5 mm, beschriftet |

Die Reihenwiderstände in S+/S− verändern die Empfindlichkeit nicht, weil der HX711-Eingang hochohmig ist. Die Waage wird ohnehin kalibriert.

### 4.1 Ferrit in E+ und Temperaturgang (Rechnung, 10.10.2026)

Der HX711 misst relativ zu AVDD (Eingangsbereich ±0,5 · AVDD / Verstärkung [V]). Ein Widerstand R in der Speiseleitung senkt die Brückenspannung um den Anteil R / 404 Ω, unabhängig von AVDD [A, Rechnung]. Das ist ein fester Verstärkungsfehler und wird mit kalibriert. Es bleibt der Temperaturgang des Leiters (Kupfer ca. +0,39 %/K [A]):

| Widerstand in E+ | Verstärkungsfehler | Änderung über 80 K (−20 … +60 °C) | bei 100 kg Last |
|---|---|---|---|
| 0,1 Ω | 0,025 % | 0,008 % | ca. 8 g |
| 0,5 Ω | 0,12 % | 0,039 % | ca. 39 g |

Daher Ferrit mit **≤ 0,1 Ω** [A]; Teil wählen [P]. Das Kabel der Zelle (E+ und E−, 1,8 m) wirkt genauso; sein Querschnitt ist nicht bekannt [P]. Der HX711 hat keine Fühlereingänge für eine 6-Leiter-Zelle [V: Pinbelegung]; ein Rest wird von der Temperaturkorrektur auf dem Server mit erfasst (Abschnitt 1) [A].

## 5. Auflösung (Rechnung)

Rauschen des HX711, auf den Eingang bezogen: 50 nV eff. bei 10 Werten/s, 90 nV bei 80 Werten/s [V: HX711-Datenblatt Tab. 2].

Gewicht eines Rauschwerts: σ = Rauschen ÷ (2 mV/V × AVDD) × 200 kg [A]

| AVDD | Signal bei 200 kg | σ je Einzelwert (10/s) | Mittel aus 10 Werten |
|---|---|---|---|
| **4,3 V (gewählt)** | 8,6 mV | **1,2 g** | ca. 0,4 g |
| 3,0 V (Alternative an 3,3 V) | 6,0 mV | 1,7 g | ca. 0,5 g |

**Bewertung:** Beide Varianten liegen weit unter dem, was ein Bienenstock braucht (Tagesschwankungen von einigen 100 g). Die 5-V-Speisung gibt rund 40 % mehr Signal und liegt näher an der Herstellerempfehlung. Im Feld bestimmen ohnehin Temperatur und Kriechen der Zelle die Genauigkeit, nicht das Rauschen des Wandlers [A].

## 6. Energie

- Last am 5-V-Ausgang: 10,6 mA Brücke + 1,5 mA HX711 = 12,1 mA
- Aus dem Akku bei 3,7 V und 85 % Wirkungsgrad: **ca. 19 mA** [A]
- Messdauer etwa 1,8 s: 400 ms Einschwingen, dann 10 Werte
- Das sind etwa **35 mAs je Messung**

Ergebnis in `energiebilanz.py`:

| | vorher (Annahme 2 × 1 kΩ an 3,3 V) | jetzt (1 × H40A an 5 V) |
|---|---|---|
| Szenario A, Tage ohne Laden (5 %/Monat Selbstentladung) | 210 | 200 |
| Szenario B | 292 | 273 |
| Ungünstigster Fall (SF12, Szenario A) | 132 | 128 |

Stand 09.10.2026: ein HX711, Flash dauernd versorgt, Ladesperre nur bei Sonne versorgt (Ruhestrom 15,7 µA; Szenario A 200 Tage, B 273 Tage, ungünstig 128 Tage).

Die Reserve bleibt groß. Sparen ließe sich noch mit kürzerem Einschwingen und 80 Werten/s, auf Kosten des Rauschens. Das ist eine Firmware-Frage.

## 7. Regeln für den Block

1. Nur Aufwärtswandler mit **fester Ausgangsspannung und echter Lasttrennung**; nie ein einstellbares Modul.
2. Wandler nur während der Messung an.
3. Wandler an SYS, nicht an der 3,3-V-Schiene.
4. DVDD der HX711 an 3,3 V (gleiche Pegel wie der STM32).
5. Analogmasse der HX711 und Wägezellen-Leitungen getrennt von Wandler und Funk führen; der Wandler sitzt weit weg vom Mikrofoneingang.
6. Signalleitungen der Zelle nur mit Bauteilen mit kleinem Leckstrom schützen.

## 8. Offene Prüfpunkte

1. TPS61240: Burst- oder PWM-Betrieb bei 25 mA, Welligkeit an VSUP, Strom bei 3,0 V Eingang
2. HX711: Stromaufnahme mit DVDD an und VSUP aus
3. Passende TVS für E± und ESD-Teil mit kleinem Leckstrom für S± auswählen
4. JLCPCB-Bestand TPS61240 (601 Stück) kurz vor der Bestellung, sonst MCP1640B
5. Temperaturgang der H40A unter −10 °C im Feld
6. Footprint WSON-6 2 × 2 mm (KiCad) mit der TI-Zeichnung DRV0006A vergleichen; Spule 1 µH (Isat ≥ 0,7 A) und Ferrite FB501/FB502 auswählen
7. Pinfolge des gelieferten S8550 (SOT-23) mit 1 B, 2 E, 3 C vergleichen
8. Kanal B über R507 an INA−: Einfluss auf Rauschen und Nullpunkt am Muster prüfen

## 9. Schaltplan (Blatt „Waage“, 10.10.2026)

Generator `hardware/kicad/hauptplatine.py`, Funktion `waage()`; Teile 5xx. Entwurf, T3 (ERC, Netzprüfung), kein Muster.

| Teil | Funktion |
|---|---|
| U501, L501, C501, C502, R501, R502 | TPS61240 an SYS; EN = WAAGE_EIN (PB10) mit 100 kΩ nach GND; 100 kΩ Entladung am 5-V-Ausgang |
| FB501, C503, C504 | Ferrit und Abblockung VSUP_HX |
| U502, Q501, R503, R504, C505–C508 | HX711, AVDD 4,30 V über S8550 und 20 k / 8,2 k; VBG 100 nF; DVDD an 3V3_SW |
| R508, R509 | je 1 kΩ zu PB9 (SCK) und PB8 (DOUT) |
| J501 (= J4), D501, FB502 | Klemme 5-polig, ESD TPD4E05U06 an E+, S+, S−, Ferrit in E+ |
| R505, R506, C510–C512 | 100 Ω in S±, 100 nF zwischen S+ und S−, je 10 nF C0G nach Masse |
| R507 | Kanal B an INA− (0 Ω) |

`netz_tests.py` prüft u. a. EN-Pull-down, Wandler an SYS, FB an VOUT, DVDD an 3V3_SW, AVDD aus den Teilerwerten (4,2–4,4 V und ≥ 0,1 V unter VSUP) und dass an S± nur Klemme, ESD-Baustein und Reihenwiderstand hängen.

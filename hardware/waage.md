# Block Waage (Lastenheft 0.4, F3 – Entwurf, 08.10.2026, geändert 09.10.2026)

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
| Ein/Aus | EN an **PB10** (neu belegt), Pull-down 100 kΩ: Im Standby ist der Wandler sicher aus. |
| Ruhestrom aus | 1,5 µA typ. [V, S. 5; das Kurzblatt nennt „< 1 µA“]. In der Energiebilanz enthalten (Ruhestrom gesamt 13,2 → 14,7 µA). |
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
| Kanal B | nicht genutzt (Eingänge mit 0 Ω auf Gleichtakt legen) [A] | |

**Zustand bei ausgeschaltetem 5-V-Wandler:** DVDD liegt dann noch an, VSUP/AVDD nicht. Das Datenblatt beschreibt diesen Zustand nicht. Die Firmware hält SCK low und schaltet die Sensorschiene nach der Messung ab. **[P]** Strom in diesem Zustand am Muster messen.

## 4. Anschluss der Wägezelle (Kabel 1,8 m)

| Leitung | Beschaltung [A] |
|---|---|
| E+ / E− (Speisung) | von AVDD/AGND; TVS-Diode 5 V nach Masse, Ferrit |
| S+ / S− (Signal) | je 100 Ω in Reihe, 100 nF zwischen S+ und S−, je 10 nF nach Masse. Keine TVS mit Leckstrom über ca. 100 nA (100 nA × 100 Ω = 10 µV, das sind etwa 0,2 kg). |
| Schirm | nur auf der Platinenseite an Masse, an der Zelle offen |
| Klemme | steckbare Schraubklemme 5-polig (E+, E−, S+, S−, Schirm), Raster 3,5 mm, beschriftet |

Die Reihenwiderstände in S+/S− verändern die Empfindlichkeit nicht, weil der HX711-Eingang hochohmig ist. Die Waage wird ohnehin kalibriert.

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

Stand 09.10.2026: ein HX711, Flash dauernd versorgt, TMP390-Ladesperre (Ruhestrom 16,6 µA; Szenario A 199 Tage, B 272 Tage, ungünstig 128 Tage).

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

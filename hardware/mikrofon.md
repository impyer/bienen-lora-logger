# Block Mikrofon (Lastenheft 0.4, F6 und 2.2 – Entwurf; neu seit HW-07 am 14.10.2026)

Kennzeichnung:
- **[V]** im Datenblatt gelesen
- **[A]** Annahme oder Rechnung
- **[P]** vor dem Schaltplan bzw. am Muster prüfen

Bezug:
- Entscheidung **HW-07** (`docs/entwicklung/entscheidungen.md`): zwei Mikrofone verschiedener Bauart am Audio-ADC; ersetzt GY-MAX4466 mit Analogfilter an PA1 (Stand bis 13.10.2026 im Git-Verlauf)
- `docs/fft-konzept.md`: Auswertung bei 2048 Hz, Nutzband 60–900 Hz
- Lastenheft F6, A1–A7; Befund HW26-05 (Anti-Aliasing, Kalibrierung)
- Rechnung reproduzierbar: `python3 hardware/mikrofon_filter.py` (Taktplan, Vorspannung, Hochpass, Kabellast, Dezimation)

## 1. Aufgabe und Prinzip

Zwei Mikrofone sitzen **dicht nebeneinander im Mikrofonkopf auf dem Gitterboden** und messen dasselbe Schallfeld:

| Kanal | Mikrofon | Signal | Eingang am ADC |
|---|---|---|---|
| links | Elektretkapsel (Typ offen [P]) | analog, pseudo-differenziell über ein Kabelpaar | IN2L(P) / IN3L(M) |
| rechts | **Infineon IM69D127** auf fertiger Platine (IP57 auf Bauteilebene [V]) | PDM (1 Bit) | DMDIN / DMCLK |

Beide sind kapazitive Druckempfänger; verschieden sind Bauform, Alterung und typische Ausfälle (Elektret: Drift bei Feuchte, hochohmiges Signal; MEMS: kleine Schallöffnung, kann verkleben) [A]. **Zweck ist die Plausibilisierung:** Weicht ein Kanal im Spektrum oder Pegel vom anderen ab, wird der Messwert markiert statt als Veränderung des Volkes gedeutet. Mitteln bringt nur etwa 3 dB [A]. Gemeinsame Störungen (Regen, Wind, Verkehr durch das offene Gitter) zeigen sich in beiden Kanälen.

Der **Audio-ADC TI TLV320ADC3101** erledigt Verstärkung, Anti-Aliasing (Delta-Sigma mit digitalem Dezimationsfilter) und das PDM-Mikrofon. Nur der 3101 hat den Digitalmikrofon-Eingang, der 3100 nicht [V: TI E2E, Datenblatt-Vergleichstabelle]. Digitalmikrofon und Analogeingang sind **je Kanal** wählbar („only-left, only-right, or stereo“, Abschnitt 10.3.12.6) [V].

## 2. Schaltung (Blatt Mikrofon, Teile 6xx)

```
Mikrofonkopf (Gitterboden)        Cat7 S/FTP 0,5–1 m, RJ45 (T568B)   Hauptplatine (RJ45 J601, geschirmt)
Elektret ─ MIC+ ───────────── Paar 7/8 ───── J601.7 ─┬ 100 pF ┬ ESD ─ 1 µF ─ IN2L(P) ┐
         └ MIC− ───────────── Paar 7/8 ───── J601.8 ─┴ 100 pF ┴ ESD ─ 1 µF ─ IN3L(M) │  U601
           MICBIAS 2,5 V ─ 1 kΩ ─ MIC+ ;  MIC− ─ 1 kΩ ─ GND (symmetrisch)            │  TLV320ADC3101
IM69D127 ─ DATA ─ ca.100 Ω ── Paar 3/6 ───── J601.3 ─ ESD ─ 22 Ω ─ DMDIN          │  I²S → PB12/PA15/PB5
         ─ CLK ─────────────── Paar 1/2 ───── J601.2 ─ ESD ─ 33 Ω ─ 74LVC1G17 ─ DMCLK┘  I²C 0x18
         ─ VDD/GND ─────────── Paar 4/5 ───── J601.4/5 ─ 3V3_MEMS (Ferrit, 1 µF);  Schirm → SH
```

### 2.1 Bauteile

| Ref. | Wert | Aufgabe / Quelle |
|---|---|---|
| U601 | TLV320ADC3101IRGET (VQFN-24, RGE) | Audio-ADC; Pinbelegung SLAS553B Abschnitt 7 [V]; Thermal-Pad an AVSS [V]; Gehäusevariante RGE0024B (EP 2,45 mm) im Footprint, RGE0024F prüfen [P] |
| U602, C609, C610 | TPS70918DBVR, 1 µF, 4,7 µF | DVDD 1,8 V (1,65–1,95 V [V]); gleiche Familie und Pinfolge wie U204 [V] |
| FB601, R602, C601, C602 | 600 Ω, 10 Ω, 22 µF, 100 nF | AVDD = 3V3_ANA aus 3V3_SW (A1); 10 Ω statt 47 Ω, weil AVDD + MICBIAS einige mA ziehen [A] |
| C612–C617 | je 100 nF + 1 µF | AVDD, DVDD, IOVDD (TI Abb. 48) [V] |
| R609, C618 | 10 kΩ, 100 nF | Reset nach dem Einschalten (Versorgungen zuerst stabil, Abschnitt 10.3.1 [V]); danach Software-Reset über I²C; kein freier GPIO [A] |
| R610, R611, C621 | 2 × 1 kΩ, 1 µF | Elektret-Vorspannung aus MICBIAS1 (2,5 V, max. 4 mA [V]), symmetrisch: Kapsel schwebt über dem Paar |
| C619, C620 | 2 × 1 µF X7R | Koppelkondensatoren; mit ca. 35 kΩ Eingangswiderstand 4,5 Hz [V/A] |
| C622, C623 | 2 × 100 pF C0G | HF-Ableitung an der Klemme |
| U603, C624 | 74LVC1G17, 100 nF | Schmitt-Puffer für den PDM-Takt ins Kabel; Pinbelegung Herstellerdatenblatt prüfen [P] |
| R612, R613 | 33 Ω, 22 Ω | Takt-Serienwiderstand; Schutz vor DMDIN |
| FB602, C611 | 600 Ω, 1 µF | 3V3_MEMS über das Kabel zum IM69D127 (1,65–3,6 V [V]) |
| J601, D601 | RJ45 geschirmt ohne Übertrager (Footprint-Vorschlag RCH RC01937; Teil wählt der Layouter), ESDS304 | Buchse (= J5): 1 GND, 2 CLK, 3 DATA, 4 VDD, 5 GND, 6 GND, 7 MIC+, 8 MIC−, SH Schirm; ESD an CLK, DATA, MIC+, MIC− |

### 2.2 Taktplan (Rechnung `mikrofon_filter.py`)

| Größe | Wert | Grenze |
|---|---|---|
| Abtastrate fS | **24 576 Hz** (3 × 8192) | ADC 8–48 kHz [V] |
| AOSR | 128 (Filter A) | Filter A mit AOSR 64 oder 128 [V] |
| DMCLK = AOSR · fS | **3,146 MHz** | 2,8–6,2 MHz für den ADC [V, Gl. 6]; IM69D127 nur 2,9–3,3 MHz, Zwischenwerte zu 1,38–1,7 MHz nicht erlaubt [V] |
| BCLK (STM32 I²S-Master, 2 × 32 Bit) | 1,573 MHz | PLL-Eingang 0,512–20 MHz [V] |
| PLL des ADC | P 1, J 32, D 0, R 2 → 100,66 MHz | 80–110 MHz, J 4–55 [V] |
| Teiler | NADC 8, MADC 4 | PLL = NADC · MADC · AOSR · fS (genau) |
| STM32 PLLI2S | N 302, R 2 → I2SCLK 151 MHz, DIV 48 → fS 24 576,8 Hz | Abweichung 0,003 % [A]; RM0383 prüfen [P] |

Bei 3,072 MHz nennt Infineon 69 dB(A) Rauschabstand und 0,98 mA [V]. Der STM32 dezimiert danach mit FIR um den Faktor 12 auf 2048 Hz (Sperrbereich ab ca. 1150 Hz) und wertet wie bisher 60–900 Hz aus [A].

## 3. Anbindung an den STM32 (HW-07)

| Signal | Pin | Funktion |
|---|---|---|
| I2S_CK | PB12 | I2S3_CK, STM32 ist Master |
| I2S_WS | PA15 | I2S3_WS; setzt „nur SWD“ voraus (JTDI frei) |
| I2S_SD | PB5 | I2S3_SD, Empfang mit DMA |
| I2C_SCL / I2C_SDA | PB6 / PB7 | Einstellung des ADC, Adresse 0x18 (I2C_ADR0/1 an GND) [V] |
| Sensorschiene | **PA1** (vorher PB5) | ON des TPS22917 |

Pins laut STM32-Pin-Daten (ST open pin data, UFQFPN48) [V]. Folge: Am Erweiterungsstecker J11 sind keine freien GPIOs mehr (Pins 9–11 frei).

## 4. Regeln für den Ablauf (Firmware)

1. **Während der Mikrofonmessung kein Funk und kein 5-V-Wandler** (Lastenheft A5). Reihenfolge: Waage → Wandler aus → Mikrofone → Senden.
2. Einschalten: 3V3_SW an → ≥ 2 ms warten (Reset-RC 1 ms) → Software-Reset über I²C → PLL, Teiler, AOSR, Kanäle einstellen (Ablauf TI 11.2.2.2) → PLL ≥ 10 ms einschwingen lassen [V] → Koppelkondensatoren einschwingen (Zeitkonstante 35 ms, also ≥ 200 ms verwerfen) [A].
3. **AGC aus**, feste Verstärkung für beide Kanäle, damit Pegel zwischen Kanälen und Loggern vergleichbar sind (HW26-05). Pegel bleiben dBFS, kein Schalldruck.
4. Je Messung zusätzlich eine **Kanalvergleichs-Kennzahl** (Pegelverhältnis und Kohärenz im Nutzband); per Funk nur 1 Byte [A].
5. **Keine Rückspeisung:** Ist 3V3_SW aus, sind die I²S- und I²C-Pins hochohmig bzw. analog. Sonst speist der STM32 über die Schutzdioden in U601.

## 5. Kabel und Einbau

- Mikrofonkopf auf dem Gitterboden, wird bei der Durchsicht nicht bewegt (Philipp). Schallöffnungen **seitlich oder nach unten** (Gemüll, Tropfwasser) [A]; Schutz gegen Bienen durch einen Königinnenkäfig als mechanische Barriere; vorerst keine zusätzliche akustische Membran.
- **Cat7 S/FTP** mit geschirmtem, feldkonfektionierbarem RJ45-Stecker, fest verlegt, **0,5–1 m**. Paare nach T568B: 1/2 GND + CLK, 3/6 DATA + GND, 4/5 VDD + GND, 7/8 MIC+ / MIC− (Elektret am Rand des Steckers, weit weg vom Takt). Schirm über das Steckergehäuse an SH, nur am Logger an Masse. Am Mikrofonkopf Adern direkt anlöten. **Kein Netzwerk- oder PoE-Gerät anstecken** (Beschriftung).
- **Kabellast:** DATA höchstens 200 pF, Taktflanke am Mikrofon höchstens 13 ns [V Infineon]. Gerechnet bei 1 m: ca. 117 pF und ca. 12 ns [A] – knapp. **Länger als 1 m nur mit Treiber im Mikrofonkopf.** Flanke am Muster messen (T4).
- Dichtung: Lötstellen und Kabelübergang mit neutral vernetzendem Silikon (K-705 nur, wenn nicht essigsauer [P]); außen Schrumpfschlauch mit Innenkleber auf angerautem Mantel; Schutzlack nicht in die Schallöffnung. Gegen Mäuse im Bodenbereich Geflechtschlauch [A].
- Auf der Platine: ADC nahe der Klemme, weit weg von Funkmodul, SPI und 5-V-Wandler (A3).

## 6. Energie

ADC stereo ca. 14 mW bei 24,6 kHz (TI: 11 mW bei 8 kHz, 17 mW bei 48 kHz [V], dazwischen [A]) ≈ 4,2 mA, IM69D127 ca. 1 mA, Elektret ca. 0,3 mA: zusammen ca. **5,5 mA für 1,5 s ≈ 8 mAs je Messung** (`energiebilanz.py`; vorher 0,4 mAs). Reichweite ohne Laden sinkt um wenige Prozent (versorgung.md, Tabelle „Reichweite“).

## 7. Offene Prüfpunkte

1. Elektretkapsel wählen: Strom ≤ 0,5 mA, Betrieb ab 1,5 V, Empfindlichkeit; Ersatz für den bisherigen GY-MAX4466-Weg
2. Fertige IM69D127-Platine: Pinbelegung, L/R-Wahl, 100 nF und Reihenwiderstand in DATA vorhanden? Anschluss an Paar 1–3 festlegen
3. LCSC: TLV320ADC3101IRGET, TPS70918DBVR, 74LVC1G17 (SC-70-5), RJ45 geschirmt ohne Übertrager (Layouter)
4. Taktflanke und DATA-Signal am Mikrofon mit 1 m Kabel messen (T4)
5. Registerwerte (PLL, NADC/MADC, AOSR, Ressourcenklasse des Verarbeitungsblocks, Digitalmikrofon nur rechts) am Muster bestätigen
6. RM0383: I2S3 als Master-Empfang mit DMA, PLLI2S-Werte
7. Zwei Logger mit demselben Prüfton vergleichen; Kanalvergleich bei verklebtem Mikrofon (Wachs auf der Öffnung) erproben (HW26-05)

## 8. Prüfung im Entwurf (14.10.2026)

Geprüft (T3, lokal mit KiCad 10.0.6): `netz_tests.py` prüft Versorgungen, I²S/I²C-Anschluss, Elektret-Vorspannung und Koppel-C, PDM-Weg und J5/J601 gegen `anschluesse.md` (mit Gegenprobe vertauschter Adern); ERC 0; Pin-/Footprint-Abgleich 0 Abweichungen. `mikrofon_filter.py` prüft den Taktplan gegen die Datenblattgrenzen. Messungen am Muster (T4) stehen aus.

# Block Mikrofon (Lastenheft 0.4, F6 und 2.2 – Entwurf, 08.10.2026)

Kennzeichnung:
- **[V]** im Datenblatt gelesen
- **[A]** Annahme oder Rechnung
- **[P]** vor dem Schaltplan bzw. am Muster prüfen

Bezug:
- `docs/fft-konzept.md`: ADC 8192 Hz, digitale Dezimierung auf 2048 Hz, Auswertung 60–900 Hz
- Lastenheft A1–A7
- Befund HW26-05 (Anti-Aliasing, Kalibrierung)

Frequenzgang reproduzierbar: `python3 hardware/mikrofon_filter.py`.

## 1. Aufgabe des Analogteils

Die Firmware tastet mit 8192 Hz ab. Töne über 4096 Hz werden dabei gespiegelt. Die digitale Dezimierung (FIR, 127 Koeffizienten) entfernt danach alles zwischen 1025 und 4096 Hz.

**Was sie nicht mehr entfernen kann:** Töne zwischen **7168 und 8192 Hz** fallen direkt auf 0–1024 Hz, also ins Nutzband. Ein Ton bei 7292 Hz erscheint zum Beispiel als 900 Hz. Diese Frequenzen muss der analoge Tiefpass vor dem ADC dämpfen. Das Elektret-Mikrofon nimmt bis 20 kHz auf [V: Adafruit, Kapsel CMA-4544PF-W].

## 2. Schaltung

```
GY-MAX4466 (im Stock) ─ 1 kΩ (am Modul) ──Kabel ≤ 2 m, abgeschirmt──► Klemme
                                               │ OUT ─ 100 Ω ─┬─ ESD ─ GND
                                               │              └─ 220 nF ─┬─ 33 kΩ ─ VREF (1,65 V)
                                               │                         └─ Sallen-Key 2. Ordnung (LMV321) ─ 3,3 kΩ ─┬─ PA1 (ADC1_IN1)
                                               │                                                                     └─ 10 nF ─ GND
                                               │ VCC ◄── 3V3_ANA ◄─ 47 Ω ◄─ Ferrit ◄─ geschaltete 3,3-V-Schiene
                                               │                     └─ 22 µF + 100 nF
                                               └ GND, Schirm (nur hier an Masse)
VREF: 3V3_ANA ─ 47 kΩ ─┬─ 47 kΩ ─ GND, 1 µF nach GND
```

### 2.1 Bauteile

| Stufe | Bauteile | Wert | Quelle |
|---|---|---|---|
| Mikrofonmodul | GY-MAX4466 (Elektret + MAX4466), Verstärkung 25–125 am Poti | Versorgung 2,4–5,5 V, Ausgang Rail-to-Rail | [V: Adafruit, ADI MAX4466] |
| **Trennwiderstand am Modul** | **1 kΩ direkt am Ausgang des Moduls**, im Kabelende (Schrumpfschlauch) oder auf einer kleinen Adapterplatine | Der MAX4466 ist nur bis **100 pF** Last stabil (bei Verstärkung 5) [V: ADI-Datenblatt]. Das Kabel bringt 0,5–0,8 nF (siehe 5). Ohne Widerstand kann der Verstärker schwingen. | [V]/[A] |
| Versorgung 3V3_ANA | Ferrit 600 Ω bei 100 MHz + 47 Ω + 22 µF + 100 nF, hinter dem Sensorschalter | Grenzfrequenz RC ca. 150 Hz; Spannungsabfall bei 0,5 mA ca. 25 mV | [A], Lastenheft A1 |
| Vorspannung VREF | 2 × 47 kΩ + 1 µF | 1,65 V = Mitte des ADC-Bereichs; Zeitkonstante 24 ms | [A] |
| Hochpass | 220 nF in Reihe, 33 kΩ nach VREF | ca. 22–25 Hz (mit der Eingangsimpedanz des Filters) | [A], Lastenheft A2 |
| Tiefpass | Sallen-Key, Verstärkung 1: R1 = R2 = 9,1 kΩ, C1 = 22 nF (Rückkopplung), C2 = 10 nF (nach Masse) | **1179 Hz, Q = 0,74** (nahe Butterworth) | gerechnet, `mikrofon_filter.py` |
| Operationsverstärker | **LMV321TP-TR** (3PEAK), Rail-to-Rail Ein/Aus, 1,27 MHz, 45 µA, 2,1–6 V, SOT-23-5, LCSC C90297 (Extended) | | [V: JLCPCB-Teileseite] |
| RC vor dem ADC | 3,3 kΩ + 10 nF C0G | 4,8 kHz; der 10-nF-Kondensator lädt zugleich den Abtastkondensator des ADC (≈ 4 pF) | [A] |
| Schutz am Eingang | 100 Ω in Reihe, ESD-Diode an OUT und VCC der Klemme | **[P]** Teil wählen (kleine Kapazität, 3,3 V) | [A] |

Ersatz für den Operationsverstärker: TLV9001 oder MCP6001. Der MCP6001 (LCSC C116490) ist am 08.10.2026 bei LCSC nicht lieferbar [V].

### 2.2 Frequenzgang (Rechnung)

Mit Trennwiderstand 1 kΩ und 2 m Kabel (0,8 nF):

| Frequenz | Dämpfung | Bedeutung |
|---|---|---|
| 20 Hz | −3,6 dB | Rumpeln, Klopfen |
| 50 Hz | −1,0 dB | Netzbrummen (die Firmware wertet erst ab 60 Hz aus) |
| 60 Hz | −0,8 dB | untere Bandgrenze |
| 250 Hz | −0,3 dB | Summen |
| 900 Hz | −1,3 dB | obere Bandgrenze |
| 4096 Hz | −24 dB | halbe Abtastfrequenz |
| **7168 Hz** | **−36,7 dB** | erste Spiegelung ins Nutzband |
| 7292 Hz | −37,1 dB | spiegelt auf 900 Hz |
| 8132 Hz | −39,7 dB | spiegelt auf 60 Hz |
| 15360 Hz | −55 dB | erste Spiegelung, falls mit 16384 Hz abgetastet wird |

- Trennwiderstand und Kabel bilden einen Tiefpass bei etwa 200 kHz. Er wirkt im Nutzband nicht. Der Widerstand kostet mit dem 33-kΩ-Eingang etwa 0,3 dB gleichmäßig über alle Frequenzen.
- **Im Nutzband** schwankt der Pegel zwischen −0,3 und −1,35 dB. Der Frequenzgang ist bekannt; die Firmware kann die Bandpegel damit korrigieren.
- **Gegen Spiegelfrequenzen** sind es 36–39 dB. Das deckt sich mit der Abschätzung im FFT-Konzept (30–35 dB für ein Filter 2. Ordnung). Der zusätzliche RC-Tiefpass bringt die fehlenden dB.
- **Wenn das nicht reicht** (Störer im Stock über 7 kHz, z. B. Wespen oder Regen auf dem Deckel [A]): Abtastrate auf **16384 Hz** verdoppeln, dann **55 dB**. Das ist nur eine Firmware-Änderung (FIR mit Dezimierung 8), keine Platinenänderung.
- Zusätzlich begrenzt der MAX4466 bei hoher Verstärkung selbst die Bandbreite: 600 kHz Verstärkungs-Bandbreite ÷ 125 ≈ 4,8 kHz [A, aus dem MAX4466-Datenblatt gerechnet]. Das hilft, ist aber vom Poti abhängig und wird nicht eingerechnet.
- Die Rechnung behandelt den Hochpass als unbelastet. **[P]** Mit einer Schaltungssimulation oder am Muster nachmessen (Tongenerator 20 Hz–10 kHz).

## 3. Abtastung im STM32

| Punkt | Festlegung |
|---|---|
| Eingang | PA1 = ADC1_IN1 |
| Takt | Timer TIM2 oder TIM3 mit TRGO löst den ADC aus (8192 Hz) [V: ST HAL, F4-Familie; **[P]** RM0383 Tab. 42] |
| Übertragung | DMA2 Stream 0, Kanal 0 in den Puffer [A; **[P]** RM0383 Tab. 28] |
| Gegenüber Firmware 261010 | Dort wird über Register mit Abfrage abgetastet und über den DWT-Zähler getaktet (FW26-07). Für die eigene Platine ist **Timer + DMA** Pflicht (Lastenheft A7): gleichmäßiger Takt, keine verpassten Abtastungen, CPU kann schlafen. |
| VDDA | über Ferrit von 3,3 V, 100 nF + 1 µF (mcu-funk.md 1.1) |

## 4. Regeln für den Ablauf (Firmware)

1. **Während der Mikrofonmessung kein Funk und kein 5-V-Wandler** (Lastenheft A5). Der Wandler der Waage taktet mit 3,5 MHz; seine Störungen sollen nicht ins Spektrum kommen. Reihenfolge: Waage → Wandler aus → Mikrofon → Senden.
2. Nach dem Einschalten der Sensorschiene **mindestens 150 ms warten** [A]: VREF schwingt mit 24 ms Zeitkonstante ein, der Hochpass mit etwa 7 ms, das Modul selbst ist unbekannt **[P]**. Die Firmware 261010 wartet 100 ms (`MIC_EINSCHWINGEN_MS`).
3. Pegel bleiben **dBFS**, also relativ zum ADC. Das ist kein Schalldruck in dB SPL (HW26-05). Vergleiche zwischen Loggern nur nach gleicher Poti-Einstellung bzw. nach einer Kalibrierung mit demselben Prüfton.

## 5. Kabel und Einbau

- Kabel LiYCY 3 × 0,14 mm² (VCC, GND, OUT) mit Schirm, **höchstens 2 m** (Philipp, 08.10.2026); **Schirm nur an der Platine** auf Masse (Lastenheft A4).
- Kapazität laut Lapp-Datenblatt (UNITRONIC LiYCY): ca. 120 pF/m Ader/Ader und 160 pF/m Ader/Schirm [V]. Die Ader OUT sieht damit gegen GND, VCC und Schirm zusammen etwa 0,4 nF/m, bei 2 m also **0,5–0,8 nF** [A]. Daher der Trennwiderstand am Modul (2.1).
- Spannungsabfall auf VCC/GND bei 0,3 mA und 2 m: unter 1 mV [A]. Kein Thema.
- Klemme steckbar, 4-polig (VCC, GND, OUT, Schirm), Raster 3,5 mm, beschriftet.
- Mikrofonleitung auf der Platine **weit weg von Funkmodul, SPI und 5-V-Wandler** (Lastenheft A3).
- Analogmasse: eine durchgehende Massefläche; der Filter liegt nahe an PA1, der Rückstrom des Wandlers fließt nicht unter dem Filter durch [A, HW26-04-Hinweis des Reviews zur Massefläche].

## 6. Energie

Modul (ca. 0,3 mA, geschätzt) + LMV321 (45 µA) + VREF (35 µA) ≈ 0,4 mA für etwa 1,5 s je Messung, also rund 0,6 mAs. In `energiebilanz.py` stehen dafür schon 0,4 mAs; der Unterschied ist vernachlässigbar.

## 7. Offene Prüfpunkte

1. GY-MAX4466: Gleichspannung am Ausgang, Ausgangswiderstand, Stromaufnahme und Einschwingzeit messen. Das Modul hat kein offizielles Schaltbild.
2. Mikrofon mit 1-kΩ-Trennwiderstand und 2 m Kabel am Oszilloskop auf Schwingen prüfen (Rechteck- oder Sinuston, höchste Poti-Stellung)
3. Frequenzgang des Filters am Muster messen (Tongenerator oder Handy-App, 20 Hz–10 kHz)
4. ESD-Diode für die Mikrofonklemme wählen
5. RM0383 Tab. 42 und 28 (ADC-Auslöser und DMA) bestätigen
6. Zwei Logger mit demselben Prüfton vergleichen (HW26-05)

# Prüfbericht: HW-07 (zwei Mikrofone am Audio-ADC) und HW-08 (Layout extern, Platine nur Rahmen)

- **Prüfbericht-ID:** SCH-2026-10-14-HW07-HW08
- **Prüfdatum (UTC):** 14.10.2026
- **Bezug:** Entscheidungen HW-07 und HW-08 (Philipp, 14.10.2026); Befund HW26-05; Lastenheft F6, A1–A7, M4, M5, M9
- **Ausgangs-SHA:** `bbabcd4` + gelieferte, noch nicht gepushte Stände HW-05/HW-06 und Aufräumen (14.10.2026)
- **Artefakte:**
  - `hardware/kicad/hauptplatine.py`: Blatt „Mikrofon“ neu (U601 TLV320ADC3101, U602 TPS70918, U603 74LVC1G17, J601 RJ45 geschirmt, D601); Blatt MCU: PB12/PA15/PB5 = I2S3, PA1 = SENSOR_EIN; J704 Pins 9/10 frei
  - `werkzeug/symbole.py` (Symbol TLV320ADC3101), `netz_tests.py`, `pin_footprint.py`
  - `hardware/mikrofon_filter.py`: neu als Rechnung zu Taktplan, Vorspannung, Hochpass, Kabellast, Dezimation (vorher Analogfilter)
  - `hardware/energiebilanz.py`: Mikrofon-Eintrag 5,5 mA × 1,5 s
  - `hauptplatine/logger.kicad_pcb`: nur Rahmen (`platine_start.py`); entfernt: `platine_bestuecken.py`, `platine_fein.py`, `platine_lagen.py`, `platine_fanout.py`, `platine_routen.py`, `platine_nachrouten.py`, `platine_aufraeumen.py`
  - Dokumente: `mikrofon.md` (neu), Lastenheft, `anschluesse.md`, `mcu-funk.md`, `versorgung.md`, `beep-vergleich.md`, Entscheidungs- und Befundregister, READMEs
- **Änderungsklasse:** D1 (Messkette Mikrofon, Pinbelegung; keine Akku-/Ladefunktion betroffen)
- **Teststufe:** T0 (Datenblattabgleich) und T3 (KiCad 10.0.6: ERC, Netzprüfung, Pin-/Footprint-Abgleich). Keine Messung, kein Muster.

## Entwurf

- **Zwei Mikrofone, ein Schallfeld:** Elektretkapsel (analog, pseudo-differenziell: MICBIAS 2,5 V über 1 kΩ an MIC+, MIC− über 1 kΩ an GND, Kopplung 2 × 1 µF) und MEMS Infineon IM69D127 (PDM) im selben Kopf auf dem Gitterboden. Zweck ist die Plausibilisierung durch Kanalvergleich, nicht die Mittelung.
- **Audio-ADC TLV320ADC3101:** Digitalmikrofon je Kanal wählbar („only-left, only-right, or stereo“, SLAS553B 10.3.12.6) [V]; der TLV320ADC3100 hat keinen Digitalmikrofon-Eingang (TI E2E, Vergleichstabelle im 3101-Datenblatt) [V].
- **Taktplan** (`mikrofon_filter.py`, alle Grenzen eingehalten): fS 24 576 Hz, AOSR 128, DMCLK = AOSR · fS = 3,146 MHz (ADC: 2,8–6,2 MHz [V]; IM69D127: 2,9–3,3 MHz [V]); PLL aus BCLK 1,573 MHz, J 32, R 2 → 100,66 MHz (80–110 MHz, J 4–55 [V]); NADC 8, MADC 4; MADC · AOSR = 512 ≥ 188 Befehle PRB_R1 [V]. Datenblatt-Unstimmigkeit: 11.2.2.1 Gl. 8 verweist für die Ressourcenklasse auf Tab. 5, die diese Spalte nicht hat [P].
- **STM32:** I2S3 als Master-Empfang: PB12 CK, PA15 WS, PB5 SD laut ST open pin data (UFQFPN48) [V]; Sensorschiene PB5 → PA1. Folge: am Erweiterungsstecker J11 keine freien GPIOs mehr. PLLI2S N 302, R 2, DIV 48 → 24 576,8 Hz [A].
- **Kabel und Buchse:** Cat7 S/FTP 0,5–1 m mit geschirmtem RJ45 (T568B: 1/2 GND+CLK, 3/6 DATA+GND, 4/5 VDD+GND, 7/8 MIC+/MIC−). Die 8-polige DEGSON-Klemme (30 mm) hätte nicht mehr in die Klemmenreihe gepasst; RJ45 ist ca. 16 mm breit (Philipp, 14.10.2026). Gerechnet: DATA-Last bei 1 m ca. 117 pF ≤ 200 pF, Taktflanke ca. 12 ns ≤ 13 ns [V Grenzen, A Rechnung] – knapp; über 1 m nur mit Treiber im Mikrofonkopf.
- **Risiko RJ45:** Ein PoE-Netzwerkkabel würde den Eingang zerstören; Beschriftung und fest angeschlossenes Kabel (`anschluesse.md` 1.1).

## HW-08: Platine

Philipp, 14.10.2026: Platzierung und Anschlusslage soll der Layouter festlegen, damit er nicht eingeschränkt ist. `logger.kicad_pcb` wurde neu nur mit dem Rahmen angelegt (Umriss, Löcher mit Sperrflächen, 4 Lagen, Regeln, Hinweise auf User.1). Die Projektdatei `logger.kicad_pro` blieb erhalten (`platine_start.py` hätte die Wurzelblatt-Angabe geleert; wiederhergestellt). DRC des Rahmens mit Schaltplanabgleich: 0 Verstöße, 172 fehlende Footprints (gewollt, Import durch den Layouter).

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Erzeugung zweimal identisch | bestanden |
| ERC Hauptplatine (alle Schweregrade) | **0 Meldungen** |
| Netzprüfung | **187/187** (Mikrofonprüfungen neu: Versorgungen, I²S/I²C, Vorspannung, Koppel-C, PDM-Weg, RJ45 gegen `anschluesse.md` mit Gegenprobe CLK/DATA; J11 Pins 9–11 frei; SENSOR_EIN an PA1) |
| Pin-/Footprint-Abgleich | 172 Bauteile, 0 Abweichungen (TLV320ADC3101 [V]; 74LVC1G17 und RJ45 [A] [P]) |
| `hardware/mikrofon_filter.py` | alle Grenzen eingehalten |
| `tests/alle_tests_linux.sh` | rc = 0 |
| DRC Rahmen | 0 Verstöße, 172 fehlende Footprints (gewollt) |

## Grenzen und offene Hardwaretests

- Keine Messung. Taktflanke, PDM-Signal und Elektretpegel am Muster mit 1 m Kabel messen (T4).
- Elektretkapsel und fertige IM69D127-Platine noch nicht festgelegt (Pinbelegung, 100 nF, Reihenwiderstand, L/R).
- LCSC/Bestand: TLV320ADC3101IRGET, TPS70918DBVR, 74LVC1G17, RJ45 (Layouter); Gehäusevariante RGE0024F gegen den Footprint (RGE0024B, EP 2,45 mm) prüfen.
- Firmware: I2S3-DMA, ADC-Initialisierung (TI 11.2.2.2), FIR-Dezimation 24 576 → 2048 Hz, Kanalvergleichs-Kennzahl; Pins bei abgeschalteter Schiene hochohmig.
- Gegenlesen durch einen zweiten Prüfweg steht aus.

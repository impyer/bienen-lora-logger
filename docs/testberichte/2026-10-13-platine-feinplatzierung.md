# Prüfbericht: Hauptplatine – Feinplatzierung der kritischen Gruppen, Massefläche L2

- **Prüfbericht-ID:** PCB-2026-10-13-FEIN
- **Prüfdatum (UTC):** 13.10.2026
- **Bezug:** `mcu-funk.md` 1.1/1.2 (Abblockung, Quarze, AN2867/AN4488), 2.2 (Pufferkondensatoren Funkmodul); `waage.md`/TI TPS61240 (Schleife des Wandlers); `versorgung.md` (Thermal-Pad BQ25185); Lastenheft M8 (L2 durchgehende Masse)
- **Ausgangs-SHA:** `751de0f`
- **Artefakt:** `hardware/kicad/werkzeug/platine_fein.py` (neu) → `hardware/kicad/hauptplatine/logger.kicad_pcb`
- **Änderungsklasse:** D1 (Layout); keine D3-Inhalte
- **Teststufe:** T3 (KiCad 10.0.6 DRC mit Schaltplanabgleich). Kein Layout-Review, kein Routing, kein T4.

## Umsetzung

`platine_fein.py` setzt 34 Bauteile relativ zu ihrem Bezugs-IC, legt 13 Masse-Vias in Thermal-Pads an und eine durchgehende GND-Fläche auf L2. Es ist wiederholbar: absolute Lagen, Vias nur, wo noch keine liegen, die Fläche nur einmal. Andere Bauteile bleiben unverändert.

| Gruppe | Umsetzung | Abstand Kondensator-/Bauteilpad zum Pin |
|---|---|---|
| STM32 U301: 100 nF je VDD/VSS-Paar | C301 (Pin 48/47, Nord), C302 (36/35, Ost), C303 (24/23, Süd), C308 (VBAT, Pin 1) | 1,7 / 1,7 / 1,7 / 2,0 mm |
| STM32: VCAP, VDDA | C307 4,7 µF an Pin 22; C305 100 nF + C306 1 µF + FB301 an Pin 9 | 3,1 mm; 2,2 mm |
| STM32: Quarze | Y302 (32,768 kHz) nordwestlich, Y301 (25 MHz) westlich, Lastkondensatoren jeweils außen | LSE 4,1/6,0 mm, HSE 4,6/5,8 mm |
| STM32: BOOT0/BOOT1/NRST | R301 an Pin 44, R302 an Pin 20, C309 an NRST | 1,8 mm; –; 7,9 mm (unkritisch) |
| Ra-01SH U401: Puffer an Pin 3 | C403 100 nF, D401 TVS, C402 10 µF, C401 100 µF links neben dem Modul, von innen nach außen | 3,6 / 5,0 / 5,8 / 8,8 mm |
| Ra-01SH: SPI | Reihenwiderstände R401–R404 rechts auf Höhe der Pins 12–15, R405 (NSS-Pull-up) daneben; JP401/JP402 an Pin 5/11 | – |
| TPS61240 U501 | CIN C501 über dem IC zwischen VIN (Pin 6) und GND (Pin 1); L501 rechts zwischen VIN und L (Pin 5); COUT C502 links an VOUT/GND | 1,6–2,4 mm |
| Thermal-Pads (GND) | U201 2 Vias (TI DLH0010A), U301 9 Vias (Raster 1,4 mm), U501 2 Vias; Via 0,6/0,3 mm | – |
| L2 | Zone „GND_L2“ über die ganze Platine (Sperrflächen der Befestigungslöcher bleiben frei) | – |

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| DRC Kupfer, Courtyard, Abstände, Lötstoppbrücken | **0 Verstöße** |
| Schaltplanabgleich | 0 Abweichungen |
| Offene Verbindungen | 323 (vorher 344; Masseanschlüsse über die Vias an L2) |
| Bestückungsdruck | nur Warnungen (Referenzen 0,8 mm in Bauteilmitte bei den dicht gesetzten Teilen; vor der Bestellung aufräumen) |

## Offen

- **Vias in Thermal-Pads [P]:** Ohne Füllung kann Lot in die Vias laufen. TI empfiehlt verfüllte oder abgedeckte Vias. Bei JLCPCB die Option „Epoxy filled & capped“ für 4 Lagen und ihren Preis prüfen; sonst tented Vias von unten.
- LSE-Leitungen 4–6 mm: zulässig, aber beim Routing ohne fremde Signale dazwischen, mit Massefläche darunter und Masse-Schirm ringsum (AN2867).
- Feinplatzierung der übrigen Blöcke (Versorgung, Mikrofonfilter, HX711) beim Routing nachziehen.
- Lagen L3 (Versorgung 3,3 V/SYS/5 V mit Masse-Füllung) und Routing folgen.

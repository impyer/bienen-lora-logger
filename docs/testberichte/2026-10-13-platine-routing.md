# Prüfbericht: Hauptplatine – Routing mit Freerouting, Platzierung aus den Routing-Erfahrungen optimiert

- **Prüfbericht-ID:** PCB-2026-10-13-ROUTING
- **Prüfdatum (UTC):** 13.10.2026
- **Bezug:** Lastenheft M5, M8, A3; `mcu-funk.md` 1.1/1.2/2.3 (ST AN2867/AN4488); Berichte Grobplatzierung, Feinplatzierung, Lage L3, Fanout (dieser Bericht ersetzt deren Platzierungsangaben für U301, J704 und SW303)
- **Ausgangs-SHA:** `bbabcd4`
- **Artefakte:**
  - neu: `werkzeug/platine_routen.py`, `werkzeug/platine_nachrouten.py`, `werkzeug/platine_aufraeumen.py`
  - geändert: `werkzeug/platine_bestuecken.py`, `werkzeug/platine_fein.py`, `werkzeug/platine_fanout.py`
  - Ergebnis: `hauptplatine/logger.kicad_pcb`
- **Änderungsklasse:** D1 (Layout); keine D3-Inhalte
- **Teststufe:** T3 (KiCad 10.0.6 DRC mit Schaltplanabgleich). Kein Layout-Review durch eine zweite Person, kein T4.

## Ablauf (reproduzierbar)

Die Platine entsteht vollständig aus den Skripten. Reihenfolge:

1. `platine_start.py`
2. `platine_bestuecken.py`
3. `platine_fein.py`
4. `platine_lagen.py`
5. `platine_fanout.py`
6. `FREEROUTING_JAR=… platine_routen.py 40`
7. `platine_nachrouten.py`
8. `platine_aufraeumen.py <offene Netze>`

Freerouting ist nicht im Repo. Es braucht Freerouting 1.9.0 (Java 21) und ohne Bildschirm `xvfb-run`. Ein Lauf mit 40 Durchgängen dauert hier etwa 35 Minuten. Das Ergebnis des Autorouters streut je nach Platzierung um etwa ±10 Verbindungen.

## Erkenntnisse aus dem Routing

| Befund | Ursache | Maßnahme |
|---|---|---|
| Freerouting 2.1.0 verband fast nichts („maze search algorithm could not be created“) | Werkzeugfehler bzw. Unverträglichkeit mit dem DSN-Export von KiCad 10 | Freerouting 1.9.0 |
| Keine Vias möglich, solange die Innenlagen-Flächen exportiert werden | Freerouting behandelt Flächen als festes Kupfer | Flächen nicht exportieren; Innenlagen als „power“ markieren (Signale nur auf L1/L4); Zonen nach dem Import neu füllen |
| 18 STM32-Pins ohne Anschluss | Abblockkondensatoren als geschlossene Reihe parallel zu den Gehäusekanten | Kondensatoren an die Ecken, nahe ihrem VDD/VSS-Paar; Seiten frei; gerade Ausbruchstiche (0,86 mm) an allen Signalpins |
| BQ25185 (Raster 0,4 mm) und TPS61240 fast nicht angeschlossen | Freerouting findet an 0,2-mm-Pads im engen Raster keinen Eingang | Alle Pins mit gestaffelten Stichen aus dem Raster geführt; Wandler-Schleife (VIN–L–VOUT, CIN/COUT) fest verlegt (TI-Empfehlung); Freiraum 1,5 mm um U201, 1,0 mm Abstand im Versorgungsblock |
| Quarzleitungen | sollen kurz sein, ohne Fremdsignale (AN2867) | LSE, HSE, VCAP und VDDA von Hand verlegt; Y301 gedreht (Pad 1 oben links); VSSA/VSS an Pin 8/23 auf das Thermal-Pad |
| Lange Leitungen (I²C 184 mm, WAKE 146 mm) | J704 links oben, Service-Taster rechts oben | J704 an den Rand des freien Drittels nahe der MCU (80/104), SW303 nach links zum Reedkontakt; Luftliniensumme −8 % |
| Freerouting legt zusätzlich GND-Bahnen (ohne Flächen „unverbunden“) | Folge des Exports ohne Flächen | `platine_aufraeumen.py` entfernt 306 überflüssige GND-Bahnen/Vias; GND hängt über die Fanout-Vias an L2/L3 |
| Eine Drehung der MCU-Gruppe bringt nur ±1 % Luftlinie | – | MCU bleibt bei 0° |

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Offene Verbindungen | **6 von 202** (nach dem Fanout) |
| DRC Kupfer, Courtyard, Abstände, Kurzschlüsse | **0 Verstöße** |
| Schaltplanabgleich | 0 Abweichungen |
| Restliche Warnungen | 6 × lose Bahnenden (Ausbruchstiche der 6 offenen Netze, gewollt); Bestückungsdruck 35 × Überlappung, 28 × über Kupfer |
| Leiterbahnen | L1 ca. 2,8 m, L4 ca. 1,8 m, 217 Vias; Breite 0,2 mm (Default), Stiche 0,15–0,3 mm |
| Quarze | LSE 11,2 / 8,6 mm, HSE 9,0 / 11,7 mm, ohne Via |
| USB D+/D− | 74,5 / 69,3 mm, 4 / 2 Vias (USB Full Speed, unkritisch; siehe Offen) |
| Stromtragfähigkeit | 0,2 mm außen ≈ 0,6 A bei 10 K [A, IPC-2221-Näherung]; größter Dauerstrom auf SYS/VBUS/VIN_LADER < 0,3 A (Ladestrom 150 mA) |
| Bestückungsdruck | Referenzen der Kleinteile auf F.Fab; auf dem Druck bleiben Stecker, Taster, ICs, Quarze, LED; Klemmenbeschriftung aus dem Klemmenwert (M4) |

## Die 6 offenen Verbindungen (in KiCad von Hand schließen)

Alle betreffen STM32-Pins mit fertigem Ausbruchstich. Die Gegenseite ist schon geroutet. Gesucht ist jeweils ein Weg mit Via aus dem dichten Bereich um den STM32. In KiCad geht das mit dem interaktiven Router („Routen“, Push & Shove) in wenigen Minuten. Der eigene Gitter-Router (`platine_nachrouten.py`) kann keine fremden Bahnen verschieben, deshalb bleiben sie offen.

| Netz | von | nach |
|---|---|---|
| WAKE | U301 Pin 10 (101,6/89,8) | Bahn bei (58,9/94,1), zu SW303/SW304 |
| MIC_ADC | U301 Pin 11 (101,6/90,3) | Bahn bei (122,8/141,8), zu C608 |
| SPI_MISO | U301 Pin 16 (103,8/91,4) | Bahn bei (116,2/54,5), zu Flash/Funk |
| ADC_SOLAR | U301 Pin 19 (105,3/91,4) | C203 (70,7/137,0) |
| I2C_SCL | U301 Pin 42 (105,3/84,6) | Bahn bei (83,7/110,2), zu J704 |
| HX_SCK | U301 Pin 46 (103,3/84,6) | R508 (145,5/121,8) |

## Offen

- Die 6 Verbindungen oben; danach DRC ohne offene Verbindungen.
- USB-Paar als Differenzpaar von Hand kürzer führen (Ziel < 40 mm, gleiche Länge, ohne Via) [P].
- Bestückungsdruck aufräumen (Überlappungen); Via-in-Pad-Füllung bei JLCPCB [P].
- Review der kritischen Netze durch eine zweite Person vor der Bestellung: Quarze, Funk-Versorgung, Analogzweig Mikrofon, Wägezellenleitungen, Wandler-Schleife.

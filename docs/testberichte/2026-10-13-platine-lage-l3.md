# Prüfbericht: Hauptplatine – Versorgungslage L3

- **Prüfbericht-ID:** PCB-2026-10-13-L3
- **Prüfdatum (UTC):** 13.10.2026
- **Bezug:** Lastenheft M8 (4 Lagen: L1 Signal/Bauteile, L2 durchgehende Masse, L3 Versorgung mit Masse-Füllung, L4 Signal), A3 (Masse unter dem Analogteil)
- **Ausgangs-SHA:** `dd61bc9`
- **Artefakt:** `hardware/kicad/werkzeug/platine_lagen.py` (neu) → `hardware/kicad/hauptplatine/logger.kicad_pcb`
- **Änderungsklasse:** D1 (Layout)
- **Teststufe:** T3 (KiCad 10.0.6 DRC mit Schaltplanabgleich). Kein Routing, kein T4.

## Umsetzung

| Zone | Lage | Netz | Priorität | Bereich |
|---|---|---|---|---|
| GND_L2 (aus `platine_fein.py`) | L2 / In1.Cu | GND | – | ganze Platine |
| **P3V3_L3** | L3 / In2.Cu | +3V3 | 1 | oberer Teil bis y = 108 mm (MCU, Funk, Flash, USB/Taster, J302, J704, LED/Reed links) mit Arm zu U202/U203 (x 52–76 mm, bis y = 138 mm) |
| **GND_L3** | L3 / In2.Cu | GND | 0 | ganze Platine, füllt alles außerhalb von P3V3_L3 (Versorgung, Mikrofonzweig, Waage, Klemmen) |

Anschluss an die Flächen über Wärmefallen (Spalt 0,25 mm, Steg 0,3 mm), Abstand 0,2 mm. Sperrflächen der Befestigungslöcher bleiben auf allen Lagen frei.

SYS, 3V3_SW, 5V_WAAGE und 3V3_ANA bekommen beim Routing breite Leiterbahnen statt eigener Flächen. Ihre Verbraucher liegen verteilt; eigene Flächen würden L3 zerstückeln und die Masse-Füllung unter dem Analogteil unterbrechen.

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| DRC Kupfer, Courtyard, Abstände | 0 Verstöße (nur Bestückungsdruck-Warnungen wie zuvor) |
| Schaltplanabgleich | 0 Abweichungen |
| Offene Verbindungen | 322 (vorher 323); die SMD-Pads an +3V3 und GND brauchen noch Vias zu L2/L3 |
| Zweiter Lauf | legt nichts neu an, füllt nur neu |

## Offen

- Routing: Vias von jedem +3V3- und GND-Pad zu L3/L2, Leiterbahnen für SYS, 3V3_SW, 5V_WAAGE, 3V3_ANA und die Signale.
- Stromtragfähigkeit SYS (Lade- und Wandlerstrom) beim Routing nach Leiterbahnbreite prüfen.

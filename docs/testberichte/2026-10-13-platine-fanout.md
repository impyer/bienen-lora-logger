# Prüfbericht: Hauptplatine – Fanout GND/+3V3 zu den Innenlagen

- **Prüfbericht-ID:** PCB-2026-10-13-FANOUT
- **Prüfdatum (UTC):** 13.10.2026
- **Bezug:** Lastenheft M8 (L2 Masse, L3 Versorgung); Prüfbericht Versorgungslage L3
- **Ausgangs-SHA:** `dd61bc9` + gelieferte Lage L3 (noch nicht gepusht)
- **Artefakt:** `hardware/kicad/werkzeug/platine_fanout.py` (neu) → `hardware/kicad/hauptplatine/logger.kicad_pcb`
- **Änderungsklasse:** D1 (Layout)
- **Teststufe:** T3 (KiCad 10.0.6 DRC mit Schaltplanabgleich). Kein T4.

## Umsetzung

Jedes SMD-Pad an GND und jedes SMD-Pad an +3V3 über der +3V3-Fläche (P3V3_L3) bekommt eine Leiterbahn von 0,3 mm Breite zu einer eigenen Durchkontaktierung (0,6/0,3 mm). Die Via sitzt 0,8–2,4 mm vom Padmittelpunkt entfernt, bevorzugt vom Bauteil weg.

Für jede Via und jede Leiterbahn wird geprüft:

- Abstand zu Pads, Leiterbahnen und Vias anderer Netze mindestens 0,2 mm (Entwurfsregel 0,15 mm);
- Mittenabstand zwischen zwei Vias mindestens 0,8 mm;
- kein Via in fremden Courtyards (also nicht unter dem Funkmodul, den Quarzen oder den Tastern), in den Sperrflächen der Befestigungslöcher oder näher als 0,8 mm am Rand.

Zwei GND-Pins neben einem Thermal-Pad sind direkt auf dieses Pad geführt, das schon Vias hat:

- U201 Pin 5 → Thermal-Pad (0,2 mm);
- U301 Pin 35 → Thermal-Pad (0,25 mm).

Durchsteckpads (Klemmen, Stiftleisten, JST) hängen über ihre Bohrung ohnehin an den Flächen.

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Neue Anbindungen | 120 (118 Vias mit Leiterbahn, 2 auf ein Thermal-Pad); alle GND- und +3V3-SMD-Pads mit Platz versorgt |
| DRC Kupfer, Courtyard, Abstände | 0 Verstöße (nur Bestückungsdruck-Warnungen) |
| Schaltplanabgleich | 0 Abweichungen |
| Offene Verbindungen | **202** (vorher 322) |
| Zweiter Lauf | 0 neue Anbindungen (wiederholbar) |

## Offen

- Die 202 restlichen Verbindungen sind Signale und die nicht als Fläche geführten Versorgungen: SYS, 3V3_SW, 5V_WAAGE, 3V3_ANA, VBUS, VBAT, VIN_LADER sowie +3V3 außerhalb der Fläche.
- Routing der kritischen Netze von Hand: Quarze, USB, SPI, Analogzweig. Danach der Rest, gegebenenfalls mit Autorouter, und eine Sichtprüfung.

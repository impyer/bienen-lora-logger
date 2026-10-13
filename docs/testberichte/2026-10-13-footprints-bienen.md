# Prüfbericht: Projektfootprints BQ25185 und Ra-01SH, Funde Akkuhalter und Klemmen

- **Prüfbericht-ID:** SCH-2026-10-13-FOOTPRINTS
- **Prüfdatum (UTC):** 13.10.2026
- **Bezug:** REG26-08 (offene Footprints), SCH26-04 (Footprints), neuer Befund SCH26-13
- **Ausgangs-SHA:** `675f6c1` (main, nach REG26-08)
- **Artefakt:** `hardware/kicad/werkzeug/footprints.py` (neu) → `hardware/kicad/Bienen.pretty/` (2 Footprints); `kicad_gen.py` schreibt `fp-lib-table`; `pruefen.sh` (Footprints in Erzeugung und Reproduzierbarkeit); `pin_footprint.py` (Projektbibliothek)
- **Änderungsklasse:** D2; keine D3-Inhalte (Akkuhalter nur dokumentiert)
- **Teststufe:** T0 (TI SLUSF65 Package Outline/Board Layout 4226298/A; Ai-Thinker Ra-01SH Specification V1.1 S. 10, 11, 13; Keystone-Produktseite 1042; DEGSON-Datenblatt 15EDGKNH/15EDGRHC), T3 (KiCad 10.0.6). Kein T4.

## Footprints

| Footprint | Maße laut Quelle | Umsetzung |
|---|---|---|
| `WSON-10-1EP_2.2x2mm_DLH0010A` | Körper 2,2 × 2,0 mm; Padreihen 2,1 mm Mitte; Pads 0,5 × 0,2 mm; Raster 0,4 mm; Pin 1 oben links, 1–5 links, 6–10 rechts von unten nach oben; Thermal-Pad 0,9 × 1,5 mm, Paste 0,85 × 1,38 mm; 2 Vias Ø 0,2 mm (Beispiel) | genau so; NSMD; Vias setzt das Layout (verfüllt/abgedeckt) |
| `Ai-Thinker_Ra-01SH` | Modul 16 × 17 mm; Raster 2,0 mm; erstes Pad 1,0 mm unter Oberkante; Pads 1,536 × 1,0 mm; Innenkanten 13,828 mm; Pin 1 2,262 mm breit; Pin 1 oben links, 1–8 links, 9–16 rechts | genau so; Pads ragen 0,42 mm über die Modulkante (Lötkehle) |

Vergleich Ra-01SH mit dem EasyEDA-Footprint (LCSC C2764087): gleiche Rasterung und Nummerierung; EasyEDA-Pads 2,4 mm breit (Innenkante 6,8 mm), Herstellerempfehlung 1,536 mm (Innenkante 6,914 mm). Gewählt: Herstellerempfehlung.

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Erzeugung zweimal identisch (UUIDs fest) | bestanden |
| ERC Hauptplatine | **0 Meldungen** (vorher 2 erwartete zu fehlenden Footprints) |
| Pin-/Footprint-Abgleich | 161 Bauteile, 0 Abweichungen; offen nur SW304 |
| Netzprüfung | 178/178 |
| Sichtprüfung SVG-Export | Pad 1 markiert, Nummerierung wie Datenblatt |

## Neue Funde

1. **Thermal-Pad BQ25185:** `versorgung.md` 3.4 nannte 6–9 Vias. Auf 0,9 × 1,5 mm passen nach TI-Beispiel 2 Vias Ø 0,2 mm. Text in `versorgung.md` und Generator korrigiert. Via-in-Pad im JLCPCB-Angebot prüfen [P].
2. **Akkuhalter:** Keystone **1042 = SMD**, **1043 = Durchsteck („PC Pin“)**. Lastenheft V1 und `versorgung.md` nennen 1043, im Generator stand „1043 (SMD)“, der Footprint ist 1042. **Entschieden 13.10.2026 (Philipp, HW-02): Keystone 1042 (SMD).** Lastenheft V1, `versorgung.md`, Generator und Entscheidungsregister nachgeführt. [V: Keystone-Produktseite 1042 „Mounting: SMT“; Händlerangabe 1043 „PC Pin“]
3. **SCH26-13 Klemmen:** DEGSON 15EDGRHC-THR-3.5 ist eine **zweireihige** Serie (DEGSON-Datenblatt „Compact structure with double rows“, 04–48P; EasyEDA-Footprint C7603445: 2 × 2 Pads in 7,8 mm Breite). Die Platine braucht einreihige Klemmen mit eigener Polzahl (2–6). Vorschlag: DEGSON 15EDGRC-3.5 (einreihig) mit Stecker 15EDGK-3.5; LCSC-Nummern und Zeichnung [P]. Der Platzhalter Phoenix MC 1,5/x-G-3,5 entspricht der einreihigen Bauform.

## Grenzen

- Padgeometrie gegen die Zeichnungen von Hand umgesetzt; kein DRC ohne Platine. Beim Layout DRC und Sichtprüfung im 3D-Viewer (kein 3D-Modell hinterlegt).
- Datenblatt-Kopie DEGSON von einem Händler (chipdip.ru), nicht vom Hersteller direkt.

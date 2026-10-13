# Prüfbericht: Hauptplatine – Bauteile übernommen, Grobplatzierung

- **Prüfbericht-ID:** PCB-2026-10-13-GROBPLATZIERUNG
- **Prüfdatum (UTC):** 13.10.2026
- **Bezug:** Lastenheft M5 (Klemmenkante, Funkkante, freies Drittel), A3 (Mikrofonzweig fern von Funk und 5-V-Wandler), HW-03 (Bauhöhe, Hülsen); `anschluesse.md` 4; `mcu-funk.md` 2.3/3.3
- **Ausgangs-SHA:** `4fe34a6` (main)
- **Artefakt:** `hardware/kicad/werkzeug/platine_bestuecken.py` (neu) → `hardware/kicad/hauptplatine/logger.kicad_pcb`; `kicad_gen.py` (Merkmal „nicht in Stückliste“), `hauptplatine.py`/`akku_platine.py` (Testpunkte und Lötbrücken ohne Bestückteil), `platine_start.py` (Befestigungslöcher als „nur Platine“)
- **Änderungsklasse:** D1 (Layout-Startpunkt, keine Schaltungsänderung); keine D3-Inhalte
- **Teststufe:** T3 (KiCad 10.0.6: DRC mit Schaltplanabgleich, Netzprüfung, ERC). Kein Layout-Review, keine Leiterbahnen, kein T4.

## Vorgehen

`platine_bestuecken.py` entspricht „Platine aus Schaltplan aktualisieren“ in KiCad, aber reproduzierbar:

1. liest `netzliste/logger.net` und lädt jeden Footprint aus `Bienen.pretty` oder der KiCad-Standardbibliothek;
2. setzt Referenz, Wert, LCSC, Beschreibung, DNP und „nicht in Stückliste“ und die Netze an den Pads;
3. verknüpft jeden Footprint mit seinem Schaltplansymbol (Pfad aus Blatt- und Symbol-UUID). Ein späteres „Platine aus Schaltplan aktualisieren“ in KiCad erkennt die Bauteile daran wieder;
4. platziert feste Bauteile nach den Regeln (Tabelle unten). Die übrigen Bauteile legt es spiralförmig neben das Bauteil, mit dem sie die meisten Signalnetze teilen, und zwar im Bereich ihres Schaltplanblatts. Abblockkondensatoren ohne Signalnetz kommen zum IC ihres Blatts. Courtyards überlappen nicht, halten 0,5 mm Randabstand und meiden die Lochsperren.

Das Skript ergänzt nur fehlende Referenzen und überschreibt nichts, was schon platziert ist (zweiter Lauf: 0 ergänzt). Zwei Läufe ab leerer Platine ergeben gleiche Lagen, Drehungen und Padnetze. Die Datei ist nicht bytegleich, weil KiCad neue UUIDs vergibt.

## Feste Plätze

| Regel | Umsetzung |
|---|---|
| Alle Außenklemmen an der Unterkante, von links Solar – BME280 – DS18B20 – Mikrofon – Wägezelle (M5) | J201, J202, J703, J701, J702, J601, J501 in einer Reihe; Stecköffnung zur Kante, 0,9 mm innen |
| ESD direkt hinter der Klemme | D702 (I²C), D701 (1-Wire, zwischen J701/J702), D601, D501, SMAJ12A D204 hinter den Solarklemmen |
| Funkmodul an der Gegenkante, keine Leiterbahn an ANT (mcu-funk.md 2.3) | U401 mittig oben, Pin-1-Seite zur Kante. Lage der IPEX-Buchse am Modul **[A]**: nahe Pin 1 (ANT) angenommen, am gelieferten Modul prüfen |
| Lichtleiter-LED und Reedkontakt an einer Seitenkante, 10–20 mm auseinander (mcu-funk.md 3.3) | linke Kante: D301 bei y = 92 mm, Lichtaustritt zur Kante; SW304 bei y = 108 mm (16 mm Abstand), Schaltachse parallel zur Kante; R306/R305 daneben |
| USB und Akkustecker innen, gut erreichbar | J301 an der rechten Kante, Front bündig; J203 links innen über dem Versorgungsblock |
| 5-V-Wandler fern vom Mikrofonzweig (A3) | U501 rechts (149/113); OPV U601 bei (122/136), Abstand ca. 35 mm |
| Rund ein Drittel frei für Erweiterungen (M5) | links oben frei bis auf J704 (Erweiterungsstecker) und die Kantenbauteile D301/SW304 |

## Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Bauteile auf der Platine | 139 aus dem Schaltplan + 4 Befestigungslöcher |
| Schaltplanabgleich (DRC `--schematic-parity`) | **0 Abweichungen**, nach zwei Korrekturen (siehe unten) |
| DRC Kupfer/Courtyard/Rand | **0 Verstöße**; nur Bestückungsdruck: 150 × Druck über Kupfer, 116 × Druck überlappt (Referenztexte, beim Feinplatzieren aufräumen; JLCPCB schneidet Druck über Pads ab) |
| Offene Verbindungen | 344 (keine Leiterbahnen gezogen, erwartet) |
| Belegte Fläche (Courtyards) | ca. 3100 mm² von 14 641 mm² ≈ 21 % |
| Klemmenreihe | Körper von x = 49,1 bis 151,0 mm; Lochsperre rechts beginnt bei 151,6 mm |
| Prüfung des Generators (`pruefen.sh`) | reproduzierbar, ERC 0/0, Netzprüfung 178/178, Pin-/Footprint 161/0 |
| `tests/alle_tests_linux.sh` | rc = 0 |

## Korrekturen beim Abgleich

1. **Testpunkte TP201/TP202 und Lötbrücken JP401/JP402 (Haupt) sowie JP1 (Akku)** standen im Schaltplan als Stücklistenteil, ihre KiCad-Footprints aber als „nicht in Stückliste“. Sie sind kein Bestückteil (nur Kupfer). Deshalb jetzt im Schaltplan `in_bom no` (neuer Parameter `bom=False` in `kicad_gen.Teil`). Stückliste im README: „(kein Bestückteil)“.
2. **Befestigungslöcher H1–H4** haben kein Schaltplansymbol. Jetzt als „nur Platine“ markiert (`platine_start.py`).

## Hinweise für die Handarbeit in KiCad

- **Klemmenreihe ist knapp:** Die 7 Klemmen (25 Pole) füllen mit ihren Courtyards 102,7 der 103,2 mm zwischen den unteren Lochsperren. Die Körper stehen nur 1,4 mm auseinander. **[P]** Am Muster mit gesteckten 15EDGK-Steckern prüfen, ob sie nebeneinander passen und sich lösen lassen. Ausweichen ginge z. B. mit J703 (6-polig) als 5-polig ohne den freien Pin 6, oder mit einer Klemme an der Seitenkante.
- Kleinteile sind nur grob gelegt: Drehungen, Abstände und Stromwege von Hand nachziehen, vor allem Quarze direkt an U301 (mcu-funk.md 1.1), 100 µF/10 µF/100 nF direkt an Pin 3 des Funkmoduls, Thermal-Pad U201 mit 2 Vias.
- Masse: L2 durchgehend (M8). Unter dem Funkmodul durchgehende Masse, keine Leiterbahn an ANT.
- Die Hinweistexte auf User.1 aus `platine_start.py` überlagern jetzt Bauteile und können gelöscht werden.

## Grenzen

- Kein Leiterbahn-Layout und kein Layout-Review. Die DRC-Werte gelten nur für Lage und Courtyards.
- Lage der IPEX-Buchse am Ra-01SH, Klemmenabstand, Lichtleiterhöhe und Bauhöhe sind am Muster zu prüfen.
- Kein Muster, keine Messung (T4 offen).

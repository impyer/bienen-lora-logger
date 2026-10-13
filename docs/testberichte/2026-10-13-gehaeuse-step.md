# Prüfbericht: Gehäuse CBHUB-02 – Kontrolle mit dem STEP-Modell

- **Prüfbericht-ID:** MECH-2026-10-13-STEP
- **Prüfdatum (UTC):** 13.10.2026
- **Bezug:** Lastenheft M1, M2 (HW-03), M3, F7 (Lichtleiter); `mcu-funk.md` 3.3; Grobplatzierung `2026-10-13-platine-grobplatzierung.md`
- **Ausgangs-SHA:** `4fe34a6` + gelieferte Grobplatzierung (noch nicht gepusht)
- **Prüfgegenstand:** STEP-Datei „CBHUB_02 -01.1.stp“ (Camdenboss, Solid Edge, 25.02.2026, 10,3 MB), von Philipp am 13.10.2026 übergeben. **Nur lokal, nicht im Repo** (Herstellerdatei).
- **Änderungsklasse:** D0 (Dokumentation, Mechanik-Kontrolle)
- **Teststufe:** T0 (Herstellermodell) mit rechnerischer Auswertung (OpenCascade 7.x über `cadquery-ocp`): Strahlschnitte senkrecht im 1-mm-Raster (Unterteil, Deckel, Dichtung) und waagerechte Einzelschnitte. Kein Muster.

## Inhalt des Modells

Das Modell ist eine Baugruppe im geschlossenen Zustand mit diesen Teilen: Unterteil (BASE -H), Deckel (LID -N), Dichtung (CBGK-NHP-05), 2 Deckelstreifen (SC), 4 Wandhalter (CBBRACKET -03), 4 Deckelschrauben M3 × 12 mit Gewindeeinsätzen. Dazu kommen zwei **Referenzplatinen**: eine im Unterteil (152,5 × 152,5 × 1,6 mm) und eine im Deckel (146,8 × 146,8 mm). Die z-Achse zeigt vom Deckel zum Boden des Unterteils.

## Ergebnisse

| Prüfung | Soll (Lastenheft / HW-03) | Ist (STEP) | Bewertung |
|---|---|---|---|
| Lochbild Unterteil | 110,2 × 110,2 mm, Ø 3,4 mm | Referenzplatine: Ø 3,4 auf ± 55,1 mm, Auflage Ø 6 mm | bestätigt |
| Platine 121 × 121 mm im Gehäuse | ohne Kollision | kein Gehäusematerial im Platinenumriss, außer an der Domauflage | bestätigt |
| Dom | Höhe offen | Außen-Ø 5,9 mm, Spitze 9,1 mm über dem Innenboden (Boden 2,5 mm) | neu bekannt |
| **Dombohrung** | Lastenheft: Ø 3,6 mm | **Ø 2,4 → 2,3 mm, 10,1 mm tief**; auch in der Zeichnung Blatt 4 steht Ø 2,4 (Ø 3,6 steht auf Blatt 3) | **Lastenheft korrigiert** |
| Freiraum unter der Platine (Hülse 10 mm) | genug für Durchsteck-Lötstellen | Unterseite 19,1 mm über dem Innenboden; über den erhöhten Feldern (Wandhalter-Aufnahmen) mindestens **13,0 mm** | erfüllt |
| Freiraum über der Platine | ≥ 40 mm (HW-03) | 53,8 mm bis zur Deckel-Innenfläche; **45,8 mm** unter den Deckeldomen (Ø 6, Lochbild 108 mm, je 1,6 mm neben unseren Löchern); **44,3 mm** unter den Deckelpfosten an den Platinenecken | erfüllt, Reserve ≥ 4,3 mm |
| Innenwand auf Platinenhöhe | Lichtleiter-Länge 18–20 mm geschätzt | Innenwand ± 76,7 mm (Formschräge ca. 1°), Wand 2,5 mm; Platinenkante → Innenwand 16,2 mm | Lichtleiter ca. 19,4 mm (LED bis außen) |
| Ecksäulen (Deckelschrauben) | – | ca. 3–4 mm Abstand zur Platinenecke (Rastermaß 1 mm) | ausreichend, Platine passt zwischen die Säulen |

Die Freiraumkarten (unter und über der Platine) wurden als Bild an Philipp übergeben, nicht im Repo.

## Abgeleitete Maße

- **Lichtleiter-Bohrung:** Platinenoberseite 23,2 mm unter der Außenfläche des Bodens (9,1 + 10 + 1,6 + 2,5 mm). Die Lichtmitte der LED liegt ca. 0,5 mm über der Platine [A], also liegt die **Bohrungsmitte ca. 22,7 mm von der Außenfläche des Bodens** (bzw. ca. 44,6 mm von der offenen Kante des Unterteils). Seitlich liegt die LED 8 mm links der Wandmitte (Grobplatzierung).
- **Schraube:** selbstformend Ø 3 mm für Kunststoff [A, Bohrung 2,4 ≈ 0,8 × d]. Länge 1,6 + 10 + 6…8 mm Einschraubtiefe ≈ 18–20 mm, höchstens ca. 21 mm (Bohrungsgrund 10,1 mm unter der Domspitze: 1,6 + 10 + 10,1 = 21,7 mm).
- **Wandhalter** (CBBRACKET) liegen außen am Boden an zwei gegenüberliegenden Seiten. Hängt das Gehäuse an der Wand, sind das oben und unten. Die Klemmenkante (Kabel nach unten) gehört also an eine dieser beiden Seiten.

## Geänderte Unterlagen

Lastenheft 4.1 (Dombohrung) und neu 4.1a (STEP-Maße), M2; `mcu-funk.md` 3.3 (Länge und Höhe des Lichtleiters); `mechanik/README.md`; Entscheidungsregister HW-03 (Kontrolle bestanden, Dombohrung).

## Grenzen

- Die Werte stammen aus dem Herstellermodell (Nennmaße). Formteil-Toleranzen und die tatsächliche Hülsenlänge prüfen wir am Muster [P].
- Das 1-mm-Raster kann schmale Rippen unter 1 mm übersehen. Kritische Stellen (Dome, Wände, Deckeldome) sind zusätzlich mit Einzelschnitten gemessen.
- Die Höhe der LED-Lichtmitte (0,5 mm) ist angenommen, ebenso die Schraubennorm.

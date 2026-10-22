# Behebungsbericht: Plattform – Fachfehler, Testgenauigkeit, Bedienung

**Datum:** 22.10.2026 · **Prüfobjekt:** Branch `feature/plattform-behebung-20261022`, ausgehend von `e6e79fc` (Prüfstand, CI grün) · **Grundlage:** [Prüfbericht 21.10.2026](2026-10-21-plattform-bedienbarkeit-tests.md), Freigabe des Maintainers vom 22.10.2026 („in der vorgeschlagenen Reihenfolge“) · **Prüfer:** Claude (Code-Session) · **Änderungsklasse:** D2 (Anzeige und Auswertung von Messdaten, Zeitbezug) · **Teststufen:** T1/T2 lokal (Windows 11, PostgreSQL 16, Chromium 1194 über Playwright 1.56.1); CI siehe unten

## 1. Behoben

### Fachfehler

| Mangel | Befund | Ursache | Behebung | Akzeptanztest |
|---|---|---|---|---|
| M-02 | PLT26-13 | Mittel der Tagesbilanz „nachher“ ohne Filter auf `mit_eingriff` | `auswertung.py`: Tage mit Eingriff zählen nicht, Anzahl als `eingriff_vorher/nachher`; Cockpit nennt „ohne N Tag(e) mit Eingriff“ | `test_plattform` „Tarieren-Tag zählt nicht als Wirkung“ (vorher hielt der Test den Fehler fest: `nachher < -9`); Browser „Tarieren-Tag nicht als Wirkung“ |
| M-03 | PLT26-14 | Datumsfeld setzte `T23:59:59Z` (UTC) | `diagramm.js` `tagesEnde()`/`bisTag()`/`zeitraum()`: Ende = Mitternacht des Folgetags in Europe/Berlin; Kopfzeile zeigt den gewählten Tag | Node: MEZ, MESZ, Umstellungstag, alte Adressen; Browser: Datum 20.10. → `2026-10-20T22:00:00.000Z` |
| M-04 | PLT26-15 | Bei 401 ersetzte die Anmeldeseite die ganze Seite | `api.js`/`app.js`: Anmeldung als Overlay über der Seite, danach wird die Anfrage mit neuem CSRF-Token wiederholt; Abbrechen führt zur Anmeldeseite | Browser: Cookie gelöscht → Overlay, Eingabe bleibt, nach Anmeldung gespeichert |
| M-08 | PLT26-17 | Oberfläche erkannte einen Server mit altem Code nicht | `API_STAND` in `app.py` und `api.js`; `/api/gesundheit` liefert ihn; Hinweis „Server neu starten“ bzw. „Seite neu laden“; 404 „unbekannter Endpunkt“ als verständlicher Text; Netzfehler als „Server nicht erreichbar“ | Hosttest: beide Werte gleich; Browser mit simuliertem Altserver und Netzfehler |

### Testgenauigkeit (PLT26-16)

| Punkt | Umsetzung |
|---|---|
| T-01 Sollwerte | Browser vergleicht die Anzeige mit der API derselben Sitzung: Kennzahlen Gewicht, Tagesbilanz, Brutnest, Milbenfall; Chronik-Reihenfolge; mittlere letzte Tagesbilanz; Summen je Volk; Vorgabezeitraum 14/30 Tage; „veraltet“ |
| T-02 Randfälle im Generator | negativer Sprung −3 kg ohne Maßnahme; 120-min-Ausfall knapp über der Lückengrenze; ein als ungültig markierter Wert 99,9 °C; Wetterstation 1,5 K über dem Außenfühler |
| T-03 bisher ungetestet | Varroa und Maßnahme-Band ändern; Stand und Volk umbenennen; eigene Messgröße; Vorher/Nachher für Varroa und Durchsicht; Windel, die ins Fenster hineinreicht; alle Verdichtungen in SQL mit Sollwerten; Tagesgrenzen in Ortszeit; Anzahl der Felder ohne Kanal über zwei Importläufe; Weißliste beim Löschen |
| T-04 Seitenlogik | Rechenteile aus `volk.js`, `analysen.js`, `uebersicht.js`, `stockkarte.js` nach `web/kennzahlen.js` (rein, ohne Vue); Node-Tests mit Sollwerten |
| T-05 Fehlerpfade | 409 vom Server, Netzfehler, abgelaufene Sitzung, alter Server: jeweils Meldung auf Deutsch, Eingabe bleibt |
| Mutationsskript | `tests/plattform/mutation.py` mit 50 Mutanten (Grundlauf ohne Mutation, Fehlerzeile je erkanntem Mutanten, Zeilenenden bleiben, Ziel ≥ 80 %) |

### Bedienung

| Mangel | Behebung | Test |
|---|---|---|
| M-05 | Steuerfelder `Format`, `Messzeit_unix`, `Status.*` getrennt (`steuerfelder`), nicht mehr als Hinweis; Übersicht nennt Hinweise nach Art („2 Geräte ohne Zuordnung · 7 unbenannte Felder“ statt „33 Hinweise“) | Datenbankfall, Browser |
| M-06 | „Kanal beenden“ fragt mit Kanal, Messgröße und Zeitpunkt nach. Ohne eigene Zeitwahl gilt der Zeitpunkt des Klicks, sekundengenau (Anzeige „jetzt beim Speichern“, „wieder jetzt“). Messgrößen mit Namen. | Browser: Abbrechen ändert nichts, Bestätigen beendet |
| M-07 | `farbenAnpassen()` ersetzt die hellen Entwurfsfarben im dunklen Schema durch die CSS-Farben; neu zeichnen beim Wechsel | Node, Browser mit `colorScheme: dark` |
| M-09 | Achse der Tagesbilanz nach den Tagen ohne Eingriff (±0,5 kg Mindestbereich, 20 % Rand); Eingriffsbalken abgeschnitten mit Wert; Cockpit und Analysen | Node, Browser |
| M-10 | Handy: Karten in einer Spalte, Messwerte-Auswahl zugeklappt direkt über dem Diagramm mit Anzahl gewählter Kurven | Browser 390 px |
| M-11, M-12 (P3, nebenbei) | Zoom-Hinweis nach Eingabegerät; „Bienenstand“ statt „Übersicht“ | Browser |

**Beim Testen neu gefunden und behoben:**
- **Zeitpunkte nur minutengenau:** Wer einen Kanal anlegt und in derselben Minute beendet, bekam einen Konflikt. Ebenso schlug eine Durchsicht direkt nach dem Anlegen eines Volks fehl („Volk noch nicht entstanden“).
- **Behebung:** Bleibt der vorbelegte Zeitpunkt „jetzt“ unverändert, gilt er jetzt sekundengenau, in der Verwaltung wie in der Stockkarte.

## 2. Ergebnisse

| Prüfung | Stand | Ergebnis |
|---|---|---|
| `test_plattform.py` (Host + Datenbank) | lokal | 35/35 (vorher 27) |
| `test_verwaltung.py` | lokal | 14/14 (vorher 13) |
| `test_stockkarte.py` | lokal | 13/13 (vorher 11) |
| `test_importer.py` | lokal | 13/13 |
| `test_diagramm.mjs` | lokal | 26/26 (vorher 17) |
| Browser `oberflaeche_testen.sh` | lokal | leer 9/9, Verwaltung 17/17, synthetisch 47/47 (vorher 5 + 12 + 23) |
| Mutationstest auf `8e1479c` (Tests verbessert, vor M-05 bis M-10) | lokal | **46 von 51 erkannt (90 %)**, Prüfbericht vom 21.10.: 11 von 35 (31 %) |
| Die 4 Überlebenden nach Ergänzung (qualitaet-Filter, Anzahl über zwei Läufe, Mitternacht der Windel, Vorgabezeitraum) | lokal, Endstand | 4 von 4 erkannt |
| Vollständiger Lauf auf dem Endstand (`tests/plattform/mutation.py`, 50 Mutanten) | lokal | **50 von 50 erkannt (100 %)** |
| CI | GitHub Actions | CI_ERGEBNIS |

Ein Mutant wurde als **gleichwertig** gestrichen: das Zurücksetzen des Puffers der Felder ohne Kanal nach einem Zeilenfehler. Heute wirft keine Zeile mehr nach dem Sammeln, der Mutant ändert das Verhalten also nicht. Die Zeile bleibt als Absicherung im Code.

## 3. Offen und Grenzen

- **Offen aus dem Prüfbericht (P3):** M-13 (Kennzahl „Nacht-Referenzwerte“), M-14 teilweise (Sprungmarken der Verwaltung), M-15 (Schrift- und Tippflächengröße), M-16 (`aria-pressed`), M-17 (Quellfeld `l`); T-06 teilweise (Bildschirmfotos als CI-Artefakt), T-07 teilweise (Mutationstest nicht in jeder CI, weil er etwa eine Stunde dauert).
- **PLT26-11** (Plausibilitätsprüfung beim Import) bleibt offen. Der ungültige Wert im Generator ist von Hand markiert.
- Nur synthetische Daten, Chromium (Desktop, Handy-Emulation, dunkles Schema); kein echtes Handy, kein Safari/Firefox, kein Betrieb auf der ThinkStation, kein Test mit Imkern.
- **Sitzungsablauf:** Nur die eine wartende Anfrage wird wiederholt. Ungespeicherte Eingaben überstehen ein Neuladen der Seite nicht (kein lokaler Entwurf).

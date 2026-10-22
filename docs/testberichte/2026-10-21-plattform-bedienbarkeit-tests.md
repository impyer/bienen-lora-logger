# Prüfbericht: Plattform – Bedienbarkeit und Aussagekraft der Tests

**Datum:** 21.10.2026 · **Prüfobjekt:** Branch `feature/plattform-pruefung-20261021`, ausgehend von `10e09a7` (Branch `feature/plattform-auswertung-20261021`, CI grün) · **Prüfer:** Claude (Code-Session) · **Anlass:** Rückmeldung des Maintainers: Fehlermeldung „unbekannter Endpunkt“ auf der Analyse-Seite; Bitte um eine Analyse der Bedienbarkeit und um gründliche Tests, weil viele Fehler nicht erkannt werden · **Teststufen:** T1/T2 lokal (Windows 11, PostgreSQL 16, Chromium 1194 über Playwright 1.56.1), keine Hardware, kein Betrieb

Dieser Bericht ist eine **Mängelliste zur Freigabe**. Er schlägt Behebungen vor, setzt sie aber noch nicht um. Davon ausgenommen ist M-01 (Importer), weil sich die Tests ohne diese Behebung lokal nicht in vertretbarer Zeit ausführen ließen.

## 1. Ursache der Meldung „unbekannter Endpunkt“

- Der lokale Server auf Port 8081 lief noch mit dem Code **vor** dem Wechsel auf `feature/plattform-auswertung-20261021`.
- Das Serverprotokoll zeigt `GET /api/vergleich … 404` und `GET /api/voelker/1/vorher_nachher … 404`.
- uvicorn lädt neue Routen erst nach einem Neustart. Die Dateien der Oberfläche liest er dagegen bei jeder Anfrage frisch von der Platte. So trafen eine neue Oberfläche und eine alte API aufeinander.
- Mit dem neuen Code liefern beide Endpunkte 200: in der CI, auf dem lokalen Prüfserver und in den Tests unten.
- **Kein Fehler im Code. Die Oberfläche erkennt einen solchen Versionsunterschied aber nicht und zeigt eine unverständliche Meldung (M-08).**

## 2. Prüfumfang und Ergebnisse

| Prüfung | Ergebnis |
|---|---|
| Python-Tests gegen PostgreSQL 16 (`bienen_test`, lokal): `test_plattform` 27/27, `test_verwaltung` 13/13, `test_stockkarte` 11/11, `test_importer` 13/13 | bestanden (nach M-01) |
| Diagrammlogik `test_diagramm.mjs` | 17/17 |
| Browsertests `oberflaeche_testen.sh` (leer 5, Verwaltung 12, voll 23) | 40/40 |
| Zeilen- und Zweigabdeckung Python (`coverage --branch`) über `server/plattform` und `server/datenbank` | 89 % |
| **Mutationstest** (39 gezielte Fehler, davon 35 anwendbar; je Mutant die zuständige Testsuite) | **24 von 35 Mutanten überlebt** (31 % erkannt) |
| Rundgang mit Bildschirmfotos (9 Seiten × Desktop 1366 px und Handy 390 px, dunkles Schema, Ablauf der Sitzung) | 18 + 2 Aufnahmen, Mängel unten |

**Bewertung:** Die Tests führen fast den ganzen Code aus. Sie prüfen aber oft nur, dass etwas *da ist*, und nicht, dass es *stimmt*. Hohe Abdeckung bei niedriger Erkennungsrate ist genau das Muster „viele Fehler werden nicht erkannt“.

### 2.1 Mutationstest im Einzelnen

Erkannt wurden:
- falsches Vorher/Nachher-Fenster
- falsche Tagesgrenze im Fenster
- Summe mit Eingriffstagen
- fremdes Volk
- Lückenabstand
- Rasterwahl
- Zeitbereich der Ereignisse
- Nachtmedian relativ
- Summenlinie
- Ereignis am linken Rand
- Zahlenformat
- Zeitraum der Seite

**Nicht erkannt** (Test grün trotz eingebautem Fehler):

| Nr. | Ort | eingebauter Fehler | warum unerkannt |
|---|---|---|---|
| 2 | `auswertung.py` | Δ = vorher − nachher (Vorzeichen vertauscht) | kein Test prüft den Wert von `delta`, Browser nur „Tabelle vorhanden“ |
| 3 | `auswertung.py` | Messwerte mit `qualitaet = 'ungueltig'` fließen in Mittelwerte ein | synthetische Daten enthalten keine ungültigen Werte |
| 4 | `auswertung.py` | nur positive Sprünge > 1 kg gemeldet | synthetisch nur ein positiver Sprung |
| 6 | `auswertung.py` | Tagesgrenze UTC statt Europe/Berlin im Völkervergleich | Zeitraum im Test auf Monatsgrenzen, kein Randfall |
| 8 | `auswertung.py` | Milbenmessungen nur, wenn ganz im Fenster (statt überlappend) | Testfall liegt ganz im Fenster |
| 9 | `verdichtung.py` | Lücke erst ab doppelter Grenze | Logger-Ausfall (2 Tage) ist viel länger als die Grenze |
| 11–13 | `verdichtung.py` | Verdichtung `max`, `min`, `summe` rechnen Mittelwert | kein Test vergleicht verdichtete Werte |
| 17 | `stockkarte.py` | Varroa ändern speichert Milben + 1 | **Varroa ändern ist ungetestet** |
| 18 | `stockkarte.py` | Weißliste der Löschtabellen entfernt | nur gültige Tabellen getestet (SQL bleibt durch `sql.Identifier` sicher) |
| 20 | `importer.py` | `anzahl` der Felder ohne Kanal falsch summiert | Anzahl wird nirgends geprüft |
| 22 | `stapel.js` | Milbenfall-Tagesbalken am Liegeende um Mitternacht | kein Randfall „Ende genau 00:00“ |
| 26–29 | `stapel.js` | relatives Gewicht bei Lücke am Anfang; Milbenfall-Achse skaliert; Mausrad-Zoom ohne Strg; Achsenbeschriftung in jedem Feld | keine Prüfung dieser Optionen |
| 31–35 | `volk.js`, `analysen.js` | Kennzahl Tagesbilanz nimmt den **ersten** statt letzten Tag; Brutnest-Kachel zeigt beliebige Temperatur; Chronik unsortiert; „Mittlere letzte Tagesbilanz“ als Summe; mit Eingriffstagen | **Kennzahlen-Kacheln werden im Browser nicht geprüft** |
| 36 | `uebersicht.js` | „veraltet“ erst nach 300 h | keine Prüfung der Markierung |
| 37 | `stockkarte.js` | Maßnahme-Ende geht beim Bearbeiten verloren | Bearbeiten nur für Durchsichten getestet |

Drei Mutanten ließen sich nicht anwenden, weil die gesuchte Stelle nicht eindeutig war (Anmeldung `compare_digest`, Zeitgenauigkeit bei Varroa, `stand_aendern`). Diese Stellen sind über die Abdeckung bewertet: `stand_aendern`, `volk_aendern`, das Anlegen einer Messgröße und Vorher/Nachher für Durchsicht und Varroa werden **nie ausgeführt**.

## 3. Mängelliste

Prioritäten:
- **P1:** falsches Ergebnis oder Datenverlust
- **P2:** behindert die Bedienung deutlich oder Test erkennt Fehler nicht
- **P3:** Komfort, Gestaltung

### Fachlich falsch oder Datenverlust

| ID | Prio | Mangel | Beleg | Vorschlag |
|---|---|---|---|---|
| M-01 | P1 | **Importer quadratisch langsam:** Jedes Feld ohne Kanal wurde mit einem eigenen Upsert auf dieselbe Zeile gezählt, alles in einer Transaktion. Jede Zeilenversion bleibt bis zum Commit sichtbar, sodass jede Anweisung länger dauert. Beim leeren Start (Geräte senden, Kanäle fehlen) sind das alle Felder. | synthetisch 42 484 Felder ohne Kanal; `test_plattform` lokal über 15 min (abgebrochen), in der CI 52 s | **im Entwurf behoben** (siehe 4) |
| M-02 | P1 | **Vorher/Nachher zählt den Eingriffstag mit:** Die Tagesbilanz „nachher“ enthält den Tag, an dem z. B. tariert wurde. Ein Tarieren erscheint so als −10 kg/Tag „Wirkung“. | Volk 1, Tarieren 22.10., ± 3 T: nachher −10,04, Δ −10,00 | Tage mit `mit_eingriff` aus beiden Fenstern ausnehmen und Anzahl der ausgelassenen Tage anzeigen |
| M-03 | P1 | **Zeitraum „bis“ als UTC:** Das Datumsfeld setzt `T23:59:59Z`. In Berlin endet der Zeitraum damit erst um 01:59 bzw. 00:59 Uhr des Folgetags. Kopfzeile und Datumsfeld passen nicht zusammen. | `komponenten.js` `Zeitraum`; Kopf zeigt „18.10.–01.11.“ bei bis = 31.10. | Ende des Ortstags über `ortszeitNachUtc` berechnen; Test mit Sommer- und Winterzeit |
| M-04 | P1 | **Eingabe geht bei abgelaufener Sitzung verloren:** Beim Speichern ohne gültige Sitzung springt die Seite zur Anmeldung. Danach ist das Formular leer. | Rundgang: Maßnahme mit Mittel ausgefüllt, Cookie gelöscht, Speichern → „Anmelden“ | Anmeldung als Overlay über der Seite, danach Anfrage wiederholen; Entwurf zusätzlich lokal sichern |
| M-05 | P2 | **Fehlalarme:** Steuerfelder (`Format`, `Messzeit_unix`, `Status.*`) zählen als „unbenannte Felder“. Die Übersicht meldet deshalb „33 Hinweise“. Echte Hinweise (unbekanntes Gerät) gehen darin unter. | Übersicht, Verwaltung (je Gerät 7 Steuerfelder) | Steuerfelder je Vorlage als „bekannt, kein Messwert“ führen; Hinweise nach Art gruppieren |
| M-06 | P2 | **Kanal beenden ohne Rückfrage:** Ein Klick beendet die Messreihe ab dem oben eingestellten Zeitpunkt. Der Zeitpunkt steht beim Laden der Seite fest und veraltet, solange die Seite offen bleibt. | `verwaltung.js` | Rückfrage mit Zeitpunkt und Kanal; Zeitpunkt vor jeder Aktion aktualisieren oder sichtbar am Formular |
| M-07 | P2 | **Dunkles Schema unbrauchbar in Diagrammen:** Feldtitel (`#1a1f1c`) auf dunklem Grund sind unsichtbar, Gitterlinien grell, die Gewichtslinie kaum zu sehen. | Aufnahme `dunkel_volk1` | Diagrammfarben aus den CSS-Variablen lesen, bei Schemawechsel neu zeichnen |

### Bedienung und Verständlichkeit

| ID | Prio | Mangel | Vorschlag |
|---|---|---|---|
| M-08 | P2 | Oberfläche und API in unterschiedlicher Version: unverständliche Meldung (Abschnitt 1) | `GET /api/gesundheit` liefert eine Versionskennung; die Oberfläche vergleicht und meldet „Server neu starten / Seite neu laden“ |
| M-09 | P2 | Tagesbilanz im Cockpit: Ein Eingriffstag (−30 kg) bestimmt die Achse, normale Tage (±0,1 kg) sind nicht zu erkennen. | Eingriffstage wie in Analysen schraffieren, Achse auf die Tage ohne Eingriff begrenzen (Eingriff als abgeschnittener Balken mit Wert) |
| M-10 | P2 | Handy: Die Auswahl der Messwerte steht unter dem Diagramm und der Tagesbilanz. Wer eine Kurve zuschaltet, muss zurückscrollen. | Auswahl am Handy als aufklappbare Zeile über dem Diagramm |
| M-11 | P3 | Hinweis „Zoomen mit Strg + Mausrad“ auch am Handy | nach Eingabegerät unterscheiden |
| M-12 | P3 | Seitentitel „Übersicht“, Navigation „Bienenstand“; Zurück-Link „← Übersicht“ auf der Umweltseite | einheitlich „Bienenstand“ |
| M-13 | P3 | Kennzahl „Nacht-Referenzwerte 58“ in Analysen: Die Anzahl sagt dem Imker nichts. | Ersetzen, z. B. durch „Zunahme seit Beginn“ je Stand oder „Tage mit Eingriff“ |
| M-14 | P3 | Verwaltung: Messgrößen als Code (`feuchte`, `gewicht`) statt Name; lange Seite ohne Sprungmarken (4570 px am Handy) | Namen aus dem Katalog; Abschnitte als Reiter oder Inhaltsleiste |
| M-15 | P3 | Kleine Schrift: bis 10 px in Diagrammbeschriftungen und Tabellenköpfen; 44 Bedienelemente unter 32 px in der Verwaltung (Links „beenden“, Zahlenfelder) | Mindestgröße 12 px und Tippflächen ≥ 32 px (am Handy ≥ 44 px) |
| M-16 | P3 | Knöpfe zur Völkerwahl in Analysen und die Segmentknöpfe melden ihren Zustand nicht an Bildschirmleser | `aria-pressed` setzen |
| M-17 | P3 | Quellfeld `l` (Licht) in Monospace sieht aus wie `1` | Messgrößenname neben dem Quellfeld zeigen |

### Lücken in den Tests

| ID | Prio | Lücke | Vorschlag |
|---|---|---|---|
| T-01 | P2 | Kennzahlen, Vorher/Nachher-Werte, Summen und Hinweistexte werden im Browser nur auf Vorhandensein geprüft | Sollwerte aus dem synthetischen Oktober fest prüfen (z. B. Kachel Tagesbilanz = letzter Tag, Δ-Vorzeichen) |
| T-02 | P2 | Synthetische Daten zu „glatt“: außen = Luft am Stand, keine ungültigen Werte, nur positive Sprünge, kein Randfall um Mitternacht oder Monatswechsel | Generator erweitern: Versatz Stand/außen, ein Wert `ungueltig`, negativer Sprung ohne Eingriff, Windel bis 00:00, Zeitraum über die Umstellungsnacht |
| T-03 | P2 | Ungetestete Funktionen: Varroa ändern, Maßnahme bearbeiten (Ende), Stand/Volk umbenennen, Messgröße anlegen, Vorher/Nachher für Durchsicht und Varroa, Verdichtung max/min/summe | Datenbank- und Browserfälle ergänzen |
| T-04 | P2 | Seitenlogik (`volk.js`, `analysen.js` …) steckt in Vue-Komponenten und ist nur über den langsamen Browsertest prüfbar | Rechenteile (Kennzahlen, Chronik, Hinweise) in reine Funktionen auslagern und in `test_diagramm.mjs` prüfen |
| T-05 | P2 | Fehlerpfade nicht geprüft: Sitzung abgelaufen, Server nicht erreichbar, 404 eines neuen Endpunkts, 409 beim Speichern | eigene Browserfälle mit abgefangenen Anfragen (`page.route`) |
| T-06 | P3 | Kein Test der Zeitraumwahl (Knöpfe, Datumsfeld), des dunklen Schemas und des Cockpits am Handy | Browserfälle ergänzen; Bildschirmfotos in der CI als Artefakt |
| T-07 | P3 | Mutationstest nur einmalig von Hand | Skript ins Repo (`tests/plattform/mutation.py`), in der CI wöchentlich oder bei Bedarf; Ziel: ≥ 80 % erkannt |

## 4. Bereits geändert: M-01 (Importer)

- **Was:** Felder ohne Kanal sammelt `server/datenbank/importer.py` jetzt je Datei im Speicher und legt sie am Ende der Dateitransaktion mit **einer Anweisung je (Gerät, Quellfeld)** ab. Erfasst werden `zuerst`, `zuletzt` und `anzahl`.
- **Fehlerhafte Zeile:** Ihr Anteil wird mit dem Sicherungspunkt der Zeile verworfen.
- **Nachtragen:** Das Nachtragen zählt wie bisher nicht erneut.
- **Ergebnis:** `test_plattform` lokal 36 s statt > 15 min; alle Tests wie in Abschnitt 2.
- **Mutationstest:** `zuerst`/`zuletzt` falsch → erkannt (`test_importer`); `anzahl` falsch → nicht erkannt (T-03).
- **Änderungsklasse D1:** gleiche Daten, andere Reihenfolge der Schreibzugriffe.

## 5. Grenzen

- Nur synthetische Daten; Chromium als Desktop und mit Handy-Emulation, kein echtes Handy, kein Safari/Firefox.
- Kein Betrieb auf der ThinkStation, kein Apache/TLS.
- Bedienbarkeit als Expertenprüfung (Heuristiken, Messungen von Schriftgröße, Tippflächen und Scrollbreite) – **kein Test mit Imkern**.
- Kontraste nicht gemessen (kein axe-core, kein Download).
- Mutanten gezielt von Hand gewählt (39), keine vollständige Mutationsanalyse.
- Fremdwerkzeuge lokal mit Zustimmung installiert: Playwright 1.56.1 mit Chromium, coverage, pytest, hypothesis, mutmut. mutmut wurde nicht verwendet, weil es unter Windows nicht läuft; stattdessen ein eigenes Skript.

## 6. Vorschlag zur Reihenfolge

1. **Fachfehler:** M-02, M-03, M-04, M-08, jeweils zuerst mit einem Test, der den Fehler zeigt.
2. **Testgenauigkeit:** T-01 bis T-05 und das Mutationsskript im Repo, Ziel ≥ 80 % erkannte Mutanten.
3. **Bedienung:** M-05 bis M-07 und M-09/M-10, danach P3.

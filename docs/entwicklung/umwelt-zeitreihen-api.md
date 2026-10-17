# R1.1 – vollständige, begrenzte Diagrammabfragen

Zusätzlich zur kompatiblen R1-Roh-API `/api/v1/umwelt/messreihen` gibt es
`GET /api/v1/umwelt/zeitreihen` mit **Antwortversion 2**. Anmeldung und
Standrechte entsprechen ADR-0004. OpenAPI ist unter dem geschützten
`/api/v1/umwelt/openapi.json` verfügbar.

| Parameter | Vertrag |
|---|---|
| `stand_id` | Genau ein ausdrücklich freigegebener Stand. |
| `von`, `bis` | Offset-behaftete Zeitstempel, `[von,bis)`, maximal 366 Tage; intern UTC. |
| `kanal_id` | Wiederholbarer Filter, maximal 30 kanonische Kanal-IDs. Ohne Filter höchstens 30 registrierte Kanäle, sonst explizit auswählen. |
| `resolution` | `auto` (Standard), `raw`, `envelope`. `auto` lässt bis 5000 Quellwerte roh, darüber Auswahl echter Extrem-/Randbeobachtungen. |
| `bucket_seconds` | Bei Verdichtung optional explizites UTC-Intervall 1–604800 s. Keine Änderung von Messzeiten. |
| `limit` | 1–5000 zurückgegebene Punkte je Seite, Standard 5000. |
| `cursor` | Unveränderter undurchsichtiger Folgeseitencursor; alle Abfrageparameter bleiben gleich. |

Eine kurze **Repeatable-Read/Read-only-Transaktion** fixiert Quelle, Kanäle und
Messrevisionen. Der Reader verarbeitet die Daten in einem serverseitigen Cursor
mit 2000 Zeilen pro Fetch. Sein begrenztes fertiges Ergebnis wird als unveränderlicher
Snapshot für Folgeseiten gespeichert. Keine offene SQL-Transaktion während des
Browser-Pagings und keine Datenbankmigration für diesen Lesepfad.

`snapshot`, `as_of` (Transaktionsbeginn), `expires_at`, `source_points` und
`total_points` gelten für sämtliche Seiten. `offset` und `returned_points` erlauben
Lücken-/Dublettenprüfung. `complete=true` erst auf der letzten Seite; diese enthält
`next_cursor=null`. Sortierung über alle Reihen: UTC-Zeit, Kanal-ID. Innerhalb einer
Kanalreihe ist die Zeit streng aufsteigend. Die Antwort führt Kanalmetadaten und
Summaries auf jeder Seite mit; ein Kanal ohne Punkte bleibt ausdrücklich leer.

Neue oder verspätete Messungen/Korrekturen während Paging ändern den Snapshot
nicht. Der nächste Poll erhält sie in einem neuen Snapshot. Der neueste vorhandene
Punkt jedes Kanals bleibt auch bei Verdichtung enthalten. Die Browseransicht rendert
erst nach vollständiger, geprüfter Seitensammlung; Kanal-/Zeit-/Standwechsel
brechen alte Fetches ab und verwerfen Ergebnisse der alten Generation.

## Fachliche Darstellung

Für Temperatur, Feuchte, Druck, Licht, UV, Windgeschwindigkeit/-böe und Batterie
werden je UTC-Intervall erste/letzte/minimale/maximale **vorhandene Beobachtungen**
ausgewählt. Randpunkte jeder Null-/Datenlücke bleiben erhalten. Keine künstlichen
Messzeiten, Mittelwertpunkte, Interpolation oder Null-Ausfüllung.

Jeder verdichtete Punkt trägt `bucket` mit:

- UTC-Intervall und `observed-first-last-min-max` als Methode;
- Zahl aller Quellwerte, fehlende Anzahl und beobachtetem Min/Max;
- Vereinigungsmenge der QC-Codes, Quellen und Zeitqualitäten;
- Anzahl synthetischer Quellwerte.

Alle ausgewählten Punkte behalten Record-Hash/-Zeile, Rohwert, Quelle, Revision,
Importzeit und echte Mess-/Empfangszeit aus R1. `gap_before` bezeichnet eine echte
Quelllücke größer als 2,5 erwartete Intervalle. Aus ausgelassenen Beobachtungen
zwischen Min/Max-Auswahlpunkten wird keine falsche Lücke erzeugt. Die Tooltip-Zeit
ist Europe/Berlin mit Sommerzeitoffset; Position/Tiefe, Gerät, Kanal, Einheit und
Intervall-QC bleiben sichtbar.

Regenrate, unbekannte Regenzähler, Windrichtung, Status, Sendeintervall und
unbekannte Messgrößen bleiben **roh**. Kein arithmetisches Richtungsmittel, kein
Regen-Differenz-/Summenmodell. Überschreitet eine solche Reihe das Budget, liefert
die API einen klaren Fehler. Der Nutzer muss Zeitfenster/Kanäle anpassen; die UI
zeigt keine unvollständigen Kurven als erfolgreichen Abruf an.

## Verbindliche Ressourcen- und Fehlergrenzen

- Maximal zwei Millionen Eingabepunkte, 40000 tatsächlich dargestellte
  Original-/Lückenpunkte je Snapshot. Bei übermäßig vielen echten Lücken kann
  auch eine verdichtete Abfrage diesen Grenzwert erreichen; sie wird abgewiesen.
- SQL-Statementbudget 8 s, Readerbudget 20 s; keine unbegrenzte Abfrage.
- Vier Snapshots pro App-Prozess, zusammen maximal **64 MiB serialisierte Daten**,
  Lebensdauer 120 s. Tatsächlichen RSS und Jahresdatensatzumfang separat messen;
  die Bytegrenze ist keine Zusage über den gesamten Python-/Browser-RSS.
- Cursor-HMAC, Benutzer- und Abfragebindung. Jede Seite prüft aktuelle Sitzung
  und Standrechte erneut. Gleichzeitige Nutzer können bei vollem Cache ältere
  Snapshots verdrängen; der Client beginnt bei 410 höchstens einmal neu.
- Einprozess-Uvicorn wie im bestehenden Stack. App-Neustart/Workerwechsel lässt
  Cursor absichtlich verfallen; kein irreführendes Fortsetzen mit neuem Datenstand.
  Mehrere Worker benötigen einen gemeinsamen Cache oder Instanzbindung.

| Status | Bedeutung |
|---|---|
| 401 | Sitzung fehlt, abgelaufen oder widerrufen. |
| 404 | Stand/Kanal oder Snapshot für diesen Nutzer nicht freigegeben. |
| 410 | Snapshot abgelaufen, verdrängt oder App neu gestartet; neue Abfrage beginnen. |
| 422 | Ungültiges Fenster/Cursor, andere Abfrageparameter oder Eingabe-/Ausgabe-/Speicherbudget überschritten. |
| 503 | Datenbank nicht erreichbar, Migration fehlt oder SQL-Zeitbudget erreicht. |

`/messreihen` bleibt für bestehende Clients unverändert keyset-paginiert, jedoch
ohne den neuen Snapshot-Vertrag. Neue Browserabfragen verwenden ausschließlich
`/zeitreihen`. Limits sind kein Nachweis für Last-/Dauerbetrieb; R11-A10 und die
getrennte tatsächliche Sensor-/LAN-Abnahme bleiben eigene Prüfgegenstände.

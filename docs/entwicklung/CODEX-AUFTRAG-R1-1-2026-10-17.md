# Codex-Arbeitsanweisung R1.1 – belastbare Umwelt-Zeitreihen und sichere Monatsarchive

**Datum:** 17.10.2026  
**Repository:** `impyer/bienen-lora-logger`  
**Geprüfter Ausgangsstand:** `refactor/r1-umweltdaten-20261017`, Commit `91284796ab25e78d8a9efc9dd790820faed2f3e7`, PR [#22](https://github.com/impyer/bienen-lora-logger/pull/22). Vor Arbeitsbeginn GitHub-HEAD und Working Tree erneut prüfen.  
**Status:** Beauftragbare R1.1-Anforderung; keine Entwicklungs-, Merge-, Echtdaten- oder Deploymentfreigabe.  
**Ziel:** Die in R1 technisch demonstrierte Software-Datenstrecke von CSV über PostgreSQL und FastAPI zu Apache ECharts für reale, lange Zeitreihen und fortlaufende Monatsarchive vorbereiten. **Kein allgemeines Rewrite.**

## 0. Verbindliche Quellen und Arbeitsschutz

Lies **zuerst**:
- `AGENTS.md`, `CLAUDE.md`, `docs/entwicklung/regelwerk.md`, `docs/entwicklung/tests-freigaben.md` sowie das zentrale `docs/testberichte/befunde.md`.
- [Ursprünglicher Codex-Refactoringauftrag](https://github.com/impyer/bienen-lora-logger/blob/docs/codex-refactoring-20261017/docs/entwicklung/CODEX-REFACTORING-AUFTRAG-2026-10-17.md), [R0-Befund](https://github.com/impyer/bienen-lora-logger/blob/refactor/r1-umweltdaten-20261017/docs/testberichte/2026-10-17-refactoring-r0.md), [R1-Nachweis](https://github.com/impyer/bienen-lora-logger/blob/refactor/r1-umweltdaten-20261017/docs/testberichte/2026-10-17-refactoring-r1.md), [ADR-0004](https://github.com/impyer/bienen-lora-logger/blob/refactor/r1-umweltdaten-20261017/docs/entwicklung/entscheidungen/ADR-0004-umwelt-datenstrecke.md) und [R1-Betriebsanleitung](https://github.com/impyer/bienen-lora-logger/blob/refactor/r1-umweltdaten-20261017/docs/entwicklung/umwelt-r1.md).

**Nicht antasten:** Laufende ThinkStation-Installation, Docker-Volumes, bestehender Apache-Server, TTN-Webhooks, produktive PHP-Empfänger, beelogger-M.40-Eingänge, bestehende Messdateien, BEEP-Daten, Hardware/Firmware und persönliche Konfigurations-/Zugangsdaten. Weder `docker compose down -v` noch destruktive Schema-Neuinitialisierung, produktive Receiver-Umschaltung, öffentliche Portfreigaben oder direkte Deployments durchführen. Kein Zugriff auf reale Sensor- oder Benutzerdateien ohne getrennte explizite Freigabe.

Arbeite auf **einem eigenen R1.1-Implementierungsbranch**, ab dem überprüften aktuellen R1-HEAD, mit PR **gegen den R1-Entwicklungsbranch** (solange die PR-Kette offen ist). Nicht direkt auf `main` oder den laufenden Testbranch pushen. Dokumentiere Ausgangs-SHA, Risiken, betroffene Anforderungen, Tests und offenen Status. R1-Bausteine erhalten, gezielt verbessern. Die Stockkarte ist bis R3/R4 nicht Refactoring-Gegenstand; vorhandene Regressionen dürfen nicht brechen.

## 1. Die nachgewiesenen R1-Defizite

**R1.1-01 (P1): Diagramme schneiden lange Reihen ab.**  
`prototype/claude-ui/umwelt.js` sendet bei `/messreihen` `limit=5000`, verarbeitet aber nicht `result.next_cursor` und lädt keine Folgeseite. Die API in `server/datenbank/umwelt/api.py` unterstützt Cursor und meldet `truncated`. Ein Diagramm darf bei Daten oberhalb des Limits nicht unbemerkt nur die ältesten 5000 Punkte zeigen. Bisherige UI-Meldung („Zeitraum verkürzen“) ist für einen generellen 7-/30-Tage- und Saisonvergleich nicht ausreichend.

**R1.1-02 (P1): Monatsdateien sind nicht als fortlaufende Archivquelle abgebildet.**  
`deploy/heimnetz-test/compose.umwelt.yaml` bindet genau eine Wetter- und eine Bodendatei ein; `umwelt/ingest.py` importiert nach einem festen Quellpfad. Neue Monatsdateien, Nachlieferungen und Ersetzung per atomarem Rename werden nicht automatisch als neue Archive erkannt. Ein Bind-Mount kann bei Umbenennung am alten Inode bleiben.

**R1.1-03 (P1 – Feldnachweis): Die Tests verwenden synthetische CSV.**  
S2120-/Bodenkopfzeilen und Test-API sind geprüft, aber auf dem Betreibergerät wurden noch keine echten Dateien autorisiert angeschlossen. Die Zeitbedeutung der Bodensonde, `message_id`-Eindeutigkeit, Sondenbelegung und realen Wetterdateipfade müssen vor einer Echtdatenfreigabe geprüft werden. **Keine echten Pfade oder Zuordnungen erfinden.**

**R1.1-04 (P2): Import liest jede freigegebene Datei immer vollständig neu.**  
`umwelt/ingest.py` verarbeitet maximal 32 MiB pro Datei und verwendet pro Import einen Voll-Hash-/Voll-Parse-Vorgang. Für Monatsdateien mag das anfangs genügen, für Langzeitarchive braucht es eine dokumentierte inkrementelle/streamende Strategie mit atomarem Fortschritt und Replay bei File-Rotation.

**R1.1-05 (P2): Bediener muss für Quellwechsel und IDs manuell nacharbeiten.**  
Stand-, Geräte- und Quellenidentitäten dürfen keinesfalls erraten werden; dennoch braucht der Betreiber eine sichere, wiederholbare Inventur/Zuordnungs- und Diagnoseanleitung bzw. geeignete administrative CLI, nicht ständig wechselnde Einzelbefehle.

**R1.1-06 (P2 – Betriebssicherheit): Importer besitzt potenziell mehr Rechte als nötig.**  
Das optionale Overlay `importer` erbt vom `app`-Dienst weitreichende DB-Konfiguration. Prüfe ein getrenntes, auf notwendige Tabellen/Operationen begrenztes DB-Rollenmodell, ohne die bestehenden Stockkartenrechte und migrationsbezogenen Arbeiten zu beschädigen.

## 2. Exakte funktionale Anforderungen

### 2.1 Lange Zeitreihen, API und ECharts – zuerst umsetzen

1. Datenabfrage darf keine Daten stillschweigend verlieren. Unterstütze sicher und nachweisbar **24 h, 7 Tage, 30 Tage, Saison sowie frei gewählte Zeitfenster** mit vielen gleichzeitigen Kanälen und mehreren Bienenständen (soweit Rechte erteilt). Die API begrenzt bisher Einzelantworten auf 5000 Messpunkte; diese Grenze soll grundsätzlich erhalten bleiben, aber Client und Server müssen über mehrere Seiten bzw. sinnvoll verdichtete Zeitfenster vollständig kooperieren.
2. Implementiere **korrekte Cursor-Verarbeitung** (oder eine transparent besser begründete Query-Strategie) mit deterministischer Ordnung, Lücken-/Duplikatkontrolle, sauberem Zeitraumwechsel und Abbruch veralteter Anfragen. Bei laufend eintreffenden Werten darf Blättern nicht zu doppelten oder fehlenden Einträgen führen. Cursor-Vertrag bei Bedarf versionieren und mit Tests belegen.
3. Baue eine **serverseitige, fachlich richtige Zeitverdichtung** für größere Fenster bzw. Diagrammauflösungen. Methode, Aggregationsintervall, Messwertanzahl, Min/Max, fehlende Werte, Quellenqualität, Zeitbasis und Units dokumentieren. Wo Verdichtung Werte verdecken könnte, Peaks und relevante Min-/Max-Grenzen nicht verlieren. Rohabfrage für exakten Wertvergleich erhalten.
4. **Keine generische Mittelwertbildung** für kumulative/unklare Regenzähler, Status, Windrichtung (zirkulär), zeitlich diskrete Eingriffe oder FFT-Spektren. Für solche Messgrößen spezifische Semantik und Validierung definieren; wenn nicht verantwortbar, nur unveränderte Rohdarstellung mit klarer Limitmeldung anbieten. Keine Interpolation/Null-Ausfüllung.
5. Der Diagramm-Tooltip zeigt echte Zeit in `Europe/Berlin` einschließlich Sommerzeitoffset, Messquelle, Kanal, Tiefe/Position, Einheit und Datenqualität. Grafiken unterscheiden echte und synthetische Daten klar. Fehlende Werte, Datenlücken und veraltete Quellen bleiben sichtbar.
6. **Aktualität**: neue Werte müssen innerhalb eines **dokumentierten und getesteten** Poll-/Importer-Intervalls erscheinen. Es ist unzulässig, dass ein abgeschnittenes Langzeitdiagramm zwar „aktualisiert“, aber den neuesten Messpunkt nicht enthält. Kein behauptetes Echtzeitverhalten aus einem einmalig bestandenen Render-Test.
7. Keine ungeprüfte Auslieferung riesiger unverdichteter Mengen an den Browser; Limits für Zeitfenster, Reihen/Kanäle, Speicherkosten und Fehlerantworten sind verbindlich. Leere und abgelaufene/entzogene Sitzungen korrekt behandeln; die bereits vorhandenen standbezogenen Rechte müssen auch für neue Aggregationsendpunkte gelten.
8. UI zeigt immer, **welche Daten vollständig, aggregiert, abgeschnitten oder fehlerhaft sind**; Quellenzeitraum und letzte erfolgreiche Import-/Abfragezeit eindeutig benennen. Keine Chart-Erfolgsmeldung bei fehlenden Teilen.

### 2.2 Monatsarchive und Import – zweitens umsetzen

1. Unterstütze mindestens die **S2120-Wettermonatsdateien** und **Bodentemperaturmonatsdateien** inklusive neuen Monatswechseln, Lücken, verspäteten Nachlieferungen, manuellen Backfills und fortgesetztem Append.
2. Erarbeite vor der Implementierung eine kurze **Entscheidungsvorlage/ADR**: eng begrenzte Read-only-Quellverzeichnisse mit festem Dateimuster **oder** isolierte, vom Produktivempfang getrennte Staging-Kopien/Manifeste. Begründung zu Symlinks, Rechteprüfung, File-Rotation, Inode-Wechsel, Backfill, Datensicherheit und Skalierung. **Keine freie Verzeichniswahl über HTTP** und kein pauschales Mount aller Systemdaten.
3. **Quelle nie verändern**: readonly öffnen, keine chmod/chown/rename/schreibenden Locks im Produktivbereich. Belege per Vorher-/Nachher-Hash und Dateimetadaten. Keine privaten Quellpfade/-payloads in API oder öffentliche GitHub-Artefakte.
4. Pro Datei und Quelle stabile Identität und nachvollziehbare Herkunft. Ein zeitstempelgleicher Record aus mehreren Monatsdateien darf nicht unbeabsichtigt zum neuen Messwert werden; echte Korrekturen müssen als Revisionen erhalten bleiben. Vollständige Idempotenz bei Neustart, Rotation, Datei-Ersetzung und Backfill.
5. Importgrenzen und Fehler sauber melden: defekte/teilweise Zeile, BOM, UTF-8, DST, fehlender Wert vs. Null, Komma/Punkt nach belegter Quellsemantik, unbekannte Spalten, falscher Stand/Gerät, Zeitbasis, unlesbare Datei, Datei während des Lesens geändert. Keine stille Skip-Kaskade. Atomare Checkpoints und fehlertolerantes Wiederanlaufen.
6. **Streaming/inkrementeller Import**, soweit für Monatsarchive nötig, mit klaren Regeln für Append, Rücksprung, Rotation und Korrektur. Monatliche Archive müssen nicht zu einem ungesicherten einzigen Vollscan zusammengefasst werden. Ressourcenverbrauch in realistischen synthetischen Belastungsfällen messen statt erfinden.
7. Zusätzliche Sensoren bleiben über **Kanalregister und zeitliche Zuordnung**, nicht durch fest kodierte Gerätelisten im Frontend erweiterbar. Keine zweite primäre Stockmessgerätezuordnung erzeugen; Wetter/Boden sind standbezogene Quellen.
8. Konfigurationsabläufe für Stand-/Geräte-IDs nach tatsächlicher Datenbank prüfen. Bei Unklarheit hart abbrechen, nicht ähnliche Namen matchen.

### 2.3 Sichere Vorbereitung des Echtdatentests – drittens

- Eine **nur lesende Inventuranleitung** für die ThinkStation bereitstellen: Pfadexistenz, CSV-Header, Zeitraum, Dateiwechsel, Größe, Zahl gültiger Zeilen, Rechte und erwartete Geräte-/Standreferenzen; keine Passwörter, Host-Geheimnisse oder privaten Standorte kopieren.
- Eine **geführte, reversible Testanbindung** für **einen** Wetter- und **einen** Bodendatenstrom schreiben, zunächst **mit synthetischen Kopien** in eigenen Mounts. Danach nur nach separater Betreiberfreigabe autorisierte echte Dateien einbinden.
- Bestehende PostgreSQL-Revisionen, Benutzer, Testvölker und CA-Zertifikat behalten. Vor Migration bestehende DB sichern, **Restore in separate Datenbank testen**, Schemaänderungen nur additiv und ausdrücklich auslösen. Alte App-Version als Rückfall behalten; keine automatischen destruktiven Rollbacks.
- Die produktiven TTN-/PHP-/Apache-/beelogger-Module dürfen nicht verändert werden. Der Importer liest ausschließlich freigegebene Kopien oder read-only Quellen. In öffentlichen Commits keine echten Zugangsdaten/Standorte/Original-CSVs.
- Der Endbenutzer muss auf einem **anderen Heimnetzgerät** reale 5/20/50-cm- und Wetterkurven mit richtigen Zeitstempeln, Lücken, Einheiten und laufender Aktualisierung sehen; **dieser physische Feldtest kann von Codex im Cloud-CI nicht behauptet werden**.

## 3. Nicht Gegenstand von R1.1

- BEEP-Stockkarte nachbauen, Kategorien importieren, Königinnen, Durchsichten und Formulare überarbeiten (**R3/R4**).
- Neue beelogger/BEEP-Base-Gewichtskanäle integrieren oder TTN-Webhooks umstellen (**R2, nach R1.1-Feldtest**).
- Vollständiger Austausch von FastAPI, PostgreSQL, PHP-Eingängen oder ECharts; Wechsel auf Vue nur mit expliziter ADR.
- Änderungen an Firmware, Hardware, Sensorzuordnung ohne Beleg oder realen Nutzerdaten.
- Automatisches Deployment auf der ThinkStation, Merge auf `main`, BEEP-Rückschreibzugriff oder produktive Umstellung.

## 4. Abnahmeprüfungen (müssen automatisiert werden)

| Kennung | Soll / objektiver Nachweis |
|---|---|
| R11-A01 | **Mehr als 5000 Werte**, zwei oder mehr gleichzeitige Kanäle, aufsteigende und spät eintreffende Messungen; API+ECharts zeigen bei 7 und 30 Tagen vollständige oder explizit nachvollziehbar verdichtete Reihen **einschließlich jüngstem Wert**. Keine fehlenden/doppelten Seitenübergänge. |
| R11-A02 | 24 h, 7/30 Tage, Saison, Zeitfensterwechsel, Standwechsel, neue Messung während Paging, ungültige/abgelaufene Cursor, Rechteentzug; Daten gehören ausschließlich zum autorisierten Stand. |
| R11-A03 | Roh- vs. verdichtete Temperaturwerte mit bekanntem Min, Max, fehlenden Punkten und Ausreißern validieren. Regen-Summenzähler mit unbekanntem Reset und Windrichtung **nicht falsch aggregieren**. |
| R11-A04 | Zwei aufeinanderfolgende Monatsdateien, echter Monatswechsel im Testdatum, fortgesetzter Append, Rename/Ersetzung, verspätete Nachlieferung und 2× Import: exakt erwartete Records/Revisionszahlen und ursprüngliche Rohwerte bleiben erhalten. |
| R11-A05 | Defekte/teilweise CSV-Zeilen, beschädigter Header, fehlende Berechtigung, Symlink-/Path-Traversal-Versuch, Quelle ändert sich beim Lesen: sicherer Fehler und Wiederanlauf ohne Quellveränderung; Importstatus sichtbar. |
| R11-A06 | Vergleich von Dateien vor und nach Import: Byteinhalt/Hash unverändert; Docker-Mounts tatsächlich read-only, keine Freigabe kompletter produktiver Serverbäume. |
| R11-A07 | **Realer Software-E2E:** synthetische CSV → tatsächlicher periodischer Import → PostgreSQL → FastAPI → echtes CA-validiertes HTTPS → Chromium/ECharts. Keine abgefangenen HTTP-Mocks als Ersatz; mobile Ansicht, 5/20/50 cm, Zeitqualität und Quellenhinweis nachweisen. |
| R11-A08 | Restart aller isolierten Container einschließlich Importer; gespeicherte Revisionen, Checkpoints, Benutzer, CA-Zertifikat und offene Korrekturhistorie erhalten. Backup vor Migration, kontrollierter Restore in neue Testdatenbank. |
| R11-A09 | Bestehende Stockkarten-/LoRa-/Wetter-/Serverregressionen weiterhin PASS; dokumentierte Tests genau dem geprüften SHA zuordnen. Keine Felddaten/Secrets im CI. |
| R11-A10 | Ressourcen-/Dauerprobe mit synthetischen Monatsarchiven im realistischen Jahresumfang (Größen und Anzahl offen deklarieren), Laufzeiten/Speicher dokumentieren, keine unbegrenzte Browserlast. Testgrenzen benennen. |
| R11-A11 | **Manuelle Betreiberabnahme**: auf ThinkStation von echtem Laptop aus, nur nach separater Erlaubnis mit realen CSV; Vergleich ausgewählter Messpunkte, aktuelle Änderungen und Monatswechsel. Wenn nicht ausgeführt: Status **NICHT GELAUFEN**. |

## 5. Vorgehensweise und Reihenfolge der Codex-Arbeit

**Schritt R1.1-A — reproduzierbares Rot:** R1-SHA nennen und vorhandene Tests reproduzieren. Neue Negativtests demonstrieren die 5000-Punkte-Grenze sowie den fehlenden Monatsarchivwechsel, ohne echte Daten anzufassen. Kurzbefund mit Dateipfaden und Verhalten.

**Schritt R1.1-B — Langzeit-Chart:** Implementiere Paginierung/geeignete Versionierung und begründete serverseitige Verdichtung, ohne die bestehenden Werte/Provenienz zu zerstören. PR-Teilcommit mit API-Vertrag und Browser-E2E. Prüfe 24 h bis Saison.

**Schritt R1.1-C — Monatsarchive:** ADR festhalten, Importquellen/Rotation sicher modellieren, Migration gegebenenfalls additiv, atomare Provenienz und Fehlerdiagnose. Vorher/Nachher-Tests, keine produktiven Verzeichnisse mounten.

**Schritt R1.1-D — sicherer Testbetrieb:** Benutzbare lokale Inventur, Beispielkonfiguration und genaue Befehle für **isolierten** Upgrade-/Restore-/Rollback-Test liefern. Getrennte Rechte und Ressourcenprofile prüfen. Nur synthetische Quellen in Cloud und CI.

**Schritt R1.1-E — Abnahmebericht:** Tests R11-A01 bis A11 als PASS/FAIL/SKIP/NICHT GELAUFEN mit Commit-SHA, OS, DB-Version, Docker-/Browserstand, reproduzierbaren Befehlen und konkreten Gegenbeispielen auflisten. Nur erfolgreich nachgewiesene Funktionen als fertig markieren. Physischer LAN-Feldtest bleibt bis zur Betreiberprüfung offen.

**Haltepunkte:** Nach Design einer sensiblen Importpfad-/DB-Migration und vor jeglichem Kontakt mit echtem Betrieb explizite Zustimmung einholen. Keine fachliche Vollständigkeitsbehauptung ohne echte Messwertprüfung.

## 6. Abgabe an Betreiber

1. **Ein reviewbarer R1.1-Pull-Request** gegen den aktuellen R1-Branch, kleine nachvollziehbare Commits und genaue Diff-Zusammenfassung.
2. **Aktualisierte API-/Import-Dokumentation**, ADR wo nötig, reproduzierbare Konfiguration, keine produktiven Geheimnisse.
3. **Neue Unit-, DB-/Migrations-, Integrations-, echte Browser- und Container-Tests**, plus unveränderte frühere Regressionsergebnisse.
4. **Manueller ThinkStation-Testplan** für den Betreiber, mit Sicherung/Restore/Abbruch/Zurückrollen; noch **keine Befehle ungefragt ausführen**.
5. **Ehrliche Restpunktliste**, insbesondere echte CSV-Zuordnung, fehlende BEEP-/Volkdaten, UX/Stockkarte und R2–R5.

## 7. Direkt an Codex zu sendender Startauftrag

> Du bearbeitest `impyer/bienen-lora-logger`. Lies verbindlich `AGENTS.md`, `CLAUDE.md`, Entwicklungsregelwerk, die bisherigen R0-/R1-Berichte, ADR-0004 und das vollständige Dokument `docs/entwicklung/CODEX-AUFTRAG-R1-1-2026-10-17.md` auf dem bereitgestellten Dokumentationsbranch. Prüfe den aktuellen Head des R1-Branches (Referenz `91284796`) und arbeite auf einem **eigenen R1.1-Implementierungsbranch**. Behebe zuerst die **5000-Punkte-/Paging-Grenze mit fachlich korrekter Zeitverdichtung**, anschließend **Monatsarchive/Rotation/Backfill** und schließlich **sichere Testanbindung**. Beginne mit reproduzierbaren roten Integrationstests. Erhalte Rohdaten, Zeitqualitäten, Rechte, Stockkartenrevisionen, produktive Eingänge und Docker-Volumes. Verwende synthetische Daten für eigene Tests und einen echten Software-E2E ohne HTTP-Mocks. Lege einen PR mit Tests, Befundbericht, ADR, Backup-/Rollback-Anleitung und einer manuellen LAN-Abnahmefolge vor. **Kein Merge, keine echte Datenquelle und kein Deployment ohne Betreiberfreigabe.** Kennzeichne jedes nicht ausgeführte Abnahmekriterium ausdrücklich als offen.

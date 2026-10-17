# ADR-0005: Monatsarchive und begrenzte vollständige Zeitreihen

**Status:** Vorschlag zur Betreiberentscheidung, 17.10.2026.
**Klasse/Gate:** D2, R1.1/G1. **Bezug:** R1.1-01/02/04/05/06,
R11-A01–A10, [ADR-0004](ADR-0004-umwelt-datenstrecke.md).

Dieser Entwurf autorisiert keine Änderung bestehender Test-/Produktivinstallationen.
Der [R1.1-Auftrag §5](https://github.com/impyer/bienen-lora-logger/blob/docs/codex-r1-1-20261017/docs/entwicklung/CODEX-AUFTRAG-R1-1-2026-10-17.md#5-vorgehensweise-und-reihenfolge-der-codex-arbeit)
verlangt nach dem sensiblen Importpfad-/DB-Entwurf ausdrückliche Zustimmung.
Gegenstand dieser Entscheidung ist ausschließlich die nachfolgende Implementierung
und Prüfung mit synthetischen Quellen in selbst angelegten Cloud-/CI-Testdatenbanken.
Echte Quellen, ThinkStation, Merge und Deployment sind weiterhin separat.

## Ausgangslage und erhaltene Verträge

R1-HEAD `91284796ab25e78d8a9efc9dd790820faed2f3e7`: eine explizite Datei pro
Quelle, 32-MiB-Vollscan, unveränderliche Roh-/Messrevisionen, Standrechte und
Roh-API `/messreihen`. Die Oberfläche lädt nur die erste Seite. Neue Archive
werden nicht entdeckt. Die Single-File-Registrierung und Roh-API bleiben
kompatibel; Archivquellen und stabile Diagrammabfragen kommen ausdrücklich hinzu.
Stammdaten und Stockkarte werden nicht dupliziert oder neu aufgebaut.

## Zeitreihen ohne neue Datenbankobjekte

Zusätzlicher Vertrag `/api/v1/umwelt/zeitreihen`: begrenzte Abfrage in einer
kurzen PostgreSQL-Repeatable-Read-Lesetransaktion. Ergebnis wird einmal serverseitig
verdichtet und für das Paging als unveränderlicher, kurzlebiger Snapshot gespeichert.
Damit verändern Backfills/Korrekturen während des Blätterns die Folgeseiten nicht.
Der nächste normale Poll öffnet einen neuen Snapshot mit neuen Messwerten.

Snapshots sind an Benutzer, Stand und kanonische Abfrage gebunden. Jedes Abrufen
prüft Sitzung/Standrecht neu. Maximal 5000 Punkte pro Antwort, 30 Kanäle, 366 Tage,
40000 dargestellte Originalpunkte je Snapshot, vier Snapshots und insgesamt
64 MiB serialisierte Daten je App-Prozess; Lebensdauer 120 Sekunden. Überschreitung
liefert einen klaren Fehler statt einer unvollständigen Erfolgsmeldung. Cursor
sind authentifiziert, Versions-/Abfragewechsel werden abgewiesen; nach Ablauf,
Verdrängung oder App-Neustart liefert der Server 410 und der Client kann gezielt
neu beginnen. Keine langlebige SQL-Transaktion oder unveröffentlichte DB-Snapshot-ID.
Der bestehende Einprozess-Uvicorn-Betrieb ist Voraussetzung; mehrere Worker benötigen
später einen gemeinsamen begrenzten Cache oder Instanzbindung.

Verdichtung bedeutet Auswahl **echter** erster/letzter/Minimum-/Maximum-Beobachtungen
pro UTC-Intervall, einschließlich fehlender Werte und erkennbarer Unterbrechungen.
Metadaten nennen Intervall, Methode, Rohanzahl, fehlende Anzahl, Min/Max und
Qualität. Keine Mittelwerte als erfundene Messpunkte. Diskrete/unklare Größen,
Regenzähler und Windrichtung bleiben roh; überschreiten sie das verbindliche
Budget, wird die Abfrage klar begrenzt/abgewiesen und nicht falsch aggregiert.
SQL-Laufzeit und Eingabemenge werden ebenfalls begrenzt und in R11-A10 gemessen.
Die UI lädt alle Seiten, verwirft veraltete Requests und meldet Vollständigkeit
erst nach erfolgreichem Abschluss. Kein freier Datenpfad wird über HTTP angeboten.

## Archiventscheidung: isolierte Staging-Verzeichnisse

Zwei ausdrücklich freigegebene, vom Empfang getrennte Verzeichnisse mit Kopien:
ein Wetterstrom, ein Bodenstrom. Ein Read-only-Bind-Mount **je Staging-Verzeichnis**
ermöglicht das Erkennen neuer Monatsdateien und atomarer Datei-Ersetzungen.
Keine pauschalen Apache-/Logger-/Home-Verzeichnisse und kein automatisches Kopieren
von Produktivdaten. Kopieren/Synchronisieren echter Dateien ist Betreiberarbeit
nach gesonderter Freigabe; in Cloud/CI nur erzeugte synthetische Dateien.

Pro Quelle festes, nicht rekursives Muster mit genau `{YYYY}`/`{MM}`, z. B.
`soil-{YYYY}-{MM}.csv`. Keine frei ausführbaren Regex-/Glob-/Shell-Ausdrücke,
keine Pfadtrenner, `..`, Symlinks oder Spezialdateien. Maximale Dateianzahl,
Zeilen-/Recordgröße und Bearbeitungszeit werden konfigurationsunabhängig begrenzt.
Lesen relativ zum verifizierten Verzeichnisdeskriptor, `O_RDONLY|O_NOFOLLOW`,
reguläre Datei prüfen; keine chmod/chown/rename/schreibenden Quell-Locks.
Auswahl/Rechtefehler werden diagnostiziert, nicht still als leeres Archiv behandelt.

Quelle bleibt eine stabile Geräte-/Standidentität. Neue Datei wird über
`(quelle_id, relativer_name)` identifiziert; Inode, Inhalt, Offset und Status
sind veränderliche **Dateiversion**, keine neue Quelle und kein neues Gerät.
Zuordnungen/Zeiten kommen ausschließlich aus geprüfter Konfiguration und SQL.

## Additive Migration 004 – vorgesehener Datenumfang

| Objekt | Zweck / vorgesehene Felder |
|---|---|
| `um_quelle.archiv_muster` (nullable) | Expliziter Opt-in; NULL behält R1-Einzeldatei, sonst `datei` als freigegebene Staging-Wurzel. Bestehende Quellen werden nicht automatisch umgestellt. |
| `um_archiv_datei` | Quellen-ID/relativer Dateiname eindeutig; Dateiversion, Metadaten, kompletter Prefix-Hash, letzter atomarer vollständiger Byte-/Zeilenoffset, begrenzter Statusbericht. |
| `um_roh_fundstelle` | Roh-ID, Archivdatei, Dateiversion/Hash, Zeile und Bytebezug; unveränderlich. Ein identischer Record aus zwei Dateien erhält zwei Herkunftsbezüge, keine zusätzliche Messrevision. |

Bestehende Migration 003 bleibt bytegleich. 004 erhält einen eigenen
Prüfsummeneintrag und wird ausschließlich explizit ausgeführt. Keine DROP-/TRUNCATE-
Operation, kein Umdeuten alter Revisionen, keine Migration beim App-Start.
Vorher Dump und Restore in eine neue separate Test-DB; alte Benutzer, Durchsichten,
Roh-/Korrekturrevisionen und Checkpoints inhaltlich vergleichen.

Dateien werden gestreamt, Records in begrenzten Batches verarbeitet. Bei Append
wird der vorhandene Prefix verifiziert und nur der vollständige neue Suffix geparst.
Bei neuer Identität, verkürzter/ersetzter Datei oder geändertem Prefix erfolgt
Replay dieser Datei. Unveränderte geprüfte Metadaten können Arbeit vermeiden;
die genaue Prüfung, verbleibende I/O-Kosten und Grenzen werden gemessen und dokumentiert.
Partielle Endzeilen verbleiben vor dem Checkpoint. Fehler/Quelländerung rollt die
Dateitransaktion einschließlich Fortschritt zurück; andere Dateien bleiben prüfbar.
Parser behält UTC, null/0, Rohinhalt, unbekannte Spalten und begrenzte Fehlercodes.

Wiedergefundene identische Rohrecords werden nicht erneut als Korrektur aktiviert.
Damit kann ein alter Monats-Backfill eine neuere Korrektur nicht zurückdrehen.
Neu beobachtete abweichende Inhalte ergeben neue Revisionen und QC. Eine beabsichtigte
Rücknahme auf einen byteidentischen alten Record benötigt eine explizite spätere
Korrekturoperation; Replay allein wird nicht als solche interpretiert.

## Getrennte Betriebsrolle

Migration/Quellenregistrierung/Benutzerrechte bleiben beim administrativen CLI.
Ein gesondertes, ausdrücklich eingerichtetes Import-Login erhält ausschließlich:

- Schema-USAGE, SELECT auf Quell-/Kanal-/Zuordnungs- und Importdaten;
- INSERT auf Roh-/Ereignis-/Messrevisionen, Fundstellen und Importprotokoll;
- INSERT/UPDATE auf die Datei-/Importcheckpoints und notwendige Sequenz-USAGE;
- TEMP für begrenztes Bulk-Staging, keine permanenten DDL-Rechte.

Kein Lesen der Stockkartenbenutzer/Sitzungen, keine Stockkartenschreibrechte,
keine Änderung von Stand, Gerät, Kalibrierung, Quellenkonfiguration oder Migrationen,
kein Superuser/CREATEDB/CREATEROLE. Provisionierung nur als expliziter lokaler
Admin-Schritt, Passwort über privaten Eingabekanal; niemals in Git oder Logs.
Importer bekommt eine eigene DSN, **keinen Sitzungsschlüssel und keine App-DSN**.
Die App/Stockkartenrechte werden nicht nebenbei migriert. Negative Rechteprüfungen
mit echter separater PostgreSQL-Verbindung gehören zu R11-A05/A08.

## Alternativen, Rückfall und Prüfung

Einzeldatei-Mounts blieben eng, erfordern aber manuelle Rotation und verlieren
neue Monatsdateien. Direkte Produktivverzeichnisse vergrößern den freigegebenen
Datenumfang. Ein Manifest wäre möglich, benötigt jedoch eine zusätzliche gepflegte
Publikationsinstanz; isoliertes Staging mit engem Muster ist für diesen Schritt
einfacher prüfbar. Die Grenzen sind ausdrücklich kein globaler Dateisystemzugang.

Rückfall: Importer stoppen, altes App-Image verwenden, zusätzliche Objekte/Volumes
erhalten. Neue Archivquelle kann inaktiv bleiben; ursprüngliche Einzeldatei-
Konfiguration bleibt vorhanden. Keine automatische Down-Migration. Für vollständigen
Datenrücksprung ausschließlich kontrollierten Restore in neue DB planen.

Zustimmung zu diesem Entwurf erlaubt nur synthetische Implementierung/Prüfung.
Die fertige PR bleibt zur separaten Abnahme offen. R11-A11 (echter Laptop/ThinkStation/
reale Dateien), Last-/Betriebsfreigabe und R2–R5 werden dadurch nicht nachgewiesen.

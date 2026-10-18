# R1.1: isolierte Monatsarchive und Abnahme

Aktuelle [Stabilisierung vom 18.10.2026](../testberichte/2026-10-18-refactoring-r1-1-stabilisierung.md):
Temperaturvorauswahl, erhaltener Zoom/Legende, zwei zugelassene Diagrammabfragen
und [ausschließlich synthetischer Staging-Publisher](umwelt-staging-sync.md).
Unabhängige CI/Implementierungs-PR weiterhin blockiert; keine technische
Abnahmereife ohne diesen Nachweis. Historische Messzahlen unten bleiben ihrer
jeweiligen Prüfbasis zugeordnet.

D2, T0/T1/T2/T3, Entwicklungs-Gate G1. Aufbauend auf R1 `91284796`;
[ADR-0005](entscheidungen/ADR-0005-umweltarchive-und-langzeitreihen.md) wurde
am 17.10.2026 ausdrücklich **für synthetische Tests** angenommen. Keine
ThinkStation-, Echtdaten-, Merge- oder Deploymentfreigabe. Ergebnisse:
[R1.1-Prüfbericht](../testberichte/2026-10-17-refactoring-r1-1.md).
Aktuelle Befundstände stehen ausschließlich im [Register](../testberichte/befunde.md#refactoring-r11).

## Importvertrag und Grenzen

Bestehende Einzeldateiquellen bleiben erhalten; keine automatische Umstellung.
Archivquellen haben eine Staging-Wurzel und genau ein Muster wie
`soil-{YYYY}-{MM}.csv` oder `weather-{YYYY}-{MM}.csv`. Zwei getrennte, isolierte
Staging-Verzeichnisse enthalten ausschließlich ausdrücklich bereitgestellte
Kopien eines Wetter- und eines Bodenstroms. Der Importer kopiert nichts vom
Empfänger. Keine HTTP-Schnittstelle für Pfade oder Registrierung.

Die Auswahl ist nicht rekursiv: höchstens 240 passende Dateien und 10000
Verzeichniseinträge. Nicht passende Namen werden ignoriert, z. B. Sicherungskopien
oder ungültige Monatsnummern. Passende Symlinks/Spezialdateien und Symlinks in
**jedem** Pfadbestandteil werden abgewiesen. Relative `..`-Muster sind verboten.
`openat`, `O_RDONLY|O_NOFOLLOW|O_NONBLOCK`, reguläre Datei und abschließender
Dev/Inode/Größe/mtime/ctime-Vergleich schützen den Lesevorgang. Keine Änderungen
an Quellinhalt, Eigentümer, Modus, Namen oder schreibenden Locks. Betriebssysteme
können bei Lesezugriff atime aktualisieren; das ist keine unveränderte-atime-Zusage.

Dateigrenzen: **512 MiB**, **300 Sekunden je Datei**, **64 KiB je CSV-Record**,
Batches mit höchstens **500 Records**, SQL-Statement-Timeout **60 s**,
Lock-Timeout **5 s**, UTF-8 mit optionalem BOM, LF oder CRLF.
Das Dateizeitbudget wird zwischen Records/I/O geprüft; ein laufendes SQL-Statement
kann noch bis zu dessen Timeout benötigen. Mehrzeilige gequotete Records bleiben im Rohtext erhalten. Andere Kodierungen,
kaputte Header/Quote-Struktur oder übergroße Records brechen die Dateitransaktion
ab. Zuordnungs-/Zeit-/Spaltenfehler werden gezählt, höchstens 50 Diagnosen je
Bericht ausgegeben. Ihre Rohzeilen bleiben in der unveränderten Quelle;
eine separate DB-Quarantäne ist weiterhin nicht implementiert. Falsche Zahlen
werden `null` mit QC, leere Zellen bleiben von echter Null unterscheidbar.
Keine Dezimalkomma-Heuristik. Bodenzeit bleibt bis zur Feldprüfung unbekannt,
S2120-Zeit ist Empfangszeit. Unbekannte Spalten werden im Rohrecord aufbewahrt,
aber niemals automatisch zu ungeprüften Messkanälen.

`um_archiv_datei` identifiziert `(Quelle, relativer Dateiname)`. Unveränderte
Metadaten erlauben einen schnellen Skip. Bei Append werden der bereits bestätigte
Prefix und der Gesamtdateihash **streamend neu gelesen**, aber nur der neue
vollständige Suffix geparst und in SQL verarbeitet. Es handelt sich ausdrücklich
nicht um konstante I/O-Kosten: eine geänderte Datei verursacht O(Dateigröße)
Hash-I/O. Ein zusätzlicher Prefix-Hash bestätigt den neuen Checkpoint. Partielle
Endzeilen bleiben vor dem Byte-/Zeilencheckpoint und werden nach Vervollständigung
erneut gelesen. Bei unvollständiger Quote-Struktur wird die ganze Datei zurückgerollt.

Inode-Wechsel, Kürzung oder veränderter Prefix führen zu Replay mit neuer
Dateiversion. Unveränderliche `um_roh_fundstelle` hält Dateiversion, vollständigen
Dateihash, physische Zeile und Byteende jedes gültigen Records fest. Derselbe
Rohrecord in zwei Dateien erhält zwei Fundstellen, keine neue Messrevision.
Bekannte historische Rohvarianten aktivieren sich durch Replay **nicht erneut**;
ein alter Backfill dreht eine Korrektur nicht zurück. Neue abweichende Rohbytes
können eine neue Revision erzeugen. Die bewusste Rücknahme auf einen byteidentischen
alten Record benötigt eine spätere explizite Korrekturoperation; sie ist hier
nicht als eigener Bedienvorgang implementiert. Bei widersprüchlichen neuen
Records führt die zuletzt beobachtete Variante, einschließlich QC. Keine fachliche
Konfliktauflösung wird behauptet.

Jede Datei ist eine Transaktion einschließlich Daten, Provenienz und Checkpoint.
Ein Defekt rollt nur diese Datei zurück; weitere Monate werden trotzdem geprüft.
Der Quelllauf meldet anschließend Fehler. Wiederanlauf ist idempotent.
Der bisherige `um_checkpoint` bleibt als Kompatibilitätsnachweis der zuletzt
abgeschlossenen Datei vorhanden. Das Importprotokoll wächst mit den Läufen;
Aufbewahrung/Archivierung muss vor Dauerbetrieb geplant werden, hier kein Löschen.

## Nur lesende Inventur und explizite Zuordnung

**Noch nicht auf der ThinkStation ausgeführt.** Vor echtem Anschluss eigene
Freigabe einholen. Nur freigegebene Staging-Kopien untersuchen; keine privaten
Verzeichnisse rekursiv durchsuchen, Original-CSVs oder Ausgaben ins öffentliche
Repository kopieren. Dateipfade, Payloads und Standortnamen bleiben lokal.

Im aktivierten Python-Environment, mit administrativer DSN für eine eigene
Testdatenbank `bienen_test` oder `bienenlogger_test`:

```sh
python -m umwelt.cli inventory
python -m umwelt.cli inspect-config --config /privater/pfad/soil.json
```

`inventory` liest exakte Stand-/Geräte-/Kanal-/Quellen-IDs aus PostgreSQL; es
schreibt nichts und gibt keine Quellpfade, Benutzer oder Zugangsdaten aus.
`inspect-config` benötigt keine DB-Verbindung. Es öffnet nur die ausdrücklich
konfigurierten Dateien und meldet Header, gültige Recordzahl, Fehlerzahl,
UTC-Zeitraum, Größe, partielles Ende und Hash, ohne Rohpayload oder Pfadausgabe.
Diese lokalen Ergebnisse trotzdem nicht ungeprüft veröffentlichen.

Vorlage: `deploy/heimnetz-test/umwelt-soil.example.json` und
`umwelt-weather.example.json`. **IDs 0 sind absichtlich ungültige Platzhalter.**
Durch tatsächlich inventarisierte IDs ersetzen, Profil/Art, Quell-Stand/-Gerät,
Zeitbasis, Intervall, Gültigkeitsanfang und 5/20/50-cm-Belegung bestätigen.
Keine Zuordnung anhand ähnlicher Namen. Nicht vorhandene/widersprüchliche IDs
oder veränderte Konfiguration unter demselben Schlüssel brechen ab.
Identische Registrierung ist wiederholbar, kein stilles Überschreiben.

## Kontrollierter synthetischer Upgrade-Test

Diese Befehlsfolge ist eine **Anleitung**, kein Auftrag zum Ausführen auf einer
bestehenden Installation. Für einen frischen eigenen Loopback-Teststack:

1. Projekt-/Image-/Commitnamen, Docker-Version, DB-Version und Ausgangszustand
   dokumentieren. Bisheriges App-Image behalten. Nur zwei isolierte Staging-
   Verzeichnisse synthetisch befüllen und beide mit `:ro` mounten; keine gesamten
   Apache-, Home- oder Loggerbäume. Vorlage `compose.umwelt-archive.yaml` verwenden.
   Variablen `BL_WETTER_STAGING`, `BL_BODEN_STAGING`, `BL_IMPORT_DSN` nur privat
   setzen; `docker compose config` kann Geheimnisse ausgeben, daher `--quiet`.
2. **Vor 004** `pg_dump -Fc --no-owner --no-privileges` in private Datei sichern,
   in eine **neue separate Testdatenbank** mit `pg_restore` zurückspielen. Benutzer,
   Stockkartendurchsichten, Roh-/Ereignis-/Messrevisionen und Checkpoints vergleichen.
   Bei Fehler abbrechen; kein Schema neu initialisieren. Insbesondere `schema.sql`
   niemals auf einem Bestand ausführen (enthält DROP SCHEMA).
3. Ausschließlich im freigegebenen Teststack administrativ explizit ausführen:
   `python -m umwelt.cli migrate`. 003 bleibt prüfsummengleich, 004 ist additiv
   und bekommt einen eigenen Ledger-Eintrag. Wiederholung muss unverändert melden.
   Keine Migration beim App-Start. Konfiguration/DB-Backup getrennt privat sichern.
4. Als Administrator `source --config …` für genau die beiden geprüften Quellen
   ausführen. Eine Einzeldateiquelle wird dabei nicht automatisch umgebogen.
   Alte Quellen bei Archivübernahme nicht gleichzeitig weiter pollen lassen:
   zunächst einen separaten leeren Teststack verwenden; Umstellung eines bestehenden
   Quellbestands benötigt einen eigenen Migrationsplan, kein paralleles Doppelimportieren.
5. Separates Login explizit provisionieren:
   `python -m umwelt.cli import-login --role bl_um_test --password-stdin`.
   Passwort aus einem privaten Kanal zuführen, niemals in Shellhistorie oder Git.
   Mindestens 24 Zeichen. Keine bestehenden privilegierten Rollen umstellen.
   Vorhandene fremde Rollenmitgliedschaften werden abgewiesen. Provisionierung
   ist ein Admin-Schritt; der Laufzeitimporter führt sie nicht aus.
6. Nur `BIENEN_IMPORT_DSN` an `import`/`watch` übergeben, **keine** App-DSN und
   keinen Sitzungsschlüssel. Import/watch fällt absichtlich nicht mehr auf
   `BIENEN_AUTH_DSN` zurück. Auch das alte Einzeldatei-Overlay verlangt jetzt
   `BL_IMPORT_DSN`; diese kontrollierte Konfigurationsänderung vor Start ergänzen.
   Rolle darf nur notwendige Importtabellen lesen/ergänzen, Checkpoints aktualisieren
   und eigene temporäre Batchtabellen erzeugen. Keine Benutzer-/Sitzungsdaten,
   Kalibrier-/Quellkonfiguration, Stockkartenschreibrechte oder permanente DDL.
7. `python -m umwelt.cli import --source-id …`, dann `watch --interval 60` starten.
   Vorher-/Nachher-Hashes und Modus/Größe/Inode/mtime der synthetischen Quellen
   vergleichen. RO-Mounts per Inspect prüfen und Schreibversuch **nur im eigenen
   synthetischen Testverzeichnis** muss EROFS liefern. Neue Monatsdatei, Append,
   atomaren Austausch und alte Nachlieferung durch den Fixture-Erzeuger testen.
8. Alle eigenen Container einschließlich DB/App/Proxy/Importer neu starten.
   Revisionen, Datei-Checkpoints, Benutzer/Sitzung und CA-Fingerprint vergleichen.
   Keine neuen Volumes/CA erzeugen, keine `down -v`-Befehle. Anschließend eigene
   Testservices stoppen und Volumes zur Kontrolle erhalten.

Automatisiert: `python -m unittest discover -s tests/umwelt -p 'test_*.py' -v`,
`python tests/umwelt/e2e.py --long-history --output build/neuer-lauf` und
`python tests/umwelt/year_load.py --output build/neues-jahr`.
Alle DB-Prüfungen **nacheinander**, ausschließlich in einer selbst angelegten,
wegwerfbaren `bienen_test`; Fixture-Tests setzen deren Schema zurück.
Container (neues eigenes Projekt und private Test-Env-Datei):

```sh
R11_ARCHIVE=1 R1_COMPOSE_ENV=/privat/test.env COMPOSE_PROJECT_NAME=bienenlogger-r1-eigener-neuer-test bash tests/umwelt/test_compose.sh
```

Der Test verweigert vorhandene Stände und
Nicht-Loopback-Bindung, erhält alle Testvolumes. Der vorhandene Docker-Proxy-
Vertrauensbereich der App ist 172.16/12. Falls Docker nach vielen erhaltenen
Cloud-Projekten andere Subnetze vergibt, für einen **neuen eigenen** Teststack
freie /28-Netze innerhalb 172.16/12 ausdrücklich per lokalem Compose-IPAM-Overlay
setzen und als `R1_NETWORK_OVERRIDE=/privater/pfad/netz.yaml` übergeben. Kein
vorhandenes Netz umstellen und keine Authentifizierungsgrenze aufweiten. Ohne `R11_ARCHIVE=1` prüft er
weiterhin zwei einzelne Dateien mit separatem Login.

## Manuelle Browser-/LAN-Abnahme nach gesonderter Freigabe (R11-A11)

CA auf **einem anderen echten Heimnetzgerät** ausdrücklich vertrauen, vorhandenes
Zertifikat/Fingerprint vergleichen und Login über HTTPS prüfen. Nicht ohne CA-
Validierung testen. Mit nur den freigegebenen Ständen:

- 24 h, 7/30 Tage, Saison, freie UTC-Fenster und schnelle Stand-/Zeitwechsel prüfen.
  Neuester konkreter CSV-Wert muss im echten Diagramm stehen. Rohmodus gegen
  ausgewählte Originalwerte und reduzierte Temperaturansicht gegen Min/Max prüfen.
- Tooltip enthält Europe/Berlin mit Sommerzeitoffset, Kanal/Gerät, Position/Tiefe,
  Einheit, Zeitbasis und QC. 5/20/50 cm und Wetter einzeln vergleichen. Null,
  fehlende Zelle, Lücke und veraltete Quelle unterscheiden. Unklare Regenzähler,
  Windrichtung/Status bleiben roh oder liefern eine klare Limitmeldung.
- Erfolgsstatus erst nach allen Seiten; Fehlermeldung/Limit statt alter oder
  unvollständiger Kurven. Kanalregister filtert tatsächlich die Abfrage, höchstens
  30 Kanäle. Bei großem Jahresfenster zuerst nur Temperaturkanäle auswählen.
- Aktualisierung mit Uhrzeiten messen: UI-Poll **30 s**, Standardimporter **60 s**;
  im unbelasteten Test plus Import-/Abfragezeit erwarten, keine Echtzeitzusage.
  Cloud-Browserbeleg verwendet Importer **5 s** und UI **30 s**. Unter Last oder
  bei Fehlern ist keine feste Aktualitätsgrenze nachgewiesen.
- Abgelaufene Sitzung/entzogenes Standrecht und einen nicht freigegebenen Stand
  prüfen. Mobile Breite 390 px, Kurven und Kanalwahl bedienbar halten.
- Freigegebenen Monatswechsel, Nachlieferung und Neustart beobachten; ausgewählte
  Werte einschließlich Korrekturhistorie per DB/CSV vergleichen. Fachliche
  Sensorzeit/Message-ID-Eindeutigkeit/Kabeltiefen vom Betreiber bestätigen lassen.

Bei unerklärlichen Werten/Identitäten abbrechen, Importer stoppen, Belege privat
sichern. Rückfall: bisheriges App-Image und bisherige Konfiguration nutzen,
zusätzliche Tabellen/Spalten und Volumes **erhalten**. Keine destruktive Down-
Migration. Ein vollständiger Datenrücksprung benötigt einen kontrollierten Restore
in eine neue DB und eine gesonderte Entscheidung. Echte Dateien nicht verändern.
R2–R5/BEEP-/Volkdaten bleiben außerhalb dieses Abschnitts.

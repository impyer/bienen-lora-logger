# R1: Wetter- und Bodenmessreihen im isolierten Teststack

Diese Anleitung gehört zu ADR-0004 und zum Refactoring-Auftrag R1
(A-01/A-02/A-04/A-05). Änderungsklasse **D2**: additive Datenmigration und
erweiterter Sitzungsvertrag; Nachweise T0/T1/T2/T3, Entwicklungs-Gate G1.
Der Betreiber hat am **17.10.2026** den synthetisch geprüften Entwicklungsstand
aus [PR #22](https://github.com/impyer/bienen-lora-logger/pull/22),
`d672d853a3af5341dc0438756266532a66258620`, ausdrücklich freigegeben.
Die Entscheidung ist in [ADR-0004](entscheidungen/ADR-0004-umwelt-datenstrecke.md#r1-entwicklungsstand-freigegeben)
festgehalten. Echte Sensor-/LAN-Abnahme und Produktionsfreigabe bleiben offen. Der
[Prüfbericht](../testberichte/2026-10-17-refactoring-r1.md) beschreibt die
tatsächlich geprüfte Konfiguration. Aktuelle Befundstände stehen ausschließlich
im [Register](../testberichte/befunde.md#refactoring-webplattform-r0).

Der Betreiber hat für diesen Abschnitt **synthetische CSV-Dateien** erlaubt.
Es gibt keinen Echtdaten-, ThinkStation- oder physischen LAN-Nachweis. R2–R5,
vollständige BEEP-Parität und eine Produktionsfreigabe sind nicht Bestandteil.

## Aufbau und Verträge

`server/datenbank/umwelt` trennt Profile/Parser, Importdienst, Migration, CLI und
API. Die bestehende FastAPI-App und ihre Sitzung bleiben gemeinsam genutzt.
`stand`, `geraet`, `messstelle`, `kanal` und `messgroesse` bleiben die führenden
Identitäten. Zwei neue Adapter lesen die vorhandenen Semikolon-CSV-Formate;
PHP-, TTN-, Apache- und beelogger-Eingänge werden nicht verändert.

Migration `003_umwelt.sql` ergänzt unveränderliche Rohdatensätze, Ereignis- und
Messwertrevisionen, aktuelle Lesesichten, Importläufe/Checkpoints sowie explizite
Standrechte. Quelldatei-Hash, Record-Hash, Zeile, Importzeit, Interpretation
`umwelt-csv@1`, Zeitqualität und ursprünglicher Wert bleiben nachvollziehbar.
Korrekturen einer Ereigniszeit verdrängen den alten Punkt aus der aktuellen
Sicht, behalten aber dessen Historie. Widersprüche bei gleichem Zeit-/Kanalbezug
werden als QC markiert; die zuletzt gelesene Version führt die aktuelle Sicht.
Eine konfliktfreie fachliche Auflösung wird dadurch nicht behauptet.

Der Import öffnet nur explizite reguläre Dateien ohne Symlinks, mit
`O_RDONLY|O_NOFOLLOW`. Er verändert weder Inhalt noch Rechte der Quelle.
Eine während des Lesens veränderte Datei wird im nächsten Durchlauf erneut
versucht. Neue Records und Checkpoint werden atomar geschrieben. Ein bereits
bekannter Dateiinhalt erzeugt keine neuen Messrevisionen. Verkürzte, ersetzte
oder ergänzte Dateien werden erneut gelesen; alte Revisionen bleiben erhalten.

Leere Zellen ergeben `null`, echte Nullen bleiben Null. Ungültige Zahlen erhalten
QC; ungültige Zeitstempel/Zeilen werden mit Zeilennummer gemeldet. Unbekannte
Spalten bleiben in gültigen Rohrecords erhalten und werden nicht automatisch
als Sensor interpretiert. Beschädigte Zeilen bleiben in der unveränderten
Quelldatei; es gibt noch keine separate Datenbank-Quarantäne für jeden Parsefehler.
S2120-Zeit wird als **Empfangszeit**, Bodenzeit zunächst als **unbekannt** geführt.
Vor echtem Anschluss müssen Zeitbedeutung, `message_id` und Sondenkabelzuordnung
bestätigt werden. Die Bodentiefen sind 5, 20 und 50 cm.

Kanalgültigkeit wird beim Schreiben und Lesen geprüft. Nach vorhandenen Werten
sind Faktor-/Versatz-/Semantikänderungen am Kanal gesperrt; ein Wechsel benötigt
einen neuen zeitlichen Kanalabschnitt. Die Migration verweigert Altwerte außerhalb
der Kanalgültigkeit. Sie repariert solche Bestände nicht stillschweigend.

## Softwareprüfungen in einer eigenen Testdatenbank

Python 3.12 und die exakten Versionen aus `server/datenbank/requirements.lock`,
Node.js 22 oder neuer, Playwright 1.56.1, Chromium, PostgreSQL-Client und Caddy
installieren. Die neue CI enthält die vollständigen Schritte. Lokale Tests
benötigen `BIENEN_TEST_DSN` für eine **wegwerfbare** Datenbank namens `bienen_test`.
Sie setzen deren Schema zurück. Niemals eine bestehende Datenbank dazu umbenennen.

```sh
python -m pip install -r server/datenbank/requirements.lock
npm ci --prefix prototype/claude-ui --ignore-scripts
npm run vendor --prefix prototype/claude-ui
python prototype/claude-ui/build_single.py
python -m unittest discover -s tests/umwelt -p 'test_*.py' -v
# Danach, nicht parallel zu anderen Datenbanktests:
python tests/umwelt/e2e.py --output build/r1-e2e
```

Der E2E-Test startet eigene Prozesse an Loopback-Adressen, verwendet echte
PostgreSQL-/FastAPI-/HTTPS-/ECharts-Komponenten und beendet seine Prozesse wieder.
Er prüft einen Dump/Restore vor Migration in einer neu benannten zusätzlichen
Datenbank, erhält diese zur Kontrolle und schreibt synthetische Belege unter
`build/r1-e2e`. Dort liegen auch private Test-CA-Dateien: niemals das gesamte
Verzeichnis veröffentlichen. Die CI lädt nur Ergebnis, Screenshot und bereinigtes
Browserprotokoll hoch.

Für einen **frischen, selbst angelegten Cloud-/CI-Containerstack** akzeptiert
`tests/umwelt/test_compose.sh` eine explizite lokale Test-Env-Datei, Loopback-Bindung
und einen Projektnamen `bienenlogger-r1-*`. Der Test erzeugt synthetische Daten,
prüft zwei Read-only-Dateimounts und einen vollständigen Containerneustart.
Er stoppt seine Services und erhält alle Volumes. Nicht gegen einen vorhandenen
Heimnetz-Teststack ausführen; vorhandene Stände werden absichtlich abgewiesen.

## Kontrollierter Anschluss an den bestehenden Heimnetz-Teststack

Diese Schritte sind eine manuelle Abnahmevorlage nach Betreiberfreigabe,
kein hier ausgeführtes ThinkStation-Deployment. Grundlage ist die
[Heimnetz-Anleitung](../../deploy/heimnetz-test/README.md) mit bestehendem
separatem `bienenlogger_test`-Volume, Zertifikatsvolume und explizitem Projekt.

1. Den bisherigen Git-SHA, Image-IDs, Compose-Projektnamen und die Volumenamen
   festhalten. Importdienst anhalten, falls bereits eingerichtet. Mit den
   vorhandenen `backup.sh`-/`verify-restore.sh`-Werkzeugen sichern und in eine
   **separate** Datenbank zurückspielen. Vor Migration dort zusätzlich die
   Stockkartenrevisionen inhaltlich vergleichen; der neue E2E-Test zeigt diese
   Prüfung mit `to_jsonb(sk_durchsicht_revision)`.
2. R1-Commit gezielt auschecken und das App-Image bauen. Vorhandene Initialisierung
   nicht wiederholen. **`schema.sql` enthält DROP SCHEMA und ist kein Updateweg.**
   Neue Migration nur explizit auf der geprüften isolierten Testdatenbank anwenden:

   ```sh
   cd deploy/heimnetz-test
   docker compose build app
   docker compose run --rm --no-deps app python -m umwelt.cli migrate
   docker compose up -d app
   ```

   Das CLI erlaubt ausschließlich `bienen_test` und `bienenlogger_test`.
   Fehlende Basismigrationen, unbekannter Prüfsummenstand oder unzulässige Altwerte
   führen zum Abbruch. Keine Tabellen werden automatisch neu aufgebaut.
3. Exakt zwei freigegebene, für den Importbenutzer lesbare Dateien auswählen.
   Zunächst ausdrücklich synthetische Kopien benutzen. `BL_WETTER_CSV` und
   `BL_BODEN_CSV` in der privaten `.env` als absolute Pfade ergänzen. Keine
   Elternverzeichnisse und keine laufenden produktiven Dateien schreibbar mounten.
   Das optionale Overlay wird in den folgenden Befehlen stets mitgeführt:

   ```sh
   dc(){ docker compose -f compose.yaml -f compose.umwelt.yaml "$@"; }
   dc build importer
   dc config --quiet
   ```

4. Stand-/Geräte-IDs aus der bestehenden Datenbank prüfen. Geräteart muss `wetter`
   bzw. `boden` sein. Keine Zuordnung anhand ähnlicher Namen erfinden. Pro Quelle
   eine lokale, git-ignorierte `config_local.*.json` anlegen. Beispielstruktur
   für Boden; sämtliche Beispiel-IDs und Headeridentitäten müssen bewusst ersetzt
   werden:

   ```json
   {
     "key": "synthetic-soil",
     "profile": "boden",
     "path": "/sources/boden.csv",
     "stand_id": 123,
     "device_id": 456,
     "source_stand": "synthetic",
     "source_device": "synthetic-soil",
     "synthetic": true,
     "valid_from": "2026-01-01T00:00:00Z",
     "interval_seconds": 900,
     "time_quality": "unbekannt"
   }
   ```

   Wetter: eigenes vorhandenes Gerät, Profil `s2120`, Pfad `/sources/wetter.csv`,
   exakte Headeridentitäten und `time_quality: "empfang"`. Gültigkeitsbeginn und
   erwartetes Intervall anhand der Quelle prüfen. Registrierung legt benötigte
   Kanäle an oder verwendet eindeutig passende vorhandene Kanäle; widersprüchliche
   Einheiten, Belegungen und Standzuordnungen werden abgewiesen.

   ```sh
   dc run --rm --no-deps -T importer python -m umwelt.cli source --config /dev/stdin < config_local.boden.json
   dc run --rm --no-deps -T importer python -m umwelt.cli source --config /dev/stdin < config_local.wetter.json
   # Die zurückgegebenen Quell-IDs verwenden, nicht blind Beispielwerte:
   dc run --rm --no-deps importer python -m umwelt.cli import --source-id 1
   dc run --rm --no-deps importer python -m umwelt.cli import --source-id 2
   # Bestehender aktiver Benutzer und tatsächlich geprüfte Stand-ID:
   dc exec app python -m umwelt.cli grant-stand --username imker --stand-id 123
   dc --profile umwelt up -d importer
   ```

   Das Overlay startet den Watcher alle **60 Sekunden**. Einzelne Dateimounts
   können nach atomarem Austausch einer Hostdatei am alten Inode hängen bleiben;
   nach bestätigter Rotation den Importer mit `dc --profile umwelt up -d
   --force-recreate importer` neu erzeugen. Eine reine Append-Datei benötigt das
   nicht. Watcher und Browser sind getrennte Prozesse.

## Manuelle Abnahme am Laptop/Telefon

1. Eigenes HTTPS-Test-CA-Zertifikat nach bestehender Anleitung vertrauen. URL des
   freigegebenen Teststacks öffnen, **Umwelt & Tracht** wählen, sichtbar anmelden.
   Beim ersten Wechsel von der alten App kann eine Neuanmeldung nötig sein:
   das Cookie wird von `/api/v1/stockkarte` auf `/api/v1` erweitert. Login und
   Logout entfernen beide alten/neuen Pfadvarianten. Stockkarten-API bleibt erhalten.
2. Freigegebenen Stand wählen. Synthetische Kennzeichnung muss sichtbar sein.
   Drei Bodenkurven, °C, 5/20/50 cm, leere Zelle ohne Nullpunkt sowie Wetterwerte
   mit Einheiten und Vorzeichen mit den Quelldateien vergleichen. Tooltip zeigt
   Berlin-Zeit inklusive UTC-Offset, Quelle, Zeitqualität, Revision und QC.
3. 24 h, 7/30 Tage, Saison und freien UTC-Zeitraum, Kanalwahl, Legende, Zoom und
   Telefonbreite prüfen. Ein leerer Stand muss leer bleiben. Ein Importfehler muss
   im Quellenstatus erscheinen. Nach fehlgeschlagener API-Abfrage wird keine alte
   Kurve weiter als aktuell angezeigt.
4. Eine eindeutig markierte gültige Zeile an die **synthetische** CSV anhängen.
   Zeit bis Anzeige messen: mit Standardwerten bis zu 60 s Import + 30 s Browser
   zuzüglich Verarbeitung. Erneuter Import darf keine zusätzliche Messrevision
   anlegen. Der automatisierte Test nutzt 5 s Import und normale 30 s Browser.
5. Bestehende Server-Stockkarte öffnen, zwei berechtigte Völker wählen; gemeinsame
   Sitzung prüfen. Die bisherige Modal-Navigation und Offline-Stammdaten bleiben
   bis R3 bestehen. Logout/Wiederanmeldung und Entzug eines Standrechts prüfen.
   Ein nicht freigegebener Stand liefert 404, fehlende Sitzung 401.
6. Nach gesichertem Neustart DB/App/Proxy/Importer Messwerte, alte Durchsichten,
   Zertifikat und Sitzung vergleichen. Ergebnis mit SHA und Browser dokumentieren.
   Die fachliche LAN-Abnahme gesondert dokumentieren; die erteilte R1-Freigabe
   betrifft den synthetischen Entwicklungsstand. Echte Sensordaten benötigen einen eigenen
   autorisierten Anschluss- und fachlichen Abnahmenachweis.

## API-Grenzen und Rückfall

Lesende Pfade: `/api/v1/umwelt/staende`, `/kanaele`, `/quellen`, `/messreihen`;
geschützter Vertrag: `/api/v1/umwelt/openapi.json`. Standrechte werden pro Anfrage
geprüft. Keine Quell-Dateipfade oder Rohpayloads werden über HTTP ausgegeben.
Zeitfenster benötigen explizite Offsets, höchstens 366 Tage, 30 Filterkanäle und
5000 Punkte pro Seite. Cursor sortiert nach Zeit/Kanal. Die UI meldet das Punktlimit
und verlangt einen kürzeren Zeitraum; sie lädt noch keine beliebig große Historie.

Dateien sind auf 32 MiB begrenzt und werden bei Änderungen vollständig gelesen.
Große Langzeitarchive, Verdichtung, Last-/Dauerbetrieb und automatische
Archivrotation sind R5-Arbeit. Regenzähler mit unbekanntem Reset werden weder
summiert noch differenziert; Windrichtung wird nicht arithmetisch gemittelt.
ECharts verbindet keine expliziten Nullwerte und unterbricht größere Zeitlücken;
es erzeugt keine interpolierten Messpunkte.

Rückfall: Importer stoppen, Teststack stoppen **ohne `-v`**, vorheriges App-Image
und dessen geprüften Commit verwenden. Additive R1-Tabellen und Revisionen bleiben
erhalten; keine Down-Migration löscht Daten. Die bestehende Stockkarte verwendet
weiter ihre bisherigen Tabellen. Ein vollständiger Datenrücksprung erfolgt nur
aus einem geprüften Backup in eine **neue** Datenbank nach gesonderter Freigabe.
Private Env-Dateien, CSV, Dumps und CA-Schlüssel bleiben außerhalb von Git.

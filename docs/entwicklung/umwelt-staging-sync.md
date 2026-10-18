# Synthetische Monatskopien sicher bereitstellen

Ergänzung zum [R1.1-Betrieb](umwelt-r1-1.md), Abschlussauftrag vom 18.10.2026,
D2/G1. **Ausschließlich synthetische Cloud-/CI-Testverzeichnisse.** Kein
produktiver Synchronisierungsdienst wurde installiert oder gestartet. Der
Betreiberauftrag erlaubt diesen Testschritt; er erteilt keine neuen Rechte auf
reale Wetter-/Bodendateien und keine ThinkStation-Freigabe.

## Getrennte Verantwortungen

Der Empfänger schreibt weiter seine Monatsdateien. Ein eigenständiger Publisher
liest ausschließlich explizit konfigurierte synthetische Quellen und schreibt
nur in ein getrenntes Staging-Verzeichnis. Der vorhandene Importer liest dieses
Staging weiterhin readonly und erhält eine eigene eingeschränkte DB-DSN.
Publisher benötigt weder PostgreSQL-Zugang noch Sitzungsschlüssel oder Netzwerk.
Keine Änderung an TTN/PHP/Apache/BEEP, Originaldateinamen, Rechten oder Eigentümern.

Eine Konfiguration je Strom, beispielsweise lokal außerhalb des Repositorys:

```json
{
  "source": "/synthetic/receiver/soil",
  "staging": "/synthetic/staging/soil",
  "pattern": "soil-{YYYY}-{MM}.csv",
  "profile": "boden",
  "source_stand": "synthetic",
  "source_device": "synthetic-soil",
  "synthetic": true
}
```

Für Wetter entsprechend `weather-{YYYY}-{MM}.csv`, `s2120`,
`synthetic-weather`. Die Verzeichnisse müssen bereits existieren. Die CLI
fordert ausdrücklich `synthetic: true`, Stand `synthetic` und eine synthetische
Gerätekennung. Diese Betreiberdeklaration ersetzt keine Prüfung von Pfaden und
Zugriffsrechten. Die Tests erzeugen sämtliche Quellen selbst.

```sh
# Aktiviertes gelocktes Python-Environment, PYTHONPATH=server/datenbank:
python -m umwelt.cli sync-synthetic --config /privat/synthetic-soil.json
# Optional dauerhaft, vom Betreiber ausdrücklich gestartet:
python -m umwelt.cli sync-synthetic --config /privat/synthetic-soil.json --interval 60
```

Einzellauf liefert JSON und Exitcode 1 bei Dateifehlern; periodischer Lauf meldet
Fehler und versucht es im nächsten Intervall erneut. Neue Monate werden dabei
selbständig anhand des festen Musters entdeckt. Kein freier HTTP-Dateizugriff.

## Veröffentlichungsprotokoll

1. Jeden Pfadbestandteil ohne Symlink öffnen. Quelle/Staging dürfen weder
   identisch noch ineinander verschachtelt sein. Auch identische Verzeichnis-
   Inodes werden abgewiesen. Staging muss dem ausführenden Benutzer gehören
   und darf nicht durch Gruppe/Andere beschreibbar sein. Benötigte Leserechte
   für den späteren Importer sind eine eigene lokale Betreiberentscheidung;
   z. B. private Gruppe und setgid-Staging mit Gruppenleserecht, keine Quell-chmods.
2. Ein exklusiver nicht blockierender Staging-Lock verhindert zwei Publisher.
   Feste Monatsmuster, höchstens 240 passende Dateien/10000 Einträge, reguläre
   Dateien, keine Symlinks/FIFOs oder Staging-Hardlinks. Keine automatische
   Löschung alter Monate, auch wenn das Original verschwindet.
3. Vollständigen Quellenhash streamend bilden. Stimmen veröffentlichte Kopie
   und Quellenhash überein, bleibt deren Inode unverändert. Andernfalls in eine
   mit O_EXCL angelegte `.bienen-sync-….part`-Datei im Ziel schreiben (angefordert 0640, durch die lokale umask gegebenenfalls restriktiver).
   Diese temporären Namen passen nicht zum Monatsmuster.
4. UTF-8/BOM, vollständigen CSV-Header, Recordgröße, vollständiges Ende,
   konfigurierte Identität und Zeiten mit **dem vorhandenen Parser** prüfen.
   Defekte/partielle Records verhindern die ganze Veröffentlichung. Unbekannte
   Spalten und Rohbytes bleiben erhalten; ungültige numerische Zellen können
   weiterhin mit Parser-QC als null importiert werden. Keine neue Feldheuristik.
5. Hash der Kopie und ursprüngliche Quellenmetadaten Dev/Inode/Größe/mtime/ctime
   erneut prüfen. Bei Veränderung während des Lesens abbrechen, temporäre Datei
   des aktuellen Laufs entfernen und letzte veröffentlichte Version behalten.
   Quellen werden ausschließlich O_RDONLY geöffnet. Vom Betriebssystem
   aktualisierte **atime ist nicht ausgeschlossen**; readonly/noatime-Mounts
   müssen später vom Betreiber passend geprüft werden.
6. Kopie fsync, `prepared`-Audit fsync, atomarer Rename **innerhalb des Stagings**,
   Verzeichnis fsync und `published`-Audit fsync. Andere Leser sehen einen ganzen
   alten oder neuen Dateistand. Der Importer kann einen während seines Lesens
   ersetzten Inode erkennen und kontrolliert im nächsten Lauf erneut beginnen.

Private `.bienen-sync.jsonl` hält UTC-Zeit, relativen synthetischen Dateinamen,
SHA256, Größe und Zustand (`prepared`, `published`, `unchanged`, `failed`,
`scan_failed`) fest. Keine absoluten Quellpfade, Zugangsdaten oder Rohpayloads.
Audit-/Lockdatei müssen eigene reguläre Dateien ohne Mehrfachlinks sein.

Ein Absturz vor Rename lässt höchstens eine ignorierte `.part`-Datei zurück;
der nächste Lauf verifiziert die Quelle vollständig neu. Verwaiste temporäre
Dateien werden nicht pauschal gelöscht. Nach Absturz zwischen Rename und finalem
Audit bestätigt der nächste Hashvergleich die veröffentlichte Kopie und schreibt
`unchanged`. Audit und Rename bilden keine gemeinsame Dateisystemtransaktion;
`prepared` ohne Abschluss ist bis zu diesem Abgleich ausdrücklich unbestätigt.
Bei Audit-I/O-Fehler wird kein Erfolg behauptet. Quellen/alte Revisionen werden
niemals zur automatischen Fehlerbehebung zurückgeschrieben.

Eine **unerwartete Größenabnahme** überschreibt die letzte Staging-Kopie nicht.
Auch eine legitime kürzere Korrektur benötigt eine dokumentierte Betreiberprüfung
statt stiller Kürzung. Wachsende und gleich lange Korrekturen werden nach den
oben genannten Prüfungen publiziert. Im Import bleiben Originale/Fundstellen und
Revisionen erhalten; bekannte alte Rohvarianten aus Backfills reaktivieren sich
weiterhin nicht. Diese Grenze ist bewusst strenger als der Import-Replay allein.

## Grenzen und noch erforderliche reale Entscheidungen

Dateigrenzen werden wiederverwendet: 512 MiB/Datei, 64 KiB/Record, 300-s-Prüfbudget
zwischen I/O/Records. Pro verändertem Lauf werden Quellen und vorhandene Kopien
vollständig gehasht; kein konstantes I/O-Budget und kein OS-Datei-Watcher. Die
kleinen Batches/Chunks begrenzen den Arbeitsspeicher. Protokollaufbewahrung,
Kapazitätsüberwachung und Bereinigung verwaister Kopien sind vor Dauerbetrieb
zu planen, hier kein automatisches Löschen. Linux/fcntl; Windows nicht geprüft.

Vor realen Quellen separat entscheiden und dokumentieren:

- Welche **exakten** Wetter-/Bodenpfade und Besitzer-/Gruppenrechte freigegeben
  sind, wie Zeitbasis/Message-IDs/5/20/50 cm tatsächlich belegt werden.
- Ob ein eigener Host-Publisher mit eng lesbarer Originalquelle oder ein
  eigener RO-Quellmount eingesetzt wird; Importer bekommt nur RO-Staging.
- Synchronisierungsintervall, sichere Gruppenleserechte ausschließlich im
  Staging, Kapazitäts-/Audit-Retention, Umgang mit legitimer Kürzung und Alarmierung.
- Backup, verifizierter Restore, Prozess-/Timer-Verwaltung und Betriebsabnahme.
  Keine dieser Berechtigungen oder Dienste wurde in dieser Cloud am echten
  Betrieb angelegt. Die CLI wird nicht als produktionsfreigegeben bezeichnet.

## Reproduzierbare synthetische Abnahme und Rückfall

`test_staging_sync.py` prüft reale Dateien/periodischen CLI-Prozess, unveränderte
Quelle, neue Monate, Append/Korrektur, Idempotenz, partielle/defekte Dateien,
Veränderung beim Lesen, Rename-Fehler, Wiederanlauf, Symlinks/FIFO/Hardlinks,
exklusiven Lock und Staging-Schreibrechte. Dateifehler werden gezielt injiziert;
kein simulierter HTTP-Pfad ersetzt die unabhängige echte Browserstrecke.
`test_archives.py` prüft zusätzlich Sync → tatsächlichen PostgreSQL-Import mit
Korrektur und altem Monats-Backfill ohne Rücksetzung, inklusive Provenienz.

```sh
python -m unittest discover -s tests/umwelt -p 'test_*.py' -v
```

Nur auf der bereits beschriebenen wegwerfbaren synthetischen `bienen_test`;
nicht parallel zu anderen DB-Tests. Vor späterem Upgrade: privaten DB-Dump
**vor** Migration/Quellumstellung in eine neue separate Testdatenbank restoren,
Benutzer, Stockkarten-, Messrevisionen und Checkpoints vergleichen, vorhandenes
CA-Zertifikat behalten. Siehe [genaue Backup-/Rückfallfolge](umwelt-r1-1.md).

Bei Problemen Publisher stoppen, Importer bei Bedarf stoppen und letzte geprüfte
Staging-Kopien/Logs sichern. Bisheriges Testimage und bisherige Konfiguration
behalten. Keine `down -v`, Down-Migration, Änderung des Empfängers oder Rückschreiben
in Originale. Physischer ThinkStation-/Laptop-Test bleibt separat.

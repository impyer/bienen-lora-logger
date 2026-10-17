# Bienenlogger – eigenständige Stockkarte im Heimnetz testen

**Erweiterung R1:** Für die optionale Umweltstrecke, explizite additive Migration,
zwei Read-only-CSV-Mounts, gemeinsame Sitzung und manuelle Abnahme gilt zusätzlich
die [R1-Anleitung](../../docs/entwicklung/umwelt-r1.md). Der Basisstart allein
registriert keine Quellen und führt Migration 003 nicht automatisch aus.

**Status: separater HEIMNETZ-TEST, nicht produktive Freigabe.** Diese Installation startet ausschließlich eine neue PostgreSQL-Testdatenbank, den eigenen FastAPI-Stockkartendienst und den HTTPS-Reverse-Proxy. Sie hat keine Verbindung zum bestehenden Bienenlogger-/TTN-Erfassungspfad, zu BEEP oder zu dessen Server. Die grafische Oberfläche verwendet das bestehende Claude-Layout und eigenen Bienenlogger-Code.

## Voraussetzungen

- ThinkStation mit Linux und installiertem **Docker Engine + Docker Compose v2**. Der Benutzer muss `docker compose` ausführen können. Die Docker-Gruppe besitzt faktisch Root-Rechte; nur vertrauenswürdige Benutzer dürfen ihr angehören.
- Git-Zugriff auf das Repository `impyer/bienen-lora-logger`, Branch `test/thinkstation-lan-20261017` nach bestandener Vorabnahme. Ausschließlich den freigegebenen Teststand verwenden.
- Eine feste **private Heimnetz-IP** der ThinkStation und das tatsächliche CIDR deines LAN. Beispiel `192.168.1.50`, Netzwerk `192.168.1.0/24` – **nicht ungeprüft übernehmen**.
- Ein freier HTTPS-Port (Standard **8443**), keine Portweiterleitung im Router. Der bestehende Bienenlogger benutzt weiterhin seine bisherigen Dienste/Ports.
- Browser im Heimnetz; für die gültige HTTPS-Verbindung muss das **lokale Test-CA-Zertifikat** auf deinen **eigenen Testgeräten** einmalig als vertrauenswürdig hinzugefügt werden.

## 1. Repository herunterladen und Umgebungsdatei sicher einrichten

```sh
git clone -b test/thinkstation-lan-20261017 https://github.com/impyer/bienen-lora-logger.git
cd bienen-lora-logger/deploy/heimnetz-test
cp .env.example .env
chmod 600 .env
# IP, CIDR und Port in .env anpassen (z.B. nano .env)
openssl rand -hex 32      # erstes Geheimnis -> BL_DB_PASSWORD
openssl rand -hex 32      # zweites, anderes Geheimnis -> BL_SESSION_SECRET
# Beide Werte in .env einsetzen. Niemals in Git einchecken.
./start.sh
```

`start.sh` prüft private LAN-**IPv4** (die tatsächlich der ThinkStation zugeordnet ist), passendes Heimnetz, Secrets und Port, bevor es Docker Compose startet. Nach Erststart legt es eine lokale, git-ignorierte Initialisierungsmarke an. Bei einem späteren Start verweigert es das unbeabsichtigte Neuerzeugen einer zuvor vorhandenen Testdatenbank oder lokalen Caddy-CA, falls deren Docker-Volumes fehlen. In diesem Fall zuerst das Backup prüfen und eine bewusste Wiederherstellung vornehmen. Es führt keine Migration gegen eine vorhandene Host-PostgreSQL-Instanz aus. **Weder `server/datenbank/schema.sql` noch die Migrationsdateien manuell auf deinem Produktivserver ausführen.** Die alte Basisschema-Datei enthält `DROP SCHEMA`; das Initialisierungsskript darf sie ausschließlich beim ersten Start eines **neuen dedizierten Docker-Datenbank-Volumes** in `bienenlogger_test` verwenden. Eine nachträgliche Änderung vorhandener Testdaten erfolgt nicht automatisch.

## 2. Testvölker, Benutzer und Rechte explizit anlegen

Nach erfolgreichem Start:

```sh
# Nur synthetische Beispieldaten – KEIN BEEP-Import.
docker compose exec app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py seed-demo
# Liste der erzeugten Testvolk-IDs:
docker compose exec app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py list-colonies
# Interaktiv sicheres Passwort wählen; kein Standardbenutzer:
docker compose exec -it app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py create-user imker
# Die echte Volk-ID aus list-colonies statt 1 eingeben:
docker compose exec app python /srv/bienenlogger/server/datenbank/stockkarte_admin.py grant imker 1 write
```

Die CLI legt nur in der Datenbank namens `bienenlogger_test` Änderungen an. Ein Benutzer erhält anfänglich **keine Rechte**. Mit `read` kann nur gelesen, mit `write` zusätzlich geschrieben werden. Bei `revoke` werden auch bestehende Sitzungen widerrufen. Die `seed-demo`-Beispielkategorien sind **keine vollständige BEEP-Taxonomie**; reale Stockkarten sollten erst nach Katalogübernahme und Migrationstest importiert werden.

## 3. Von einem Computer oder Telefon im Heimnetz zugreifen

`https://<LAN-IP-DER-THINKSTATION>:8443` im Browser öffnen. In die **Stockkarte** navigieren und auf **„Server-Stockkarte ansehen“** klicken. Anmeldung mit dem eben angelegten Benutzer. Dort kannst du die explizit freigegebenen Testvölker auswählen, Durchsichten erfassen, bearbeiten, ältere Revisionen lesen und dich abmelden. Andere Ansichten funktionieren weiter wie im Claude-Offline-Prototyp; sie schreiben noch nicht in die Serverdatenbank.

### Lokales HTTPS-Zertifikat

Caddy verwendet eine **lokale Test-Zertifizierungsstelle**, keine öffentliche Internet-CA. Nachdem Caddy einmal gestartet ist:

```sh
docker compose cp proxy:/data/caddy/pki/authorities/local/root.crt certs/heimnetz-test-ca.crt
```

Diese Datei enthält **nur das öffentliche CA-Zertifikat**, nicht den privaten Schlüssel. Übertrage es nur auf deine eigenen Testgeräte. Importiere es dort ausdrücklich als vertrauenswürdige Stammzertifizierungsstelle. Einmaliges manuelles Vertrauen ist erforderlich; bei einem anderen Heimnetzgerät oder nach Löschen des Caddy-Datenvolumes muss die Zertifikatsprüfung erneut erfolgen. **Nicht** den privaten CA-Schlüssel weitergeben und **keine** TLS-Zertifikatsprüfung global deaktivieren.

### Heimnetzfreigabe

Docker veröffentlicht ausschließlich den gewählten HTTPS-Port an der in `.env` eingetragenen privaten `LAN_BIND_IP`. PostgreSQL und FastAPI haben **keinen direkt veröffentlichten Host-Port**. Caddy lässt nur Quell-IP-Adressen aus `LAN_ALLOWED_CIDR` zum Backend durch. Auch eine Host-Firewall sollte TCP/8443 ausschließlich für dieses Subnetz freigeben. Beachte, dass Docker-Portfreigaben je nach Linux-Firewall zusätzliche Regeln in der `DOCKER-USER`-Chain erfordern können. **Keine Router-Portweiterleitung, kein DynDNS-Zugriff und keine öffentliche Bereitstellung.**

## 4. Backup, Neustart, Stopp und Rückfall

```sh
./backup.sh
# Anschließend mit dem tatsächlich erzeugten Dateinamen auf separater DB prüfen:
./verify-restore.sh backups/stockkarte-test-YYYYMMDDTHHMMSSZ.dump
# Erzeugt ein durch pg_restore --list geprüftes, nur dem Besitzer zugängliches
# Datenbankbackup unter deploy/heimnetz-test/backups/
docker compose ps
docker compose logs --tail=100 app
docker compose restart app
# Stoppt die Testoberfläche, aber behält die Datenbank und Zertifikate:
docker compose down
```

**Niemals** beim normalen Stoppen `docker compose down -v` ausführen – das würde die Testdatenbank und die interne HTTPS-CA entfernen. Der vorhandene Bienenlogger ist von `docker compose down` nicht betroffen. Vor einem Update Backup erstellen und bevorzugt einen getesteten Git-Commit auschecken. Zur Rückkehr zu einem vorherigen Stand: `docker compose down`, vorherigen Git-Commit des Testbranches auschecken, `docker compose up -d --build`. Datenbankmigrationen sind nicht automatisch rückgängig zu machen; ein Rücksprung über Schema-Versionen erfordert eine kontrollierte Wiederherstellung des Test-Backups.

Der Stack enthält `backup.sh` zum **Sichern**. Ein **nicht-destruktiver Restore-Test** in einer zusätzlichen Datenbank `bienenlogger_restore_check` wird mitgeliefert und verifiziert Katalog- und Völkeranzahlen. Ein produktiver Restore, der bestehende Tabellen ersetzen würde, ist bewusst nicht automatisiert; dafür sind ausdrückliche Zustimmung und eine gesonderte Rückfallprüfung erforderlich.

## 5. Was technisch geprüft werden muss

- Compose-Konfiguration und Docker-Image-Build ohne Veränderung bestehender Services
- Erste PostgreSQL-16-Initialisierung ausschließlich auf leerem Test-Volume
- Login und Logout, Völkerrechte, CSRF und Revisionskonflikte
- Server-Durchsicht mit Ja/Nein, Zahlen und Auswahllisten speichern und korrigieren
- HTTPS-Zugriff von einem Gerät im LAN mit vertrauenswürdigem Zertifikat
- Backup erstellen und mindestens einmal eine **isolierte Test-Rücksicherung** validieren

**Restgrenzen:** Dies ist die testfähige Erstinstallation, **keine** Zusage für vollständige BEEP-Funktionsparität oder produktive Einsatzreife. Bilder, mehrjährige Beuten-/Königinnen-Referenzabläufe, die komplette BEEP-Taxonomie, administrative Webformulare für den Katalog sowie eine Migration bestehender privater BEEP-Datensätze sind noch nicht abgenommen. Für produktive Verwendung sind außerdem aktualisierte Sicherheitsreviews, vollständige Projekt-CI, Rechte-/Rollback-Tests und Backup-/Restore-Abnahme notwendig.


## Vorabnahme – Datenintegrität und Sicherheitsregressionen

Der Vorabnahme-Zweig `audit/thinkstation-lan-20261017` prüft zusätzlich tatsächliche HTTPS-POST-Anfragen, CSRF, manipulierte Forwarding-Header, konkurrierende Korrekturen, aktive Rechteentzüge, unzulässige Quellnetzwerke, veränderte Ports, Neustarts ohne Volume-Löschung und inhaltliche Restore-Vergleiche. Die automatisierte CI ersetzt keinen abschließenden Verbindungstest von einem zweiten Gerät im tatsächlichen Heimnetz.

R1.1 ergänzt [Monatsarchive und kontrollierten Upgrade-/Rückfalltest](../../docs/entwicklung/umwelt-r1-1.md).
Die beiden Importer-Overlays benötigen auf diesem Branch BL_IMPORT_DSN für ein
separates eingeschränktes Login; keine App-DSN/Sitzungsgeheimnisse im Importer.

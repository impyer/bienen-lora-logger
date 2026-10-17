# Bienenlogger – Vorabnahme ThinkStation-Heimnetz-Test

**Datum:** 17. Oktober 2026  
**Geprüfter Code-Commit:** `ea0dd42b6abc948a36c90a3a041ba6ca4f045477`  
**CI-Nachweis:** https://github.com/impyer/bienen-lora-logger/actions/runs/38997123035  
**Testkonfiguration:** GitHub Actions Linux-Runner, Docker Compose v2, dedizierte PostgreSQL-16-Datenbank `bienenlogger_test`, Caddy 2, FastAPI, Chromium/Playwright; ausschließlich synthetische Völker und Durchsichten.

## Entscheidung

**FREIGABE FÜR EINE ISOLIERTE HEIMNETZ-TESTINSTALLATION (bedingt).** Keine Freigabe für Produktivdaten, BEEP-Ablösung oder Internetbetrieb. Alle vier CI-Jobs auf dem exakt genannten Code-Commit erfolgreich. Noch keine Prüfung der tatsächlichen ThinkStation-Hardware, ihrer Host-Firewall oder einer Verbindung vom zweiten physischen Heimnetzgerät.

## Prüfergebnisse

| Prüffeld | Ergebnis und Nachweis |
| --- | --- |
| Python-/JS-/Shell-Syntax, Katalog- und Datenmodelltests, reproduzierbarer HTML-Build | PASS – Stockkarten-Fachlogik |
| PostgreSQL-16-Migration SK-001/SK-002 auf leerem eigenen Volume | PASS – separater Datenbankjob und Docker-Integration |
| Authentifizierung, Lese-/Schreibrechte je Volk, falsch/nicht vorhanden, CSRF, Origin, 409-Revisionskonflikt | PASS – PostgreSQL/TestClient und echte HTTPS-Requests |
| Rechteentzug bei aktiver Sitzung, Sitzungswiderruf, wiederholte Fehlanmeldungen | PASS – Datenbank-API-Regressionen |
| Caddy-Konfiguration, interne CA und echte TLS-Antwort | PASS – Docker/HTTPS-Integration |
| Verfälschter X-Forwarded-For-Header, unzulässige Quelle und Portänderung von 8443 auf 9443 | PASS – Reverse-Proxy-Negativtest |
| Stockkarte: Erfassung und Korrektur inklusive Revision, korrekte false/0-Werte, unveränderliche Altversionen | PASS – API, Browser und SQL |
| Historisch genauer Zeitstempel / aus Katalog entfernte Option | PASS – Bearbeitung im Browser sperrt möglichen Datenverlust |
| Modulare Claude-Oberfläche und Offline-Einzeldatei, Desktop und schmale Handyansicht | PASS – Chromium/Playwright |
| Docker-Stopp/Neustart ohne `down -v`, Revisionsbestand, TLS-CA und idempotentes Demo-Seeding | PASS – Integrationsjob |
| `pg_dump` und `pg_restore` auf separate Datenbank `bienenlogger_restore_check` | PASS – Wiederherstellung enthält gleiche Revisionswerte, Benutzer-/Rechte-/Checklisten-Zeilen; zweiter Restore scheitert kontrolliert |
| Vorhandene produktive Messdatendienste | Nicht angefasst; keine technische Prüfung auf der ThinkStation |

## Entdeckte und behobene Risiken

1. **Proxy-Vertrauenskette:** Uvicorn vertraut nicht mehr beliebigen Forwarding-IP-Headern (`--no-proxy-headers`). Die interne Proxy-Verbindung und HTTPS-Origin-Prüfung sind getrennt geprüft.
2. **Portkonsistenz:** Caddy und Docker veröffentlichen bei abweichender Konfiguration denselben internen und externen HTTPS-Port. Getestet: 8443 und 9443.
3. **Datenverlust durch Korrektur:** Durchsichten mit genauer/geschätzter Uhrzeit werden nicht mehr stillschweigend zu Datum-only umgeschrieben. Nicht mehr zulässige historische Auswahloptionen und fehlende Felder blockieren die Korrektur.
4. **Verlorene Testvolumes:** Das Startskript prüft die tatsächlich zugewiesene private IPv4 und verweigert nach erfolgter Erstinstallation die versehentliche Erzeugung neuer leerer Datenbank-/Caddy-Volumes, falls die bisherigen fehlen.
5. **Backup ohne Inhaltstest:** Der Restore-Test vergleicht jetzt insbesondere die vollständigen Durchsichtsrevisionen und Rechte-/Checklistenbestände statt nur einfache Kategorien- und Völkerzahlen.

## Grenzen dieser Freigabe

- Keine **echten** privaten BEEP-Datensätze importiert und keine vollständige BEEP-Kategorientaxonomie; die eingebauten Demo-Felder sind nur synthetische Tests.
- Nicht die vollständige BEEP-Funktionsparität: Königinnen-/Beutenbearbeitung mit allen historischen Abläufen, Anhänge/Bilder, administrative Weboberflächen zur serverseitigen Taxonomieverwaltung und Datenmigration sind weiterhin offen.
- Keine Untersuchung der ThinkStation selbst: Linux-/Docker-Version, tatsächlich gebundene IP, UFW/nftables/`DOCKER-USER`-Filter, Router-Portfreigaben, Zertifikatsvertrauen auf Android/iOS/PC und reale Heimnetzverbindungswege müssen vor Ort geprüft werden.
- Das Browser-E2E verwendet für UI-Routinen simulierte API-Antworten, während die HTTPS-HTTP-Integration echte API/DB-Transaktionen prüft. Ein vollständiger automatischer Playwright-Browserdurchlauf über den *echten* TLS-Stack auf einem zweiten physischen LAN-Gerät wurde nicht ausgeführt.
- Noch keine Langzeit-/Lastprüfung, kein automatisches Offsite-Backup und keine Freigabe für öffentliche Erreichbarkeit. Docker-Image-Abhängigkeiten sind versioniert über Kompatibilitätsbereiche, aber nicht per Digest vollständig eingefroren.
- Die ältere `schema.sql` ist destruktiv; sie darf **niemals** gegen vorhandene Produktionsdaten ausgeführt werden. Init-Skript und Tests erlauben sie nur auf dedizierten Wegwerf-/Testdatenbanken.

## Zwingende Bedingungen vor Installation

1. Branch `test/thinkstation-lan-20261017` mit nachweislich geprüftem Code verwenden, nicht ältere Entwicklungsversionen. Die Dokumentation liegt unter `deploy/heimnetz-test/README.md`.
2. Auf der ThinkStation vorhandene Dienste/Ports dokumentieren; Host-Zugriff auf Testport ausschließlich aus dem richtigen Heimnetz erlauben. **Keine Portweiterleitung** am Router.
3. `.env` mit korrekter, **wirklich auf der ThinkStation vorhandener IPv4-Adresse**, korrektem CIDR und zwei unterschiedlichen Zufallsgeheimnissen füllen; niemals ins Repository committen.
4. Beim Erststart **nur Demo-Völker** und einen Testbenutzer mit ausdrücklich eingerichteten Rechten verwenden. Keine privaten BEEP-Daten migrieren.
5. Von einem zweiten Heimnetzgerät HTTPS/Zertifikat, Login, Volk-Freigabe, Erfassung, Korrektur, Logout und nicht-berechtigte Zugriffe prüfen.
6. `./backup.sh` und `./verify-restore.sh <dump>` einmal mit vor Ort erzeugter Beispieldurchsicht erfolgreich durchführen und ein Backup zusätzlich außerhalb des Docker-Hosts aufbewahren.
7. Bei Problemen `docker compose down` (ohne `-v`) ausführen. Bestehende Produktionsdienste nicht anhalten oder umkonfigurieren.

**Betriebsfreigabe beschränkt sich ausdrücklich auf den isolierten Heimnetz-Test mit synthetischen Daten.**

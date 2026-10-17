# Native Stockkarte: lokale Sitzung und Völkerrechte SK-002

**Entwicklungsprototyp; keine Freigabe für das Internet oder den Produktivserver.** Die neue `stockkarte_session_api.py` ist ein **separater** HTTP-Dienst neben der bisherigen technischen Bearer-Token-API. BEEP dient ausschließlich der Funktionsreferenz; keine BEEP-Laufzeitkomponente.

## Sicherheitsmodell

- Migration `002_stockkarte_benutzer.sql` ist **additiv** und benötigt SK-001. Sie erstellt Benutzer mit Argon2-Passwort-Hash, Völkerzuordnungen mit `darf_lesen`/`darf_schreiben` und widerrufbare Sitzungen. Es gibt keine angelegten Standardkonten und **keine automatischen Zugriffsrechte**.
- Zugang über POST `/api/v1/stockkarte/session/login`, Argon2-Hashprüfung. Kurzlebiges zufälliges Token ausschließlich als `HttpOnly`, `Secure`, `SameSite=Strict` Cookie. Datenbank speichert ausschließlich dessen SHA-256-Hash; bei Logout wird die Sitzung widerrufen.
- GET `/api/v1/stockkarte/session` liefert einen temporären CSRF-Wert. Jede schreibende Anfrage benötigt `X-CSRF-Token`. Der Server prüft diesen Wert und vorhandene Origin-Header.
- Auflistungen enthalten ausschließlich ausdrücklich freigegebene Völker. Nicht berechtigte Völker und Durchsichten liefern 404, auch wenn ihre Identitäten erraten werden.
- Änderungen protokollieren den tatsächlich angemeldeten Benutzernamen, nicht einen technischen Sammelbenutzer.
- Deaktiviert ohne `BIENEN_AUTH_DEV_MODE=1`, DSN und Servergeheimnis mit mindestens 32 Zeichen. Fehlende/abgelaufene Sitzung: 401. Keine Browser-Dauertokens.
- Anwendung benötigt `fastapi`, `psycopg[binary]`, `argon2-cffi`. Das CLI `stockkarte_setup_user.py` erstellt nur nach ausdrücklicher Ausführung und Passworteingabe einen zunächst unberechtigten Account.

## Grenzen

Es handelt sich um einen lokal isolierten Entwicklerdienst: Prozesslokale Login-Drosselung, noch keine vollständige Produktions-Rate-Limitierung, Rollenadministration, Benutzer-UI, TLS-Proxy-Härtung, Zugriffstokenrotation, Recovery, zentralisierte Sitzungsverwaltung und Backup/Restore. Nicht auf `0.0.0.0` veröffentlichen.

Ein Königinnenwechsel kann mehrere Völker über die Zeit betreffen. Die Sitzungsschnittstelle aktiviert deshalb **noch keine Königinnenbearbeitung**, bis die Zugriffsregeln für historische Zuordnungen separat spezifiziert und getestet sind. Die bestehende Königinnen-Historie in PostgreSQL bleibt erhalten.

Die Claude-HTML-Oberfläche bleibt bis zum nächsten Schritt unverändert und speichert wie bisher lokale Entwürfe. Die Browseranmeldung wird erst angebunden, nachdem Logout, CSRF, Völkerfilter und vollständiger HTTP-E2E erfolgreich geprüft wurden. Keine privaten BEEP-Dateien im öffentlichen Repo.

## Test

`tests/datenbank/test_stockkarte_session.py`: PostgreSQL-16-Wegwerfdatenbank `bienen_test`, gesperrte Konfiguration, echte Argon2-Kennwörter, Secure-/HttpOnly-Cookie, CSRF/Origin, fremde Völker, Lese-/Schreibrechte, Versionierung, Logout und auditierter Benutzername.

**Wichtig:** Die alte `server/datenbank/schema.sql` ist destruktiv; der DB-Test ruft sie ausschließlich nach strikter Prüfung des Datenbanknamens `bienen_test` auf. Für Produktionsdaten sind vorerst keine Migrationen freigegeben.
## Lesender Anschluss an das Claude-Layout

Mit `server/datenbank/stockkarte_dev_web.py` kann der **modulare** Claude-Prototyp vom selben localhost-Ursprung wie die authentifizierte API geladen werden. Der Dienst liefert ausschließlich freigegebene statische Dateien (`index.html`, `app.js`, `stockkarte_native.js`, `stockkarte_live.js`, `style.css`) und eine strikte Content-Security-Policy; die inline-script-haltige HTML-Einzeldatei wird nicht vom Webserver ausgeliefert.

Im Bereich **Stockkarte → Server-Stockkarte ansehen** kann man sich anmelden und zugelassene Völker, Durchsichten sowie Revisionen lesen. Das Formular ordnet die aus PostgreSQL stammenden Volk-IDs **nicht** automatisch den alten Demo-/BEEP-Volknummern zu. BEEP-Originale und lokale Testentwürfe bleiben unverändert. Das Passwort wird nach dem Absenden aus dem Formular gelöscht, die CSRF-Kennung bleibt ausschließlich im Arbeitsspeicher des Browser-Tabs, der Sitzungswert bleibt im HttpOnly-Cookie.

Die HTML-Einzeldatei bleibt offline funktionsfähig und zeigt beim Serverzugriff einen entsprechenden Hinweis. **Noch keine schreibende Browserfunktion**, damit kein versehentliches Synchronisieren von Offline-Testentwürfen stattfindet.

Der Session-Dienst weist Verbindungen mit nicht-lokaler Peer-Adresse zurück; ein Reverse Proxy, der externe Nutzer auf die Loopback-Adresse weiterleitet, ist in dieser Entwicklungsphase nicht erlaubt.

Nur für ein ausdrücklich isoliertes localhost-Entwicklungssystem kann `BIENEN_AUTH_INSECURE_LOCALHOST=1` die Secure-Cookie-Pflicht vorübergehend für HTTP abschalten. Standardmäßig bleibt Secure aktiv und erfordert HTTPS. Niemals diese Option in einer öffentlich erreichbaren Umgebung verwenden.

Beispiel ausschließlich lokal (nach Installation von uvicorn, argon2-cffi, psycopg und FastAPI und manueller Einrichtung eines berechtigten Testkontos):

```sh
BIENEN_AUTH_DEV_MODE=1 BIENEN_AUTH_DSN='...' BIENEN_AUTH_SECRET='...mindestens 32 zufällige Zeichen...' \
uvicorn stockkarte_dev_web:app --app-dir server/datenbank --host 127.0.0.1 --port 8765
```

Keine reale DSN und keine Geheimnisse im Repository hinterlegen. Vor dem ersten Produktionsbetrieb sind TLS, Rollenverwaltung, Backups, Account-Recovery und Schema-Konsolidierung zu prüfen.
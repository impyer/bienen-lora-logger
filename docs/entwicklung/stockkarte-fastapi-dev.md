# Native Stockkarte: interne FastAPI v0.1

Status: Entwicklungsbaustein, weder internetfähig noch produktiv freigegeben. Es wird ausschließlich eigener Bienenlogger-Code verwendet, keine eingebundene BEEP-Anwendung.

## Sicherheit

- Keine aktive Standardkonfiguration: ohne BIENEN_API_DEV_MODE=1, BIENEN_API_DSN und zwei unterschiedliche Tokens mit mindestens 32 Zeichen liefert die API 503.
- Authentifizierung ausschließlich über den Header Authorization: Bearer TOKEN. Ein Lesetoken erlaubt GET, ein Schreibtoken zusätzlich POST. Keine Token in URL oder BrowserlocalStorage speichern.
- Keine CORS-Freigabe, keine öffentliche OpenAPI-/Swagger-Route. Cache-Control: no-store. Die API ist absichtlich nur für localhost-Entwicklung vorgesehen.
- Der Bearbeiter wird vorläufig als technische Dienstidentität stockkarte-dev-editor protokolliert. Echte Nutzerkonten, Rollen je Stand und Volk, sichere Sessions, Audit-Zuordnung und Browser-Login fehlen. Deshalb ausdrücklich kein Produktivbetrieb.

Start nach manueller Installation von fastapi, uvicorn, psycopg[binary]: Umgebungsvariablen BIENEN_API_DEV_MODE, BIENEN_API_DSN, BIENEN_API_READ_TOKEN und BIENEN_API_WRITE_TOKEN setzen; dann uvicorn stockkarte_api:app --app-dir server/datenbank --host 127.0.0.1 --port 8765. Keine realen Geheimnisse in GitHub eintragen.

## Pfade unter /api/v1/stockkarte

| Operation | Berechtigung |
| --- | --- |
| GET /voelker, GET /katalog | reader / writer |
| GET /voelker/{id}/durchsichten | reader / writer, paginiert |
| POST /voelker/{id}/durchsichten | writer |
| GET /durchsichten/{id}/revisionen | reader / writer |
| POST /durchsichten/{id}/revisionen | writer mit expected_revision |
| GET /koeniginnen/{id}/revisionen | reader / writer |
| POST /koeniginnen/{id}/revisionen | writer |

Die API ist strikt: keine freie Quellkennzeichnung als BEEP-Import, keine DELETE-Endpunkte, unbekannte Anforderungsfelder abgewiesen. Alte Revisionen bleiben unverändert. Nur-Datum-Einträge erhalten keinen erfundenen Zeitstempel. Alte Bearbeitungsstände führen zu 409; ungültige Werte zu 422.

## Grenzen und Tests

Der getrennte PostgreSQL-16-CI-Job prüft mit FastAPI TestClient die Authentifizierung, Schreibrechte, Format- und Datenbankvalidierung, stabile Historie, die Königinnenkorrektur und API-Fehlerfälle. Die Testdatenbank ist ausschließlich bienen_test; das alte Schema mit DROP SCHEMA wird außerhalb dieser Datenbank nicht angewandt.

Die Claude-Weboberfläche bleibt noch Offline-Testoberfläche und ist NICHT mit der API gekoppelt. Eine echte Browseranbindung erfordert zunächst nutzerbezogene Authentifizierung und Rechte, damit keine lang gültigen Diensttokens im Frontend stehen. Die experimentellen sk_-Tabellen sind vor Produktionsfreigabe mit den bisherigen Stockkarten-Entwurfstabellen zu konsolidieren.
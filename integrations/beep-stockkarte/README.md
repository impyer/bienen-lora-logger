# Bienenlogger + originale BEEP-Stockkarte – Integrationsentwurf (16.10.2026)

## Entscheidung: kein weiterer Stockkarten-Nachbau

**Die originale BEEP-Vue-Anwendung** ist das führende UI für Stockkarte, Durchsicht, Checklisten, Königinnen und Beutenkonfiguration. Das vollständige Originalprojekt liegt als **Git-Submodul** unter `../beep-vue-app` und ist auf den Stand `24fd68890d62495a94090b242e686ad811b714cb` fixiert:

- https://github.com/beepnl/beep-vue-app (MIT; originale Lizenzdatei im Submodul erhalten)
- https://github.com/beepnl/BEEP (Laravel-Backend, AGPL-3.0; **nicht** in diesen PR vendort)

Vue 2, Vuetify 2, Vuex, Vue Router und diverse Eingabekomponenten müssen zusammen betrieben werden. **Die Original-App ist nicht als einzelne HTML-Datei lauffähig.** Deshalb werden keine kopierten, funktionsreduzierten Formulare mehr als BEEP-Original ausgegeben.

### Von BEEP unverändert übernommene Bereiche

| Funktion | Quelle im Submodul | Status |
| --- | --- | --- |
| Durchsichten ansehen, suchen, filtern, ändern | `src/router/views/hive-inspections.vue`, `inspect.vue` | Originalcode referenziert; noch kein eigenes Deployment |
| BEEP-Feldtypen & verschachtelte Kategorien | `src/components/checklist-fieldset.vue`, `checklist-input.vue` | Originalcode referenziert |
| Checklisten anlegen/ändern | `src/router/views/checklist.vue`, `src/components/checklist-tree.vue` | Originalcode referenziert |
| Königinnen bearbeiten | `src/components/queen-edit-details.vue`, `src/router/views/hive-edit.vue` | Originalcode referenziert |
| Beutenaufbau | `src/components/hive-edit-details.vue`, `hive-factory.vue` | Originalcode referenziert |
| API/Auth/Übersetzungen/Offline-Karten | Restliche Original-App | Originalcode referenziert |

### Originalrouten (aus `src/router/routes.js`)

- `/hives/:id/inspections/` – Stockkarte/Durchsichten
- `/hives/:id/inspections/:inspection` – bestehende Durchsicht bearbeiten
- `/inspect?hiveId=:id` – neue Durchsicht
- `/checklist/:id/edit` und `/checklists/` – Checklisten
- `/hives/:id/edit` – Beute und Königin bearbeiten

Die hier beigefügte URL-Funktion `stockkarte_urls.js` erzeugt bewusst nur **pfadbasierte Navigation** und enthält keine echten Hive-IDs und keine Anmeldedaten.

## Sofort testbarer Weg (bestehendes BEEP-Konto)

Bis zur Eigeninstallation können Bienenlogger-Kacheln den Nutzer unter `https://app.beep.nl/hives/{beep_hive_id}/inspections/` bzw. `/hives/{beep_hive_id}/edit` in die **unveränderte offizielle BEEP-Oberfläche** weiterleiten. BEEP-Login erfolgt dort. Export-Snapshots werden weiterhin nur lesend im Bienenlogger angezeigt. Die BEEP-ID ist **nicht** die dauerhafte Volk-ID; sie wird als externe Identität hinterlegt.

## Selbsthosting (spätere, separate Deployment-Freigabe)

1. `git submodule update --init integrations/beep-vue-app` (für neue Klone `git clone --recurse-submodules ...`).
2. Prüfen: `git -C integrations/beep-vue-app rev-parse HEAD` == oben fixierter SHA.
3. In einer **isolierten Testumgebung**: `cd integrations/beep-vue-app && npm ci && npm run build`. Node-/Abhängigkeitskompatibilität des alten Vue-2-Stacks und bekannte Sicherheitsupdates sind vor öffentlicher Bereitstellung zu prüfen.
4. Original-App auf eigener HTTPS-(Sub-)Domain **im Webroot** bereitstellen (Vue `publicPath:'/'` und HTML5-Router). Den Vue-Fallback nur für den App-VHost aktivieren; keine bestehenden PHP/TTN-Endpunkte dadurch überschreiben.
5. Über `VUE_APP_API_URL` und `VUE_APP_BASE_API_URL` die **autorisierte** BEEP-API konfigurieren. Die Original-App setzt Bearer-Token (siehe `src/api/axios.js`). Keine API-Keys/Tokens in Git, Buildvariablen oder ausgelieferte JS-Pakete legen; `VUE_APP_*` wird öffentlich in den Browser-Build eingebettet. Cross-Origin/CORS und Login müssen zuerst bestätigt sein.
6. Eigene Datenhaltung: entweder den AGPL-lizenzierten BEEP-Backend-Dienst **separat und rechtskonform** selbst hosten oder einen später zu entwickelnden kompatiblen API-Adapter einsetzen. Der Adapter benötigt Auth, Mandantentrennung, IDs, vollständige Taxonomie, Inputtypen, Checklisten, Inspektionen, Fotos und Versionierung. **Noch nicht implementiert.**
7. Vergleich mit dem originalen BEEP-Konto: Checklisten, Eingabetypen, Königinnenänderungen und ältere Durchsichten. Erst danach eventuell eigene Datenquelle auf Schreibbetrieb umstellen.

**Datenschutz/Sicherheit:** Kein öffentliches GitHub mit echten BEEP-Exporten, privaten Hive-IDs, Anmeldedaten oder Ortsbezügen. Der direkte Link ist ein Navigationspfad, kein authentifizierter API-Zugriff und keine Synchronisation. Eine Dual-Write-Strecke (BEEP und eigener Server zugleich) wäre konfliktträchtig und ist ausdrücklich nicht vorhanden.

### Änderungsklasse und Prüfgrenze

UI-/Integrationsentwurf: D1, T0/Hosttests. Keine produktive Inbetriebnahme, kein npm-Build der Vollanwendung in ChatGPT, keine Browser-/API-E2E-Abnahme, kein DB-Schema geändert. Der bestehende Serverbetrieb und PR #13/14 bleiben unberührt.

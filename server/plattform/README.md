# Plattform: Lese-API und Oberfläche (Phase B, nur lesend)

Konzept 0.2, §4 Nr. 4–5, §6 und §10 Schritt 5: Die eigene Plattform verbindet die **Stockkarte** (Vorbild BEEP) mit der **Datenauswertung** (Vorbild beelogger). Diese Stufe zeigt die Daten an. Schreiben (Stockkarte erfassen, Stammdaten pflegen) kommt erst mit Phase C.

```
Eingänge (server/eingang, lora, wetter) → JSONL-Rohprotokolle → importer.py → PostgreSQL (server/datenbank)
                                                                                   │
                                     Browser ← Oberfläche (web/) ← Lese-API (api/, FastAPI) ┘
```

**Status:** Entwurf, getestet nur mit synthetischen Daten in der CI (T1/T2). Nicht auf der ThinkStation eingerichtet, kein Betrieb mit echten Daten. Der Betrieb startet leer; Stammdaten (Stände, Völker, Geräte, Kanäle) gibt es noch nicht als Eingabemaske.

| Pfad | Inhalt |
|---|---|
| `api/app.py` | FastAPI-App: Endpunkte, Anmeldung, Sicherheitskopfzeilen, liefert `web/` aus |
| `api/abfragen.py` | alle SQL-Abfragen, jede Anfrage in einer Nur-Lese-Transaktion; Kennwerte kommen aus den Sichten des Schemas (`berechnung@version`) |
| `api/verdichtung.py` | Rasterweite (höchstens 2000 Punkte je Reihe), Verdichtung nach `messgroesse.verdichtung`, Lücken als `null` |
| `api/anmeldung.py` | ein Konto, scrypt-Hash, signiertes Sitzungscookie, Bremse gegen Durchprobieren |
| `web/` | Oberfläche: Vue 3 und Apache ECharts ohne Build-Schritt (`vendor/README.md`) |
| `synthetisch.py` | synthetischer Oktober 2026 mit Fehlern und Grenzfällen, nur für Testdatenbanken |
| `plattform_config.beispiel.toml` | Vorlage der lokalen Konfiguration (`plattform_config.toml` bleibt lokal) |
| `requirements.txt` | Python-Pakete mit festen Versionen |

## Endpunkte

Alle lesend. Ohne Sitzung erreichbar sind nur `GET /api/gesundheit` und `POST /api/anmelden`. Zeiten gehen ISO 8601 mit Zeitzone ein (`2026-10-01T00:00:00Z`) und kommen in UTC zurück. Die Oberfläche zeigt sie in Europe/Berlin.

| Endpunkt | Antwort |
|---|---|
| `POST /api/anmelden` `{"passwort": …}`, `POST /api/abmelden`, `GET /api/sitzung` | Sitzung; 401 falsches Passwort, 403 fremde Herkunft, 429 nach 5 Fehlversuchen für 60 s |
| `GET /api/gesundheit` | Datenbank erreichbar, Zeit des letzten Imports |
| `GET /api/messgroessen` | Katalog = Register der Oberfläche (Achse, Farbe, Darstellung, Verdichtung) |
| `GET /api/staende?zeit=` | Stände mit ihren Völkern zum Zeitpunkt (Aufstellung → Belegung), Gewicht, Tagesbilanz des Vortags, letzte Messung |
| `GET /api/voelker/{id}?zeit=` | Stand, Beute mit Zargen, Königin, Geräte mit Zeitraum |
| `GET /api/voelker/{id}/messreihen?von&bis&groessen=` | Reihen je Messgröße und Messstelle, verdichtet; `null` = Lücke, nie 0 |
| `GET /api/staende/{id}/umwelt?von&bis&groessen=` | dasselbe für Geräte am Stand (Wetterstation) |
| `GET /api/voelker/{id}/tagesbilanz?von&bis` | Sicht `gewicht_tagesbilanz` mit `mit_eingriff` (Leitplanke L8) |
| `GET /api/voelker/{id}/ereignisse?von&bis` | Durchsichten (mit `zeitgenauigkeit`), Maßnahmen als Zeitraum, Varroa pro Tag, Vereinigung usw. |
| `GET /api/pruefungen` | unbenannte Quellfelder (K-06), Geräte ohne Zuordnung, Zuordnungsprüfung (HB-09), Importstand |

Fehler: 400 bei ungültiger Zeit, Zeitraum über 400 Tage oder unbekannter Messgröße; 404 bei unbekanntem Volk oder Stand. Ausgeschlossen sind Werte mit `qualitaet = 'ungueltig'`. Den Regenzähler (`unbekannte_summe`) zeigt die API mit seinem letzten Stand je Raster und summiert ihn nie. Die Windrichtung wird als Kreismittel verdichtet.

## Oberfläche

- **Übersicht**: Kacheln je Stand und Volk, Hinweis bei veralteten Messungen und auf Meldungen der Datenquellen.
- **Volk-Cockpit**: Kurven frei wählbar (vorgewählt Gewicht und Temperaturen), Achsen nach Katalog, Zoom mit Strg + Mausrad oder Schieber, Gewicht relativ.
  - Maßnahmen erscheinen als Bänder, kurze als Linie.
  - Durchsichten mit Uhrzeit als Linie, Einträge ohne Uhrzeit als Tagesband „Uhrzeit übernommen“ (K-03).
  - Tagesbilanz als Balken, Tage mit Eingriff grau.
- **Umwelt**: Klima, Wind (Richtung als Pfeile) und Regen eines Stands.
- **Datenquellen**: was der Importer nicht zuordnen konnte, Geräte, Importstand.

## Betrieb (beschrieben, nicht eingerichtet)

1. Python ≥ 3.11 und eine eigene virtuelle Umgebung: `python3 -m venv /opt/bienen/venv && /opt/bienen/venv/bin/pip install -r requirements.txt`
2. **Datenbankrolle** nur mit Leserecht, z. B. `CREATE ROLE bienen_lesen LOGIN; GRANT USAGE ON SCHEMA bienen TO bienen_lesen; GRANT SELECT ON ALL TABLES IN SCHEMA bienen TO bienen_lesen;`
3. **Konfiguration**:
   - `plattform_config.beispiel.toml` nach `/etc/bienen/plattform_config.toml` kopieren.
   - Passwort-Hash und Sitzungsschlüssel erzeugen: `cd server/plattform && python3 -m api.anmeldung`.
4. **Dienst** (systemd), nur auf localhost: `BIENEN_PLATTFORM_CONFIG=/etc/bienen/plattform_config.toml /opt/bienen/venv/bin/uvicorn --factory api.app:erstellen --app-dir /pfad/zu/server/plattform --host 127.0.0.1 --port 8081`
5. **Apache**:
   - `ProxyPass /bienen/ http://127.0.0.1:8081/` mit `ProxyPreserveHost On` (für die Herkunftsprüfung der Anmeldung).
   - Zugriff nur aus dem Heimnetz (`Require ip 192.168.…`), nur über HTTPS (`cookie_sicher = true`).
   - Die TTN-Eingänge bleiben die einzigen Pfade, die von außen erreichbar sind (Konzept §6a).

Grenzen:
- Die Sitzung ist ein signiertes Cookie. Abmelden löscht es nur in diesem Browser; alle Sitzungen beendet ein neuer `sitzungsschluessel`.
- Die CSP erlaubt `unsafe-eval`, weil Vue ohne Build die Vorlagen im Browser übersetzt. Es gibt keine Inline-Skripte.
- Die Bremse gilt je Adresse; hinter dem Proxy ist das eine gemeinsame Bremse.
- Schreiben mit CSRF-Schutz gibt es noch nicht (PLT26-04, Teil Schreiben).

## Tests

```bash
pip install -r server/plattform/requirements.txt
python3 tests/plattform/test_plattform.py                       # ohne Datenbank: 10 Hosttests, Datenbankteil NICHT GELAUFEN
BIENEN_TEST_DSN="host=… dbname=bienen_test user=…" python3 tests/plattform/test_plattform.py
node tests/plattform/test_diagramm.mjs                          # Diagrammlogik, ohne Browser
BIENEN_TEST_DSN=… bash tests/plattform/oberflaeche_testen.sh    # Chromium über Playwright, leer und synthetisch
```

In der CI laufen alle drei im Job `datenbank` von `tests.yml`. Die Datenbanktests löschen das Schema `bienen` der Testdatenbank.

**Synthetische Daten** (`synthetisch.py`, Zeitpunkte in `FAELLE`):
- **Bestand:** 2 Stände, 4 Völker, Wetterstation.
- **Stockkarte:** Füttern, Tarieren und Umsetzen mit Gewichtssprung samt Maßnahme; Vereinigung (die Waage sendet danach weiter, ihre Zuordnung endet); AS-Behandlung als Zeitraum; Durchsicht nur mit Datum; Windelzählung.
- **Zeit:** Lücke von zwei Tagen; Winterzeit-Nacht; Uhr nicht abgeglichen.
- **Funk und Import:** doppelte Zustellung; FCnt-Rücksprung bei 16384; leerer Uplink nach Join; defekte und halbe Protokollzeile.
- **Sensoren:** Sensortausch mit Versatz; DS18B20 −127/85 °C; Gewichtsspitze; unbekanntes Feld und Gerät; Regenzähler-Rücksetzung; Windrichtung um 0/360°.

Lizenz: GPL-3.0-or-later; Fremddateien siehe `web/vendor/README.md`.

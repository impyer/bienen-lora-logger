# Plattform: Lese-API, Oberfläche und Stammdaten-Pflege

Konzept 0.2, §4 Nr. 4–5, §6 und §10 Schritt 5: Die eigene Plattform verbindet die **Stockkarte** (Vorbild BEEP) mit der **Datenauswertung** (Vorbild beelogger). Phase B zeigt die Daten an. Phase C pflegt die **Stammdaten** (Seite „Verwaltung“, Teil 1) und erfasst die **Stockkarte** am Handy (Seite „Stockkarte“, Teil 2: Durchsicht mit Checkliste, Maßnahme, Varroa, Aufgabe).

```
Eingänge (server/eingang, bienen, umwelt) → JSONL-Rohprotokolle → importer.py → PostgreSQL (server/datenbank)
                                                                                   │
                                     Browser ← Oberfläche (web/) ← Lese-API (api/, FastAPI) ┘
```

**Status:** Entwurf, getestet nur mit synthetischen Daten in der CI (T1/T2). Nicht auf der ThinkStation eingerichtet, kein Betrieb mit echten Daten. Der Betrieb startet leer: Katalog, Stände, Völker, Geräte und Kanäle werden in der Verwaltung angelegt.

| Pfad | Inhalt |
|---|---|
| `api/app.py` | FastAPI-App: Endpunkte, Anmeldung, Sicherheitskopfzeilen, liefert `web/` aus |
| `api/abfragen.py` | alle SQL-Abfragen, jede Anfrage in einer Nur-Lese-Transaktion; Kennwerte kommen aus den Sichten des Schemas (`berechnung@version`) |
| `api/verdichtung.py` | Rasterweite (höchstens 2000 Punkte je Reihe), Verdichtung nach `messgroesse.verdichtung`, Lücken als `null` |
| `api/anmeldung.py` | ein Konto, scrypt-Hash, signiertes Sitzungscookie, CSRF-Token, Bremse gegen Durchprobieren |
| `api/verwaltung.py`, `api/stammdaten.py` | Stammdaten-Pflege: Endpunkte mit Eingabeprüfung; fachliche Aktionen mit Historie |
| `api/auswertung.py` | Vorher/Nachher zu einem Stockkarten-Ereignis, Völkervergleich (Nachtmedian, Tagesbilanz, Summen, Plausibilitätshinweise) |
| `api/katalog.py` | Standardkatalog der Messgrößen, Kanalvorlagen (beelogger, SenseCAP S2120), Standard-Checkliste der Durchsicht |
| `api/stockkarte.py`, `api/stockkarte_api.py` | Stockkarte: Durchsicht mit Werten je Eingabetyp, Maßnahme, Varroa, Aufgabe; Ändern und Löschen |
| `web/` | Oberfläche: Vue 3 und Apache ECharts ohne Build-Schritt (`vendor/README.md`) |
| `synthetisch.py` | synthetischer Oktober 2026 mit Fehlern und Grenzfällen, nur für Testdatenbanken |
| `plattform_config.beispiel.toml` | Vorlage der lokalen Konfiguration (`plattform_config.toml` bleibt lokal) |
| `requirements.txt` | Python-Pakete mit festen Versionen |

## Endpunkte

Alle lesend. Ohne Sitzung erreichbar sind nur `GET /api/gesundheit` und `POST /api/anmelden`. Zeiten gehen ISO 8601 mit Zeitzone ein (`2026-10-01T00:00:00Z`) und kommen in UTC zurück. Die Oberfläche zeigt sie in Europe/Berlin.

| Endpunkt | Antwort |
|---|---|
| `POST /api/anmelden` `{"passwort": …}`, `POST /api/abmelden`, `GET /api/sitzung` | Sitzung; 401 falsches Passwort, 403 fremde Herkunft, 429 nach 5 Fehlversuchen für 60 s |
| `GET /api/gesundheit` | Datenbank erreichbar, Zeit des letzten Imports, `api_stand` (Stand der Schnittstelle; die Oberfläche meldet einen Server, der noch mit altem Code läuft) |
| `GET /api/messgroessen` | Katalog = Register der Oberfläche (Achse, Farbe, Darstellung, Verdichtung) |
| `GET /api/staende?zeit=` | Stände mit ihren Völkern zum Zeitpunkt (Aufstellung → Belegung), Gewicht, Tagesbilanz des Vortags, letzte Messung |
| `GET /api/voelker/{id}?zeit=` | Stand, Beute mit Zargen, Königin, Geräte mit Zeitraum |
| `GET /api/voelker/{id}/messreihen?von&bis&groessen=` | Reihen je Messgröße und Messstelle, verdichtet; `null` = Lücke, nie 0 |
| `GET /api/staende/{id}/umwelt?von&bis&groessen=` | dasselbe für Geräte am Stand (Wetterstation) |
| `GET /api/voelker/{id}/tagesbilanz?von&bis` | Sicht `gewicht_tagesbilanz` mit `mit_eingriff` (Leitplanke L8) |
| `GET /api/voelker/{id}/ereignisse?von&bis` | Durchsichten (mit `zeitgenauigkeit`), Maßnahmen als Zeitraum, Varroa pro Tag, Vereinigung usw. |
| `GET /api/pruefungen` | unbenannte Quellfelder (K-06), Geräte ohne Zuordnung, Zuordnungsprüfung (HB-09), Importstand |

### Auswertung (lesend)

| Endpunkt | Antwort |
|---|---|
| `GET /api/voelker/{id}/vorher_nachher?art=massnahme\|durchsicht\|varroa&ereignis_id=&tage=1\|3\|7\|14` | Mittelwerte im Fenster vor dem Beginn und nach dem Ende des Ereignisses: Tagesbilanz (kg/Tag), Temperaturen je Messstelle, Luft am Stand, Milbenfall pro Tag; mit Anzahl der Werte |
| `GET /api/vergleich?volk_ids=1,2&von&bis` | je Volk Nachtmedian 00–04 Uhr (`gewicht_tagesreferenz`), Tagesbilanz mit `mit_eingriff`, Summe (alle bzw. ohne Eingriffstage), Sprünge über 1 kg ohne Eingriff, Sensor-Fehlercodes −127/85 °C (Hinweis zu PLT26-11), Anzahl Messpunkte |

Keine biologische Deutung: Hinweise sagen nur, wo eine Maßnahme fehlt oder ein Sensor zu prüfen ist.

### Verwaltung (schreibend)

Nur mit Sitzung, **CSRF-Token** und passender Herkunft:
- Das Token liefert `GET /api/sitzung`; jede schreibende Anfrage schickt es im Header `X-CSRF-Token` mit.
- Ohne Token oder bei fremder Herkunft (`Origin`/`Referer`) kommt 403 (PLT26-04).
- Jede Anfrage ist eine Transaktion. Der Commit läuft vor der Antwort; bei einem Fehler wird nichts geändert.
- Konflikte mit den Regeln der Datenbank (Beute schon belegt, zweite Waage am Volk, Name doppelt) und fachliche Widersprüche ergeben **409** mit Klartext, ungültige Eingaben **422**.

| Endpunkt | Wirkung |
|---|---|
| `GET /api/verwaltung?zeit=` | Stände, Völker mit Beute und Konfiguration, Geräte mit Zuordnung, Kanälen und unbenannten Feldern, Katalog, Vorlagen |
| `POST /api/verwaltung/katalog/standard` | fehlende Messgrößen des Standardkatalogs anlegen; `POST …/messgroessen` legt eine eigene an oder ändert sie |
| `POST /api/verwaltung/staende`, `PUT …/staende/{id}` | Stand anlegen bzw. umbenennen |
| `POST /api/verwaltung/voelker` | Volk **mit neuer Beute** am Stand anlegen (Belegung, Aufstellung mit Platz, Zargen) |
| `PUT /api/verwaltung/voelker/{id}` | Name und Notiz |
| `POST …/voelker/{id}/umsetzen` | in eine neue (`beute`) oder leere vorhandene Beute (`beute_id`); legt die Maßnahme `umsetzen` an (Leitplanke L8) |
| `POST …/voelker/{id}/aufloesen` | `aufloesung` oder `vereinigung` mit `ziel_volk_id`; beendet Belegung und Waagenzuordnung (HB-09) |
| `POST …/beuten/{id}/aufstellen`, `…/konfiguration` | Stand und Platz bzw. Zargen ab Zeitpunkt |
| `POST /api/verwaltung/geraete`, `PUT …/geraete/{id}` | Gerät (TTN-Gerätename) anlegen bzw. Art, Modell, DevEUI ändern; Geräte, die schon gesendet haben, legt der Importer selbst an |
| `POST …/geraete/{id}/zuordnen` | ab Zeitpunkt an ein Volk (Stockwaage) oder einen Stand (Umweltgerät); ohne Ziel nur beenden |
| `POST …/geraete/{id}/vorlage` | Kanäle aus `beelogger` bzw. `s2120`, Messstelle am Ziel der Zuordnung |
| `POST …/geraete/{id}/kanaele` | Deutung eines Quellfelds ab Zeitpunkt; eine offene Deutung desselben Felds endet dort (Sensortausch, Versatz, Kalibrierung) |
| `POST …/kanaele/{id}/beenden` | Deutung beenden |
| `POST …/geraete/{id}/nachtragen` | Werte, die vor dem Anlegen eines Kanals ankamen, aus den Rohprotokollen übernehmen (braucht `[protokolle]` in der Konfiguration) |

**Historie:**
- Jede Änderung „ab Zeitpunkt“ beendet die offene Angabe und legt eine neue an.
- Liegt der Zeitpunkt vor dem Beginn der offenen Angabe, lehnt die API ab. Rückwirkende Korrekturen der Historie sind nicht Teil dieser Masken.
- Die Oberfläche nimmt die Zeit in Ortszeit (Europe/Berlin) an. In der doppelten Stunde der Winterzeit-Umstellung gilt die erste (Sommerzeit).

**Grenze:** Endet die Deutung eines Kanals rückwirkend, behalten schon importierte Werte nach dem Ende ihren alten Kanal. Neu nachgetragen werden nur fehlende Werte.

### Stockkarte (schreibend, Schutz wie die Verwaltung)

| Endpunkt | Wirkung |
|---|---|
| `GET /api/stockkarte/checklisten`, `POST …/checkliste/standard` | aktuelle Version mit Merkmalen; Standard-Checkliste übernehmen. Bei geänderter Merkmalsfolge entsteht eine neue Version, alte Durchsichten behalten ihre (K-10) |
| `POST /api/stockkarte/durchsichten` | Durchsicht für **mehrere Völker** (`volk_ids`), mit `zeit`, `zeitgenauigkeit`, Notiz und `werte` `{merkmal_code: wert}`. Werte geprüft je Eingabetyp: ja/nein, Zahl, ganze Zahl, Bewertung 1–5, Liste, Datum, Text |
| `PUT`/`DELETE …/durchsichten/{id}` | ändern (Werte werden ersetzt) bzw. löschen. Eine neue Uhrzeit gilt als `exakt`, wenn keine Genauigkeit angegeben ist (K-03); verknüpfte Maßnahmen und Aufgaben bleiben |
| `POST`, `PUT`, `DELETE …/massnahmen` | Zeitpunkt (ohne `bis`, gespeichert als [t, t + 1 min)) oder Zeitraum (K-04) |
| `POST`, `PUT`, `DELETE …/varroa` | Windel, Puderzucker, Auswaschung; Milben pro Tag nur für die Windel (Sicht `varroa_pro_tag`) |
| `GET`/`POST …/aufgaben`, `POST …/aufgaben/{id}/erledigt`, `DELETE …/aufgaben/{id}` | Aufgaben für Völker oder einen Stand; fällige erscheinen in der Übersicht |
| `GET …/eintrag/{durchsicht\|massnahme\|varroa}/{id}` | ein Eintrag zum Bearbeiten |

Völker müssen zum Zeitpunkt bestehen. Vor der Entstehung oder nach der Auflösung kommt 409, und bei mehreren Völkern wird dann keines gespeichert.

Fehler: 400 bei ungültiger Zeit, Zeitraum über 400 Tage oder unbekannter Messgröße; 404 bei unbekanntem Volk oder Stand. Ausgeschlossen sind Werte mit `qualitaet = 'ungueltig'`. Den Regenzähler (`unbekannte_summe`) zeigt die API mit seinem letzten Stand je Raster und summiert ihn nie. Die Windrichtung wird als Kreismittel verdichtet.

## Oberfläche

- **Bienenstand** (Übersicht): Kacheln je Stand und Volk, Hinweis bei veralteten Messungen; Meldungen der Datenquellen nach Art (Geräte ohne Zuordnung, unbenannte Felder, Zuordnungen). Steuerfelder des Funkformats (`Format`, `Messzeit_unix`, `Status.*`) zählen nicht als unbenannt.
- **Bedienung allgemein**: Läuft die Sitzung ab, fragt die Seite das Passwort darüber ab und wiederholt die Aktion; Eingaben bleiben. Server nicht erreichbar oder mit älterem Code: verständliche Meldung statt „Failed to fetch“ bzw. „unbekannter Endpunkt“. Zeitraum „bis“ = Ende des Ortstags. Diagramme folgen dem dunklen Schema.
- **Gestaltung** nach dem Designentwurf „Bienenlogger Weboberfläche“ (16.10.2026): Navigation oben, weiße Karten auf ruhigem Grund, Messwerte in IBM Plex Mono (falls installiert, sonst Systemschrift), dunkles Farbschema nach Systemeinstellung.
- **Volk-Cockpit** (nach dem Entwurf):
  - Kennzahlen Gewicht, Brutnest, Milbenfall, Durchsicht.
  - **Gestapelte Felder mit gemeinsamer Zeitachse**: Gewicht, Temperatur, weitere Messgrößen, Milbenfall als Tagesbalken aus der Windel.
  - **Ereignisleiste** mit Buchstabenmarken (D Durchsicht, B Behandlung, F Fütterung, U Umsetzen, T Tarieren, V Varroa …). Maßnahmen als Bänder, Einträge ohne Uhrzeit als Tagesband.
  - **Messwerte**-Auswahl nach Messgröße und Messstelle, Gewicht relativ.
  - **Vorher/Nachher** zum gewählten Eintrag (± 1/3/7 Tage) mit Bändern im Diagramm; Tage mit Eingriff zählen nicht zur Tagesbilanz und werden genannt.
  - Tagesbilanz (Achse nach den Tagen ohne Eingriff, Eingriffe abgeschnitten mit Wert); **Stockkarte** als Chronik mit „bearbeiten“.
  - Am Handy: Messwerte-Auswahl zugeklappt über dem Diagramm.
- **Analysen & Vergleich** (Vorbild beelogger): Stand und Völker wählen; Kennzahlen; Nachtmedian je Volk (relativ oder absolut); Tagesbilanz je Volk (Eingriffstage grau schraffiert); Summe der Tagesbilanzen (wahlweise ohne Eingriffstage); letzte Nacht als Balken; Methodik; Hinweise; Tagestabelle.
- **Umwelt**: Klima, Wind (Richtung als Pfeile) und Regen eines Stands.
- **Datenquellen**: was der Importer nicht zuordnen konnte, Geräte, Importstand.
- **Stockkarte** (Handy zuerst): Reiter Durchsicht, Maßnahme, Varroa, Aufgabe; Völker je Stand ankreuzen (auch „alle“); Checkliste nach Gruppen mit Knöpfen für ja/nein und 1–5; offene Aufgaben zum Abhaken. Im Cockpit stehen die Merkmalswerte und ein Link „bearbeiten“ je Eintrag.
- **Verwaltung**: Standardkatalog; Stände; Völker anlegen, Zargen, versetzen, umsetzen, auflösen und vereinigen; Geräte anlegen, zuordnen, Vorlage, Kanal, Werte nachtragen. Änderungen gelten ab dem oben gewählten Zeitpunkt, ohne eigene Wahl ab dem Klick. „Kanal beenden“ fragt nach.

## Betrieb (beschrieben, nicht eingerichtet)

1. Python ≥ 3.11 und eine eigene virtuelle Umgebung: `python3 -m venv /opt/bienen/venv && /opt/bienen/venv/bin/pip install -r requirements.txt`
2. **Datenbankrollen**:
   - Lesen, z. B. `CREATE ROLE bienen_lesen LOGIN; GRANT USAGE ON SCHEMA bienen TO bienen_lesen; GRANT SELECT ON ALL TABLES IN SCHEMA bienen TO bienen_lesen;`
   - Schreiben (`dsn_schreiben`) zusätzlich mit `INSERT, UPDATE` auf die Stammdatentabellen und `USAGE` auf die Sequenzen.
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
- Kein Offline-Zwischenspeicher: Die Stockkarte braucht am Stand eine Verbindung (WLAN laut Konzept §6a, Abdeckung **[PRÜFEN]**). Fotos (`anhang`) und der Export an BEEP fehlen noch.

## Tests

```bash
pip install -r server/plattform/requirements.txt
python3 tests/plattform/test_plattform.py                       # ohne Datenbank: 11 Hosttests, Datenbankteil NICHT GELAUFEN
BIENEN_TEST_DSN="host=… dbname=bienen_test user=…" python3 tests/plattform/test_plattform.py
node tests/plattform/test_diagramm.mjs                          # Diagrammlogik, ohne Browser
BIENEN_TEST_DSN=… python3 tests/plattform/test_verwaltung.py     # Stammdaten-Pflege und Nachtragen
BIENEN_TEST_DSN=… python3 tests/plattform/test_stockkarte.py     # Stockkarte erfassen, ändern, löschen
BIENEN_TEST_DSN=… bash tests/plattform/oberflaeche_testen.sh    # Chromium über Playwright: leer, Verwaltung, synthetisch
BIENEN_TEST_DSN=… python3 tests/plattform/mutation.py          # Mutationstest: erkennen die Tests eingebaute Fehler? (~1 h)
```

**Mutationstest** (`tests/plattform/mutation.py`): ändert je Mutant eine Stelle (Vorzeichen, Grenze, Zeitzone, Filter …), führt die zuständigen Tests aus und stellt die Datei wieder her. Ziel ≥ 80 % erkannt; überlebende Mutanten zeigen Stellen, die kein Test genau prüft. Läuft nicht in jeder CI, sondern bei Änderungen an Auswertung, Diagrammen oder Tests. Zuerst ein Grundlauf ohne Mutation; nach Abbruch `git status` prüfen. Rechenteile der Seiten stehen in `web/kennzahlen.js`, damit sie ohne Browser mit Sollwerten geprüft werden.

In der CI laufen alle drei im Job `datenbank` von `tests.yml`. Die Datenbanktests löschen das Schema `bienen` der Testdatenbank.

**Synthetische Daten** (`synthetisch.py`, Zeitpunkte in `FAELLE`):
- **Bestand:** 2 Stände, 4 Völker, Wetterstation.
- **Stockkarte:** Füttern, Tarieren und Umsetzen mit Gewichtssprung samt Maßnahme; Vereinigung (die Waage sendet danach weiter, ihre Zuordnung endet); AS-Behandlung als Zeitraum; Durchsicht nur mit Datum; Windelzählung.
- **Zeit:** Lücke von zwei Tagen; Winterzeit-Nacht; Uhr nicht abgeglichen.
- **Funk und Import:** doppelte Zustellung; FCnt-Rücksprung bei 16384; leerer Uplink nach Join; defekte und halbe Protokollzeile.
- **Sensoren:** Sensortausch mit Versatz; DS18B20 −127/85 °C; Gewichtsspitze; unbekanntes Feld und Gerät; Regenzähler-Rücksetzung; Windrichtung um 0/360°.
- **Randfälle für genaue Tests:** negativer Sprung −3 kg ohne Maßnahme; Ausfall von 120 min (Lücke knapp über der Grenze); ein als ungültig markierter Wert (99,9 °C); Wetterstation 1,5 K wärmer als der Außenfühler, damit Verwechslungen auffallen.

Lizenz: GPL-3.0-or-later; Fremddateien siehe `web/vendor/README.md`.

## Stockkarte aus BEEP übernehmen (`beep_stockkarte_import.py`)

Übernimmt aus dem BEEP-Kontoexport (Einstellungen → Daten exportieren, `beep-export-user-….xlsx`) Stand, Völker mit Beute und Königin, Durchsichten, Varroa-Zählungen, Behandlungen, Fütterungen und Erinnerungen (als Aufgaben). Liest die xlsx ohne Zusatzpaket. Wiederholbar über `extern_ref` (BEEP-IDs); vorhandene Völker gleichen Namens werden verknüpft. `--pruefen` führt alles aus und nimmt es zurück.

```
sudo -u bienen /opt/bienen/venv/bin/python /opt/bienen/repo/server/plattform/beep_stockkarte_import.py \
    --dsn "dbname=bienen user=bienen" /var/lib/bienen/beep_export/beep-export-user-….xlsx --pruefen
```

Abbildung und Annahmen stehen im Kopf des Skripts. Die wichtigsten: Durchsichtszeiten sind Ortszeit, `12:00:00` heißt „nur Datum“; „natürlicher Fall n p/d“ wird als Windel über einen Tag mit n Milben übernommen (geschätzt, Original in der Anmerkung); Felder ohne Gegenstück in der Checkliste stehen wörtlich in der Notiz; Hives vom Typ `custom` (Wetterstation) sind keine Völker. Test: `tests/plattform/test_beep_stockkarte.py`.


# Änderungen

## 2026-10-20 – Plattform Phase C, Teil 2: Stockkarte erfassen

- **Neue Seite „Stockkarte“** (`#/stockkarte`, Handy zuerst), Endpunkte `/api/stockkarte/…` (`api/stockkarte.py`, `api/stockkarte_api.py`):
  - **Durchsicht** mit Checkliste für mehrere Völker zugleich
  - **Maßnahme** als Zeitpunkt (gespeichert als [t, t + 1 min)) oder Zeitraum (K-04)
  - **Varroa** mit Windel, Puderzucker oder Auswaschung; Milben pro Tag nur für die Windel
  - **Aufgabe** für Völker oder einen Stand, mit Fälligkeit und Abhaken
- **Checkliste und Zeit:**
  - Standard-Checkliste „Durchsicht“ mit 15 Merkmalen in 4 Gruppen auf Knopfdruck (`api/katalog.py`). Eine geänderte Merkmalsfolge ergibt eine neue Version; alte Durchsichten behalten ihre (K-10).
  - Werte werden je Eingabetyp geprüft (ja/nein, Zahl, ganze Zahl, Bewertung 1–5, Liste, Datum, Text).
  - Uhrzeit in Ortszeit, vorbelegt mit jetzt; Genauigkeit wählbar.
- **Ändern und Löschen:**
  - Eine korrigierte Uhrzeit gilt als exakt (K-03).
  - Beim Löschen einer Durchsicht bleiben verknüpfte Maßnahmen und Aufgaben erhalten.
  - Völker müssen zum Zeitpunkt bestehen; bei einem Konflikt wird für keines der gewählten Völker gespeichert (409).
- **Lese-API und Oberfläche:**
  - Das Cockpit zeigt die Merkmalswerte der Durchsichten, Varroa aller Methoden, offene Aufgaben und einen Link „bearbeiten“ je Eintrag.
  - Die Übersicht zeigt die letzte Durchsicht und die fälligen Aufgaben je Volk.
  - Die Navigation bricht am Handy um.
- **Tests:**
  - neu `tests/plattform/test_stockkarte.py`: 2 Hosttests (Werteprüfung, Schutz auch bei PUT/DELETE, 422) und 9 Datenbankfälle
  - Browsertest: Stockkarte bei 390 px Breite ohne waagrechtes Scrollen, danach Cockpit und Bearbeiten
  - CI in zwei Sitzungszeitzonen
- **Änderungsklasse D2, Nachweis T1/T2 in der CI** (`2008d2b`, alle Jobs grün). Im Lauf für `c3aec01` war einmal ein LoRa-E2E-Schritt rot, ohne Änderung an `server/lora`; das ist als CI26-02 geführt ([Prüfbericht](docs/testberichte/2026-10-20-plattform-stockkarte.md)). Ohne Offline-Zwischenspeicher, Fotos und BEEP-Export; nur synthetische und erfundene Daten.

## 2026-10-20 – Plattform Phase C, Teil 1: Stammdaten pflegen (Verwaltung)

- **Neue Seite „Verwaltung“** mit Endpunkten `/api/verwaltung/…` (`api/verwaltung.py`, `api/stammdaten.py`). Fachliche Aktionen statt Rohtabellen:
  - Volk mit neuer Beute am Stand anlegen
  - Umsetzen in eine neue oder leere Beute; die Maßnahme `umsetzen` erklärt den Gewichtssprung (L8)
  - Auflösen bzw. Vereinigen; beendet Belegung und Waagenzuordnung (HB-09)
  - Beute versetzen, Zargen ändern
  - Gerät anlegen, Art ändern und einem Volk oder Stand zuordnen
  - Kanäle einzeln (mit Versatz und Kalibrierung) oder per Vorlage `beelogger` bzw. `s2120` (`api/katalog.py`); Kanal beenden
  - Standardkatalog der Messgrößen übernehmen
- **Historie:** Eine Änderung „ab Zeitpunkt“ beendet die offene Angabe und legt eine neue an; eine Änderung davor lehnt die API ab (409). Konflikte mit den Datenbankregeln ergeben 409 mit Klartext, ohne Teiländerung. Eingabe in Ortszeit Europe/Berlin.
- **Schutz (PLT26-04):** Schreiben nur mit Sitzung, CSRF-Token (`GET /api/sitzung`, Header `X-CSRF-Token`) und passender Herkunft. Der Commit läuft vor der Antwort (`Depends(scope="function")`). Optional eigene Schreibrolle `dsn_schreiben`.
- **Importer `--nachtragen [--geraet]`:** Werte, die vor dem Anlegen eines Kanals ankamen, werden aus den Rohprotokollen übernommen (Prüfsumme je Zeile); in der Verwaltung als „Werte nachtragen“, wenn `[protokolle]` konfiguriert ist. `Importer.zeile()` ist dafür in `messwerte()` aufgeteilt, ohne Verhaltensänderung beim Import.
- **Datenquellen:** Ein Feld gilt als „unbenannt“ nur, solange es keinen Kanal hat.
- **Tests:**
  - neu `tests/plattform/test_verwaltung.py`: 2 Hosttests und 11 Datenbankfälle vom leeren Start an
  - Browsertest um den Verwaltungsdurchlauf ergänzt; die CI läuft dafür in zwei Sitzungszeitzonen
- **Änderungsklasse D2, Nachweis T1/T2 in der CI** (`be40d0e`, grün). Nur synthetische und erfundene Daten; kein Betrieb, kein Apache/TLS. Die Stockkarte zu erfassen folgt als Teil 2. [Prüfbericht](docs/testberichte/2026-10-20-plattform-stammdaten.md).

## 2026-10-20 – Plattform Phase B: Lese-API und Oberfläche (Konzept §10 Schritt 5)

- **Neu `server/plattform/`** (GPL-3.0-or-later), nur lesend:
  - FastAPI-Lese-API: Stände mit Völkern, Volk mit Beute, Königin und Geräten, verdichtete Messreihen je Messgröße und Messstelle, Tagesbilanz, Stockkarten-Ereignisse, Umwelt je Stand, Prüfungen.
  - Oberfläche mit Vue 3.5.42 und ECharts 6.1.0 als feste Dateien ohne Build-Schritt (`web/vendor/README.md` mit Quelle, Lizenz, SHA-256). Seiten: Übersicht, Volk-Cockpit, Umwelt, Datenquellen.
  - Anmeldung mit einem Konto (ADR-0003 Nr. 10): scrypt-Hash, signiertes Sitzungscookie (HttpOnly, SameSite=Strict), Herkunftsprüfung, Bremse nach 5 Fehlversuchen.
- **Fachregeln:**
  - Achsen, Farben und Verdichtung stammen aus dem Messgrößen-Katalog; es gibt keine festen Sensorfelder.
  - Lücken bleiben `null`, nie 0.
  - Windrichtung als Kreismittel; den Regenzähler mit unbekanntem Rücksetzpunkt zeigt die API mit seinem letzten Stand je Raster und summiert ihn nie.
  - Tagesbilanz aus der Sicht `gewicht_tagesbilanz`; Tage mit Eingriff sind markiert (L8).
  - Behandlung als Band (K-04), Durchsicht ohne Uhrzeit als Tagesband (K-03), Anzeige in Europe/Berlin.
- **Synthetische Testdaten `server/plattform/synthetisch.py`:** Oktober 2026 im echten Eingangsformat, den `importer.py` einliest. Eingebaute Fehler und Grenzfälle:
  - Lücke, Winterzeit-Nacht, Uhr nicht abgeglichen
  - doppelte Zustellung, FCnt-Rücksprung, leerer Uplink nach Join, defekte und halbe Zeile
  - DS18B20 −127/85 °C, Gewichtsspitze
  - Füttern, Tarieren, Umsetzen, Vereinigung, Sensortausch
  - unbekanntes Feld und Gerät, Regenzähler-Rücksetzung, Wind um 0/360°
- **Tests:**
  - `tests/plattform/test_plattform.py`: 10 Hosttests und 14 Datenbankfälle mit festen Sollwerten.
  - `test_diagramm.mjs`: 10 Prüfungen der Diagrammlogik.
  - `test_oberflaeche.mjs` mit `oberflaeche_testen.sh`: Chromium über Playwright, leer und synthetisch, Browser in America/New_York.
  - CI-Job `datenbank` erweitert. `.gitignore`: `server/plattform/plattform_config.toml`.
- Änderungsklasse **D2** (Zeitstempel und Anzeige von Messdaten). Nachweis T1/T2 nur mit synthetischen Daten. Lokal liefen die Hosttests und die Diagrammlogik (Windows, ohne PostgreSQL), dazu eine Sichtprüfung im Browser mit nachgebildeten Abfragen. Datenbank- und Browsertests laufen nur in der CI. Kein Betrieb auf der ThinkStation, keine echten Daten, keine Schreibfunktionen (Stockkarte und Stammdaten folgen in Phase C).

## 2026-10-20 – Importer: Rohprotokolle der Eingänge → PostgreSQL (Konzept §10 Schritt 4)

- **Neu `server/datenbank/importer.py`** (GPL-3.0-or-later): liest `lora_log/JJJJ-MM.jsonl` (Herkunft `geraet`) und `wetter_log/JJJJ-MM.jsonl` (Herkunft `station`). Jede Zeile `"art": "uplink"` wird `rohnachricht` (Kennung `id`, Datei, Zeile, SHA-256 der Protokollzeile, Empfangs- und Gerätezeit; nicht der Inhalt). Zahlenfelder aus `decoded_payload` werden `messwert`, wenn zum Messzeitpunkt ein `kanal` gilt; sonst nur `quellfeld_ohne_kanal` (K-06). Messzeit wie `le_messzeit()` (Gerätezeit bei `Status.zeit_ok` und ≤ 900 s, sonst Empfang). Unbekannte Geräte werden angelegt und gemeldet.
- **Wiederholbar (PLT26-02 R-5, K-09):** Leseposition je Datei mit SHA-256 der gelesenen Bytes in der neuen Tabelle `import_position` (Schema 0.4); Daten und Position je Datei in einer Transaktion; Dubletten über die Kennung verworfen; unvollständige letzte Zeile bleibt liegen; geänderter Dateianfang wird gemeldet und nicht weiter gelesen (Teil von R-4). Ein Lauf zur Zeit (Advisory Lock). Eine einzelne nicht speicherbare Zeile (NUL-Zeichen, zu tiefe Verschachtelung) wird über einen Sicherungspunkt übersprungen und gemeldet, statt die Datei bei jedem Lauf zu blockieren (Hinweis der automatischen Sicherheitsprüfung).
- **Tests `tests/datenbank/test_importer.py`:** 4 Hosttests ohne Datenbank (Zeit, Felder, Messzeit, Lesen ab Position) und 9 Datenbankfälle (Grundfall, fehlerhafte Einzelzeilen, K-06, R-5 Doppelimport samt Neulesen ohne Position und anderer Sitzungszeitzone, K-09 über Monatswechsel, halbe Zeile, R-4, Zeitqualität/Herkunft, Kanalzeitraum mit Faktor). Der CI-Job `datenbank` (PR #29, Eintrag darunter) ist mit dem Job dieses Branches zu einem zusammengeführt: `test_schema.py` in Europe/Berlin, UTC und America/New_York, dazu `test_importer.py` in Europe/Berlin und UTC (`PGTZ`); Dienst unverändert aus PR #29.
- Änderungsklasse **D1** (neue Datenbank-Persistenz, keine Änderung an Eingängen, Firmware, Formatter oder Server-Antworten). Nachweis: Hosttests 4/4 lokal (Windows, Python 3.14); **Datenbankfälle lokal NICHT GELAUFEN** (kein PostgreSQL auf dem Entwicklungsrechner), T1 erst über den CI-Job. Kein Lauf gegen echte Protokolle, nicht auf der ThinkStation. Offen: Monatsprüfsumme (R-4), Sicherung (R-6).

## 2026-10-20 – CI: Datenbankschema 0.3 gegen PostgreSQL 16

- Neuer Job `datenbank` in `.github/workflows/tests.yml`: Dienst `postgres:16` (mit `btree_gist` aus contrib), `psycopg[binary]==3.2.3`, `tests/datenbank/test_schema.py` dreimal mit den Sitzungszeitzonen Europe/Berlin, UTC und America/New_York (`PGTZ`). Bisher lief das Schema, Kern der Zielarchitektur (Stockkarte, Messdaten, Sichten), nur von Hand auf einer Testinstanz. Das Kennwort im Workflow gilt nur für den Wegwerf-Container des CI-Laufs.
- Schema und Tests unverändert. Grundlage für die Tests des Importers (Konzept 0.2, §10 Schritt 4). Änderungsklasse D1, Nachweis T1 in der CI; keine Produktivdatenbank.

## 2026-10-20 – Refactoring: gemeinsame Eingangsschicht `server/eingang/` für alle TTN-Webhooks

- **Ziel:** Vorbereitung der Zielarchitektur (Konzept 0.2, §4/§4a: Eingänge → Rohprotokoll → Importer → PostgreSQL → Lese-API → Weboberfläche). Verhalten nach außen unverändert: gleiche Antworten an TTN (Codes und Texte), gleiche Dateien (`week.csv`-Aufruf, `lora_zusatz.csv`, Wetter-CSV, `staende.json`), gleiche Protokollzeilen (Feldnamen und Reihenfolge), gleiche Kennungen.
- **Neu `server/eingang/`:** `eingang_funktionen.php` (TTN-Zeit, Zahlen, Nachrichtenfelder, Funk, Kennung, Duplikatliste, Monatsprotokoll, CSV anhängen, Sperre) und `eingang_webhook.php` (Konfiguration, Token/Methode/JSON, Rohprotokoll R-1/R-2 an einer Stelle, Antwort mit Warnungen). Vorher war die Webhook-Annahme in `lora_eingang.php` und `wetter_eingang.php` doppelt, ebenso `le_log`/`we_log` und `le_verz_sicher`/`we_verz_sicher`; der Wetter-Eingang hing über `le_*` am LoRa-Eingang. Künftige Eingänge (Boden, BEEP Base) nutzen dieselbe Schicht (Grundlage für R-3, noch nicht nachgewiesen).
- **LoRa-Eingang:** `le_verarbeiten()` (130 Zeilen) zerlegt in `le_auftrag()` (Prüfen, Ziel, Messzeit, Zeitbasis) und `le_weitergeben()` (unter der Sperre), dazu `le_beelogger_url()`, `le_beelogger_aufrufen()`, `le_zusatz_schreiben()`, `le_zeitbasis()`, `le_erwarteter_zeitstempel()`, `le_logger_typ()`, `le_statusbits()`, `le_nachholen_noetig()`. Allgemeine Hilfen heißen jetzt `ein_*` statt `le_*`.
- **Einzige Abweichungen, nur im Fehlerfall:** CSV-Anhängen prüft beim Wetter-Eingang jetzt auch `fflush` (vorher nur beim LoRa-Eingang); scheitert die Kopfzeile einer neuen Zusatzdatei, wird die Datenzeile nicht mehr versucht (Ergebnis war schon vorher „nicht geschrieben“).
- **Einspielen:** Ordner `eingang/` zusätzlich neben `lora/` und `wetter/` kopieren (READMEs). Ohne ihn antworten beide Eingänge mit HTTP 500. Der Wetter-Eingang braucht `lora/` nicht mehr.
- **Tests:** neu `tests/server/test_eingang_funktionen.php` (Tests aus `test_lora_funktionen.php` übernommen, ergänzt um Nachrichtenfelder, Protokoll, CSV, Sperre, Konfiguration, Warnungen); `test_lora_funktionen.php` um Zeitbasis, erwarteten Zeitstempel, Logger-Typ, Statusbits, Aufruf-Adresse, Nachholklassen ergänzt. E2E-Tests kopieren `server/eingang` mit; der Wetter-E2E-Test ohne `server/lora`. CI: Syntax und Unit-Tests für `server/eingang/`.
- Änderungsklasse **D2** (Persistenz, Zeitstempel, Server-Antwort; reine Strukturänderung). Nachweis: T2 über die CI (`tests.yml`: Unit-Tests, LoRa-E2E `eigen`/`original` je 05:00 und 14:00, Wetter-E2E). Lokal nicht gelaufen (kein PHP auf dem Entwicklungsrechner). Kein Apache-, TTN- oder Feldtest.

## 2026-10-19 – CI: CodeQL, statische Analyse und Testabdeckung (Erst-Baseline)

- CodeQL läuft über das GitHub-Default-Setup des Repos (Actions/C-C++/Go/JavaScript/Python; PHP nicht abgedeckt); die zuvor im PR-Branch angelegte `codeql.yml` (Advanced Setup) entfällt, weil GitHub beide Betriebsarten nicht gleichzeitig annimmt (SARIF abgewiesen). Neu `.github/workflows/static-analysis.yml` mit sieben Jobs: Syntax aller eingecheckten Python-/JS-/PHP-/Shell-Dateien und actionlint (verpflichtend); Ruff, Bandit, ShellCheck je mit verpflichtender Mindeststufe und informativer Baseline; Abdeckung C++ (gcov/gcovr über Host-Tests und Simulation, nur `firmware/`), JavaScript (c8, `formatter/`) und Python (coverage) als Artefakte und Laufzusammenfassung, noch ohne Mindestwerte. Beschreibung in `tests/README.md`.
- Neu `ruff.toml` (E, W, F, B ohne E501; Baseline 22 Hinweise). `tests/formatter/test_s2120_formatter.js` übergibt den Dateinamen an `vm.runInContext`, damit c8 die Abdeckung zuordnet (vorher 0 %, jetzt 100 % Zeilen). `.gitignore`: Abdeckungsausgaben.
- `tests/server/test_beelogger1_inventur.py` läuft damit erstmals in der CI (Linux; unter Windows scheitert der Symlink-Fall am fehlenden Recht, kein Codefehler).
- Werkzeuge gepinnt: ruff 0.17.1, bandit 1.9.4, gcovr 8.7, coverage 7.16.2, c8 10.1.3, actionlint 1.7.7. Software-CI ersetzt keine T4-/HiL-/Feldnachweise (Regelwerk 1.1).

## 2026-10-18 – HW-11: sechs Bauteile weniger, Sanftanlauf am BLE-Schalter

- **HW-11 (Philipp):** R302 (PB2 direkt GND), C308 (VBAT), FB301 + C306 (VDDA direkt an +3V3, C305 bleibt), R407 + R408 (Flash-WP/HOLD direkt an +3V3) entfallen; neu **R314 10 kΩ** und **C317 47 nF** als Sanftanlauf des BLE-Lastschalters (Netz BLE_GATE). 5-V-Wandler der Waage bleibt (Entscheidung Philipp). 186 → 182 Bauteile, kein PWR_FLAG für VDDA mehr.
- `netz_tests.py`: BLE_GATE, R314/C317, direkte Verbindungen und Fehlen der gestrichenen Teile geprüft; `schaltplan_spice.py` S3 bewertet jetzt den Stand mit Sanftanlauf (55 mA, 3,29 V). Dokumente: `mcu-funk.md` 1.1/1.6/3.2/4, Pflichtenheft 9 und Teilezahl, Fiverr, KiCad-README, Entscheidungsregister HW-11. Layout-Stand neu erzeugt, Paket neu gebaut (Nachtrag im Übergabebericht).

## 2026-10-18 – Schaltplan-Review mit SPICE-Modell: Einsparungen, Kniffe, Leckstrom-Befund

- Neu `hardware/schaltplan_spice.py` (GPL-3.0-or-later): treibt die ngspice-Bibliothek aus KiCad 10 (`ngspice.dll` bzw. `libngspice0`) über ctypes und prüft 12 Größen mit Grenzen – Elektretpfad (Hochpass 5 Hz, Kapsel 1,9 V), HX711-AVDD 4,30 V (Eckwerte 4,24–4,36 V), BLE-Lastschalter (Einbruch auf 3,06 V heute, Sanftanlauf 10 kΩ + 47 nF → 55 mA), RN4871-Reset 4–9 ms, BLE_VCC-Entladung 2,4 s, ADC-Teiler-Leckstromfehler, Sensorschiene 25 mA, 1-Wire 3,1 µs. Ohne Bibliothek meldet das Skript ÜBERSPRUNGEN (nicht bestanden). CI-Job `hardware-rechnungen` installiert `libngspice0` und führt es aus.
- Bericht [2026-10-18-schaltplan-optimierung](docs/testberichte/2026-10-18-schaltplan-optimierung.md): keine Fehler; Vorschläge **−6 Teile ohne Funktionsverlust** (R302, C308, FB301, C306, R407, R408), **5-V-Wandler der Waage zur Entscheidung** (−6 Teile, −0,5 mAh/Tag, PB10 frei; Gleichtakt am Steckbrett prüfen), **Sanftanlauf BLE** (2 Teile), **Pin-Tauschgruppen** für den Layouter (Pflichtenheft 2.3, neue Tabelle). Nicht umgesetzt (Layout-Stand eingefroren) – Entscheidung HW-11 offen.
- Befundregister: **HW26-21** (ADC-Teiler-Leckstrom, analysiert/akzeptiert mit Firmware-Kalibrierung). `mcu-funk.md` 4: PA8 ohne Reihenwiderstand (Text widersprach dem Schaltplan). CLAUDE.md und `hardware/README.md`: neuer Prüfbefehl.

## 2026-10-18 – Dritter Mikrofoneingang (HW-10)

- **HW-10 (Philipp):** alle drei Anschlussmöglichkeiten des TLV320ADC3101 belegt: zusätzlich **Elektret 2** pseudo-differenziell am rechten Analogeingang IN2R(P)/IN3R(M) mit MICBIAS2 (R614/R615 1 kΩ, C629 1 µF, Koppel-C C625/C626 1 µF X7R, C627/C628 100 pF), auf den **Pins 5 (MIC3+) und 6 (MIC3−) der RJ45-Buchse J601** (Philipp: ein Stecker für alle drei Mikrofone; die Pins waren Masse-Paarpartner von VDD und DATA) mit ESDS304 D602. Bis zu drei Mikrofone; rechter Kanal je Messung PDM oder Elektret 2 (zwei Durchgänge, `energiebilanz.py` 2b: +0,2 mAh/Tag).
- `netz_tests.py`: MICBIAS2/MIC3-Netze, gleiche Vorspannung und Koppel-C wie Elektret 1, IN1L/IN1R offen, D602, J601 Pin 5/6 (mit Gegenprobe vertauschter Adern) und J5 gegen `anschluesse.md`.
- Dokumente: `mikrofon.md` (1, 2, 2.1, 4, 5, 6, 7), `anschluesse.md` (J5 Pin 5/6), Lastenheft F6/A8, Pflichtenheft (D602 an J601, MIC3-Paar, 185 Teile / 21 LCSC), Fiverr, Entscheidungsregister HW-10, KiCad-README. Layout-Stand neu erzeugt und geprüft (Nachtrag im Übergabebericht).
- Zählung und Anschluss festgelegt (Philipp): J5/J601 trägt **alle drei Mikrofone** – 1 Elektret (7/8), 2 MEMS (1–4), 3 Elektret 2 (5/6); die zuerst gezeichnete eigene Klemme J602/J12 entfällt wieder. Regel: Mikrofon 3 nur bei stehendem PDM-Takt messen.
- **Pinreihenfolge J601 (Philipp, 18.10.2026 abends):** 4 MIC3+, 5 MIC3−, 6 VDD – jedes Mikrofon auf einem eigenen T568B-Paar (1/2 CLK+GND, 3/6 DATA+VDD, 4/5 MIC3, 7/8 MIC); Standardkabel und -stecker, kein Sonderlöten; die PDM-Regel für Durchgang 2 ist nur noch Empfehlung. `netz_tests.py` prüft die Paarzuordnung. Dokumente nachgezogen.
- **Review-Nachtrag (18.10.2026 abends):** `mikrofon.md` Bauteiltabelle und Schaltbild auf J601 Pin 5/6 = MIC3+/MIC3− berichtigt (stand noch auf GND), Lastenheft A4 Paarung; **Q501** ohne LCSC-Nummer (AnBon-Datenblatt ohne Pinbild), Pflichtenheft 7 verlangt ein Teil mit 1 B, 2 E, 3 C; **R313 100 kΩ** von BLE_VCC nach GND (definierter Aus-Zustand, Power-Cycle als Reset). Offen bleiben die BLE-Musterprüfungen B-1 … B-6 (HW26-20) und die Antennenlage (Pflichtenheft 11, Layouter).
- **Pin-Review** (auf Nachfrage): Pinfunktionen aller ICs und Module gegen die Datenblätter gelesen – STM32F411 (ST open pin data: USART6, I2S3, SPI1, I2C1, USART1, ADC, WKUP, SWD, OSC32), TLV320ADC3101, BQ25185, TPS22917 (CT-Kondensator an VIN laut Tab. 6-1), TPS61240, TMP390, HY2111, FS8205, AO3400A/AO3401A, 74LVC1G17, HX711, RN4871, Ra-01SH, ESD-Arrays: **keine Abweichung**; `pin_footprint.py` von [A]/[V*] auf [V] gehoben (AO3400A, AO3401A, HY2111, FS8205, 74LVC1G17, STM32). Offen bleiben S8550-Pinfolge (Hersteller), Flash-Typ, Keystone-1042-Polung, RJ45-Teil, DEGSON-Zeichnung, TVS D401. Bericht [2026-10-18-pinfunktionen-review](docs/testberichte/2026-10-18-pinfunktionen-review.md).

## 2026-10-18 – Schaltplan für den Layout-Auftrag freigegeben (Layout-Stand)

- Titelblock aller Blätter: Rev „0.1 Layout-Stand“, Datum 2026-10-18 (Generator `hauptplatine.py`). Pflichtenheft **issue 3**: HW-09 (BLE-Modul, Ladepads), Prüfstand im Paketinhalt, Bauteile mit knappem Bestand (RN4871, Ra-01SH), DNP-Teile und Lötbrücken benannt.
- Nachweis (KiCad 10.0.7, Windows; Bericht [2026-10-18-layout-uebergabe](docs/testberichte/2026-10-18-layout-uebergabe.md)): `pruefen.sh` reproduzierbar, ERC 0, Netzprüfung 220/220, Pin/Footprint 177 Bauteile / 0 Abweichungen / 0 offen; Rahmenplatine DRC 0; Übergabepaket `build/layout-auftrag-PCB-MAIN-0.1-4c36898.zip` (41 Dateien) entpackt mit ERC 0 und DRC 0 geprüft; `netz_vergleich.py --selbsttest` ok; Formatter-Tests 14/14, 14/14, 12/12. C++-/PHP-Tests über die CI.
- Freigabe: Schaltplan zur Layout-Bearbeitung (HW-08); keine Bestell- oder Laborfreigabe, D3-Gates unverändert offen.

## 2026-10-18 – BLE-Firmware-Eckpunkte gegen das RN4870/71 User's Guide geprüft (HW-09, HW26-20)

- `hardware/mcu-funk.md` 1.6 (Firmware): gelesen **DS50002466C** (User's Guide, Rev. C 07/2018) und DS50002489D. Ergebnis: UART 115 200 8N1 und Flusskontrolle **ab Werk aus** (SR-Bit 0x8000 nie setzen, Fast Mode 0x2000 nie setzen); Befehlsfolge `$$$` → `SN`/`S-` → `SS,C0` → `R,1` (einmalig im NVM) und je Sitzung `A,03E8,03A9`, Statusmeldungen `%CONNECT%`, `%STREAM_OPEN%`, `%DISCONNECT%`, `%ADV_TIMEOUT%`; Kopplung `SA,4` + fester 6-stelliger PIN empfohlen (Entscheid Philipp offen); `SO,1` (60 µA) und `O,0` (1–2,9 µA, Aufwecken nur P1_6/Hardreset) bestätigen die Abschaltung über PB13; Modul-Update über P2_0 = low, UART, ISUpdate (Werkzeug nur aus Suchergebnis, **[A]**).
- Kein Widerspruch zum Schaltplan, **keine KiCad-Änderung**. Befundregister: HW26-20 Beschreibung nachgeführt, Status unverändert. T0 (Dokumentenprüfung), keine Messung, keine BLE-Firmware.

## 2026-10-18 – BLE-Modul RN4871 statt USB-Daten (HW-09)

- **HW-09 (Philipp, Vorschlagspaket „USB → BLE RN4871“ eingearbeitet):** Blatt MCU: Microchip **RN4871-I/RM130** (U303, LCSC C633942) an **USART6** PA11/PA12 (AF8) als Transparent-UART-Service-Konsole; Versorgung über P-FET **Q301 AO3401A** an PB13 (low = ein, Ruhestrom ≈ 0), Gate-Pull-up R309, 1 kΩ R310/R311 im UART, R312 10 kΩ (P2_0) an BLE_VCC, C314 10 µF + C315 100 nF, C316 an RST_N, Lötbrücke JP301 „BLE dauernd“; Modul-UART und Modus an **J704 Pin 9–11** (Modul-Firmware-Update, Brücke 11–12 = Testmodus). Abweichung vom Vorschlag: Modul geschaltet statt dauernd versorgt, RST_N ohne MCU-Pin, USB-C bleibt Ladebuchse.
- **USB-C-Buchse entfällt (Philipp, 18.10.2026):** statt dessen zwei Lötpads J301/J9 (1 GND, 2 +5 V → D203, Stiftleiste nicht bestückt) zum Laden am Tisch; USBLC6 U302, VBUS-Teiler R307/R308 und CC-Widerstände R303/R304 entfallen (SCH26-10 gegenstandslos). Aufspielen über SWD oder ROM-Bootloader an USART1 (J10). Netzprüfung: J9 gegen `anschluesse.md`, VBUS nur Pad 2 und D203.
- Neu: Symbol `Bienen:RN4871` (DS50002489D Tab. 1-2) und Footprint `Bienen:Microchip_RN4871` nach Fig. 4-7/4-8 [V] (Pads 0,7 × 1,5 mm, zwei F.Cu-Sperrflächen der Testpunkte) mit Antennen-Sperrzone auf allen Lagen und User.1-Linie für die Platinenkante (Antennenteil ragt nach Fig. 4-9 über die Kante); `netz_tests.py` prüft BLE-Netze, Pull-up nur an BLE_VCC (Gegenprobe), J704 Pin 9–12, USB ohne Daten; `pin_footprint.py` mit RN4871 [V] und AO3401A.
- Dokumente: `mcu-funk.md` 1.3 (USB nur Laden) und neu 1.6 (BLE: Pins, Versorgung, Energie, Antenne/Layout, Firmware, Prüfplan B-1 … B-6), Pinbelegung PA11/PA12/PB13; Lastenheft K5/K6/F9/M5/M8; `anschluesse.md` J9/J11; `versorgung.md`; `energiebilanz.py` (Ruhestrom-Posten, Abschnitt 2a BLE-Sitzung ≈ 1,1 mAh); Pflichtenheft/Fiverr (Platzierungsregel 4 Ladepads, 11 BLE, 177 Teile); Entscheidungsregister HW-09; Befundregister HW26-20; Bericht [2026-10-18-hw09-ble-rn4871](docs/testberichte/2026-10-18-hw09-ble-rn4871.md).
- Nachweis: `pruefen.sh` lokal (KiCad 10.0.7, Windows): reproduzierbar, ERC 0, Netzprüfung 220/220, Pin/Footprint 177 Bauteile, 0 Abweichungen; `energiebilanz.py` läuft. T0/T3 – keine Messung, keine BLE-Firmware.

## 2026-10-15 – Datenplattform: Konzept, Schema, Review #11, Rohprotokoll

- Neu `docs/architektur/konzept-plattform-v02.md` (Fassung 0.2.7): Gesamtkonzept eigene Plattform (Stockkarte, Messdaten, Umwelt, Auswertung) auf Basis der ChatGPT-Architekturdokumente; Abgleich, Vereinfachungen, Zielarchitektur, Datenmodell, Migration von BEEP, Zugriff und Veröffentlichung, Bewertung Review #11.
- Neu ADR-0003 (Datenplattform-Grundentscheidungen 15.10.2026, Maintainer): u. a. Beute/Volk höchstens 1:1, Waage am Volk, Python für API/Analyse, ThinkStation + PostgreSQL, Anmeldung auch im Heimnetz, öffentliche Lese-API über den Webhoster, Bodensonden 5/20/50 cm.
- Neu `server/datenbank/schema.sql` 0.3 (PostgreSQL 16) mit `tests/datenbank/test_schema.py`: 24/24 auf Testinstanz (T1), Sitzungszeitzonen Europe/Berlin, UTC, America/New_York.
- Befundregister: Familie PLT26 (Review [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11)); Bewertung `docs/testberichte/2026-10-15-plattform-review-issue11.md`.
- **PLT26-02:** LoRa- und Wetter-Eingang melden Fehler beim Rohprotokoll (Warnung in der Antwort, PHP-Fehlerprotokoll), Rohzeilen mit `roh_sha256`; neue E2E-Prüfungen R-1/R-2. Bericht `docs/testberichte/2026-10-15-plt26-02-rohprotokoll.md`. Nachweis T2: `alle_tests_linux.sh` rc 0, LoRa 81/81 (Serveruhr 05:00/14:00 je 82/82, original 64/64), Wetter 29/29.

## 2026-10-14 – Pflichtenheft für den Layout-Auftrag

- Neu `hardware/layout-auftrag/PFLICHTENHEFT.md` (englisch, deutsche Kurzfassung): Umfang (Platzierung, Routing, LCSC-Auswahl für 151 von 172 Teilen, JLCPCB-Gerber/Bohrdaten/BOM/CPL), Mechanik, Platzierungs- und Routingregeln (u. a. B− ≠ GND, ANT ohne Leiterbahn, L2 durchgehende Masse, PDM/Mikrofon), Meilensteine mit Platzierungsfreigabe vor dem Routing, Abnahme (DRC 0, Netzvergleich IPC-D-356, JLCPCB-DFM), Lizenz CERN-OHL-S-2.0.
- 4 oder 6 Lagen nach Wahl des Layouters (Philipp, Preise geprüft): Lastenheft M8 und Pflichtenheft 5.1 mit Lagenaufbau für beide Fälle; Pflicht bleibt die durchgehende Masselage unter L1.
- Layout-Werkzeug frei (Philipp): Lieferung bearbeitbarer Quelldateien plus KiCad-Importprüfung, IPC-D-356-Netzliste; Abnahme über den Netzvergleich statt KiCad-Schaltplanabgleich.
- Neu `hardware/layout-auftrag/netz_vergleich.py`: vergleicht die IPC-D-356-Netzliste der gelieferten Platine pinweise mit `logger.net` (Netznamen dürfen gekürzt sein); Selbsttest mit Gegenproben (Kurzschluss MIC_P/MIC_N, getrenntes B−, B− an GND) und Prüfung an einer echten KiCad-10-IPC-D-356-Ausgabe (Testplatine mit allen 172 Footprints): gleich, vertauschte Pins erkannt.
- Neu `hardware/layout-auftrag/paket_bauen.py`: baut das Übergabe-ZIP (KiCad-Projekt mit Bibliotheken, PDF, Netzliste, Stückliste als CSV, Blockdokumente, Pflichtenheft) unter `build/`; geprüft: entpacktes Paket ERC 0, DRC 0 (Footprints fehlen gewollt).

## 2026-10-14 – Zwei Mikrofone am Audio-ADC (HW-07), Layout extern (HW-08)

- **HW-07 (Philipp):** Blatt Mikrofon neu: Audio-ADC **TLV320ADC3101** (U601) mit Elektretkapsel (analog, pseudo-differenziell, MICBIAS über 2 × 1 kΩ) und MEMS **IM69D127** (PDM, Takt über Schmitt-Puffer 74LVC1G17); DVDD aus TPS70918, 3V3_MEMS über eigenen Ferrit; Anschluss über geschirmte **RJ45-Buchse** J601 (Cat7 S/FTP 0,5–1 m, Paare T568B). GY-MAX4466-Zweig mit Sallen-Key-Filter entfällt.
- STM32: **I2S3** an PB12 (CK), PA15 (WS), PB5 (SD); Sensorschiene von PB5 auf **PA1**; J11 Pins 9/10 frei (keine Erweiterungs-GPIOs mehr).
- `hardware/mikrofon_filter.py` rechnet jetzt Taktplan (fS 24 576 Hz, AOSR 128, PDM-Takt 3,146 MHz, PLL aus BCLK), Vorspannung, Hochpass, Kabellast und Dezimation gegen die Datenblattgrenzen; `energiebilanz.py` mit 5,5 mA × 1,5 s für die Mikrofone (Reichweite B 436 statt 454 Tage).
- **HW-08 (Philipp):** Platzierung und Layout durch den beauftragten Layouter; `logger.kicad_pcb` nur noch Rahmen (`platine_start.py`); Platzierungs- und Routing-Skripte entfernt (Erkenntnisse in den Berichten vom 13.10.2026). Lastenheft M5 und `anschluesse.md` 4 als Randbedingungen statt fester Lage.
- Dokumente: `mikrofon.md` neu, Lastenheft (F6, A1–A7, M2, M4, M5, M9), `anschluesse.md`, `mcu-funk.md`, `versorgung.md`, `beep-vergleich.md`, Entscheidungs- und Befundregister (HW26-05), READMEs; Bericht [2026-10-14-hw07-mikrofone](docs/testberichte/2026-10-14-hw07-mikrofone.md).
- Nachweis: `pruefen.sh` lokal (KiCad 10.0.6): reproduzierbar, ERC 0, Netzprüfung 187/187, Pin/Footprint 0; `tests/alle_tests_linux.sh` rc 0 (T0/T3, keine Messung).

## 2026-10-14 – Aufräumen vor der Layout-Übergabe

- Restbezüge auf die entfallene Akku-Platine bereinigt: Beschreibung U204 („Ladesperre (Blatt Akku)“), R808 und #FLG805 mit neuen Bezeichnern; `sicherheit-akku.md` Prüfaufbau und Rückverfolgbarkeit LH-V1 auf HW-06, Zuordnung alte → neue Bezeichner in Abschnitt 10 (Abschnitte 1–9 bleiben als Analyse zum Bezugsstand `2076c20`).
- `README.md`: Stand der SMD-Platine (Schaltplan V0.1, Platzierung, Layout extern) und Regelwerk 1.1; `hardware/README.md`: nicht existierenden Pfad `hardware/logger-platine/production/` entfernt.
- GitHub (Maintainer): Branches `review/2026-10-10-4c12b6d-hardware-audit` (vollständig in `main`), `review/claude-regelwerk-e1-e12` (durch Regelwerk 1.1/ADR-0002 ersetzt) und `automation/claude-codex-pr-pipeline` (nicht übernommener Vorschlag) werden vom Maintainer gelöscht; Issues #4, #5, #7 (SCH26-09/-10/-12, im Entwurf behoben) werden geschlossen, #6 (SCH26-11) bleibt offen. Status führt weiter nur das Befundregister.
- Nachweis: `pruefen.sh` lokal (KiCad 10): reproduzierbar, ERC 0, Netzprüfung 168/168, Pin/Footprint 0 Abweichungen (T0/T3, keine Hardwaremessung).

## 2026-10-14 – Eine Platine (HW-06) und USB für Programmierung/Kommunikation (HW-05)

- **HW-06 (Philipp):** Zelle 18650 (Halter Keystone 1042), Zellschutz HY2111 + FS8205, NTC und Temperatur-Ladesperre auf die Hauptplatine (Blatt „Akku“, Bauteile 8xx, Schaltung unverändert). Akku-Platine, Kabel und Stecker J1/J203 entfallen (`akku_platine.py` und `akku-platine/` entfernt). Netzprüfung neu: Zelle B− ist nicht GND. D3-Nachtrag in `sicherheit-akku.md` Abschnitt 10.
- **HW-05 (Philipp, ersetzt HW-01):** USB auch für Programmierung und Kommunikation (USB-CDC); VBUS-Erkennung nach ST AN4879 mit R307 33 kΩ / R308 82 kΩ an PB13; J704 Pin 11 frei.
- Prüfungen: ERC 0, Netzprüfung 168/168, Pin-/Footprint 161/0, `alle_tests_linux.sh` rc = 0. Platine neu platziert (Halter unter dem Funkmodul, Zellschutz am Minuspol), DRC 0, **nicht geroutet** – das Layout übernimmt ein Layouter. Bericht: `docs/testberichte/2026-10-14-hw05-hw06-schaltplan.md`.

## 2026-10-13 – Routing der Hauptplatine, Platzierung aus den Routing-Erfahrungen optimiert

- Neu `platine_routen.py` (Freerouting 1.9.0 über Specctra DSN/SES, Innenlagen als Flächenlagen, Signale auf L1/L4), `platine_nachrouten.py` (Gitter-Router A* für Restverbindungen), `platine_aufraeumen.py` (überflüssige GND-Bahnen, lose Enden, Bestückungsdruck, Klemmenbeschriftung).
- Platzierung verbessert: Abblockkondensatoren an die STM32-Ecken (Seiten frei für die Signale), Quarze/VCAP/VDDA von Hand verlegt, alle BQ25185-Pins und die TPS61240-Schleife vorverlegt, Freiraum um U201, J704 und SW303 näher an die MCU (Luftlinie −8 %).
- Ergebnis: 196 von 202 Verbindungen geroutet, DRC 0 Verstöße, Schaltplanabgleich 0. 6 STM32-Verbindungen bleiben für den interaktiven Router in KiCad (Liste im Bericht `docs/testberichte/2026-10-13-platine-routing.md`).

## 2026-10-13 – Fanout GND/+3V3 zu den Innenlagen

- Neu `hardware/kicad/werkzeug/platine_fanout.py`: jedes SMD-Pad an GND und an +3V3 (über der +3V3-Fläche) mit kurzer Leiterbahn und eigener Via an L2/L3; kein Via unter fremden Bauteilen oder in den Lochsperren. 120 Anbindungen, DRC 0, Schaltplanabgleich 0, offene Verbindungen 322 → 202. Bericht: `docs/testberichte/2026-10-13-platine-fanout.md`.

## 2026-10-13 – Versorgungslage L3

- Neu `hardware/kicad/werkzeug/platine_lagen.py`: auf L3 eine +3V3-Fläche über Mikrocontroller, Funkmodul, Flash und Bedienteilen mit Arm zu den Reglern U202/U203, darunter GND-Füllung über die übrige Platine (Lastenheft M8, A3). DRC 0 Verstöße, Schaltplanabgleich 0. Bericht: `docs/testberichte/2026-10-13-platine-lage-l3.md`.

## 2026-10-13 – Feinplatzierung der kritischen Gruppen, Massefläche L2

- Neu `hardware/kicad/werkzeug/platine_fein.py`: 100-nF-Kondensatoren 1,7–2,0 mm an jedem VDD-Pin des STM32, VCAP/VDDA, Quarze direkt am Gehäuse; 100 nF + TVS + 10 µF + 100 µF an Pin 3 des Ra-01SH, SPI-Reihenwiderstände auf Pinhöhe; kurze Schleife am TPS61240; 13 Masse-Vias in den Thermal-Pads (U201, U301, U501); durchgehende GND-Fläche auf L2.
- DRC: 0 Verstöße (nur Bestückungsdruck-Warnungen), Schaltplanabgleich 0, offene Verbindungen 323. Offen: Via-Füllung bei JLCPCB [P], Routing. Bericht: `docs/testberichte/2026-10-13-platine-feinplatzierung.md`.

## 2026-10-13 – Mikrocontroller-Auswahl bestätigt (HW-04)

- **HW-04 (Philipp):** STM32F411CEU6 bleibt; kein FPGA, kein externer RAM. Vergleich mit STM32L433, F401, APM32F411, AT32F403A, GD32F303, CH32V203 und STM32WLE5 (Preise/Lager JLCPCB 13.10.2026), Energie- und RAM-Abschätzung in `hardware/mcu-funk.md` 1.5; STM32L433CCU6 als Ausweichoption bei Lieferproblemen.

## 2026-10-13 – Gehäuse mit STEP-Modell geprüft

- STEP-Modell CBHUB_02 -01.1 von Camdenboss ausgewertet (nur lokal, nicht im Repo): Lochbild 110,2 × 110,2 mm bestätigt, Platine 121 × 121 mm ohne Kollision; Dom 9,1 mm hoch; mit 10-mm-Hülsen (HW-03) Freiraum unter der Platine ≥ 13 mm, darüber ≥ 44,3 mm (Deckelpfosten an den Ecken), sonst 53,8 mm → 40-mm-Grenze mit Reserve erfüllt.
- **Korrektur:** Dombohrung Ø 2,4 mm, 10,1 mm tief (Zeichnung Blatt 4 und STEP), nicht Ø 3,6 mm → Schraube selbstformend Ø 3 mm, Länge 18–20 mm [A/P].
- Lichtleiter: Länge LED bis außen ca. 19,4 mm, Bohrungsmitte ca. 22,7 mm von der Außenfläche des Bodens. Lastenheft 4.1/4.1a/M2, `mcu-funk.md` 3.3, `mechanik/README.md`, HW-03. Bericht: `docs/testberichte/2026-10-13-gehaeuse-step.md`.

## 2026-10-13 – Alle Bauteile auf der Hauptplatine (Grobplatzierung)

- Neu `hardware/kicad/werkzeug/platine_bestuecken.py`: übernimmt die 139 Bauteile aus der Netzliste auf `logger.kicad_pcb` (Footprint, Netze, LCSC, Verknüpfung zum Schaltplansymbol) und platziert sie grob nach Lastenheft M5/A3: Klemmen an der Unterkante mit ESD dahinter, Ra-01SH an der Oberkante, LED und Reedkontakt an der linken Kante, USB rechts, 5-V-Wandler fern vom Mikrofonzweig, links oben frei für Erweiterungen. Ergänzt nur Fehlendes, gleiche Platzierung bei jedem Lauf.
- Schaltplanabgleich 0 Abweichungen; DRC ohne Kupfer-, Courtyard- und Randverstöße (nur Bestückungsdruck); 344 offene Verbindungen (noch keine Leiterbahnen).
- Testpunkte TP201/TP202 und Lötbrücken JP401/JP402/JP1 sind kein Bestückteil (`in_bom no`, neuer Parameter `bom=False`); Befestigungslöcher „nur Platine“.
- Hinweis: Klemmenreihe nutzt 102,7 von 103,2 mm zwischen den Lochsperren → mit Steckern am Muster prüfen [P]. Bericht: `docs/testberichte/2026-10-13-platine-grobplatzierung.md`.

## 2026-10-13 – Bauhöhe festgelegt (HW-03), Platinendatei angelegt

- **HW-03 (Philipp):** Hauptplatine auf glatten Distanzhülsen 10 mm über den Gehäusedomen, selbstformende Schrauben in die Dombohrung Ø 3,6 mm; Bauhöhe über der Platine höchstens 40 mm. Das Layout hängt damit nicht mehr vom STEP-Modell ab (angefragt, nur zur Kontrolle). Lastenheft M2/M3, `mcu-funk.md` (Lichtleiter-Bohrung am Muster), `mechanik/README.md`, Entscheidungsregister.
- Neu `hardware/kicad/hauptplatine/logger.kicad_pcb` (Grundgerüst aus `werkzeug/platine_start.py`): 4 Lagen, Umriss 121 × 121 mm, 4 Befestigungslöcher Ø 3,4 mm auf 110,2 mm mit Kupfersperre, JLCPCB-Regeln, Hinweise zu Klemmen- und Funkkante. Footprint `Bienen:Befestigung_3.4mm_Huelse`. DRC: 0 Verstöße.

## 2026-10-13 – Reedkontakt und Side-View-LED gewählt, alle Footprints vorhanden

- **SW304: MiRelay MRS03-B-3** (SMD-Reed, J-Anschlüsse, 10–15 AT, LCSC C41432613) und **D301: Lite-On LTST-S220KGKT** (grün, seitlich abstrahlend, LCSC C160469); Footprints nach Datenblatt in `Bienen.pretty` (`footprints.py`). `mcu-funk.md` 3.3 nachgeführt.
- Pin-/Footprint-Abgleich: alle 161 Bauteile mit Footprint, 0 Abweichungen; ERC 0; Netzprüfung 178/178. Offen am Muster: LED-Helligkeit (ca. 1,3 mA) und Schaltabstand des Reedkontakts.

## 2026-10-13 – Projektfootprints BQ25185 und Ra-01SH; Funde Akkuhalter und Klemmen

- Neu `hardware/kicad/werkzeug/footprints.py` → `hardware/kicad/Bienen.pretty/`: **WSON-10 DLH0010A** (BQ25185) nach TI-Gehäusezeichnung 4226298/A und **Ai-Thinker Ra-01SH** nach Herstellerdatenblatt V1.1 (empfohlenes Pad-Layout). Reproduzierbar (feste UUIDs), in `pruefen.sh`; `kicad_gen.py` schreibt `fp-lib-table`.
- ERC Hauptplatine jetzt **0 Meldungen**; Pin-/Footprint-Abgleich 161 Bauteile, 0 Abweichungen (offen nur Reedkontakt SW304). Netzprüfung 178/178.
- Funde: Thermal-Pad BQ25185 trägt 2 Vias (nicht 6–9, `versorgung.md` korrigiert); **Akkuhalter Keystone 1042 (SMD) festgelegt** (HW-02, Philipp; 1043 wäre Durchsteck); **SCH26-13: DEGSON 15EDGRHC ist zweireihig** → auf Wunsch Philipp **einreihige DEGSON 15EDGRC-3.5** mit LCSC-Nummern je Polzahl (alle lieferbar) und 5 eigenen Klemmen-Footprints. Bericht: `docs/testberichte/2026-10-13-footprints-bienen.md`.

## 2026-10-13 – Pin-/Footprint-Abgleich (REG26-08)

- Neu `hardware/kicad/werkzeug/pin_footprint.py` (in `pruefen.sh`): je Bauteil Footprint vorhanden, Symbol-Pins = Footprint-Pads und Symbol-Pinnamen = Pinbelegung laut Datenblatt (Tabelle mit Quelle und Status). Erzeugt `hardware/kicad/pin_footprint.md`; Exit 1 bei Abweichung, Gegenprobe bestanden.
- Funde behoben: Footprints für U401, U501 (WSON-6), U502 (SOIC-16, laut HX711-Datenblatt), Q501 (SOT-23), D501 (USON-10) eingetragen; **TVS D401 gedreht** (Pad 1 an +3V3, sonst Kurzschluss mit einer unidirektionalen TVS).
- Ergebnis: 161 Bauteile, 0 Abweichungen; offen: eigene Footprints U201 (BQ25185 DLH), U401 (Ra-01SH), Reedkontakt SW304 sowie Datenblätter mit [A]/[P]. ERC Hauptplatine 2 erwartete Meldungen (fehlende Footprints U201, U401). Netzprüfung 178/178. Bericht: `docs/testberichte/2026-10-13-reg26-08-pin-footprint.md`.

## 2026-10-13 – Schaltplanblatt Anschlüsse, Schaltplan vollständig (SCH26-07)

- **Neues Blatt „Anschlüsse“** (`hauptplatine/anschluesse.kicad_sch`, Teile 7xx): DS18B20-Klemmen J701/J702 (= J6/J7) am gemeinsamen 1-Wire-Bus PA8 mit 4,7 kΩ an 3V3_SW und ESDS304; BME280-Klemme J703 (= J8, 6-polig, Pin 6 frei) mit 1,8-kΩ-Pull-ups an 3V3_SW und ESDS304; Erweiterungsleiste J704 (= J11, 2 × 6). Damit sind alle Blätter der Hauptplatine im Entwurf; SCH26-07 im Entwurf behoben.
- DBG_TX/DBG_RX sind jetzt globale Netze (Debug-Leiste und Erweiterungsleiste). `anschluesse.md`: Platinenreferenzen J701–J704.
- `netz_tests.py`: Blatt Anschlüsse (Netze, Pull-ups nur an 3V3_SW mit Gegenprobe, ESD, Polzahlen, Masse an Pin 1, J8-Pin 6 frei) und Stecker J6/J7/J8/J11 gegen `anschluesse.md`; freie Pins werden als unverbunden erwartet. 139 → 178 Prüfungen.
- ERC Hauptplatine 7 → 1 erwartete Meldung (nur der fehlende Footprint U201). Prüfung lokal mit KiCad 10.0.6: reproduzierbar, 178/178, Gegenproben bestanden. Stückliste 161 Teile. Bericht: `docs/testberichte/2026-10-13-sch26-07-anschluesse.md`.

## 2026-10-13 – Schaltplanblatt Mikrofon (SCH26-07, Teil Mikrofon)

- **Neues Blatt „Mikrofon“** auf der Hauptplatine (`hauptplatine/mikrofon.kicad_sch`, Teile 6xx): Siebung 3V3_SW → Ferrit → 47 Ω → 3V3_ANA (22 µF + 100 nF), Vorspannung 1,65 V (2 × 47 kΩ, 1 µF), Klemme J601 (= J5) mit ESDS304 direkt an OUT und VCC, 100 Ω, Hochpass 22 Hz, Sallen-Key 1179 Hz / Q 0,74 als Spannungsfolger, RC 4,8 kHz vor PA1 (MIC_ADC).
- **Operationsverstärker TLV9001IDBVR** (C398363) statt LMV321TP (C90297 laut LCSC am 13.10.2026 nicht lieferbar, TLV9001IDBVR dort 39.765 Stück; Pinfolge der 3PEAK-Variante nicht bestätigt). Pinfolge DBV nach TI-Datenblatt; TLV9001U passt nicht. ESD-Lage an die Regel „direkt hinter der Klemme“ angeglichen. `mikrofon.md` (2.1, Skizze, 7, neuer Abschnitt 8), `anschluesse.md` J5 (Platine: J601).
- Prüfwerkzeug: `netz_tests.py` prüft das Blatt Mikrofon (Siebung, VREF, ESD-Lage, Hochpass, Sallen-Key-f0/Q und RC aus den Bauteilwerten mit Gegenprobe, Spannungsfolger, J5/J601 gegen `anschluesse.md`), 114 → 139 Prüfungen.
- ERC Hauptplatine 8 → 7 erwartete Meldungen (MIC_ADC hat jetzt seine Gegenstelle). Prüfung lokal mit KiCad 10.0.6: reproduzierbar, 139/139, Gegenproben bestanden; ältere Blätter unverändert; CI und Muster offen. Stückliste 152 Teile. Bericht: `docs/testberichte/2026-10-13-sch26-07-mikrofon.md`.

## 2026-10-10 – Schaltplanblatt Waage (SCH26-07, Teil Waage)

- **Neues Blatt „Waage“** auf der Hauptplatine (`hauptplatine/waage.kicad_sch`, Teile 5xx): 5-V-Wandler TPS61240 an SYS (EN = PB10 mit 100 kΩ nach GND, 1 µH, Ferrit zu VSUP), HX711 mit AVDD 4,30 V über S8550 und 20 k/8,2 k, DVDD an 3V3_SW, je 1 kΩ zu PB8/PB9, Wägezellenklemme J501 (= J4) mit TPD4E05U06, 100 Ω, 100 nF und 2 × 10 nF C0G. Kanal B über 0 Ω an INA− [A].
- `waage.md`: Spulen- und Kondensatorwerte nach TI-Datenblatt, Kanal B, **Ferrit in E+ mit ≤ 0,1 Ω** (neue Rechnung 4.1: Temperaturgang des Leitungswiderstands), Abschnitt 9 Schaltplan, Prüfpunkte 6–8. `anschluesse.md`: J4 (Platine: J501).
- Prüfwerkzeug: `netz_tests.py` prüft das Blatt Waage (Wandler an SYS, EN-Pull-down, FB an VOUT, AVDD aus den Teilerwerten mit Gegenprobe, Zellenleitungen, J4/J501 gegen `anschluesse.md`), 79 → 114 Prüfungen. Neues Symbol TPS61240 (`symbole.py`). `kicad_gen.py`: gemeinsames GND-Symbol für verbundene GND-Pins, feste Textlage; ältere Blätter unverändert.
- ERC Hauptplatine 11 → 8 erwartete Meldungen (HX_DOUT, HX_SCK, WAAGE_EIN haben jetzt ihre Gegenstelle). Prüfung lokal mit KiCad 10.0.7: reproduzierbar, 114/114, Gegenproben bestanden; CI und Muster offen. Bericht: `docs/testberichte/2026-10-10-sch26-07-waage.md`.

## 2026-10-10 – USB-Rolle festgelegt, Ra-01SH nach Herstellerschaltbild (SCH26-10/-11)

- **SCH26-10 / HW-01:** USB-C nur zum Laden und Aufspielen (ROM-DFU); die Anwendungsfirmware nutzt USB nicht, Konsole über Serial1/SWD. Keine VBUS-Erkennung nötig. Lastenheft K5, `mcu-funk.md` 1.3, Entscheidungsregister HW-01.
- **SCH26-11:** Herstellerschaltbild des Ra-01SH (Datenblatt V1.1, S. 12) ausgewertet: DIO2 schaltet den HF-Schalter, **TXEN ist im Modul DIO2 (0 Ω)**, RXEN offen, ANT-Pad parallel zur IPEX, DC-DC-Spule vorgesehen. Regel: JP401/JP402 offen, PB14/PB15 nur Eingänge, `setDio2AsRfSwitch(true)`. Prüfplan F-1…F-7 überarbeitet (Pegelmessung an TXEN, RSSI-Vergleich bei −9 dBm, Reglerprüfung).
- Neu: `hardware/funk_modell.py` (Schaltlogik in 6 Konfigurationen, Funkstrecke 5–8 m). `netz_tests.py` prüft die offenen Lötbrücken und DIO2 (79 Prüfungen). Beschreibungen an JP401/JP402/U401 im Generator.
- Prüfung (lokal, KiCad 10.0.7): reproduzierbar, ERC unverändert, 79/79; Modell Exit 0. Bericht: `docs/testberichte/2026-10-10-sch26-10-11-analyse.md`.

## 2026-10-10 – Behebung Schaltplan-Review 4c12b6d (SCH26-09 bis -12)

- **SCH26-09:** Debug-Leiste J302 im Generator an den Kabelplan `anschluesse.md` J10 angeglichen (1 3V3, 2 SWDIO, 3 SWCLK, 4 NRST, **5 GND, 6 TX1, 7 RX1**). `anschluesse.md`: Platinenreferenzen J1/J201, J2/J202, J9/J301, J10/J302, neuer Abschnitt 1.2 Debug-Leiste. `netz_tests.py` prüft J302 je Pin und vergleicht die Stecker-Pinbelegung aus `anschluesse.md` mit der KiCad-Netzliste, mit Gegenprobe (48 → 74 Prüfungen).
- **SCH26-12:** `pruefen.sh` vergleicht alle erzeugten Blätter (Liste aus den Ordnern), prüft die Abdeckung gegen die Blattverweise der Wurzelblätter und hat den Modus `--gegenprobe` (Zufalls-UUIDs über `BIENEN_GEGENPROBE_ZUFALL` in `kicad_gen.py`).
- **SCH26-10/11:** Entscheidungsvorlage USB-Rolle/VBUS-Erkennung (`mcu-funk.md` 1.3) und Prüfplan Funkmodul F-1…F-6 (`mcu-funk.md` 6.1); Schaltplan dafür unverändert.
- Prüfung (lokal, KiCad 10.0.7): reproduzierbar, ERC Akku 0 / Hauptplatine 11 erwartete Meldungen, 74/74 Netzprüfungen; Gegenproben bestanden. Bericht: `docs/testberichte/2026-10-10-sch26-09-12-behebung.md`.

## 2026-10-10 – Blatt Funk + Flash

- Neues Blatt `hauptplatine/funk.kicad_sch` nach `mcu-funk.md` 2, 3.1, 3.2: Ra-01SH (eigenes Symbol, Pinbelegung Datenblatt V1.1 S. 11) an SPI1 mit 33-Ω-Reihenwiderständen, NSS-Pull-up 100 kΩ, Puffer 100 µF + 10 µF + 100 nF und TVS am 3,3-V-Eingang, TXEN/RXEN über offene Lötbrücken, ANT/DIO2/DIO3 offen; SPI-NOR-Flash 64 Mbit (SOIC-8 208 mil) am selben Bus mit CS-Pull-up 100 kΩ, WP/HOLD über 10 kΩ, 100 nF.
- Die 10 Funk-/Flash-Schnittstellen des Blatts MCU sind damit verbunden; `erc_erwartet.json` entsprechend gekürzt.
- Prüfung: `pruefen.sh` reproduzierbar, ERC OK (Hauptplatine 11 erwartete Meldungen), Netzvergleich 48/48. Der Netzvergleich fand beim Zeichnen einen verdrehten Pull-up an WP/HOLD; behoben vor der Lieferung.

## 2026-10-10 – Blatt MCU der Hauptplatine

- Neues Blatt `hauptplatine/mcu.kicad_sch` nach `hardware/mcu-funk.md` 1, 3.3 und 4: STM32F411CEU6 (UFQFPN-48) mit Abblockung (3 × 100 nF, 10 µF, VBAT 100 nF), VDDA über Ferrit, VCAP 4,7 µF; Reset- und BOOT-Taster, BOOT1-Pull-down; HSE 25 MHz (C9006, 2 × 18 pF) und LSE 32,768 kHz SC-32S (C97604, 2 × 8,2 pF); USB-C (C165948) mit CC-Widerständen und USBLC6-2SC6; Debug-Leiste SWD + Serial1; Magnet/Taster an PA0 (WKUP1) mit Pull-down; LED an PC13.
- 20 Schnittstellen-Netze zu den folgenden Blättern (Funk + Flash, Waage, Mikrofon, Anschlüsse) als globale Labels; in `erc_erwartet.json` begründet. VBUS hat jetzt beide Enden.
- `kicad_gen.py`: `*.kicad_pro` wird nur noch angelegt, wenn sie fehlt (REG26-14); Ausrichtung der Beschriftung bei gedrehten Teilen; Netz „NC“ nie global.
- Stückliste im KiCad-README aus den Generatoren erzeugt (87 Teile).
- Prüfung: `pruefen.sh` reproduzierbar, ERC OK (Akku 0, Hauptplatine 21 erwartete Meldungen), Netzvergleich 48/48.

## 2026-10-09 – Schaltpläne lesbar gezeichnet (Verdrahtungsmodus)

- Akku-Platine und Blatt Versorgung werden jetzt mit **echten Leitungen nach dem Stromfluss** gezeichnet statt mit Netzlabels an jedem Pin (Wunsch Philipp). Akku: Leistungspfad oben, Zellschutz im Minuspfad, darunter Ladesperre Stufe 2 und Stufe 1 mit TMP_VCC vom Stecker. Versorgung: Panels/USB → VIN_LADER → BQ25185 → SYS, Akku-Stecker mit VBAT/CE/NTC/TMP_VCC, unten SYS → 3,3 V → 3V3_SW.
- `kicad_gen.py`: Verdrahtungsmodus (`setze`, `draht`, `label`, `versorgung`), Drehung, Junctions, Teilen von Drähten an Pin-Enden, Abbruch bei Pins ohne Draht; Referenzen von `#`-Symbolen verborgen.
- `netz_tests.py`: vollständiger Netzvergleich KiCad-Netzliste ↔ Netzbeschreibung je Projekt (48 Prüfungen). Gegenproben: fehlender Draht → Abbruch, falscher Draht → 9 Prüfungen rot.
- Schaltung elektrisch unverändert (Netzvergleich identisch); ERC wie vorher (Akku 0, Hauptplatine 2 erwartete Meldungen).

## 2026-10-09 – REG26-09/10/11 vor dem Layout

- **REG26-09:** Begründung je `PWR_FLAG` als Symbolbeschreibung im Generator und als Tabelle in `hardware/kicad/README.md`.
- **REG26-10:** Board-Kennungen PCB-AKKU-0.1 / PCB-MAIN-0.1 und Auslegungsumgebung im Titelblock (neue Option `kommentare` in `kicad_gen.py`), Lastenheft M11.
- **REG26-11:** Schienentabelle und DC-Bias-Bewertung (`versorgung.md` 3.9). C204 22 µF/1206, C212 4,7 µF/0805, C208/C209 2,2 µF, weil die bisherigen Werte unter Gleichspannung voraussichtlich unter das Datenblatt-Minimum fallen. Herstellerkurven je LCSC-Nummer stehen noch aus.
- `sicherheit-akku.md` A-5 an LH-M8 (Schutzlack nach dem Test) angeglichen.
- Prüfung: `pruefen.sh` reproduzierbar, ERC unverändert (2 erwartete Warnungen), 42/42 Netzprüfungen.

## 2026-10-09 – Sicherheitsanalyse Akku (REG26-06/07)

- Neu: `hardware/sicherheit-akku.md` (SAF-AKKU 0.1): Sicherheitsziele, Gefährdungsliste, Einzelfehleranalyse der Ladesperre, Schutz- und Wiederanlaufzustände, sicherer Versuchsplan (Zell-Emulator mit Stromaufnahme, Strombegrenzung, Abbruchkriterien, SCH-T01 … T11), Rückverfolgbarkeit LH-V1/V2/V3/V7. Stufe T0, Gegenlesen offen.
- Neue Befunde HW26-16 … -19 (gemeinsamer Fehlerpunkt BQ25185, 0-V-Laden HY2111, Überspannung TMP_VCC, Kältereserve).
- SHA `2076c20` im SCH26-Bericht und im Befundregister nachgetragen (REG26-05, REG26-13).

## 2026-10-09 – Audit gegen Regelwerk 1.1, Wiederherstellung SCH26

- Audit AUD-2026-10-09-01 (`docs/testberichte/2026-10-09-regelwerk-audit.md`), Befunde REG26-01 … -12 im Befundregister.
- **REG26-01:** Die lokal verworfene Behebung SCH26 (Akku-Platine TMP_VCC, zweite Stufe, J3 5-polig, Prüfskripte, Berichte) wiederhergestellt; zusammen mit Regelwerk 1.1 (ADR-0002) eingecheckt.
- REG26-05: SHA in den Behebungsberichten SRV26 (`3f2f9d6`) und HW26/CI26 (`cc6ba60`) nachgetragen.

## 2026-10-09 – Entwicklungsregelwerk 1.1 (ADR-0002) nach Review

- Review des Regelwerks 1.0 durch Claude (`docs/testberichte/2026-10-09-regelwerk-review.md`); Entscheidungen des Maintainers in ADR-0002.
- **Befundregister** `docs/testberichte/befunde.md` als einzige Stelle für Befundstände; **Statusmodell** offen / analysiert / im Entwurf behoben / nachgewiesen / geschlossen (R-05a).
- **D3-Gates:** G2 mit Gefährdungsanalyse, Netz-/ERC-Prüfung und sicherem Versuchsplan (Zell-Emulator, Strombegrenzung); G3/G4 zusätzlich T4-Messungen und unabhängiges Review durch befreundete Hardware-Entwickler. Maintainer namentlich genannt.
- **Übergabe** zwischen Beteiligten nur über committete und gepushte Stände (R-06 Nr. 2); Lastenheft-Zeilen als Anforderungs-IDs `LH-…`; Reproduzierbarkeit ohne zeitgestempelte Exporte, KiCad-Hauptversion 10.
- **GOV-01 entschieden:** Skripte in `hardware/`/`mechanik/` GPL-3.0-or-later (SPDX ergänzt), Schaltpläne/Symbole/Footprints/Exporte CERN-OHL-S-2.0; `LICENSE.md` angepasst.
- Ausnahme **EX-01** (beelogger-Passwort im GET) eingetragen.
- Zusammenführung der parallelen Stände (Regelwerk-Commits `72e4f79`/`8fc2aa4` und lokale Behebung SCH26) in `CLAUDE.md` und `CHANGELOG.md`.

## 2026-10-09 – Entwicklungsregelwerk 1.0 angenommen

- Entwurf 0.1 als verbindlichen Standard für Menschen und Coding-Agents beschlossen; ADR-0001 und Governance-Register eingeführt.
- GOV-02 und GOV-03 angenommen; GOV-01 (Lizenzfrage) und GOV-04 (bauteilabhängige Grenzwerte) bleiben offen.
- AGENTS.md ergänzt; README, CLAUDE und CONTRIBUTING aktualisiert. **Keine Firmware-/Hardware-/Serverlogik geändert.**

## 2026-10-09 – Behebung Schaltplan-Review V0.1 (SCH26-01 … -08)

- **SCH26-01:** Ladesperre auf der Akku-Platine (2 × TMP390, Gate-Pull-ups) versorgt aus TMP_VCC = TPS70933 am Ladereingang; dadurch Wiederanlauf nach Tiefentladung (HY2111-GB gibt nur durch Laden frei) und 0 µA Ruhestrom der Sperre. J3/J203/J1 JST PH 5-polig (P−, NTC, CE_FREI, TMP_VCC, P+).
- **SCH26-02:** R5/R8/R205 100 kΩ statt 10 MΩ; Pegelrechnung in `versorgung.md` 3.3.
- **SCH26-03:** zweite unabhängige Stufe: TMP390 U3 (42 °C) öffnet mit Q3 den NTC-Kreis (TS offen → BQ25185 sperrt).
- **SCH26-04:** `pruefen.sh` prüft Reproduzierbarkeit, ERC aller Schweregrade gegen `erc_erwartet.json`, exportiert Netzlisten; `netz_tests.py` (42 Prüfungen an KiCad-Netzlisten); CI-Job `kicad-schaltplan` (KiCad 10, `git diff --exit-code`).
- **SCH26-05/06/08:** R208 100 kΩ; Kabelplan Akku ↔ Hauptplatine; C201 50 V.
- Ruhestrom 15,7 µA.

## 2026-10-09 – KiCad-10-Schaltplan, Schritt 1: Versorgung und Akku-Platine

- `hardware/kicad/`: Erzeuger für KiCad-10-Schaltpläne aus einer Netzbeschreibung (`werkzeug/kicad_gen.py`), Projektsymbole `bienen.kicad_sym` (BQ25185, TMP390, HY2111-GB, FS8205, RT9080), Prüfskript `pruefen.sh` (Erzeugen, ERC, PDF).
- Akku-Platine (eigenes Projekt): HY2111 + FS8205 nach Herstellerschaltung, Messbrücke, TMP390 mit 2,49 kΩ (42 °C) / 18,7 kΩ (+5 °C, 5 °C Hysterese) und AO3400A an CE_FREI, NTC 10 k B3435, JST PH 4. ERC 0/0.
- Hauptplatine, Blatt Versorgung: Solar mit SS34/SMAJ12A, Teiler 3,3 MΩ/470 kΩ, BQ25185 (ISET 2,0 kΩ = 150 mA, ILIM/VSET 130 kΩ = 4,1 V/500 mA), CE-Pull-up 10 MΩ, Akkuteiler, RT9080, TPS22917 (CT 1 nF nach VIN, QOD über 0 Ω an VOUT, ON mit 1 MΩ). ERC 0 Fehler.

## 2026-10-09 – Behebung Hardware-Review 0.4 (HW26-07 … -13) und CI26-01

- **CI26-01:** `lora_verarbeitung.php` erkennt „gespeichert“ über den letzten Zeitstempel vorher/nachher (`le_speicherung_erkannt`), nicht mehr über die Dateigröße. Ursache: beelogger kürzt `week.csv` vor 08:00 Uhr Serverzeit. E2E-Test mit `SERVER_UHR` (libfaketime), CI prüft 05:00 und 14:00; Protokoll je DST-Ereignis; Unit-Tests 66/66.
- **HW26-07:** Ladesperre zweistufig: TMP390 an der Zelle sperrt über CE außerhalb +5 … 42 °C (ausfallsicher bei Leitungsbruch), NTC am TS als zweite Stufe; J3 4-polig.
- **HW26-08:** Solar-Teiler 3,3 MΩ / 470 kΩ + 100 nF hinter den Dioden (25 V → 3,12 V).
- **HW26-09:** BME280 über Outdoor-Netzwerkkabel (105–135 pF); `i2c_leitung.py` mit Kabelvarianten und Fehlercode.
- **HW26-10:** EEPROM AT24C256 entfällt; LoRaWAN-Sitzung im SPI-Flash (Ringpuffer, Generation, CRC-32, Gültig-Byte).
- **HW26-11:** Ladestrom 150 mA; Wärmerechnung BQ25185.
- **HW26-12/13:** Flash-Aufteilung, FFT-Rohdaten nur als Schnappschüsse; J10 1 × 7, J11 2 × 6.
- Energiebilanz: Ruhestrom 16,6 µA, 128–452 Tage ohne Laden.

## 2026-10-08 – Lastenheft Platine 0.4: Versorgung

- `hardware/versorgung.md`: Laderegler BQ25185 (Eingang bis 18 V, Kältesperre per NTC, Ladeschluss 4,1 V), zweistufiger Tiefentladeschutz (BQ25185 3,0 V, HY2111-GB 2,9 V), Akku-Platine am Halter, LDO RT9080, Sensorschalter und Regeln gegen Rückspeisung, Regeln aus den beelogger-Erfahrungen, Montage der Panels
- 09.10.2026: J8 (BME280) 6-polig mit freiem Pin 6 als Verwechslungsschutz zu J4 (Wägezelle, E+ 4,3 V > 4,25 V BME280-Grenze); Steckerfarbe zusätzlich
- 09.10.2026: BME280-Leitung höchstens 1 m, Pull-ups 1,8 kΩ statt 1,5 kΩ (`hardware/i2c_leitung.py`: 290–440 pF, Anstiegszeit ≤ 671 ns); Bestückung komplett bei JLCPCB inkl. Durchsteckteile
- 09.10.2026: `hardware/anschluesse.md`: Klemmenbelegung J1–J11 (Masse/Schirm an Pin 1), steckbare Klemmen DEGSON 3,5 mm, ESD ESDS304 bzw. TPD4E05U06 (Wägezelle, 5,5 V, ≤ 10 nA), I²C für BME280 mit 50 kHz, alle Außenklemmen an einer Kante; Lastenheft F4, F5, F10, M4, M5 angepasst
- 09.10.2026: Wand-Lichtleiter mit Dichtung (Kandidat Bivar PLTR2, IP67); STEP-Modell des Gehäuses wird bei Camdenboss angefragt; Reedkontakt-Schaltabstand am Prototyp
- 09.10.2026: **4 Lagen** festgelegt (L2 durchgehende Masse); **Lichtleiter durch Gehäusebohrung** mit seitlich abstrahlender LED und Reedkontakt an der Platinenkante
- 09.10.2026: nur noch **ein HX711**; **SPI-Flash 64 Mbit fest** (SPI1, CS PB3, dauernd versorgt, Typ nach Bestand); Bedienung per Magnet mit **LED unter Lichtleiter** (Sofortmessung, Durchsicht ein/aus); Energiebilanz neu (≥ 128 Tage ohne Laden)
- `hardware/beep-vergleich.md`: Auswertung BEEP base v3 (Schaltplan, Stückliste); übernommen: Lastschalter TPS22917, Reedkontakt an PA0, ESD-Arrays an allen Sensorklemmen, Platz für SPI-Flash; 4 Lagen zur Entscheidung
- `hardware/mikrofon.md` und `mikrofon_filter.py`: Sallen-Key-Tiefpass 1179 Hz + RC 4,8 kHz (−36 bis −39 dB bei den Spiegelfrequenzen, ≤ 1,1 dB im Nutzband), Hochpass 22 Hz, gesiebte Versorgung, Timer + DMA, Ablaufregeln (kein Funk und kein 5-V-Wandler während der Messung)
- `hardware/waage.md`: HX711 mit 5 V aus festem Wandler TPS61240 (Lasttrennung, EN an PB10), AVDD 4,3 V, Bosche H40A 200 kg (404 Ω, 2 mV/V), Eingangsschutz der Zellenleitungen, Auflösung ca. 1,2 g je Einzelwert; Energiebilanz neu (≥ 122 Tage ohne Laden)
- `hardware/mcu-funk.md`: Beschaltung STM32F411 (VCAP 4,7 µF, LSE-Quarz 7 pF statt 12,5 pF nach ST AN4488), USB-C mit ESD und Laden über VBUS, Ra-01SH (Antenne an IPEX, TXEN/RXEN über Lötbrücken, Hinweis LLCC68 ohne SF11/12), EEPROM an der geschalteten Schiene, Pinbelegung 0.4
- `hardware/energiebilanz.py`: reproduzierbare Energiebilanz mit Quellen und Status je Wert; Ergebnis 130–510 Tage Reichweite ohne Laden, Dezemberertrag ca. 40-facher Bedarf

## 2026-10-08 – LoRa-Eingang und Server nach Review 5c1b847 (SRV26-02/03/04/05/07/08)

- **SRV26-07:** Zeitbasis je Logger statt über eine Datei im Hauptordner. Der Eingang liest das Merkmal `$BL_UTC_FAEHIG=1;` im `beelogger_log.php` des Ziel-Loggers. Alte Fassung → Ortszeit (keine 2-h-Verschiebung), Meldung „Mischinstallation“. `utc_zeit=true` stellt Nachrichten an alte Endpunkte zurück.
- **SRV26-05:** eigene Fassung (eigen-utc-2) sendet BEEP/ThingSpeak nur für gespeicherte Datensätze; Prüfung der BEEP-ID/ThingSpeak-API mit `AND` statt `OR`.
- **SRV26-03/04:** Sperre je Logger; Kennung je Nachricht (Gerät, FPort, FCnt, Nutzdaten, `received_at`) → doppelte Nachrichten werden nicht erneut weitergegeben; Schreibfehler der Zusatzdatei werden protokolliert und gemeldet.
- **SRV26-02:** Ergebnisklassen `gespeichert`/`abgelehnt`/`doppelt`/`ignoriert`; vorübergehende Fehler → 202 und Zwischenspeicher, `lora_nachholen.php` (cron) verarbeitet nach.
- Aufteilung: `lora_eingang.php` (HTTP), `lora_verarbeitung.php` (Verarbeitung), `lora_nachholen.php` (Kommandozeile).
- **SRV26-08:** Playwright 1.56.1 fest in der CI; `BROWSER_PFLICHT=1` lässt den Test ohne Browser fehlschlagen.
- Tests: Ende-zu-Ende eigen 73, original 56 Prüfungen (neu: doppelt, 4 parallele Webhooks, Nachholen, Zeitbasis-Matrix, BEEP-Nachbildung, Schreibfehler Zusatzdatei); Unit-Tests 59. Gegenprobe: Ohne die SRV26-05-Korrektur schlagen 3 BEEP-Prüfungen fehl.

## 2026-10-08 – Eigene Server-Fassung mit UTC (eigen-utc-2)

- `server/beelogger_eigen/`: beelogger M.40 mit Unix-Zeitstempel (UTC) als maßgeblicher Zeit; Zeitzone wählbar in `beelogger_zeitzone.php`
  - `beelogger_log.php`: `UTC=1` beim EE-Weg (vom LoRa-Eingang gesetzt); Zeitstempel nicht mehr aus dem Ortszeit-Text zurückgerechnet
  - Grafik (`beelogger_show.php`, `beelogger_sml.php`, `beelogger_mobileWatch.php`): Zeitachse als ISO 8601 mit Versatz aus dem Zeitstempel, eindeutig auch in der doppelten Stunde; Stundenauswertung nach Zeitstempel
  - Hauptordner-Skripte (`beelogger_cron21.php`, `scraper.php`, `local_Updater.php`, `local_Split_Archivnotes.php`) setzen die Zeitzone; bisher galt die php.ini-Vorgabe
- `server/eigen_anpassen.py` erzeugt die Fassung aus dem Original-ZIP (jede Stelle muss genau einmal vorkommen); `server/eigen_utc.patch` zeigt den Unterschied
- LoRa-Eingang: `utc_zeit` (`'auto'`), Speicherprüfung über den Zeitstempel
- Tests: Ende-zu-Ende für beide Fassungen (eigen 29, original 22 Prüfungen), Grafik im Browser (Playwright); CI vergleicht die erzeugte Fassung mit dem Repo

## 2026-10-08 – Firmware 261010: Korrekturen nach Trockenprüfung (Review zu 261009)

- FFT-Spitze nur noch mit deutlichem Abstand zum Grundrauschen: `spitze_gueltig` erst ab 10 dB über dem Median der Linien 60–900 Hz (`BF_SNR_DB`). Gesamt- und Bandpegel werden weiter gesendet (`gueltig`). Vorher wurde bei Rauschen eine zufällige Linie als Spitze gemeldet.
- Spitzen, deren interpolierte Frequenz außerhalb von 60–900 Hz liegt (z. B. Ton bei 59 Hz), zählen nicht; es gilt die nächstgrößere Spitze im Bereich (Toleranz 0,5 Hz).
- ADC-Warteschleife mit Zeitgrenze (50 µs): Antwortet der ADC nicht, wird die FFT-Messung verworfen statt zu hängen.
- Unkalibrierte Waage (`Taragewicht` = 10) wird nicht mehr als 0,01 kg gesendet und nicht als Ausfall gemeldet.
- `#error` bei `FUNKFORMAT 2` mit mehr als 2 Waagen (Waage 3/4 haben im Funkformat v2 noch keine Bits).
- Mit `FUNKFORMAT 1` wird keine FFT gemessen (Ergebnis würde nicht gesendet; spart 1,25 s und 38 KB RAM).
- Tests: FFT 32 Prüfungen (neu: ±1 LSB, Rauschen ×20, Ton im Rauschen, 50/55/58/59/60/61 Hz); CI prüft zusätzlich den `#error`.

## 2026-10-08 – Firmware 261009: Funkformat v2 und FFT

- `FUNKFORMAT 2` (Vorgabe): Datensatz im Funkformat v2 auf FPort 2 (`STM32_LORA_v2.ino`, `funkformat_v2.h`)
  - 2. Innentemperatur mit Vorzeichen in 1/100 °C statt über `FeuchteIn`
  - keine CPU-Temperatur mehr als Ersatz für die Außentemperatur; Ausfälle als Zustandsbits
  - Messzeitpunkt (bei abgeglichener Uhr), Neustart-Grund, Firmware-ID nach Neustart und in jedem 96. Paket, CPU-Temperatur
- FFT des Mikrofons (`beelogger_Audio 1`): `bee_fft.h` nach `docs/fft-konzept.md`, Abtastung über ADC-Register und DWT-Takt
- Tests: C-Kodierer gegen den JavaScript-Referenz-Kodierer (303 Fälle), FFT mit künstlichen Signalen (21 Prüfungen); CI übersetzt drei Varianten
- Kommentar zur Gewichtsgröße im beelogger-Format richtiggestellt (2 Byte)

## 2026-10-08 – LoRa-Eingang am Server

- `server/lora/`: Webhook-Ziel für TTN; Messzeit aus dem Gerät bzw. `received_at`; Weitergabe über den EE-Weg an das unveränderte `beelogger_log.php`; Prüfung der Speicherung; `lora_zusatz.csv` und Protokoll
- Tests: 46 Unit-Tests (PHP), Ende-zu-Ende-Test mit den echten beelogger-Skripten M.40 und dem echten Formatter (22 Prüfungen, einschließlich Winterzeit-Nacht)

## 2026-10-08 – TTN-Formatter

- `formatter/formatter.js`: FPort 1 (beelogger, gleiche Ausgabe wie das Original) und FPort 2 (Funkformat v2)
- `docs/funkformat-v2.md`: Spezifikation 1.0
- Tests: Vergleich mit dem Original-Formatter, Goldenes Paket, Fehlerfälle, Prüfung in goja
- `formatter/ttn_formatter.min.js` (3846 Byte) zum Einfügen in TTN

## 2026-10-08 – Server-Analyse, FFT-Konzept, Verbesserungsliste

- Server-Skripte M.40 unverändert in `server/beelogger_M40_original/`
- `docs/server-analyse.md`: LoRa-Eingang geprüft (u. a. Winterzeit-Fehler, Aux2 = RSSI, Aux3 = Sketch-ID)
- `docs/fft-konzept.md`: 4-Hz-Teilung, Anti-Aliasing, dBFS, Bandpegel
- `docs/verbesserungen.md`: Liste der Notbehelfe mit Prioritäten
- Lastenheft: Mikrofon-Filter A2/A7 neu

## 2026-10-08 – Datenformat

- `docs/datenformat.md`: Daten weiter an den beelogger-Webserver, neues Funkformat auf FPort 2, Formatter liefert beelogger-Feldnamen

## 2026-10-08 – Lastenheft Platine 0.3

- Ra-01SH festgelegt (Datenblatt ausgewertet: Quarz statt TCXO, HF-Schalter über DIO2)
- neue Firmware ohne beelogger-Kompatibilität, neue Pinbelegung, USB-C
- Platine 121 × 121 mm nach Camdenboss-Zeichnung CBHUB_02 Rev. N

## 2026-10-08 – Lastenheft Platine 0.2

- Funk SX1262-Modul (E22-900M22S oder Ra-01SH), Firmware-Folgen beschrieben (RadioLib)
- Mikrofon GY-MAX4466 mit Entstörung, Akku per Kabel, Gehäuse CBHUB-02-GY mit Reserve

## 2026-10-08 – Firmware STM32_LORA_261008_ZS (Testversion, Review-Stand 2)

Grundlage: beelogger `STM32_LORA_260705`.

- MCCI LoRaWAN LMIC library statt LMIC-Arduino 1.5.0
- Zeitabgleich per LoRaWAN `DeviceTimeReq` einmal täglich, RTC läuft in UTC
- Weckraster `k × Intervall + LOGGER_SLOT × 10 s + 1 s`, Nachtfenster in Ortszeit mit EU-Sommerzeit
- 8 Kanäle, ADR aus
- RTC-Lesen ohne veraltetes Datum nach Mitternacht (STM32RTC 1.3.7, Schattenregister)
- Bei LMIC-Fehler schlafen statt Endlosschleife
- Plausibilitätsprüfung der Uhr beim Wecken; Prüfwort für die Backup-Register
- Frame-Counter beim Sendeversuch fortschalten
- Sketch-ID nur in jedem 10. Paket (Fehler im Original)
- Gerätedaten in `Config_Geraet.h` ausgelagert (nicht im Repo)

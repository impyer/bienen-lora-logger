# Bienen-Plattform – Gesamtkonzept 0.2 (Stockkarte, Messdaten, Umwelt, Auswertung)

**Stand:** 15.10.2026, Fassung 0.2.7 (Entscheidungen zu Waage, Login, Bodentiefen; Review Issue #11 eingearbeitet, siehe §11; Variante B bestätigt; öffentliche Lese-API statt statischem Hochladen; Zugriff und Veröffentlichung ergänzt; Rückmeldungen Philipp vom 15.10. eingearbeitet: Beute = Volk, Bienenbuch, Uhrzeit, BEEP Base, Waage am Volk, Python, ThinkStation) · **Status:** ENTWURF zur Abnahme durch den Betreiber, keine SQL-Freigabe  
**Änderungsklasse / Prüfung:** D0 (Dokumentation) / T0 (Abgleich der Dokumente untereinander und mit Quellcode-Dokumentation). Keine Laufzeit-, Datenbank- oder Feldtests.  
**Prüfbasis:** Repository `impyer/bienen-lora-logger`, Commit `bf2ea5f` (15.10.2026)  
**Verfasser:** Claude (Cowork), auf Grundlage der ChatGPT-Vorarbeit in `docs/architektur/` und der Claude-Projektdokumente

**Kennzeichnung:**
- **[BESTÄTIGT]** vom Betreiber entschieden
- **[VORSCHLAG]** Architekturvorschlag, noch nicht entschieden
- **[OFFEN]** Entscheidung des Betreibers nötig
- **[PRÜFEN]** Tatsachenfrage, vor Umsetzung an Quelle oder Gerät zu verifizieren

**Geprüfte Unterlagen:**

| Dokument | Herkunft |
|---|---|
| `anforderungen-datenplattform.md` | ChatGPT, 12.10. |
| `er-modell-datenplattform-v01.md` | ChatGPT, 12.10. |
| `beute-volk-stand-beziehungen-v01.md` | ChatGPT, 12.10. |
| `messreihe-messkontext-zeitqualitaet-v01.md` | ChatGPT, 12.10. |
| `messgroessen-am-bienenvolk.md` | ChatGPT, 12.10. |
| `sensoren-messkanaele-entwurf.md`, `messgroessen-kanalinventar.md/.csv` | ChatGPT, 12.10. |
| `ist-inventur-beelogger1.md` | ChatGPT, 12.10. |
| `docs/beep-anbindung.md`, `server/lora/README.md`, `server/wetter/README.md` | Repo |
| Projekt: `datenbank-konzept-review-2026-10-13`, `beep-stockkarte-setup`, `beelogger-datenanalyse-grundgeruest`, `weboberflaeche-design-2026-10-15` | Claude |

---

## 1. Zielbild

**[BESTÄTIGT, 15.10.2026]** Eine eigene Plattform vereint das Beste aus BEEP und beelogger: eine **digitale Stockkarte** und **gute Datenauswertung**. Langfristig wird alles auf der eigenen Plattform gespeichert:

- Messdaten der Stockwaagen (eigene Logger, BEEP Base)
- Umweltdaten (Wetterstation, Bodentemperatur, später weitere)
- Daten der imkerlichen Arbeit (Völker, Beuten, Durchsichten, Behandlungen, Fütterung, Königinnen, Ernte)

**[BESTÄTIGT]** BEEP läuft zunächst parallel und wird abgelöst, wenn die eigene Plattform zuverlässig läuft.

**[BESTÄTIGT, aus den ChatGPT-Anforderungen]** Mehrere Völker und Stände, standübergreifende Vergleiche, automatisierte Analysen als eigene Datenobjekte, interner und öffentlicher Bereich, Apache ECharts.

**Leitlinie für dieses Konzept:** „Keep it simple as needed“. Das Modell muss die bestätigten Fälle sauber abbilden und erweiterbar sein. Es baut aber nichts, wofür es noch keinen konkreten Fall gibt.

---

## 2. Was sich durch das Zielbild ändert

Das neue Zielbild widerspricht mehreren Festlegungen vom 12. und 13.10. Diese müssen ausdrücklich angepasst werden, sonst gelten widersprüchliche Regeln nebeneinander.

| # | Bisherige Festlegung | Quelle | Neu (Vorschlag) |
|---|---|---|---|
| Ä1 | Stockkarte und Inspektionen bleiben in BEEP; eigene DB nur Messwerte | Claude-Review 13.10., §4 | **[VORSCHLAG]** Stockkarte zieht auf die eigene Plattform um (Phasen in §7) |
| Ä2 | BEEP-Stockkarte ist **führende Quelle** für Beutenaufbau und Zargenhistorie | ChatGPT, Anforderungen §3.1; Commit `ecf2918` | **[VORSCHLAG]** Gilt nur bis zur Umschaltung (Phase C). Danach führt die eigene Stockkarte |
| Ä3 | BEEP Base sendet an BEEP, **nicht direkt** an den eigenen Server | ChatGPT, Anforderungen §2 | **[BESTÄTIGT, 15.10.2026]** BEEP Bases senden über die eigene TTN-Applikation an den eigenen Server **und** an BEEP. Damit liegen alle Messwerte auf dem eigenen Server. **[PRÜFEN]** Firmware-Voraussetzung und Vorgehen laut BEEP-Dokumentation, je Gerät |
| Ä4 | Drei-Tabellen-Modell für Messwerte | Claude-Review 13.10. | **[VORSCHLAG]** Bleibt Kern der Messdaten, erweitert um Kanal und Messgröße (§5.3) |
| Ä5 | Datenbank auf Webhosting, eventuell nur MySQL | Claude-Review 13.10., Punkt 6 | **[BESTÄTIGT, 15.10.]** Alles läuft auf der eigenen **ThinkStation**; PostgreSQL ist möglich, die Einschränkung entfällt |

---

## 3. Abgleich mit der ChatGPT-Vorarbeit

### 3.1 Übernehmen – fachlich richtig und wichtig

| Punkt | Dokument |
|---|---|
| Volk, Beute, Stand und Gerät sind getrennte Identitäten; Ableger bekommen eine neue ID mit Herkunft | Anforderungen §3, Beute-Volk-Stand |
| Eine Beute beherbergt höchstens ein Volk gleichzeitig | Beute-Volk-Stand §4 |
| Zeiträume `[von, bis)` in UTC; Zuordnungen historisiert, nie überschrieben | ER-Modell §4 |
| Messzeit, Empfangszeit und Importzeit getrennt; Zeitqualität mitführen | ER-Modell §6.2 |
| Quellfeld ≠ Messgröße: `FeuchteIn`, `Aux1–3` nie nach Namen deuten | Sensoren §4, Kanalinventar §3 |
| Wertsemantik: Momentanwert, Intervallsumme, Spitzenwert, Zähler, zirkulär (Windrichtung), Status | ER-Modell §6.3 |
| `rain_mm` mit unbekanntem Rücksetzzeitpunkt nicht summieren; `p` und `p_hpa` sind **ein** Druckwert | Kanalinventar §5 |
| Qualitätsstufen statt ok/fehlerhaft; Lücke ≠ 0 | ER-Modell §7 |
| Rohdaten unverändert behalten; Import idempotent | Anforderungen §4 |
| Gemessen ≠ berechnet ≠ Modellergebnis; Cluster gehören zu Lauf und Zeitfenster | Anforderungen §5 |
| Akustik: FFT-Merkmale ≠ Rohsignal; dBFS ≠ dB SPL | Messgrößen §3.4 |
| Öffentlich nur über freigegebene Datensatzversionen | ER-Modell §8.3 |
| Akzeptanzfälle ER-01 bis ER-17 | ER-Modell §9 |

### 3.2 Vereinfachen – richtig gedacht, aber für den Start zu schwer

| ChatGPT-Vorschlag | Vereinfachung | Warum |
|---|---|---|
| `devices` + `measurement_units` + `unit_assignments` | `geraet` + `geraet_zuordnung` (an Beute **oder** Stand) | Mehrfachlogger sind ausdrücklich nicht geplant. Eine Messeinheit je Gerät reicht; erweiterbar, wenn nötig |
| `device_channels` + `channel_mappings` + `ingest_profiles` | **eine** Tabelle `kanal` mit Gültigkeit von/bis | Ein Quellfeld mit zeitlicher Deutung ist dasselbe Objekt. Neue Deutung = neue Zeile |
| `raw_records` + `raw_channel_values` als DB-Tabellen | Rohdaten bleiben in den vorhandenen JSONL-Protokollen (`lora_log/`, Wetterprotokoll); DB speichert Verweis und Hash | Die Eingänge schreiben schon jede Webhook-Nachricht unverändert mit. Doppelte Speicherung bringt nichts |
| `observation_series` + `observations` + `observation_revisions` | `messwert(kanal, zeit, wert, qualitaet)`; Neuinterpretation über neuen Kanal-Datensatz | Revisionen erst einführen, wenn eine echte Korrektur vorkommt |
| Polymorphe `measurement_positions` | `messstelle` mit genau einem Bezug: Beute **oder** Stand (CHECK) | Einfache referentielle Integrität |
| `lifecycle_events` + `lifecycle_participants` | So übernehmen, aber nur 4 Ereignisarten zum Start: Ableger, Vereinigung, Schwarm, Auflösung | Deckt Philipps reale Fälle 2026 ab (Vereinigungen, Ableger) |

### 3.3 Zurückstellen – erst bei konkretem Bedarf

- `sensor_components`, `sensor_installations`, `calibrations`
  - Sensortausch und Tara werden zunächst als Ereignis an der Beute bzw. am Gerät dokumentiert.
  - Die Firmware sendet kalibrierte kg.
- `signal_segments` (Rohaudio)
  - Die neue Platine liefert FFT-Merkmale.
  - Rohaudio erst mit konkretem Forschungsplan, Speicher- und Datenschutzkonzept.
- Analyse-Schicht (`analysis_runs`, `cluster_assignments`, `classification_results`)
  - Schnittstelle vorsehen, Tabellen erst mit dem ersten echten Analyselauf.
- Veröffentlichung (`dataset_releases`, `publications`)
  - Erst wenn `radeberger-honig.de` steht.

### 3.4 Widersprüche und Lücken in der Vorarbeit

**W1 – Beute = Volk: kein Widerspruch, aber eine Zuordnungsregel für den Import (geklärt 15.10.).**
- **[BESTÄTIGT, 12.10.]** Eine Beute ist eine eigene physische Identität und beherbergt zu einem Zeitpunkt **0 oder 1** Volk; Wiederbelegung ist möglich.
- **[BESTÄTIGT, 15.10., ADR-0003]** Ein Volk bewohnt zu einem Zeitpunkt **0 oder 1** Beute (bis dahin offen). Zusammen: zu jedem Zeitpunkt höchstens 1:1. Leere Beuten und wechselnde Völker bleiben möglich.
- **Importregel, keine Identitätsregel:** Philipps Arbeitsregel lautet **neues Volk = neuer BEEP-Hive; ein Hive wird nie weiterverwendet**. Der Import nutzt sie als Heuristik und meldet Hives, bei denen Name oder Königin auf eine Wiederverwendung hindeuten, statt still zuzuordnen.
- Ein BEEP-Hive enthält beides: das Volk (Name, Königin, Durchsichten) und die Beutenangaben (Typ, `brood_layers`, `honey_layers`). Beim Import heißt das:
  - BEEP-Hive-ID → **Volk** (`extern_ref` mit `system='beep'`, `typ='hive'`).
  - Beutentyp und Zargen → **Beute** dieses Volks bzw. deren `beute_konfiguration` mit Zeitraum.
  - Beim ersten Import wird je BEEP-Hive automatisch eine Beute angelegt und belegt. Keine zusätzliche Pflegearbeit.
- Beute und Volk fallen nur bei Umsetzen, Ableger und Vereinigung zeitlich auseinander. Genau dafür bleibt die Belegung mit Zeitraum im Modell.
- **[BESTÄTIGT, 15.10.; nach Review erneut bestätigt, ADR-0003 Nr. 5/9]** Die Stockwaage wird dem **Volk** zugeordnet (wie im Drei-Tabellen-Modell vom 13.10.), nicht der Beute. Bei 1:1 ist das gleichwertig. Beim Umsetzen in eine neue Beute auf derselben Waage läuft die Volkskurve weiter, und der Sprung wird über die Maßnahme „umsetzen“ erklärt. Das entspricht Philipps Regel, Umsetzen mit Datum und Uhrzeit zu dokumentieren.

**W2 – Bienenbuch ist nur Hilfsmittel (geklärt 15.10.).**
- **[BESTÄTIGT]** Das Bienenbuch ist ein Hilfsmittel und soll langfristig wegfallen.
- Alle Bienenbuch-Einträge sind bereits in BEEP übertragen (Momentaufnahme 13.10.: 512 Einträge; keine feste Importerwartung). Migrationsquelle ist deshalb **nur BEEP**. Ein eigener Bienenbuch-Import entfällt.

**W3 – Uhrzeit historischer Einträge.**
- Neue Einträge in der eigenen Stockkarte haben immer Datum **und** Uhrzeit. Die Uhrzeit wird mit der Erfassungszeit vorbelegt und ist beim Nachtragen änderbar.
- Nur die bisher aus dem Bienenbuch nach BEEP übertragenen Einträge haben keine echte Uhrzeit: Das Übertragungsskript setzt dort einheitlich 12:00, weil das Bienenbuch nur das Datum führt (`beep-stockkarte-setup.md`, Mapping).
- Folge: Eine Durchsicht, die tatsächlich um 16:00 war, steht im Diagramm vier Stunden zu früh. Der Gewichtseinbruch beim Öffnen liegt dann neben der Linie.
- **[VORSCHLAG, überarbeitet nach Review #11]** Feld `zeitgenauigkeit` (exakt, geschätzt, nur_datum), Vorgabe `exakt`. Neue Einträge merken davon nichts. Die übertragenen Altdaten bekommen `nur_datum` und erscheinen im Diagramm als Tagesband statt als Linie. Die Herkunft allein reicht nicht, weil im Parallelbetrieb auch direkt in BEEP erfasste Einträge mit echter Uhrzeit kommen können. Ereigniszeit (`zeit`) und Erfassungszeit (`erfasst_am`) sind getrennt.

**W4 – Behandlungen sind Zeiträume.**
- Beispiel AS-Verdunster Volk 8: 01.–11.10. BEEP speichert nur Einzeleinträge.
- Die Ereignistabelle braucht `von` und `bis`. ChatGPT erwähnt das, das ER-Modell 0.1 hat es nicht.

**W5 – ER-Modell 0.1 ist in sich nicht konsistent.**
- Diagramm und §4.1 enthalten noch `colony_placements` (Volk direkt am Stand).
- Laut Beute-Volk-Stand-Entwurf ist das nicht mehr das fachliche Standortmodell.
- Hier gilt: Stand eines Volks = Stand seiner Beute zum Zeitpunkt (§5.1).

**W6 – Abruf der Inspektionen.**
- `GET /api/inspections` ist auf 1000 Einträge begrenzt, bevor gefiltert wird (Claude-Review 13.10., Quellcode geprüft).
- Import nur über `GET /api/inspections/hive/{id}`.

**W7 – Zu viele Prüfschleifen.**
- Jedes ChatGPT-Dokument endet mit „vor SQL noch X klären“.
- Die meisten dieser Punkte werden erst durch echte Daten entscheidbar (Feldnamen, Intervalle, `rain_mm`).
- Vorschlag: Kernschema jetzt festlegen, gerätespezifische Kanäle beim Anschluss des jeweiligen Geräts eintragen.

---

## 4. Zielarchitektur

```
                        ┌──────────────── Eingänge (bestehend, PHP, getestet) ───────────────┐
 Logger L01–L10  ─┐     │ lora_eingang.php   → beelogger M.40 (bleibt parallel) + lora_log/*.jsonl │
 BEEP Base 1/2   ─┼TTN─▶│ lora_eingang.php → BEEP-Decoder → lora_log/beep/*.jsonl [ENTWURF]    │
 S2120           ─┤     │ wetter_eingang.php → Wetter-CSV + Protokoll-JSONL                       │
 LSN50v2-D23     ─┘     │ [neu] boden-Eingang (oder wetter_eingang verallgemeinert)               │
                        └───────────────┬────────────────────────────────────────────────────────┘
                                        │ Importer (alle 1–5 min, idempotent über Nachrichten-ID)
                                        ▼
 BEEP-API (lesend) ──Import──▶  PostgreSQL  ◀── Stockkarte (Eingabe über Web/Handy)
                                   ├──▶ Lese-API ──▶ Weboberfläche (Dashboard, Volk-Cockpit, Umwelt, Vergleich, Stockkarte)
                                   ├──▶ Analyse-Jobs (Kennwerte nach Grundgerüst, später Modelle)
                                   └──▶ Export an BEEP (einseitig, solange gewünscht)
```

**Entscheidungen:**

1. **[VORSCHLAG] Die getesteten Eingänge bleiben, ein separater Importer liest deren Rohprotokolle in die Datenbank.**
   - Voraussetzung: verlustfreies Rohprotokoll nach §4a. R-1/R-2 sind seit 15.10. im Entwurf behoben (T2), R-4 bis R-6 kommen mit dem Importer (Befund PLT26-02).
   - Der Import ist wiederholbar; die Kennung gegen Doppelzustellung existiert schon (SRV26-03).
**[BESTÄTIGT, 16.10.2026] BEEP Base, klassischer beelogger und eigener Logger sind alternative primäre Stockmessgeräte (maximal eines je Volk). BEEP Base wird über denselben `lora_eingang.php` empfangen wie ein beelogger, mit internem Decoder; komplementäre Zusatzsensoren können weitere Größen liefern. Für die erste Ansicht stehen Gewicht, Temperatur und akustische FFT-Frequenzbänder im Fokus. Die BEEP-Base-JSONL-Zwischenablage bleibt Übergangslösung bis zum PostgreSQL-Importer; direkte Rückübertragung derselben Uplinks an BEEP ist nicht erlaubt.**

2. **[VORSCHLAG] beelogger M.40 läuft weiter**, bis die eigene Oberfläche alles kann. Danach wird er abgeschaltet oder bleibt als reine Referenz.
3. **[BESTÄTIGT] Eine Datenbank: PostgreSQL** auf der ThinkStation. TimescaleDB erst bei Bedarf. Bei ca. 4–5 Mio. Werten pro Jahr reicht normales PostgreSQL mit Index auf (kanal, zeit).
4. **[BESTÄTIGT, 15.10.] Python für Lese-API und Analyse** (FastAPI, pandas/numpy/scipy, später scikit-learn).
   - Kennwerte und Modelle werden nur einmal in Python definiert; die API liefert dieselben Berechnungen, die auch der Wochenbericht nutzt.
   - Die PHP-Eingänge bleiben unverändert. Damit gibt es genau zwei Sprachen: PHP für den Empfang, Python für alles danach.
   - Betrieb: eigener Dienst (uvicorn als systemd-Dienst), nur auf localhost; Apache leitet `/api/` dorthin weiter. Abhängigkeiten in einer festen virtuellen Umgebung mit gesperrten Versionen.
5. **[VORSCHLAG] Oberfläche: Vue 3 + Apache ECharts** (ECharts ist bestätigt). Für die Stockkarte am Bienenstand als installierbare Web-App mit Offline-Zwischenspeicher, weil das Handy am Stand nicht immer Netz hat. **[PRÜFEN]** Netz am Stand.
6. **[VORSCHLAG] Datensicherung:**
   - Täglicher `pg_dump` plus Rohprotokolle auf ein zweites Medium.
   - Wiederherstellung einmal pro Quartal testen.
   - Voraussetzung für die Abschaltung von BEEP.

---

## 4a. Rohprotokoll (Raw-Ingest) – Anforderungen

Ist-Stand, geprüft am Quelltext (Commit `c5e998e`):
- `lora_eingang.php` schreibt jede Uplink-Nachricht **vollständig** (`'nachricht' => $msg`) in `lora_log/JJJJ-MM.jsonl`, und zwar **vor** der Verarbeitung, auch bei unbekanntem Gerät.
- `wetter_eingang.php` ebenso in `wetter_log/`.
- **Aber:** Beide Logfunktionen unterdrücken Schreibfehler (`@file_put_contents`, kein Rückgabewert). Ein Fehler beim Rohprotokoll bleibt unbemerkt, während die Verarbeitung weiterläuft.
- Eingaben über 64 KiB werden abgeschnitten (für TTN-Uplinks unkritisch, aber nicht geprüft).
- Rotation, Sicherung und Wiedereinspielen sind nicht getestet.

**[VORSCHLAG] Anforderungen R-1 bis R-6:**

| ID | Anforderung | Akzeptanz |
|---|---|---|
| R-1 | Jede Uplink-Nachricht wird vor jeder Verarbeitung unverändert mit Empfangszeit und Nachrichtenkennung angehängt | Test: 100 Nachrichten, davon 10 unbekanntes Gerät → 100 Zeilen |
| R-2 | Scheitert das Rohprotokoll, wird das sichtbar: Warnung in der Antwort an TTN und Eintrag im Fehlerprotokoll (wie SRV26-04) | Test mit schreibgeschütztem Verzeichnis |
| R-3 | Gleiches Format für alle Eingänge (LoRa, Wetter, Boden, BEEP Base) | Test je Eingang |
| R-4 | Monatsdateien werden nie umgeschrieben, nur angehängt; Prüfsumme je abgeschlossenem Monat | Prüfskript |
| R-5 | Wiedereinspielen: Importer liest ab gespeicherter Position, Dubletten über Kennung verworfen | Test: Import zweimal → gleiche Datenbank |
| R-6 | Rohprotokolle sind Teil der täglichen Sicherung | Rücksicherungstest |

## 5. Datenmodell – Kern 0.2

Tabellennamen deutsch, passend zum Drei-Tabellen-Modell vom 13.10. Alle Zeiten `timestamptz` in UTC; Zeiträume `[von, bis)`, `bis` NULL = offen.

### 5.1 Modul A – Stammdaten (Stand, Volk, Beute)

| Tabelle | Wichtige Felder | Regeln |
|---|---|---|
| `stand` | id, name, lage (Punkt), lage_oeffentlich (unscharf) | Genaue Koordinaten nie öffentlich |
| `volk` | id, name (z. B. „Volk 8“), entstanden_am, aufgeloest_am, status | Interne ID, nie aus BEEP- oder Logger-Nummer abgeleitet |
| `beute` | id, bezeichnung, beutentyp, rahmenmass, bemerkung | Physischer Beutenkörper; **[BESTÄTIGT]** eigene Identität |
| `beute_konfiguration` | beute_id, von, bis, brutzargen, honigzargen, rahmen, schied, gitter, notiz | Zargenaufbau über die Zeit; neue Zeile bei jeder Änderung |
| `belegung` | volk_id, beute_id, von, bis | **[BESTÄTIGT]** Beute = Volk: je Beute und je Volk keine Überlappung (1:1 zu jedem Zeitpunkt). Beim BEEP-Import automatisch angelegt |
| `aufstellung` | beute_id, stand_id, von, bis, platz (Reihenfolge am Stand) | Stand des Volks = Stand seiner Beute. `platz` für die Kachelreihenfolge |
| `volk_ereignis` + `volk_ereignis_teil` | art (ableger, vereinigung, schwarm, aufloesung), zeit; teil: volk_id, rolle (quelle, ergebnis, bleibt) | Herkunft n:m, z. B. Vereinigung aus zwei Völkern |
| `koenigin` | id, jahrgang, farbe, rasse, begattet, gezeichnet, geschnitten, herkunft_text, mutter_volk_id | Eigene Identität |
| `koenigin_volk` | koenigin_id, volk_id, von, bis, grund | Königinnenwechsel ≠ neues Volk |
| `extern_ref` | system (beep, bienenbuch, ttn), typ, extern_id, intern_typ, intern_id, von, bis | Z. B. BEEP-Hive 87155 → Volk 8 |

### 5.2 Modul B – Stockkarte

Ziel: BEEP-Checklisten fachlich übernehmen (vergleichbare Altdaten), aber versioniert und mit Zeiträumen.

| Tabelle | Wichtige Felder | Regeln |
|---|---|---|
| `merkmal` | id, code, name, eltern_id, eingabetyp (ja/nein, zahl, liste, text, datum, bewertung 1–5 …), einheit, optionen | Merkmalskatalog nach BEEP-Kategorien; **[PRÜFEN]** vollständige Liste der BEEP-Eingabetypen |
| `checkliste` / `checkliste_version` / `checkliste_merkmal` | name; version, gueltig_ab; reihenfolge, pflicht | Eine geänderte Vorlage erzeugt eine neue Version; alte Antworten behalten ihre Bedeutung |
| `durchsicht` | id, volk_id, zeit, erfasst_am, checkliste_version_id, notiz, quelle (eigen, beep_import) | Zeit immer mit Uhrzeit. Durchsicht mehrerer Völker = mehrere Zeilen mit gleicher Zeit |
| `durchsicht_wert` | durchsicht_id, merkmal_id, wert_zahl / wert_text / wert_option | Antworten |
| `massnahme` | id, volk_id, art, **von, bis**, quelle, menge, einheit, mittel, konzentration, notiz, durchsicht_id | Zeitraumereignisse für die Diagrammlinien und -bänder: Behandlung, Fütterung, Ernte, Zargen auf/ab, Umsetzen, Waage tarieren |
| `varroa_messung` | volk_id, von, bis, methode (windel, puderzucker, auswaschung), milben, bienen_probe, anmerkung | Milbenfall pro Tag wird berechnet, nicht gespeichert; eigene Tabelle, weil Hauptauswertung |
| `aufgabe` | volk_id oder stand_id, faellig_am, text, erledigt_am, quelle_durchsicht_id | Erinnerungen wie in BEEP |
| `anhang` | bezug (durchsicht, massnahme), datei_pfad, hash, aufgenommen_am | Fotos von Waben, Windeln usw. |

**Varroa:** Heute laufen Varroa-Werte als Merkmal 911 und Behandlungen als 595/845/904 in BEEP. Beim Import werden daraus `varroa_messung` und `massnahme`; im Export an BEEP wieder die BEEP-Kategorien. Das Mapping aus `beep-stockkarte-setup.md` wird dafür direkt verwendet.

### 5.3 Modul C – Messdaten

| Tabelle | Wichtige Felder | Regeln |
|---|---|---|
| `geraet` | id, dev_eui, name, art (stockwaage, beep_base, wetter, boden …), hersteller_modell, firmware | Physisches Gerät |
| `geraet_zuordnung` | geraet_id, volk_id **oder** stand_id, von, bis | Genau ein Ziel (CHECK). Je Gerät keine Überlappung. **[BESTÄTIGT]** max. ein primäres Stockmesssystem je Volk zur Zeit (keine Überlappung je Volk) |
| `messgroesse` | code, name, einheit, semantik (momentan, intervallsumme, spitze, zaehler, zirkulaer, status, merkmal), verdichtung, achse, farbe, darstellung | **Katalog = Register der Oberfläche.** Die Oberfläche kennt keine festen Sensorfelder |
| `messstelle` | id, volk_id **oder** stand_id, zone (brutnest, deckel, aussen_strahlungsschutz, boden, waage, elektronik), hoehe_cm, tiefe_cm | Bodensonden in drei Tiefen = drei Messstellen |
| `kanal` | id, geraet_id, quellfeld, messgroesse_code, messstelle_id, umrechnung, von, bis, status (geprueft, ungeprueft) | Deutung eines Quellfelds für einen Zeitraum. Neues Gerät oder neuer Sensor = neue Zeilen, kein Code |
| `messwert` | kanal_id, zeit, wert, qualitaet, zeitqualitaet, roh_ref | PK (kanal_id, zeit). Volk ergibt sich über kanal → geraet_zuordnung zum Zeitpunkt |
| `rohnachricht` | id (Nachrichten-ID des Eingangs), geraet_id, empfangen, messzeit_quelle, datei, zeile, hash | Verweis auf die JSONL-Protokolle, nicht deren Inhalt |

**Unbekannte Felder:** Ein Quellfeld ohne Kanal wird als Rohnachricht behalten, aber nicht als Messwert normalisiert. In der Oberfläche erscheint es unter Datenquellen als „unbenannt, noch nicht freigegeben“. Damit ist ChatGPTs offene Frage (ER-Modell §5.2) entschieden.

**Stockwaage am Volk:** Die Waage misst die Beute samt Inhalt (Messgrößen §3.1). Weil Beute und Volk 1:1 sind, wird sie dem Volk zugeordnet (siehe W1). Ändert sich das Leergewicht (Umsetzen, Zarge auf/ab, Tarieren), steht das als Maßnahme in der Stockkarte und wird nicht biologisch gedeutet (Leitplanke L8).

### 5.4 Modul D – Auswertung (vorbereitet, Tabellen später)

- **Berechnete Werte als Ansichten:** Tagesbilanz, Nachtgefälle, Tagesamplitude usw. nach `beelogger-datenanalyse-grundgeruest.md` §3.4–3.8 zunächst als SQL-Sichten bzw. Funktionen, nicht als Tabelle. Damit sind sie automatisch aktuell und nachvollziehbar.
- **Gespeicherte Ergebnisse, sobald Modelle laufen:** `analyse_lauf` (Version, Parameter, Zeitraum, Völker) und `analyse_ergebnis` (lauf, volk, fenster, art, wert, konfidenz, evidenz). Das entspricht ChatGPT §8, mit den Evidenzstufen [M]/[Q]/[E]/[H] aus dem Grundgerüst.

**Tabellenzahl:**
- Phase 1: rund **25 Tabellen**.
- ChatGPT-Entwurf: rund 35 plus Analyse- und Veröffentlichungsschicht.
- Drei-Tabellen-Modell: 3.

Der Zuwachs gegenüber dem 13.10. kommt fast vollständig aus der Stockkarte (Modul B), die jetzt zum Ziel gehört.

---

## 6. Oberfläche – das Beste aus BEEP und beelogger

| Funktion | Vorbild | Umsetzung |
|---|---|---|
| Beutensymbol mit Zargen, Farbe, Königin | BEEP | Aus `beute_konfiguration` und `koenigin_volk` erzeugt |
| Völker nach Stand, Kacheln und Liste | BEEP | Designentwurf v0.3, Seite 1 |
| Checklisten mit Kategorien, Durchsicht für mehrere Völker zugleich, Erinnerungen | BEEP | Modul B; Eingabe am Handy |
| Kurven frei wählbar, Zoom, relative Gewichte, Tageswerte und Summen | beelogger | Volk-Cockpit; Verdichtung je `messgroesse` |
| Anmerkungen direkt im Diagramm | beelogger | Durchsichten, Maßnahmen und Varroa als Linien bzw. Bänder |
| Zeitraumereignisse, Vorher/Nachher, Einträge ohne Uhrzeit gekennzeichnet | neu | Volk-Cockpit |
| Umwelt mit Boden, Wind und Regen | neu | Seite Umwelt & Tracht |
| Neue Sensoren ohne Programmierung | neu | Kanalregister (`kanal` + `messgroesse`) |
| Wochenbericht mit Evidenz und Konfidenz | Grundgerüst | Analyse-Jobs, später |

**Neue Seiten, die der Designentwurf noch nicht hat:**
- Stockkarte erfassen (Handy)
- Durchsichtsverlauf eines Volks
- Varroa-Übersicht des Standes mit Ampel
- Königinnen
- Verwaltung von Beuten und Belegung

---

## 6a. Zugriff und Veröffentlichung

**[BESTÄTIGT, 15.10.2026]**
- Die **interne Anwendung** (Dashboard, Volk-Cockpit, Stockkarte, Konfiguration) ist nur im **Heimnetz** erreichbar, ohne Zugang von außen.
- Die **Auswertung** wird **öffentlich ohne Login** auf `radeberger-honig.de` geteilt. Gezeigt wird nur eine **Übersicht**, nicht alle Daten.
- **Auswertungen und Studien** erscheinen auf einer eigenen Unterseite, ähnlich einem Blog.

**[VORSCHLAG] Umsetzung:**

| Teil | Wo | Wie |
|---|---|---|
| Datenempfang (TTN-Webhooks) | ThinkStation | Muss von außen erreichbar sein, weil TTN die Daten zustellt. Apache gibt **nur** `lora_eingang.php`, `wetter_eingang.php` und künftige Eingänge frei (Token wie heute). Alles andere: nur Heimnetz. **[PRÜFEN]** heutige Freigaben in Apache und Router |
| Interne Anwendung | ThinkStation | Apache: Zugriff nur aus dem Heimnetz-Adressbereich. **[BESTÄTIGT, 15.10., ADR-0003 Nr. 10]** Anmeldung auch im Heimnetz; Schreiben (Stockkarte, Konfiguration) nur angemeldet, mit CSRF-Schutz. Ein Konto, lange Sitzung auf dem eigenen Handy. Stockkarte am Stand über WLAN. **[PRÜFEN]** WLAN-Abdeckung am Stand (ca. 5–8 m vom Haus) |
| Öffentliche Seite | Webhosting für `radeberger-honig.de` | **[BESTÄTIGT, 15.10.: Variante B]** Die ThinkStation stellt eine **schmale öffentliche Lese-API** bereit, getrennt von der internen API. Sie liefert nur freigegebene Übersichtswerte als fertige Momentaufnahme, die alle 30 min neu berechnet wird (keine Datenbankabfrage je Besucher, keine frei wählbaren Parameter). **Variante B (gewählt):** Der Webhoster holt diese Werte alle 30 min ab und puffert sie; Besucher sprechen nur mit dem Webhoster. **Variante A:** Die Browser der Besucher fragen die API direkt ab. **[PRÜFEN]** Kann das Webhosting zeitgesteuerte Abrufe (Cron, PHP)? |
| Studien und Blog | dieselbe Webseite | Statischer Seitengenerator (z. B. Hugo oder Astro) mit Artikeln in Markdown; Diagramme mit ECharts aus einer eingefrorenen, versionierten Datendatei je Studie |

**Abwägung öffentliche Lese-API, Variante A und B:**

| | A: Browser fragen die ThinkStation direkt | B: Webhoster holt ab und puffert |
|---|---|---|
| Wer greift auf die ThinkStation zu | jeder Besucher | nur der Webhoster |
| Heimanschluss und Heim-IP | öffentlich sichtbar; Last hängt von der Besucherzahl ab | nur dem Webhoster bekannt; Last konstant |
| ThinkStation oder Internet zu Hause aus | Seite zeigt keine Werte | Seite zeigt den letzten Stand |
| Absicherung | Ratenbegrenzung, CORS, TLS mit DynDNS-Name | zusätzlich Token oder Freigabe nur für den Webhoster |
| Aufwand | geringer | ein Abrufskript beim Webhoster |

In beiden Varianten gibt es keinen direkten Datenbankzugriff von außen. Die ThinkStation ist ohnehin schon für die TTN-Webhooks von außen erreichbar; die Lese-API kommt als weiterer, eng begrenzter Endpunkt dazu.

**[VORSCHLAG] Inhalt der öffentlichen Übersicht:**
- Standwetter und Bodentemperatur
- Gewichtsverlauf und Tagesbilanz je Volk (Volksname, keine Stockkartendetails)
- Saisonkennzahlen
- Grober Ort („Radeberg“), keine Koordinaten
- **[OFFEN]** Werte mit Verzögerung veröffentlichen (z. B. 24 h), damit der aktuelle Zustand am Stand nicht live von außen sichtbar ist

**Nicht öffentlich:**
- Stockkarte, Durchsichten, Behandlungen, Varroa-Rohwerte, Königinnen
- Genaue Lage, Geräte-IDs, Funk- und Technikdaten
- Unbestätigte Analyseergebnisse

**Studien:** Jede Veröffentlichung bekommt einen eingefrorenen Datensatz mit Version, Zeitraum, Methode und Evidenzstufen nach dem Grundgerüst. Spätere Korrekturen ändern einen veröffentlichten Artikel nicht stillschweigend.

**Hinweis:** Eine öffentliche Webseite in Deutschland braucht Impressum und Datenschutzerklärung. Das ist keine Rechtsberatung; die Texte bitte vom Anbieter des Webhostings oder einem Generator prüfen lassen.

## 7. Migration und Ablösung von BEEP

**Grundsatz [VORSCHLAG]:** Zu jedem Zeitpunkt gibt es **genau eine führende Eingabestelle** für die Stockkarte. Ein Abgleich in beide Richtungen wird nie gebaut.

| Phase | Führende Eingabe | Was passiert | Abnahme |
|---|---|---|---|
| **A – Aufbau** | BEEP (Bienenbuch als Hilfsmittel) | PostgreSQL aufsetzen; Importer für Logger-, BEEP-Base-, Wetter- und Bodenprotokolle; einmaliger Import aus BEEP (Völker mit Beute, Königinnen, Checklisten, Merkmale, alle Durchsichten je Hive) | Anzahl Durchsichten je Volk = BEEP zum Importzeitpunkt (per Hive-Endpunkt gezählt); Stichproben stimmen |
| **B – Lesen** | BEEP | Oberfläche lesend: Dashboard, Volk-Cockpit, Umwelt. BEEP-Import regelmäßig (täglich), weiterhin nur lesend | Durchsichten erscheinen am richtigen Volk |
| **C – Umschaltung** | **eigene Stockkarte** | Eingabe nur noch auf der Plattform, mit Uhrzeit; ein Export schreibt einseitig nach BEEP (wie heute `desired.py`), damit die BEEP-Gruppe weiter Daten sieht. Bienenbuch entfällt | 4 Wochen ohne Abweichung; Sicherung und Wiederherstellung getestet |
| **D – BEEP aus** | eigene Stockkarte | Export abschalten, BEEP-Konto archivieren (Excel- und CSV-Export als Archiv) | Rücksicherungstest; alle BEEP-Base-Daten auch lokal vorhanden |

**BEEP Base (je Gerät, nacheinander):**
1. Bestand aufnehmen: Hardwareversion, Firmware, DevEUI, Sensoren. **[PRÜFEN]** Laut ChatGPT-Strategie nennt BEEP für die eigene TTN-Applikation eine Mindestfirmware; im Rahmen dieses Konzepts nicht selbst geprüft.
2. **[BESTÄTIGT als Ziel, Inbetriebnahme nicht nachgewiesen]** Base 1 in die eigene TTN-Applikation, zwei Webhooks (eigener Eingang und BEEP). Rückfallplan: Base wieder in der BEEP-Applikation registrieren.
3. Zwei Wochen Daten vergleichen, dann Base 2.
4. **[PRÜFEN]** Was die Base über Funk sendet (Kanäle, FFT-Bänder, Einheiten): erst an echten Nachrichten festlegen, keine Feldliste annehmen (so auch ChatGPT, Kanalinventar §7).
5. **[PRÜFEN]** Offline gespeicherte Base-Messungen (Auslesen über Bluetooth und BEEP-App) gibt es nur über BEEP. Vor Phase D braucht es dafür einen eigenen Weg oder den Verzicht darauf.

**Bienenbuch:** Kein Import. Alle Inhalte sind bereits in BEEP. Es wird bis zur Umschaltung als Hilfsmittel weitergeführt und entfällt danach.

---

## 8. Zusätzliche Akzeptanzfälle (ergänzen ER-01 bis ER-17)

| ID | Fall | Erwartet |
|---|---|---|
| K-01 | BEEP-Hive 87155 „Volk 8“ importieren | Volk 8 mit `extern_ref`; dazu eine Beute (Segeberger 1,5, 1 Brutzarge) mit Belegung |
| K-02 | Volk 3 (vereinigt, grauer Hive) | Volk mit `aufgeloest_am` und Ereignis „vereinigung“ mit Zielvolk; Belegung seiner Beute endet |
| K-03 | Importierte Durchsicht 07.10. (12:00 aus dem Übertragungsskript) | `quelle = beep_import`; Oberfläche zeigt „Uhrzeit übernommen“; Uhrzeit korrigierbar |
| K-04 | AS-Verdunster Volk 8 vom 01.10. bis 11.10. | Eine `massnahme` mit von/bis; Diagramm zeigt ein Band |
| K-05 | Neue Bodensonde (LSN50v2-D23) | Drei `messstelle` + drei `kanal`; erscheint ohne Codeänderung im Cockpit. **[BESTÄTIGT, 15.10.]** Einbautiefen 5 cm (weiß), 20 cm (rot), 50 cm (schwarz); Zuordnung Kabelfarbe ↔ Decoderfeld an echten Daten prüfen |
| K-06 | Quellfeld ohne Kanal | Rohnachricht vorhanden, kein Messwert, Anzeige „unbenannt“ |
| K-07 | Inspektionen eines Volks > 1000 BEEP-Einträge gesamt | Import über `/inspections/hive/{id}` vollständig |
| K-08 | Waage tariert | `massnahme` „tarieren“; Gewichtssprung wird nicht biologisch gedeutet (Leitplanke L8) |
| K-09 | Datenbank zwei Tage aus | Nach Neustart importiert der Importer alle Nachrichten aus den Protokollen, ohne Dubletten |
| K-10 | Checkliste „Herbst/Winter“ 2027 geändert | Durchsichten 2026 behalten ihre alte Version und Bedeutung |

---

## 9. Offene Entscheidungen für Philipp

1. **Zielbild bestätigen:** Stockkarte zieht auf die eigene Plattform (ersetzt Ä1 und Ä2).
2. **Öffentliche Übersicht:** Inhalt wie in §6a vorgeschlagen? Mit Verzögerung (z. B. 24 h)?
3. **Umschaltpunkt:** Phase C zum Saisonstart 2027 (vor der ersten Frühjahrsdurchsicht) oder schon im Winter?
4. **BEEP Bases:** Wann und welche zuerst umziehen?

Geklärt am 15.10.: Beute = Volk (1:1), Bienenbuch nur Hilfsmittel ohne Import, BEEP Base an beide Server, Stockwaage am Volk, Python für API und Analyse, alles auf der ThinkStation mit PostgreSQL, interne Anwendung nur im Heimnetz, öffentliche Übersicht und Studien ohne Login auf radeberger-honig.de, öffentliche Lese-API nach Variante B (Webhoster holt alle 30 min ab und puffert), Waage bleibt am Volk (nach Review bestätigt), Anmeldung auch im Heimnetz, Bodensonden 5/20/50 cm (weiß/rot/schwarz).

---

## 10. Nächste Schritte

| Nr. | Schritt | Wer | Voraussetzung |
|---|---|---|---|
| 1 | Entscheidungen §9 | Philipp | – |
| 2 | Schema 0.2 als SQL-DDL mit Tests der Akzeptanzfälle (wie `kiss_modell_test.py`, gegen PostgreSQL) | Claude | 1 |
| 3 | BEEP-Import lesend: Völker, Königinnen, Checklisten, Merkmale, Durchsichten | Claude | 2, BEEP-Token lokal |
| 4 | Importer für die vorhandenen Logger- und Wetterprotokolle | Claude | 2 |
| 5 | Lese-API und Oberfläche Phase B (Dashboard, Cockpit) mit echten Daten | Claude | 3, 4 |
| 6 | Stockkarte erfassen (Handy) | Claude | 5 |
| 7 | BEEP Base 1 in eigene TTN-Applikation | Philipp | Firmware geprüft |

Die ChatGPT-Dokumente in `docs/architektur/` bleiben als Fachgrundlage erhalten. Abweichungen sind oben in §2 und §3 begründet. Bei Abnahme sollten Anforderungen §2 und §3.1 (BEEP Base, führende Stockkarte) mit Datum nachgeführt werden.

---

## 11. Review Issue #11 (ChatGPT, 15.10.2026) – Bewertung und Maßnahmen

Prüfbericht: `docs/testberichte/2026-10-15-plattform-review-issue11.md`; Befunde PLT26-01 bis PLT26-10 im Befundregister.

| Nr. | Einwand | Bewertung | Maßnahme |
|---|---|---|---|
| P1-1 | 1:1-Regel zu stark; BEEP-Hive→Volk nur als Heuristik | **teilweise bestätigt.** Die Gegenrichtung war offen und ist seit 15.10. vom Betreiber entschieden; das fehlte als datierter Beschluss. Heuristik-Hinweis berechtigt | ADR-0003; Text W1 präzisiert; Tests HB-02/HB-03 (leer, neu besetzt) |
| P1-2 | Kein nachgewiesener verlustfreier Raw-Ingest | **teilweise bestätigt.** Die Behauptung, der LoRa-Weg protokolliere nicht jeden Uplink, stimmt nicht (vollständig vor Verarbeitung). Richtig: Schreibfehler werden verschluckt, Replay und Sicherung ungetestet | §4a, R-1 bis R-6; PHP-Änderung als eigener Befund PLT26-02 |
| P1-3 | Waage physisch ≠ logische Zuordnung zum Volk | **bestätigt als offene Frage.** Bei Zuordnung zum Volk muss ein Auszug von Hand beendet werden (HB-09) | Prüfsicht `pruefung_geraet_zuordnung`; Tests HB-01 bis HB-04, HB-09; Option B „Waage am Platz“ zur Entscheidung (§9 Nr. 5) |
| P1-4 | Heimnetz ersetzt keine Anmeldung beim Schreiben | **bestätigt** | §6a: Schreiben nur mit Login (Entscheidung §9 Nr. 6) |
| P2-5 | Synthetische 12:00 nicht als exakte Zeit anzeigen | **bestätigt** (eigene frühere Lösung über `quelle` reicht nicht) | Feld `zeitgenauigkeit` in Schema 0.3; Test |
| P2-6 | Sensorwechsel und Kalibrierung nicht ganz aufschieben | **bestätigt** | `kanal` um `kalibriert_am`, `kalibrierung`, `sensor` ergänzt; Wechsel = neue Kanalzeile mit Zeitraum |
| P2-7 | BEEP Base: Ziel ≠ Inbetriebnahme | **bestätigt** | Kennzeichnung §7, Rückfallplan |
| P2-8 | Provenienz abgeleiteter Werte | **bestätigt** | Tabelle `berechnung` mit Version; Sichten liefern `berechnung@version`; Test |
| P2-9 | BEEP-Import gehört in einen autorisierten Integrationstest; 512 nur Momentaufnahme | **bestätigt** | Wortlaut §3.4/§7 geändert; Integrationstest Teil des Importer-Schritts |
| P2-10 | Bodentiefen nicht verallgemeinern; GTS aus Lufttemperatur | **bestätigt**; Tiefen 5/20/50 cm von hier nicht prüfbar | K-05 als [PRÜFEN]; Testdaten sind Platzhalter |

Schema 0.3: 24 von 24 Tests bestanden (PostgreSQL 16.15, Testinstanz, Sitzungszeitzonen Europe/Berlin und UTC). Keine Produktivprüfung.

**Zu P1-3, Optionen für die Waage:**

| | A: Waage am Volk (Stand 15.10.) | B: Waage am Platz |
|---|---|---|
| Modell | `geraet_zuordnung` → Volk | Waage fest an einem Platz am Stand; Volk ergibt sich aus Platz → Beute (`aufstellung`) → Volk (`belegung`) |
| Umsetzen in neue Beute auf derselben Waage | nichts zu tun | neue Belegung (ohnehin über die Stockkarte „Umsetzen“) |
| Volk zieht weg, Waage bleibt (HB-09) | Zuordnung muss von Hand beendet werden; Prüfsicht warnt | automatisch richtig, sobald Aufstellung/Belegung stimmt |
| Pflege | zwei Stellen: Belegung und Gerätezuordnung | eine Stelle: wo steht welche Beute mit welchem Volk |
| Aufwand im Schema | vorhanden und getestet | zusätzliche Tabelle `platz`, Umbau der Sicht `messwert_bezug` |

Empfehlung von Claude war B. **Entscheidung Philipp (15.10.): A bleibt**, weil der Aufwand überschaubar ist und sich das Verfahren bei BEEP bewährt hat. Absicherung: Die Prüfsicht `pruefung_geraet_zuordnung` meldet vergessene Zuordnungen; die Oberfläche zeigt diese Meldungen an.

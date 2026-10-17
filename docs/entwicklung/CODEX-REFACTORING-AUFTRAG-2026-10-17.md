# Bienenlogger – verbindlicher Refactoring-Auftrag für Codex

**Stand:** 17.10.2026 · **Status:** fachlicher Refactoring- und Abnahmeauftrag, keine Implementierungs- oder Produktivfreigabe  
**Repository:** https://github.com/impyer/bienen-lora-logger  
**Ausgangsbasis:** Branch test/thinkstation-lan-20261017, Commit 034c9e1d31612679dcc3cc15155208b9c0c82e72  
**Installierte Testumgebung:** Ubuntu 22.04.5 LTS / x86_64, Docker 29.9.1, Docker Compose v5.6.0, ThinkStation 192.168.178.41, Test-HTTPS-Port 9443 (nur Heimnetz).  
**Verbindliche Prozessregeln:** [AGENTS.md](../../AGENTS.md), [CLAUDE.md](../../CLAUDE.md), [Entwicklungsregelwerk](regelwerk.md), [Entscheidungsregister](entscheidungen.md), [Befundregister](../testberichte/befunde.md), [Testgates](tests-freigaben.md).  
**Fachquellen:** [Plattformkonzept](../architektur/konzept-plattform-v02.md), [Datenplattform-Anforderungen](../architektur/anforderungen-datenplattform.md), [Beute/Volk/Stand](../architektur/beute-volk-stand-beziehungen-v01.md), [Messkontext/Zeitqualität](../architektur/messreihe-messkontext-zeitqualitaet-v01.md), [Stockkarten-Teststrategie](stockkarte-teststrategie.md), [Heimnetz-Vorabnahme](../testberichte/thinkstation-heimnetz-vorabnahme-20261017.md), [Issue #15](https://github.com/impyer/bienen-lora-logger/issues/15), [Issue #19](https://github.com/impyer/bienen-lora-logger/issues/19).

## 0. Anlass, Urteil und Definition von fertig

Der reale Bedienertest vom 17.10.2026 hat **Start, HTTPS vom Laptop, Anmeldung und Anzeige zweier Testvölker** bestätigt. Gleichzeitig wurden die Anmeldung als umständlich und die Stockkarte als **deutlich unvollständiger und anders bedienbar als BEEP** beanstandet. Die technisch grünen Tests belegen folglich **weder Fachparität noch eine funktionsfähige Gesamtplattform**. Ziel ist nicht kosmetisches Aufräumen, sondern **ein nachweislich zusammenhängendes, wartbares, erweiterbares und fachlich korrektes System**.

**Fertig** bedeutet: Eine reale, autorisierte Messung gelangt über eine eindeutig definierte, nachvollziehbare Quelle in den eigenen Datenbestand, ist im Browser am richtigen Stand/Volk und im passenden Diagramm sichtbar, bleibt nach Neustart erhalten und wird mit echten Komponenten Ende-zu-Ende getestet. Danach muss dasselbe Qualitätsniveau für die eigenständige Stockkarte erreicht werden. Eine schön gerenderte, isolierte Demo zählt nicht als Fertigstellung.

## 1. Quellwahrheit und Umgang mit Widersprüchen

1. **An erster Stelle stehen zuletzt ausdrücklich bestätigte Betreiberentscheidungen und angenommene ADRs.** Danach gelten Anforderungen, neuere Architekturkonzepte und schließlich bestehender Code; der Code ist kein Beweis fachlicher Richtigkeit.
2. Unterschiede im Repository **vor dem Umbau in einer Entscheidungsliste erfassen**: z. B. ältere Vorgabe „BEEP bleibt dauerhaft führend“ vs. neuer bestätigter Plan „BEEP parallel, schrittweise eigene führende Stockkarte“; „BEEP Base nur an BEEP“ vs. später beschriebener eigener TTN-Eingang im Parallelbetrieb. Nicht stillschweigend eine Variante wählen.
3. **Bestätigt:** BEEP läuft parallel weiter, bis Import, eigene Bedienung, Auswertung und Sicherung tatsächlich abgenommen sind. Fremde BEEP-UI **nicht einbetten, nicht kopieren**; BEEP ist eine fachliche Referenz für Datenmodell, Kategorien, Checklisten und Arbeitsabläufe.
4. Technologiewahl: **Python/FastAPI und PostgreSQL** als bestätigte Datenplattform, bestehende **PHP-Empfänger unverändert**, **Apache ECharts** als bestätigte Diagrammbibliothek. **Vue 3** ist bislang Architekturvorschlag, nicht ohne ADR als zwingender Komplettumbau zu behandeln.
5. Keine stillschweigende Datenmigration und keine Behauptung „vollständige BEEP-Parität“, solange die Taxonomie, Eingabeformen und Historienfunktionen nicht wirklich nachgewiesen sind.

## 2. Belegte Ist-Defizite – Diagnose, keine spekulative Fehlerbehauptung

| Kennung | Befund / überprüfbare Quelle | Konsequenz |
| --- | --- | --- |
| RF-01 | prototype/claude-ui/app.js führt lokale Entwürfe in localStorage, feste Beispielvölker und manuell hinterlegte Demo-/Einzelwerte; produktive PostgreSQL-Völker sind nicht dieselbe Datenquelle. | Eine verbindliche Datenquelle pro Entität; Demo explizit getrennt. |
| RF-02 | prototype/claude-ui/stockkarte_live.js öffnet Server-Stockkarte in einem separaten Modal inklusive Login/Volkauswahl; stockkarte_edit.js ist primär Durchsichteneditor. | Ein gemeinsames, nutzerfreundliches Login und durchgängige Navigation ohne konkurrierende Stockkarten. |
| RF-03 | prototype/claude-ui/app.js verwendet eigene chartSVG-Funktion; Umweltansicht zeigt statische Bodentemperatur-Einzelwerte und keine live geladenen Reihen. | Reale, API-gespeiste ECharts mit korrekter Zeit-/Einheitensemantik. |
| RF-04 | Das aktive Docker-Compose enthält PostgreSQL, FastAPI-Stockkartenserver und Caddy, aber **keinen konfigurierten Wetter-/beelogger-Dateiimport** in das Test-Dashboard. | Eigener, lesender Import-/Abfragepfad und Messreihen-API. |
| RF-05 | server/datenbank/stockkarte_admin.py seed-demo erzeugt nur zwei synthetische Völker und einen kleinen Beispielkatalog; keine komplette BEEP-Taxonomie. | Keine Fachparitätsbehauptung; autorisierte Referenzdaten und funktionale Katalogtests erforderlich. |
| RF-06 | CI-Vorabnahme meldet grüne Tests für isolierte Teilfunktionen; UI-Browsertests arbeiten teilweise mit simulierten API-Antworten. | Zusätzlich Browser-E2E **mit echter API, echter PostgreSQL-DB und echtem HTTPS**. |
| RF-07 | server/datenbank/schema.sql enthält DROP SCHEMA; die Testinitialisierung ist bewusst auf eine neue Wegwerf-Datenbank begrenzt. | Niemals ungeschützt gegen Bestandssysteme; additive, versionierte Migrationen und Wiederherstellungstests. |

**Nicht belegt:** genereller Defekt jeder Codezeile, konkrete Leistung unter Last oder fehlende Hardwarefunktion. Codex muss Befunde nachprüfen statt sie zu erfinden. Der Feldtest belegt dagegen klar: **fachliche Gesamt-Abnahme verfehlt**.

## 3. Unverhandelbare Randbedingungen

### 3.1 Bestandsschutz und Isolation

- Bestehende TTN-Webhooks, LoRa-Empfang, Wetterstation, Bodensonde, beelogger M.40, Apache und produktive CSV/JSONL **nicht verändern, anhalten, löschen, umbenennen oder migrieren**, sofern dafür keine separate explizite Freigabe erteilt wird.
- **Keine Hardware-/Firmwareänderungen** im Rahmen dieses Web-/Backend-Refactorings. Git-Bereiche firmware/, hardware/, mechanik/ und produktive Formatter bleiben unberührt; bestehende Kompatibilitätsverträge gelten.
- Heimnetz-Teststack getrennt auf der ThinkStation belassen, derzeit **192.168.178.41:9443**; Apache belegt **8443**. Keine Portweiterleitung, keine Veröffentlichung im Internet.
- Docker-Datenvolumes, Benutzer, Rechte, lokale CA und Demo-Datensätze erhalten. **Niemals docker compose down -v.** Bestehende Schemata nicht mit schema.sql überschreiben.
- Reale Quelldaten **nur lesend** einbinden: zuerst Inventur/Pfade/Dateirechte, dann eng begrenzte Read-only-Mounts bzw. explizite Konfiguration. Keine automatische Freigabe des gesamten /var/lib, /var/www oder /srv. Originale und Importprovenienz bewahren.
- Keine Zugangsdaten, BEEP-Tokens, DevEUIs, privaten Stockkartendaten oder nicht freigegebene Standorte nach GitHub/CI. Nur anonymisierte bzw. synthetische Test-Fixtures.
- Vor jedem Eingriff in Laufzeitdaten **verifiziertes Backup mit separatem Restore-Test**, bei relevanter Änderung mit dokumentiertem Rollback/Releaseverfahren.
- Erweiterungen/Refactoring **auf separatem Feature-Branch und über PR**; keine automatische Aktualisierung der ThinkStation und kein Merge auf main ohne Betreiberprüfung.

### 3.2 Fachliche Identitäten und Beziehungen

- **Bienenstand**, **Volk**, **physische Beute**, **Königin**, **Gerät**, **Messstelle**, **Sensor/Messkanal**, **Messgröße** und **Quelle** haben eigene stabile IDs. Kein Volk-ID-Recycling; keine Ableitung der fachlichen ID aus BEEP-ID, Gerätenummer oder Beutenname.
- Ein Ableger bekommt **eine neue Volk-ID mit dokumentierter Muttervolk-Herkunft**; Vereinigungen können mehrere Herkunftsvölker besitzen. Königinnen-/Gerätewechsel ändern die Volk-ID nicht.
- **Eine Beute hat zeitgleich höchstens ein Volk; ein Volk höchstens eine aktive Beute.** Standort-, Beuten-, Königinnen- und Gerätezuordnungen historisiert mit Intervallen (von einschließlich, bis ausschließlich).
- **Höchstens ein primäres Stockmesssystem je Volk und Zeitpunkt**: BEEP Base oder klassischer beelogger oder eigener beelogger oder keines. Zusätzliche Sensoren für andere Messgrößen sind erlaubt. Ein prinzipiell erweiterbares Datenmodell darf Duo/Triple-Messgeräte ermöglichen, ohne solche Geräte als vorhanden vorauszusetzen.
- Unabhängig vom primären Gerät kann jedes Volk eine digitale Stockkarte haben.
- Nicht erfasst, 0, false und unbekannt sind unterschiedliche Zustände. Niemals Nullwerte zu scheinbaren Messungen umdeuten.

### 3.3 Zeit, Qualität, Nachvollziehbarkeit

- Rohzeitpunkte in **UTC**, Darstellung und imkerliche Tagesreferenz in **Europe/Berlin**; Sommer-/Winterzeit und doppelte Stunde zuverlässig behandeln.
- Ereigniszeit, Messzeit, Empfangszeit und Importzeit sauber trennen. Ein Datum ohne echte Uhrzeit bleibt **nur Datum**; keine erfundene 12:00-Uhr-Messzeit. Exakt/geschätzt/nur Datum bei stockkartenbezogenen Ereignissen verwalten.
- Zeitreihen behalten Quelle, Gerät, Feldnamen, Kanalbelegung zum Messzeitpunkt, Messstelle/Stand/Volk-Zuordnung, Einheit, Rohwert, Umrechnungs-/Kalibrierversion und Qualitätsmerkmale. Gerätetausch und Kalibrierwechsel historisieren.
- Import **idempotent**, wiederholbar und nachholbar; Dubletten vermeiden, Unterbrechungen/Lücken/fehlerhafte Zeitstempel sichtbar melden. Niemals Daten stillschweigend glätten oder fiktive Punkte erzeugen.
- Roh-Nachrichten nicht ersetzen; bereits vorhandene JSONL/CSV-Quellen bleiben unverändert. Keine stillschweigende Zuordnung fremder Geräte zu Völkern aufgrund eines zufällig passenden Namens.
- Korrekturen und Importupdates müssen provenance-/revisionsfähig sein. Eine Datenkorrektur darf Rohdaten und historische Revisionen nicht zerstören.

## 4. Zielarchitektur und Modulgrenzen

**Verbindliches Verhalten, keine erzwungene neue Framework-Wahl:**

~~~text
Bestehende produktive TTN-/PHP-Empfänger ──> CSV / JSONL / beelogger M.40
                                                  │  NUR LESEN
                                                  ▼
                                      Quelladapter / idempotenter Import
                                                  ▼
                              PostgreSQL (Stammdaten, Katalog, Zeitreihen,
                                 Herkunft, Zuordnung, Revision, Ereignis)
                                                  ▼
                                    Python-FastAPI (Versionierte APIs)
                                      │                      │
                              Messreihen-API          Stockkarten-API
                                      └──────────┬───────────┘
                                                 ▼
                          Eine authentifizierte Bienenlogger-Webanwendung
                            ECharts + Volk-Cockpit + Umwelt + Stockkarte
~~~

**MUSS:**
1. Verantwortlichkeiten trennen: Parser/Adapter; Validierung/Normierung; Domänenmodell; Datenzugriff/Repository; Authentifizierung/Autorisierung; HTTP-API; Frontend-Darstellung; Tests.
2. **Eine kanonische Identität und API für Stammdaten**: keine lokale zweite Volk-Liste neben den PostgreSQL-Völkern. Offline-Daten ausschließlich als ausdrücklich markierter Demo-Modus, nie gleichzeitig ohne Kennzeichnung mit Echtdaten vermischt.
3. Konfigurierbares Sensor-/Kanalregister: neue Geräte, zusätzliche Kanäle und Messstellen hinzufügen **ohne fest verdrahtete IDs im Frontend oder Änderungen an jeder Diagrammkomponente**.
4. Einheitliche, dokumentierte, versionierte API-Verträge mit stabilen DTOs/Schemata, begrenzter Paginierung und Zeitfenstern, verständlichen Fehlerantworten, OpenAPI und rückwärtskompatiblen Migrationen.
5. Komponenten testbar ohne laufende echte Geräte; deterministische, anonymisierte CSV/JSONL-Beispiele; eindeutige Trennung von Demo-, Test- und Produktionskonfiguration.
6. Kein vollständiges Neuschreiben nur aus ästhetischen Gründen. **Strangler-/Vertical-Slice-Vorgehen**: kleine, vollständige Wege vom Datenursprung bis zum Browser, danach alte doppelte Pfade kontrolliert entfernen. Bestehende gute Funktionalität und M.40-Kompatibilität erhalten.
7. Dependencies kontrolliert pinnen/locken, keine unnötigen zusätzlichen Laufzeitdienste; dokumentierte Entwicklungs- und Betriebsanleitung.

### 4.1 Mindest-API-Semantik

- Stammdaten: Stände, Völker, Beuten-/Geräte-/Messstellen-/Kanalzuordnungen einschließlich Gültigkeit und Rechte.
- Messdaten: Abfrage nach Messgröße/Kanal, Volk oder Stand, Zeitraum, Zeitzonenbezug, Roh-/verdichtete Auflösung; Metadaten enthalten Einheit, Quelle, Zeitqualität, Zähler- und Aggregationssemantik, Datenlücken und QC.
- Ereignisse: Stockkarte, Behandlungen, Fütterungen, Königinnen- und Geräteaustausch sowie weitere Annotationen separat von Sensormessungen. Historische Korrekturen als neue Revision.
- Kennwerte: gemessen, berechnet und modelliert **getrennt kennzeichnen**, Ergebnisversion und Berechnungsbasis nennen.
- HTTP-Fehler mit nachvollziehbaren Statuscodes (u. a. 401, 403, 404, 409, 422), keine Roh-Tracebacks oder Secrets gegenüber dem Client.
- Geeignete Grenzen und Indizes für größere Zeiträume/Millionen Messwerte, stabile Sortierung und skalierbare Verdichtung. Keine unkontrollierte Vollabfrage aller Rohdatensätze.

## 5. Priorität P0 – zuerst echte Umweltdaten und Volk-Charts

**Diese Priorität folgt ausdrücklich der neuen Betreiberanweisung und hat Vorrang vor der optischen Stockkarten-Überarbeitung.**

### 5.1 Read-only-Quellinventur und Adapter

**Wetterstation S2120:** Quelle gemäß server/wetter/: Semikolon-CSV mit zeit_utc, stand, station, t, h, p_hpa, l, uv, wind_ms, wind_dir_deg, gust_ms, rain_mmh, rain_mm, battery_pct, interval_min und Telemetrie. Keine falsche Aufsummierung des rain_mm-Zählers bei unbekanntem Reset; Windrichtung als zirkulärer Wert behandeln.

**Bodentemperatursensor:** Betreiber-Nachweis für Datei
/var/lib/bienen-logger/boden/hauptstand/erdboden-temperatur_2026-10.csv
mit Header time_utc;stand;device_id;temp_5cm;temp_20cm;temp_50cm;battery_v;alarm_status;f_cnt;f_port;rssi;snr;payload_base64;message_id.
Pfad ist ein **belegtes Beispiel**, kein frei erfundener universeller Pfad. Drei Tiefen sind getrennte Messkanäle mit Tiefen-/Positionsmetadaten an einem Standort, nicht drei separate Stockmessgeräte.

**beelogger:** Bestehende week.csv / lora_zusatz.csv / lora_log/*.jsonl gemäß server/lora/; **echte Dateipfade und Feldbelegung erst auf der ThinkStation ermitteln**. Kein aus Aux1/2/3 blind erschlossener Messwert; Gewicht ausschließlich bei belegter Kalibrierung als kg anzeigen. BEEP-Base-Daten erst integrieren, wenn der eigene Empfang bzw. eine autorisierte Quelle auf dem Zielsystem bestätigt ist.

**Verarbeitung:** Konfiguration pro Quelle, idempotenter Import mit Checkpoint, Datums-/Dezimal-/CSV-Fehlerbehandlung, Leerwerte, veränderliche Dateien und Backfill. Änderungen an Quelldateien sollen ohne Eingriff in die produktive Erfassung nachvollziehbar im Testbestand ankommen. Ein einfaches regelmäßiges Lesen ist zunächst zulässig, sofern korrekt, sicher, performant und dokumentiert.

### 5.2 Diagramme / UX für diesen Schritt

- Apache ECharts für produktive Diagramme; SVG-Altgrafiken nicht als Ersatz für vollständige Diagrammfunktion ausgeben.
- **Umwelt:** Wettertemperatur, Luftfeuchte, Druck, Wind, Regen und Bodentemperaturen 5/20/50 cm, mit Einheiten, Quell-/Zeitangaben und geeigneten Skalierungen. Keine Scheingenauigkeit bei seltenen Messungen.
- **Volk:** Gewichts-, Temperatur- und, soweit vorhanden, relative FFT-/Akustikkanäle; pro Volk und Messquelle auswählbar, echte Leerzustände bei fehlenden Kanälen.
- **Stand- und standübergreifender Vergleich:** mehrere Völker und Stände mit gemeinsamer Zeitachse; geeignete synchronisierte Einzelspuren oder getrennte Y-Achsen bei inkompatiblen Einheiten.
- Interaktion: 24 h, 7 Tage, 30 Tage, Saison/freier Zeitraum; Zoom, Pan, Legende, Tooltip mit Europe/Berlin, Herkunft, Kanal und QC; mobile Ansicht; begrenzte Datenmengen.
- Einspeisung der Rohwerte plus fachlich begründete Verdichtung (z. B. Tagesreferenzgewicht aus gültigen Nachtwerten und Tagesbilanz nur zwischen aufeinanderfolgenden Tagen). Aggregation muss dokumentiert und getestet sein.
- Fehlende Messungen **als Lücke**, nie als 0; keine verbundenen Linien über fachlich relevante lange Ausfälle. Grafiken dürfen keine Simulation oder historischen Einzelwerte als aktuelle Livemessung ausgeben.
- Ein neu eintreffender Testmesswert muss mit dokumentiertem Aktualisierungsintervall im Browser sichtbar werden; Datenbestände auch nach Container-Neustart vorhanden.

## 6. Priorität P1 – eine benutzbare Oberfläche statt paralleler Prototypen

1. **Einmaliger Login** als eigenständige, gut erkennbare Seite oder eingebetteter Hauptdialog, nicht erst über „Stockkarte → Server-Stockkarte ansehen“. Danach sehen eingeloggte Benutzer nur freigegebene Völker/Stände; Ablauf/Abmeldung klar kommunizieren.
2. Navigation und Funktionen basieren auf **demselben serverseitigen Datenmodell**: Bienenstand/Völkerübersicht (pro Volk eine Kachel), Volk-Cockpit, Umwelt & Tracht, Datenquellen & Kanäle, Analysen & Vergleich, digitale Stockkarte und Beuten-/Königinnenverwaltung.
3. Kein hartcodiertes Demo-Volk 8 oder feste 11 Völker als produktive Liste. Dynamische Völker-/Standauswahl und Sensorzuordnung. Die Oberfläche ist durch neue Geräte/Quellen ohne strukturelle Frontend-Änderungen erweiterbar.
4. Desktop und Mobiltelefon am Bienenstand: große Eingabeflächen, tastatur- und touchbedienbar, verständliche Beschriftungen, sichtbarer Speicherstatus, Fehlermeldungen, Vor-/Zurück, Abbrechen ohne unbeabsichtigten Verlust.
5. Anwendungszustand (Login, gewählter Stand/Volk, Zeitraum) konsistent; keine Modalschachtelung und kein Wechsel zwischen zwei unabhängigen Datenwelten. Klare Unterscheidung zwischen Datenbankstand, lokalem Offline-Entwurf und Demonstration.
6. Vorhandene Gestaltungsvorlage mit horizontaler Navigation respektieren, aber fachlich fehlerhafte UI bewusst korrigieren. Nicht nur statische Screenshots oder Mock-Grafiken liefern.

## 7. Priorität P2 – eigenständige Stockkarte mit BEEP als überprüfbarer Referenz

**BEEP darf nicht eingebettet werden.** Funktionelle Parität bedeutet eigene Implementierung entsprechender Workflows anhand autorisiert ausgelesener Taxonomie und überprüfter Quellreferenzen; keine bloße optische Ähnlichkeit.

- **Volk bearbeiten:** Stammdaten, Status, Notizen, Historie; neue Ableger mit Herkunft; Volk-ID bleibt stabil.
- **Königinnenverwaltung:** neue Königin vs. Korrektur vs. Wechsel unterscheiden; Jahr/Geburt, Farbe, Rasse, Herkunft/Zuchtlinie, Begattung, Zeichnung/Flügelschnitt, Einführung, Abgang, Mutter/Stammbaum, Historie; alte Korrektur darf die aktuelle Königin nicht unbeabsichtigt ersetzen.
- **Stockkartenformular:** vollständiger BEEP-Kategorie-/Unterkategoriebaum und autorisierte auswählbare Optionen; richtige BEEP-Kategorie-IDs und Option-IDs, verschachtelte Struktur, Eingabetypen, Gültigkeit, Pflichtstatus und Reihenfolge. Mehrere persönliche Checklisten und deren Versionen. Fehlende/noch nicht unterstützte Eingabetypen sichtbar blockieren statt Daten als Freitext oder Fake-Speicherung umzudeuten.
- **Imkerliche Arbeit:** Durchsichten, Brut/Weiselstatus, Varroa-Naturfall, Proben, Behandlungen (mit Mitteln, Methode, Dosis und Zeiträumen soweit dokumentiert), Fütterung, Honigernte, Beutenänderungen, Erinnerungen/Aufgaben, Fotos/Anhänge nach Sicherheits-/Ablagekonzept. Vollständigkeitsprüfung ausdrücklich gegen BEEP-Referenzkatalog.
- **Korrekturen:** Änderungsverlauf/Revisionsgrund, Autor, Ereigniszeit und Quelle; ursprüngliche BEEP-Einträge read-only erhalten, Importquelle referenzieren. Keine implizite Rückschreibung an BEEP.
- Neue Eingaben mit Datum **und** Uhrzeit als Vorgabe, sinnvoll veränderbar; ältere reine Datumseinträge ohne erfundene Zeit darstellen.
- Beuten-/Zargenaufbau getrennt vom biologischen Volk mit Gültigkeitsgeschichte. Bis zum expliziten BEEP-Umstellungsentscheid bleibt BEEP fachlich führend für bereits dort gepflegte historische Beutenangaben; bei späterer Umschaltung Konflikte und Verantwortungswechsel dokumentieren.
- **Abnahme erst nach echten fachlichen Eingabe- und Historien-Workflows im Browser**; ein Formular mit sechs Demo-Feldern ist nicht ausreichend.

## 8. Priorität P3 – Sicherheit, Betrieb und Datenlebenszyklus

- Stabile Sessions mit sicheren, HttpOnly-/Secure-/SameSite-Cookies, Authentifizierung und serverseitigen Berechtigungen je Volk/Stand; CSRF, Origin-/Host-Prüfung, Rate-Limits, Sitzungswiderruf, konsequente 401/403. Kein Standardpasswort und keine Client-geheimen API-Tokens.
- Alle Abfragen serverseitig nach Nutzerrechten filtern; Rechteentzug muss auch für laufende Sitzung sofort gelten. Datenbankzugang nur intern, keine direkte Veröffentlichung von Rohdateien oder PostgreSQL-Ports.
- Produktionsdateien nur read-only und per minimalem Dateibereich einbinden; keine Pfad-Traversal/API-getriebene freie Dateiauswahl. Container als Nicht-Root soweit möglich, Least Privilege, Secrets nicht in Logs/Images/Repo.
- HTTPS nur privates Heimnetz (Port 9443 auf 192.168.178.41 im bisherigen Feldtest); Caddy/Apache unvermischt, Firewall inklusive Docker-Regeln prüfen. Lokale CA auf eigenen Testclients bewusst vertrauen.
- Versionierte **additive** PostgreSQL-Migrationen, Probe-/Testdaten getrennt von späteren Live-Daten, Backups mit nachweisbarer Wiederherstellung und überwachte Importfehler. Migration niemals über destruktiven Rebuild des Schemas.
- Betriebsmetriken: letzte Quelleingänge, letzte erfolgreiche Imports, Datenverzug, Fehler-/Dublettenraten, fehlende Kanäle, Backupalter. Besser „keine aktuellen Daten“ als grüne Statusanzeige ohne Messung.
- Datenschutz/Lizenzen: private BEEP-Zugangsdaten und Exportdaten nur autorisiert, nicht im öffentlichen Repository; BEEP und beelogger entsprechend Lizenz und Urheberrecht als **Referenz**, nicht ungeprüft kopieren.

## 9. Verbindliche Tests und Nachweise

| Test-ID | Verfahren und Akzeptanz |
| --- | --- |
| A-00 | **Baseline:** Codex nennt geprüften Ausgangs-SHA, bestehende Architektur, Ist-/Soll-Differenz und betroffene Dateien. Vor erster Änderung reproduzierbarer FAIL-Test für den Kernmangel. |
| A-01 | **Wetter:** eigene anonymisierte S2120-CSV mit fehlenden Zellen, doppelten Uplinks, Vorzeichen, ungültigen Zahlen und Zeitstempeln → realer DB-Import → API → ECharts im Browser. Werte/Einheiten/Zeit vergleichen. |
| A-02 | **Boden:** CSV mit temp_5cm, temp_20cm, temp_50cm → drei verschieden beschriftete Kurven am richtigen Stand, keine 0 aus leerem Wert, keine fiktiven Zwischenmessungen. |
| A-03 | **Volk:** belegter beelogger-Gewichtskanal und Temperatur (reale/synthetisch markierte Fixtures) → korrektes Volk gemäß gültiger Zuordnung, Zeit-/Kalibrier-/Einheitenprüfung. Eine zweite Quelle darf nicht zur zweiten primären Gerätezuordnung werden. |
| A-04 | **Live-Aktualisierung:** nach Import eines neuen, gültigen Testdatensatzes zeigt Browser ihn innerhalb des dokumentierten Intervalls; erneuter Import verursacht keine Dublette. |
| A-05 | **End-to-End:** Browserautomation mit **echtem** Caddy-HTTPS, echter FastAPI und PostgreSQL; Login, UI, Messkurve, Volkwechsel, Rechte, Logout und Wiederanmeldung. Mock-Tests zusätzlich erlaubt, ersetzen E2E aber nicht. |
| A-06 | **Katalog/Stockkarte:** BEEP-Referenzkatalog mit anonymisierten Daten; Auswahl-IDs, Hierarchien, Feldtypen, Mehrfachwahl, Pflichtfelder, null/false/0, Bilder nur bei funktionierender Speicherung; Revisionen/Zeiten unverändert. |
| A-07 | **Historie:** neues Volk/Ableger/Herkunft, Königinnentausch und Korrektur eines älteren Eintrags, Beutenwechsel ohne ID-Verlust und ohne Überschreiben historischer Zuordnungen. |
| A-08 | **Robustheit:** unbekannte Spalten, beschädigte CSV/JSONL, fehlende Dateirechte, DST-Doppelstunde, Datenlücken, Importabbruch/Restart, Revisionskonflikt, 401/403/409 und Rechteentzug. |
| A-09 | **Persistenz/Betrieb:** Backup vor Änderung; Docker-Neustart ohne Volume-Löschung; geprüfter Restore in getrennte DB; Alt-/Neuschema-Migrationsprüfung; bestehender Apache/TTN/beelogger unverändert. |
| A-10 | **UX-Abnahme:** reales Laptop-/Telefon-Fenster, klare Erst-Anmeldung, direkte Volkauswahl, sichtbare Echt-/Demo-/Offline-Kennzeichnung; keine verschachtelte Server-Stockkarten-Modal-Navigation. Betreiber prüft Fachworkflow. |

**CI-Disziplin:** separate schnelle Domain-/API-/Frontend-Tests, danach Integration mit realen Diensten und vor Integration vollständige betroffene Projektmatrix. Jedes Ergebnis: SHA, Umgebung, Testbefehl, Anzahl, PASS/FAIL/SKIP/NICHT GELAUFEN; kein grüner Gesamttitel bei noch offenen Kernfunktionen. Testabdeckung an **Verhalten und Invarianten**, nicht nur UI-Text oder Renderbarkeit messen. Keine erfundenen Feld-, Hardware- oder Lasttests.

## 10. Umsetzungsreihenfolge und PR-Gates

**Gate R0 – ehrliche Bestandsaufnahme:** Architektur-, Abhängigkeits- und Datenflussdiagramm aus realem Code; Code-/SQL-/UI-Duplikate, tote Pfade, Schema-/Rechteprobleme und offene Konflikte erfassen. Architektur-ADR, falls Änderung nötig. Bestehende Tests ausführen und Aussagekraft auflisten. Noch kein Rewrite.

**Gate R1 – erste funktionierende vertikale Datenstrecke:** nur lesende Inventur → S2120- und Boden-CSV-Adapter → PostgreSQL/API → **echte ECharts auf Umweltseite** → A-01/A-02/A-04/A-05. Bediener muss auf Laptop einen realen, zeitlich korrekten Verlauf sehen. Keine Produktions-Eingangsänderung.

**Gate R2 – Völker/Messkanäle:** beelogger-Gewicht/Temperatur mit echter Kanal-/Volkzuordnung, dynamisches Register, Volk-Cockpit, Vergleich und Datenqualitätsanzeigen → A-03/A-08. BEEP-Base erst bei bestätigtem Datenzugang.

**Gate R3 – konsolidierte UX:** ein Login/eine Völkerliste/ein Datenmodell, sinnvolle Navigation, mobile Eingabefähigkeit → A-10; doppelte localStorage-/Server-Pfade mit Migrations-/Rückfallplan entfernen.

**Gate R4 – Stockkarten-Parität:** vollständige autorisierte BEEP-Katalogreferenz, eigene Eingabekomponenten, Königinnen-/Beuten-/Ereignishistorie, Checklisten und Revisionen → A-06/A-07 plus echte Fachabnahme. Nicht als erledigt melden, solange Quellkatalog fehlt.

**Gate R5 – Betriebsfreigabe:** Sicherheit, Berechtigungen, Backup/Restore, Migration, Last-/Langzeittests, Dokumentation, Releasenotes → A-09; ausschließlich nach Betreiberfreigabe produktive Daten/Parallelbetrieb erweitern und BEEP später ersetzen.

Nach **jedem Gate** eine PR mit einem fertig demonstrierbaren Teilprodukt. Kein großer „alles gefixt“-Commit, der weder getestete Funktion noch Rückfallweg hat.

## 11. Abzugebende Artefakte für jede Codex-Iteration

1. **Ist-Befundbericht** mit Dateipfaden, Zeilen/SHA, realen Lücken und reproduzierbaren Fehlern; unbelegte Annahmen getrennt.
2. **Kurzes Architektur-/Datenfluss-Design** samt ADR für strittige Entscheidungen; API-/DB-Vertragsänderungen und Migration.
3. **Reviewfähiger PR** mit kleinen, logisch getrennten Commits, aufgabenbezogenen Tests und dokumentierter Änderungsklasse D0–D3.
4. **Testmatrix und Nachweisprotokoll** pro A-ID, inklusive bewusst offener Punkte, CI-URLs, Resultaten und Umgebungsgrenzen.
5. **Reproduzierbarer Installations-/Update-/Rollback-Plan** nur für isolierten Teststack, kein ungefragtes Deployment.
6. **Fachliche Demo-Anleitung**: genaue Schritte, wie der Betreiber die Funktion auf der ThinkStation im LAN überprüft.

## 12. Direkt kopierbarer Startauftrag an Codex

> Du arbeitest an impyer/bienen-lora-logger. Lies zuerst AGENTS.md, CLAUDE.md, docs/entwicklung/regelwerk.md, akzeptierte ADRs und **dieses gesamte Dokument**. Nutze den zuletzt geprüften Test-Commit 034c9e1d31612679dcc3cc15155208b9c0c82e72 als Referenz, prüfe aber vor Änderungen den aktuellen Branch-HEAD und den Git-Status. Arbeite ausschließlich auf eigenem Feature-Branch. **Beginne mit Gate R0 (Ist-/Soll-Analyse) und anschließend Gate R1 (echte Wetter- und Bodentemperaturcharts Ende-zu-Ende); bearbeite die Stockkarte noch nicht neu.** Starte mit reproduzierbaren fehlschlagenden Verhaltensprüfungen und implementiere dann die kleinste tragfähige Architekturverbesserung. Keine produktiven Dateien/Dienste/Tokens ändern, keine destruktive Datenmigration, keine Demo als Live-Daten kennzeichnen, kein BEEP-Code einbetten. Stelle für R1 den Weg „S2120-/Boden-CSV read-only → PostgreSQL → FastAPI → ECharts → Laptop im Heimnetz“ mit echten Integrations-/Browserprüfungen her. Dokumentiere exakt, welche Tests wirklich liefen, und liefere PR, Tests, Migration/Backup und eine kurze manuelle Abnahmefolge. **Frage die Betreiberfreigabe an jedem Gate an, statt stillschweigend weiterzumachen oder auf der ThinkStation zu deployen.**

## 13. Explizite Stoppschilder für Codex

- **STOP**, wenn der echte Datenpfad, eine primäre Sensorzuordnung oder die BEEP-Quellsemantik unbekannt ist: als offen markieren, nur sichere synthetische Fixture verwenden, fehlenden Nachweis nennen.
- **STOP**, wenn ein Schritt Bestandsschema löschen, vorhandene CSV/JSONL überschreiben, BEEP/TTN-Webhooks umstellen, Apache verändern, Docker-Volumes löschen, Schlüssel veröffentlichen oder Daten ins Internet geben würde.
- **STOP**, wenn Tests nur Mock-Daten prüfen, während die PR echte Ende-zu-Ende-Funktion behauptet.
- **STOP**, wenn vorgeschlagene Vereinfachung Datenprovenienz, Zeitzonen-/Zeitqualität, Königinnen-/Volksgeschichte oder Historienkorrekturen verliert.
- **STOP**, wenn Quellcode oder Daten aus BEEP/beelogger ohne geklärte Lizenzrechte eingebunden werden sollen.

**Abnahmegrundsatz:** „Es lädt im Browser“ ist ein Konnektivitätstest, kein Nachweis fachlicher Funktion. Der Betreiber entscheidet anhand **echter Messreihen, überprüfbarer Stockkartenabläufe, Datenintegrität und sicherem Update/Rollback**.

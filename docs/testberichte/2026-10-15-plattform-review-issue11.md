# Bewertung Review Issue #11 – Plattformkonzept 0.2.4 und Schema 0.3

**Datum:** 15.10.2026 · **Bearbeiter:** Claude (Cowork) · **Basis:** `main` `c5e998e` + lokaler Arbeitsstand (Konzept 0.2.6, Schema 0.3, noch nicht committet)  
**Gegenstand:** [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) (ChatGPT, T0-Review), `docs/architektur/konzept-plattform-v02.md`, `server/datenbank/schema.sql`  
**Änderungsklasse:** D0 (Dokumentation, Schema-Entwurf). **Prüfung:** T0 (Quelltext- und Dokumentabgleich) und T1 (Schema gegen PostgreSQL 16.15 auf einer Testinstanz in der Cloud).  
**Nicht gelaufen:** Test auf der ThinkStation, PHP-Eingänge unter Fehlerbedingungen, BEEP-API-Integration, Browser-UI, Rücksicherung.

## Ergebnis je Einwand

| Nr. | Einwand | Prüfung | Bewertung | Maßnahme | Befund |
|---|---|---|---|---|---|
| P1-1 | 1:1 Beute–Volk zu stark formuliert; BEEP-Hive→Volk nur Heuristik | Anforderungen §3.1 (12.10.): Beute 0..1 Volk bestätigt, Gegenrichtung offen. Betreiber hat am 15.10. im Chat „eine Beute = ein Volk“ bestätigt; ein datierter Beschluss fehlte | teilweise bestätigt | ADR-0003 (Beschluss 15.10.); Konzept W1 präzisiert (0..1 in beide Richtungen, Importheuristik mit Meldung bei Verdacht auf Wiederverwendung); Tests HB-02/HB-03 | PLT26-01 |
| P1-2 | Verlustfreier Raw-Ingest nicht nachgewiesen | `lora_eingang.php` Zeile „`if (isset($msg['uplink_message'])) le_log(... 'nachricht' => $msg)`“ läuft **vor** `le_verarbeiten`, also auch bei unbekanntem Gerät. Die Aussage im Review, Uplinks würden teils vor dem Rohprotokoll verworfen, trifft daher nicht zu. Zutreffend: `le_log` und `we_log` nutzen `@file_put_contents` ohne Rückgabewert; ein Schreibfehler bleibt unbemerkt. Replay, Rotation und Sicherung sind ungetestet | teilweise bestätigt | Konzept §4a mit R-1 bis R-6; PHP-Änderung (Rückgabewert, Warnung wie SRV26-04, Tests) als eigener Arbeitsschritt | PLT26-02 |
| P1-3 | Waage physisch am Messpunkt ≠ logische Zuordnung zum Volk | Schema 0.2: Zuordnung nur zum Volk. HB-09 (Volk zieht aus, Waage bleibt) wird nur richtig, wenn die Zuordnung von Hand beendet wird | bestätigt | Prüfsicht `pruefung_geraet_zuordnung`; Tests HB-01 bis HB-04, HB-09; Option B „Waage am Platz“ zur Betreiberentscheidung (Konzept §11) | PLT26-03 |
| P1-4 | Heimnetz ersetzt keine Anmeldung beim Schreiben | – | bestätigt | Konzept §6a: Schreiben nur nach Anmeldung, CSRF-Schutz (Betreiberentscheidung offen) | PLT26-04 |
| P2-5 | 12:00-Platzhalter nicht als exakte Zeit | Konzept 0.2.4 löste es über `quelle`; reicht im Parallelbetrieb nicht | bestätigt | `zeitgenauigkeit` (exakt, geschaetzt, nur_datum) in `durchsicht`, `massnahme`, `varroa_messung`; Test | PLT26-05 |
| P2-6 | Sensorwechsel und Kalibrierung nicht aufschieben | – | bestätigt | `kanal.kalibriert_am`, `kalibrierung`, `sensor`; Wechsel = neue Kanalzeile | PLT26-06 |
| P2-7 | BEEP Base: Ziel ≠ Inbetriebnahme | – | bestätigt | Kennzeichnung im Konzept §7, Rückfallplan | PLT26-07 |
| P2-8 | Provenienz abgeleiteter Werte | – | bestätigt | Tabelle `berechnung` (Code, Version, Formel, Quelle); Sichten liefern `berechnung@version`; Test | PLT26-08 |
| P2-9 | BEEP-Import autorisiert testen; 512 nur Momentaufnahme | – | bestätigt | Wortlaut Konzept §3.4/§7; Integrationstest im Importer-Schritt | PLT26-09 |
| P2-10 | Bodentiefen nicht verallgemeinern | Tiefen 5/20/50 cm stammen laut Review aus dem ChatGPT-Gespräch; hier nicht prüfbar | bestätigt | Konzept K-05 [PRÜFEN]; Testtiefen im Schematest als Platzhalter gekennzeichnet | PLT26-10 |

## Testnachweis Schema 0.3 (T1)

- Umgebung: PostgreSQL 16.15 (Ubuntu 24.04), Erweiterung `btree_gist`, psycopg 3; Testinstanz, keine Produktivdaten.
- Aufruf: `python3 tests/datenbank/test_schema.py`
- Ergebnis: **24 von 24 bestanden**, gleich mit Sitzungszeitzone Europe/Berlin und UTC.
- Neu gegenüber 0.2: HB-02/HB-03, HB-04, HB-09, Zeitgenauigkeit, Berechnungsversion.

## Grenzen

- Die Bewertung von P1-2 beruht auf dem Quelltext am Commit `c5e998e`; das Verhalten bei vollem Datenträger oder fehlenden Rechten ist nicht getestet.
- Option B für die Waage ist beschrieben, aber nicht umgesetzt.
- Keine Aussage zur tatsächlichen Konfiguration von Apache und Router auf der ThinkStation.

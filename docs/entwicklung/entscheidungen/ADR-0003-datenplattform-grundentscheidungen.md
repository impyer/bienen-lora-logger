# ADR-0003: Datenplattform – Grundentscheidungen vom 15.10.2026

**Status:** angenommen (Punkte 1–8, 10, 11); Punkt 9 verworfen  
**Datum:** 2026-10-15 · **Entscheidender:** Philipp Schnabel (Maintainer) · **Ausgearbeitet:** Claude (Cowork) · **Issue:** [#11](https://github.com/impyer/bienen-lora-logger/issues/11)  
**Betroffen:** `docs/architektur/konzept-plattform-v02.md` (Fassung 0.2.7), `docs/architektur/anforderungen-datenplattform.md` §2 und §3.1, `server/datenbank/schema.sql` (0.3)

## Ausgangslage und Anforderung

Die Anforderungsbasis vom 12.10.2026 (`anforderungen-datenplattform.md`) sah BEEP als führende Stockkarte und die BEEP Base nur mit Übertragung an BEEP vor; die Kardinalität „Volk → höchstens eine Beute“ war offen. Am 15.10.2026 hat der Betreiber im Gespräch mit Claude neue Festlegungen getroffen. Das Review in Issue #11 (P1-1) verlangt dafür einen datierten Beschluss, statt die älteren Dokumente still zu überschreiben.

## Entscheidungen

| Nr. | Festlegung | Ersetzt/präzisiert |
|---|---|---|
| 1 | **Zielbild:** eigene Plattform mit digitaler Stockkarte und Auswertung; langfristig alle Messdaten (eigene Waagen, BEEP Base), Umweltdaten und imkerliche Daten auf der eigenen Plattform. BEEP läuft parallel und wird nach erfolgreicher Umschaltung abgelöst | Anforderungen §2 „BEEP-Stockkarte führend“ gilt nur bis zur Umschaltung |
| 2 | **Beute und Volk:** zu jedem Zeitpunkt höchstens 1:1 (Beute 0..1 Volk, Volk 0..1 Beute); Wiederbelegung und leere Beuten möglich | Anforderungen §3.1, offene Gegenrichtung |
| 3 | **Bienenbuch** ist nur Hilfsmittel und entfällt nach der Umschaltung; kein eigener Import (Inhalte sind in BEEP) | – |
| 4 | **BEEP Base** soll über die eigene TTN-Applikation an den eigenen Server und an BEEP senden (Architekturziel; Inbetriebnahme je Gerät mit Nachweis) | Anforderungen §2 „Base sendet nicht an den eigenen Server“ |
| 5 | **Stockwaage dem Volk zuordnen** (Stand 15.10.; siehe Punkt 9) | – |
| 6 | **Python** für Lese-API und Analyse; PHP-Eingänge bleiben | – |
| 7 | **Alles auf der ThinkStation, PostgreSQL** | Claude-Review 13.10. (Webhosting/MySQL-Annahme) |
| 8 | **Zugriff:** interne Anwendung nur im Heimnetz; öffentliche Übersicht und Studien ohne Login auf `radeberger-honig.de`; öffentliche Lese-API nach Variante B (Webhoster holt alle 30 min ab und puffert) | – |
| 9 | *verworfen 15.10.:* Waage einem festen **Platz** am Stand zuordnen. Betreiber: Zuordnung zum Volk bleibt (Punkt 5); der Pflegeaufwand ist überschaubar und hat sich bei BEEP bewährt. Absicherung: Prüfsicht `pruefung_geraet_zuordnung` | – |
| 10 | **Anmeldung auch im Heimnetz** für die interne Anwendung; Schreiben (Stockkarte, Konfiguration) nur angemeldet, mit CSRF-Schutz | präzisiert Punkt 8 |
| 11 | **Bodentemperatur:** drei Sonden des LSN50v2-D23 in **5 cm (weiß), 20 cm (rot), 50 cm (schwarz)** Tiefe | – |

## Auswirkung auf Sicherheit, Energie, Kompatibilität und Lizenzen

- Die ThinkStation bleibt für TTN-Webhooks von außen erreichbar; dazu kommt der eng begrenzte öffentliche Lese-Endpunkt (Variante B, nur für den Webhoster).
- Die gesamte Datenhaltung liegt auf einem Rechner: tägliche Sicherung auf ein zweites Medium und ein Rücksicherungstest sind Voraussetzung, bevor BEEP abgeschaltet wird.
- Keine Auswirkung auf Firmware, Funkformat oder Energiebilanz.
- Lizenz eigener Server- und Testdateien: GPL-3.0-or-later.

## Nachweis- und Rückfallplan

- Schema 0.3: T1, 24/24 Tests auf Testinstanz (Bericht `docs/testberichte/2026-10-15-plattform-review-issue11.md`).
- **Nicht ausgeführt:** Test auf der ThinkStation, BEEP-Base-Doppelzustellung, BEEP-API-Integrationstest, Rücksicherung.
- Rückfall: Solange Phase C (Umschaltung) nicht erreicht ist, bleibt BEEP führend; eine Base kann jederzeit wieder in die BEEP-Applikation zurück.

## Ergebnis und spätere Revision

Entscheidungen zu Punkt 9–11 am 15.10.2026 durch den Maintainer. Offen: Abnahme per Commit.

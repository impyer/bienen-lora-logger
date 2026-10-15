# Datenbank (PostgreSQL)

Schema 0.3 der Bienen-Plattform nach [`docs/architektur/konzept-plattform-v02.md`](../../docs/architektur/konzept-plattform-v02.md), Abschnitt 5.

**Status:** Entwurf. Getestet nur auf einer Testinstanz (PostgreSQL 16.15, T1). Noch nicht auf der ThinkStation eingespielt, keine Produktivdaten.

| Datei | Zweck |
|---|---|
| `schema.sql` | Legt das Schema `bienen` neu an. **Löscht ein vorhandenes Schema `bienen` samt Daten** (`DROP SCHEMA … CASCADE`), deshalb nur auf einer leeren Datenbank verwenden |
| `../../tests/datenbank/test_schema.py` | 24 Prüffälle (u. a. ER-01, ER-03–05, ER-07, ER-12, K-01, K-02, K-04–06, K-10, HB-01–04, HB-09, Zeitumstellung, Zeitgenauigkeit, Berechnungsversion) |

## Aufbau

| Modul | Tabellen |
|---|---|
| A – Stammdaten | `stand`, `volk`, `beute`, `beute_konfiguration`, `belegung`, `aufstellung`, `volk_ereignis`, `volk_ereignis_teil`, `koenigin`, `koenigin_volk`, `extern_ref` |
| B – Stockkarte | `merkmal`, `checkliste`, `checkliste_version`, `checkliste_merkmal`, `durchsicht`, `durchsicht_wert`, `massnahme`, `varroa_messung`, `aufgabe`, `anhang` |
| C – Messdaten | `messgroesse`, `geraet`, `geraet_zuordnung`, `messstelle`, `kanal`, `rohnachricht`, `messwert`, `quellfeld_ohne_kanal` |
| Auswertung | `berechnung` (Versionen der Berechnungen) |
| Sichten | `messwert_bezug`, `gewicht_tagesreferenz`, `gewicht_tagesbilanz`, `varroa_pro_tag`, `pruefung_geraet_zuordnung`; Funktion `stand_von_volk(volk, zeit)` |

**Regeln, die die Datenbank selbst durchsetzt:**
- Beute = Volk, 1:1 zu jedem Zeitpunkt.
- Höchstens ein Stockmesssystem je Volk zur selben Zeit.
- Ein Gerät nie an zwei Zielen gleichzeitig.
- Keine zwei Deutungen desselben Quellfelds im selben Zeitraum.
- Zeiträume immer `[von, bis)`.

## Test lokal

```bash
pip install "psycopg[binary]"
# leere Testdatenbank mit Erweiterung btree_gist (im Paket postgresql-contrib)
BIENEN_TEST_DSN="host=localhost dbname=bienen_test user=..." python3 tests/datenbank/test_schema.py
```

Zeitangaben beim Schreiben immer mit Zeitzone angeben. Die Tests laufen mit den Sitzungszeitzonen Europe/Berlin, UTC und America/New_York gleich.

**Änderungen 0.3 (15.10.2026, Review Issue #11):** `zeitgenauigkeit` in Durchsicht, Maßnahme und Varroa-Messung; Kalibrierangaben am Kanal; Tabelle `berechnung` und Versionsangabe in den Sichten; Prüfsicht für vergessene Waagenzuordnungen. Bewertung: `docs/testberichte/2026-10-15-plattform-review-issue11.md`.

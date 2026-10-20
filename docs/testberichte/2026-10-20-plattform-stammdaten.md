# Prüfbericht: Plattform Phase C, Teil 1 – Stammdaten-Pflege mit CSRF, Importer-Nachtragen

**Datum:** 20.10.2026 · **Prüfobjekt:** Branch `feature/plattform-stammdaten-20261020`, Commit `be40d0e` (von `main` `f245f2f`; PR impyer/bienen-lora-logger#31) · **Prüfer:** Claude (Code-Session) · **Änderungsklasse:** D2 · **Teststufen:** T1/T2 (CI)

## Prüfumfang

- Seite „Verwaltung“ und Endpunkte `/api/verwaltung/…` (`server/plattform/api/verwaltung.py`, `stammdaten.py`, `katalog.py`)
- CSRF-Token und Herkunftsprüfung beim Schreiben
- Commit vor der Antwort (`Depends(scope="function")`)
- `server/datenbank/importer.py --nachtragen`

CI: GitHub Actions `tests` und `statische-analyse` für `be40d0e`, *success*. Job `datenbank` mit postgres:16, Python 3.12, Pakete wie `server/plattform/requirements.txt`, Playwright 1.56.1 mit Chromium.

## Ergebnisse

| Prüfung | Ort | Soll | Ist |
|---|---|---|---|
| Hosttests `test_verwaltung.py`: CSRF an die Sitzung gebunden; Schreiben ohne Sitzung 401, ohne bzw. mit falschem Token 403, fremde Herkunft 403, ohne Zeitzone und mit leerem Namen 422, jeweils ohne Datenbankzugriff | lokal (Windows, ohne PostgreSQL) und CI | 2/2 | 2/2 |
| Datenbankfälle `test_verwaltung.py`: <br>• leerer Start; Logger sendet vor der Zuordnung (Importer legt ihn an) <br>• Zuordnung und Vorlage; Nachtragen 480 Werte, beim zweiten Lauf 0 <br>• veränderte Zeile per Prüfsumme erkannt <br>• Zargen mit Historie; Änderung vor dem Beginn ergibt 409 <br>• Konflikte (zweite Waage, belegte Beute) ohne Teiländerung <br>• Umsetzen mit Maßnahme; Kanal neu mit Versatz und Kanal beenden <br>• Vereinigung beendet die Zuordnung (keine HB-09-Meldung); Wetterstation per Vorlage | CI, Sitzungszeitzonen Europe/Berlin und UTC | 11/11 je Zone | bestanden |
| `test_plattform.py` (Phase B) nach der Änderung | lokal Hosttests, CI vollständig | 10/10 bzw. 24/24 je Zone | bestanden |
| Browser `oberflaeche_testen.sh`: leer, **Verwaltung** (Katalog → Stand → Volk → Gerät → Zuordnung → Vorlage → Kachel in der Übersicht), synthetisch | CI | bestanden | bestanden |
| Statische Analyse | CI | grün | grün |
| Sichtprüfung der Verwaltungsseite mit nachgebildeten Daten; CSRF mit `fetch`: ohne Token 403, falsches Token 403, gültiges Token kommt durch | lokal, eingebauter Browser | wie Soll | wie Soll |

**Verlauf:**
- Im ersten CI-Lauf (`466c93c`) brach der Browsertest im Schritt „Stand anlegen“ ab: `leer()` war in der Vorlage nicht erreichbar. Gespeichert wurde trotzdem, nur das Formular blieb stehen. Behoben in `be40d0e`.
- Beim Entwurf zeigte sich: Mit der Vorgabe `scope="request"` liefe der Commit erst nach dem Senden der Antwort. Die Schreibabhängigkeit läuft deshalb mit `scope="function"`.

## Grenzen

- Nur synthetische und erfundene Daten; nicht auf der ThinkStation, kein Apache-Proxy, kein TLS.
- Rückwirkende Korrekturen der Historie gibt es nicht: Eine Änderung vor dem Beginn der offenen Angabe wird abgelehnt.
- Endet die Deutung eines Kanals rückwirkend, behalten schon importierte Werte ihren alten Kanal.
- Keine eigene Datenbankrolle getestet (`dsn_schreiben` = `dsn`); Rechte nur beschrieben.
- Die Stockkarte (Durchsicht, Maßnahme, Varroa) lässt sich noch nicht erfassen (Phase C, Teil 2). PLT26-11 (Plausibilität) bleibt offen.

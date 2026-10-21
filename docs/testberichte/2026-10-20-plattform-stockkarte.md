# Prüfbericht: Plattform Phase C, Teil 2 – Stockkarte erfassen

**Datum:** 20.10.2026 · **Prüfobjekt:** Branch `feature/plattform-stockkarte-20261020`, Commits `c3aec01` (Code) und `2008d2b` (Doku), von `main` `b775f25` · **Prüfer:** Claude (Code-Session) · **Änderungsklasse:** D2 · **Teststufen:** T1/T2 (CI)

## Prüfumfang

- Seite „Stockkarte“ (`server/plattform/web/seiten/stockkarte.js`) und Endpunkte `/api/stockkarte/…` (`api/stockkarte.py`, `api/stockkarte_api.py`)
- Standard-Checkliste (`api/katalog.py`)
- Erweiterungen der Lese-API: Merkmalswerte, Varroa aller Methoden, Aufgaben, letzte Durchsicht
- Cockpit und Übersicht

CI: GitHub Actions für `2008d2b`, Läufe `tests` #39430006244 und `statische-analyse` #39430006246, alle Jobs *success*. Datenbankjob mit postgres:16 und Python 3.12, Playwright 1.56.1 mit Chromium.

## Ergebnisse

| Prüfung | Ort | Soll | Ist |
|---|---|---|---|
| Hosttests `test_stockkarte.py`: Werteprüfung je Eingabetyp; Schutz bei POST, PUT und DELETE (401/403) ohne Datenbankzugriff; Eingaben 422 | lokal (Windows, ohne PostgreSQL) und CI | 2/2 | 2/2 |
| Datenbankfälle `test_stockkarte.py`: <br>• Checkliste idempotent; Durchsicht für zwei Völker mit Werten in Reihenfolge der Checkliste <br>• falscher Wert, fremdes Merkmal, aufgelöstes Volk: 409 ohne Teilanlage <br>• K-03-Korrektur; Maßnahme als Zeitpunkt und Zeitraum <br>• Varroa Windel und Puderzucker; Aufgaben mit Fälligkeit in der Übersicht <br>• Löschen mit erhaltener Maßnahme; neue Checklistenversion (K-10) | CI, Sitzungszeitzonen Europe/Berlin und UTC | 9/9 je Zone | bestanden |
| `test_plattform.py` und `test_verwaltung.py` nach der Änderung | lokal Hosttests, CI vollständig | bestanden | bestanden |
| Browser: Verwaltungsdurchlauf, dann Stockkarte bei 390 × 844 px (Checkliste übernehmen, Durchsicht mit ja / 6 / 4, kein waagrechtes Scrollen, Fütterung), Cockpit mit Werten, Bearbeiten mit vorbelegten Werten | CI | bestanden | bestanden |
| Statische Analyse | CI | grün | grün |

**Ausreißer:** Im Lauf für `c3aec01` (#39428606699) war genau ein Schritt rot: „LoRa-Eingang Ende-zu-Ende, Original M.40, Serveruhr 14:00“. Datenbank- und Plattformjob waren dort grün.
- Der Branch ändert nichts unter `server/lora`, `server/eingang`, `server/beelogger_eigen` oder `tests/server`.
- Im nächsten Lauf (`2008d2b`, nur Doku) war derselbe Schritt grün.
- Die Ursache ist nicht ermittelt, weil das Log ohne Anmeldung nicht lesbar ist. Die gleichzeitige Umstellung von `ubuntu-latest` auf Ubuntu 26 ist ein möglicher Faktor. Geführt als Befund CI26-02.

## Grenzen

- Nur synthetische und erfundene Daten; kein Betrieb auf der ThinkStation, kein Apache/TLS, kein echtes Handy (nur Chromium mit Handy-Breite).
- Kein Offline-Zwischenspeicher: Die Stockkarte braucht am Stand Netz; die WLAN-Abdeckung ist **[PRÜFEN]**.
- Fotos (`anhang`), Export an BEEP und Import aus BEEP fehlen.
- Werte einer Durchsicht mit älterer Checklistenversion lassen sich nur für Merkmale bearbeiten, die auch in der aktuellen Version stehen.

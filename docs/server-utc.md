# Eigene Server-Fassung mit UTC (eigen-utc-2, 08.10.2026, ergänzt nach Review 5c1b847)

Grundlage: beelogger Server-Skripte M.40 (`server/M40_261004_ServerSkripte.zip`). Analyse des Fehlers: `docs/server-analyse.md`, B2.

## Problem im Original

`beelogger_log.php` arbeitet mit dem Ortszeit-Text (`Y/m/d H:i:s`, Europe/Berlin):

1. Der Zeitstempel wird mit `strtotime()` aus diesem Text zurückgerechnet.
2. In der doppelten Stunde der Winterzeit-Umstellung (25.10.2026, 02:00–03:00) gibt es jeden Text zweimal. `strtotime()` liefert für beide Fälle denselben Zeitpunkt.
3. Die Speicherregel „nur speichern, wenn mehr als 200 s nach dem letzten Datensatz“ verwirft deshalb die zweite Stunde.

Ergebnis im Test (30-min-Takt): 5 von 7 Datensätzen gespeichert.

Zusätzlich liest Dygraph die erste CSV-Spalte als Ortszeit des Browsers. Auch die Anzeige ist in der doppelten Stunde also mehrdeutig.

## Lösung

| Teil | Änderung |
|---|---|
| Zeitzone | neue Datei `beelogger_zeitzone.php` mit `$Zeitzone="Europe/Berlin";`. Alle Skripte mit Zeitbezug lesen sie. Ungültige Namen fallen auf `Europe/Berlin` zurück. |
| Speichern (`beelogger_log.php`) | maßgeblich ist der Unix-Zeitstempel (UTC) in der letzten CSV-Spalte |
| Empfangszeit | `time()`, auf die Minute gekürzt (wie bisher) |
| EE-Weg | mit `UTC=1` gilt die Zeit im Datensatz als UTC; der LoRa-Eingang setzt das. Ohne `UTC=1` gilt die Ortszeit wie im Original. |
| Erste CSV-Spalte | bleibt Ortszeit-Text, nur zur Anzeige und Kompatibilität |
| Grafik (`beelogger_show.php`, `beelogger_sml.php`, `beelogger_mobileWatch.php`) | Die Zeitachse wird aus dem Zeitstempel als ISO 8601 mit Versatz gebildet, z. B. `2026-10-25T02:30:00+02:00` und `…+01:00`. Dygraph liest das als eindeutigen Zeitpunkt. |
| Anmerkungen | ebenfalls ISO 8601 mit Versatz |
| Stundenauswertung (Xanalyse) | gruppiert nach dem Zeitstempel statt nach dem Text |
| Merkmal für den LoRa-Eingang | `beelogger_log.php` enthält `$BL_UTC_FAEHIG=1;`. Daran erkennt der Eingang **je Logger**, dass `UTC=1` ausgewertet wird (SRV26-07). |
| BEEP/ThingSpeak (`beelogger_log.php`) | Nur gespeicherte Datensätze werden übertragen. Das Original bereitet die Daten vor der Speicherentscheidung vor und sendet auch abgelehnte (SRV26-05). |
| Prüfung BEEP-ID / ThingSpeak-API | `AND` statt `OR`: Die Prüfung war im Original immer wahr. Mit der Platzhalter-ID „meine BeepID“ wird jetzt nichts gesendet. |
| Hauptordner (`beelogger_cron21.php`, `scraper.php`, `local_Updater.php`, `local_Split_Archivnotes.php`) | setzen jetzt die Zeitzone. Bisher galt die Vorgabe der php.ini, auf vielen Servern UTC. |

Ergebnis im Test: 7 von 7 Datensätzen gespeichert, Zeitstempel lückenlos im Abstand von 1800 s.
Im Browser (Chromium, Playwright) ist die Zeitachse streng steigend, ohne JavaScript-Fehler.

## Einspielen

1. **Datensicherung** des beelogger-Ordners auf dem Server.
2. Inhalt von `server/beelogger_eigen/` über die bestehende Installation kopieren. Die Bilder `beelogger_icons/` bleiben aus der bestehenden Installation.
   - Die Verzeichnisse `beelogger1`, `Duo1` … mit ihren CSV-Dateien und `beelogger_ini.php` bleiben, wie sie sind.
   - **[P]** Bei mehreren Logger-Verzeichnissen prüfen, ob dort Kopien von `beelogger_show.php` usw. liegen. `local_Updater.php` kopiert sie aus `beelogger1/` in die anderen Verzeichnisse; also die eigene Fassung einspielen und dann den Updater laufen lassen oder die Dateien selbst kopieren.
3. Zeitzone in `beelogger_zeitzone.php` prüfen.
4. Im LoRa-Eingang `'utc_zeit' => 'auto'` lassen. Er prüft **je Logger** das Merkmal in dessen `beelogger_log.php`.
   - Ein Logger, der noch die alte Fassung hat, bekommt weiter Ortszeit (richtige Zeit, nur die Winterzeit-Lücke bleibt). Das Protokoll meldet „Mischinstallation“.
   - Wer sicherstellen will, dass alle Logger umgestellt sind: `'utc_zeit' => true`. Dann wird eine Nachricht an einen alten Endpunkt zurückgestellt (`lora_log/nachholen/`) und nach dem Update mit `lora_nachholen.php` verarbeitet.
5. Kontrolle nach dem Einspielen, je Logger-Verzeichnis:
   ```
   grep -L 'BL_UTC_FAEHIG=1' */beelogger_log.php
   ```
   Die Ausgabe muss leer sein. Jede genannte Datei ist noch die alte Fassung.
6. **Rücknahme:** Datensicherung zurückspielen. Der LoRa-Eingang stellt sich mit `'auto'` von selbst auf Ortszeit um, weil das Merkmal dann fehlt.

Alte Datensätze bleiben gültig. Sie haben schon den Zeitstempel in der letzten Spalte; er wurde damals mit `strtotime()` gebildet. Alte Lücken aus früheren Umstellungen bleiben Lücken.

## Grenzen (bekannt)

- **Geräte mit Ortszeit-Uhr über den EE-Weg ohne `UTC=1`:** In der doppelten Stunde bleibt die Zeit mehrdeutig. Das betrifft nicht unsere LoRa-Logger; deren RTC läuft in UTC.
- Die Zeitzone wird nur über die Datei eingestellt, es gibt keine Einstellung in der Oberfläche.
- `error_reporting(0)` in den beelogger-Skripten verdeckt PHP-Warnungen. Die Tests sehen deshalb nur, was gespeichert wird, nicht jede Warnung.
- Die BEEP-Weitergabe sendet `time=$timestamp` (Unix-Zeit). Mit der eigenen Fassung ist das auch in der doppelten Stunde der richtige Zeitpunkt. Getestet ist sie mit einer lokalen Nachbildung des BEEP-Servers, nicht mit api.beep.nl. **[P]** Erste echte Übertragung im BEEP-Konto prüfen.
- Ein Datensatz, der vom Original wegen gleicher Zeit verworfen wurde, ging bisher trotzdem an BEEP/ThingSpeak. Ob das in der Vergangenheit doppelte Werte im BEEP-Konto erzeugt hat, ist nicht geprüft.
- Neue beelogger-Fassungen (M.41 …): `eigen_anpassen.py` auf das neue ZIP anwenden. Bricht das Skript ab, hat sich die betroffene Stelle geändert und muss angesehen werden.

## Dateien

- `server/eigen_anpassen.py`: erzeugt die Fassung. Jede Ersetzung muss genau einmal passen, sonst bricht das Skript ab.
- `server/beelogger_eigen/`: Ergebnis, ohne die Bilder `beelogger_icons/` (wie beim Original nur im ZIP). Die CI erzeugt es neu und vergleicht.
- `server/eigen_utc.patch`: Unterschied zum Original, zum Lesen.
- Tests: `tests/server/test_lora_eingang.sh` (`VARIANTE=eigen` / `original`), `tests/server/grafik_pruefen.js`.

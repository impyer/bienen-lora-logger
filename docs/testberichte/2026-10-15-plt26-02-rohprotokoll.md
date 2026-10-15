# Behebung PLT26-02 – Rohprotokoll der Eingänge

**Datum:** 15.10.2026 · **Bearbeiter:** Claude (Cowork) · **Basis:** `main` `c5e998e`  
**Befund:** PLT26-02 (Review [Issue #11](https://github.com/impyer/bienen-lora-logger/issues/11) P1-2, [Bewertung](2026-10-15-plattform-review-issue11.md))  
**Änderungsklasse:** D1 (Serverlogik der Eingänge, keine Änderung an Speicherformat oder Antwortcodes). **Prüfung:** T2 (Host- und Ende-zu-Ende-Tests mit PHP-Testserver, echten beelogger-Skripten und echtem Formatter). Kein Test auf der ThinkStation, kein TTN-Feldtest.

## Ursache

`le_log` (`server/lora/lora_verarbeitung.php`) und `we_log` (`server/wetter/wetter_eingang.php`) schrieben mit `@file_put_contents` und gaben nichts zurück. Konnte die Protokollzeile nicht geschrieben werden (Datei gesperrt, Datenträger voll, Rechte), lief die Verarbeitung ohne Hinweis weiter. Ein späterer Import aus dem Protokoll hätte die Nachricht nie gesehen.

Nicht zutreffend war die Annahme im Review, der LoRa-Eingang protokolliere nicht jeden Uplink: Er schrieb die vollständige Nachricht schon bisher vor der Verarbeitung, auch bei unbekanntem Gerät.

## Änderung

| Datei | Änderung |
|---|---|
| `server/lora/lora_verarbeitung.php` | `le_log` gibt `true` nur zurück, wenn die ganze Zeile geschrieben wurde; JSON-Fehler ergeben `false`; Zahlen behalten ihre Nachkommastelle (`JSON_PRESERVE_ZERO_FRACTION`) |
| `server/lora/lora_eingang.php` | Rohzeile je Uplink mit `roh_sha256` (SHA-256 des empfangenen Textes). Bei Fehler: Verarbeitung läuft weiter (kein Messwertverlust), Antwort endet auf `| WARNUNG: Rohprotokoll nicht geschrieben`, Kennung im PHP-Fehlerprotokoll |
| `server/wetter/wetter_eingang.php` | dasselbe für `we_log`; Warnung über alle Antwortpfade |
| `tests/server/test_lora_eingang.sh` | R-1: 10 Uplinks (5 unbekannte Geräte) → 10 Rohzeilen, Prüfsumme je Zeile und gleich SHA-256 der gesendeten Datei; R-2: Protokolldatei unbeschreibbar → Warnung, HTTP 200, Datensatz trotzdem in `week.csv`, Eintrag im Fehlerprotokoll |
| `tests/server/test_wetter_eingang.sh` | R-1 Prüfsumme je Uplink; R-2 wie oben, Zeile trotzdem in der Wetter-CSV |
| `server/lora/README.md`, `server/wetter/README.md` | Rohprotokoll beschrieben |

Antwortcodes bleiben unverändert (200 bei Warnung), damit TTN den Webhook nicht abschaltet.

## Nachweis (T2)

| Test | Ergebnis |
|---|---|
| `bash tests/alle_tests_linux.sh` | rc 0 |
| `tests/server/test_lora_eingang.sh` (eigene Fassung) | 81/81 (vorher 73/73) |
| dto. mit `SERVER_UHR="2026-10-09 05:00:00"` und `"2026-10-09 14:00:00"` | je 82/82 |
| dto. `VARIANTE=original` | 64/64 (vorher 56/56) |
| `tests/server/test_wetter_eingang.sh` | 29/29 (vorher 24/24) |
| `test_lora_funktionen.php`, `test_wetter_funktionen.php` | 66/66, 41/41 |

Umgebung: Ubuntu 24.04, PHP 8.3.6, Node, libfaketime 0.9.10; Cloud-Testumgebung, nicht die ThinkStation.

## Offen (Anforderungen aus Konzept §4a)

- **R-3** einheitliches Format: LoRa und Wetter haben jetzt dieselben Felder (`art`, `id`, `roh_sha256`, `nachricht`, `log_zeit`); der Gerätename heißt noch `geraet` bzw. `station`. Boden- und BEEP-Base-Eingang folgen.
- **R-4** Prüfsumme je abgeschlossenem Monat, **R-5** Wiedereinspielen durch den Importer, **R-6** Sicherung: mit dem Importer.
- **Betrieb (G3):** Nach dem Einspielen auf der ThinkStation prüfen, dass die Protokollzeilen `roh_sha256` enthalten und das PHP-Fehlerprotokoll keine Meldung zeigt.

# Tests

| Teil | Inhalt | Start |
|---|---|---|
| `host/` | Unit-Tests der Zeitlogik (`beelogger_zeitsync.h`) | `g++ -std=c++11 -O2 -o t host/test_zeitsync.cpp && ./t` |
| `sim/` | Simulation von 10 Loggern mit dem echten ZS-Code (Modell: Quarz, Temperatur, Funk, Gateway) | `g++ -std=c++17 -O2 -DZEITSYNC_AKTIV=1 -o sim sim/sim_zeitsync.cpp && ./sim --hilfe` |
| `ttn_auswertung/` | Auswertung von TTN-Exporten: Sendezeiten, Slots, Uhrkorrekturen, verlorene Pakete | `python3 ttn_auswertung/ttn_zeitanalyse.py export.json` |
| `STM32_ZS_Selbsttest/` | Selbsttest-Sketch für die BlackPill (Unit-Tests + RTC-Tests auf der Hardware) | Arduino-IDE |
| `formatter/` | TTN-Formatter: Vergleich mit dem beelogger-Original, Funkformat v2, Fehlerfälle; `goja/` prüft in der Laufzeit von The Things Stack | `node formatter/test_formatter.js`; goja: `cd formatter/goja && go run . ../../../formatter/formatter.js vektoren.json` (Vektoren mit `VEKTOREN=vektoren.json node …`) |
| `server/` | Eingangsschicht, LoRa- und Wetter-Eingang: Unit-Tests (PHP) und Ende-zu-Ende-Tests mit den echten beelogger-Skripten | `php server/test_eingang_funktionen.php`; `php server/test_lora_funktionen.php`; `bash server/test_lora_eingang.sh` |
| `datenbank/` | Schema 0.3 der Plattform gegen PostgreSQL 16: Akzeptanzfälle ER/K/HB, Zeitumstellung, Berechnungsversion; CI-Job `datenbank` mit drei Sitzungszeitzonen | `BIENEN_TEST_DSN="host=… dbname=… user=…" python3 datenbank/test_schema.py` |
| `windows/` | `tests_starten.bat` für die Windows-Programme | Die Programme aus dem Actions-Lauf laden (Artefakt `windows-tests`) |

Alles auf einmal unter Linux, WSL oder macOS: `./alle_tests_linux.sh`.

`zs_testfaelle.h` und `zs_testvektoren.h` werden von den PC-Tests und vom Selbsttest gemeinsam genutzt.
Im Selbsttest-Ordner liegen Kopien, weil die Arduino-IDE keine Dateien außerhalb des Sketch-Ordners einbindet.
Der CI-Lauf prüft, dass die Kopien gleich bleiben.

## Statische Analyse und Testabdeckung in der CI

Neben `tests.yml` (funktionale Tests) und dem CodeQL-Default-Setup des Repos (GitHub-seitig konfiguriert, Actions/C-C++/Go/JavaScript/Python, kein PHP; keine Workflow-Datei im Repo) läuft `.github/workflows/static-analysis.yml`:

| Job | verpflichtend | informativ (continue-on-error, Baseline 19.10.2026) |
|---|---|---|
| `syntax` | `compileall`, `node --check`, `php -l` (alle PHP-Dateien), `bash -n`, actionlint | – |
| `ruff` | E9, F63, F7, F82 (Syntax, undefinierte Namen; `--isolated`) | Regelsatz aus `ruff.toml` (E, W, F, B ohne E501): 22 Hinweise |
| `bandit` | Schweregrad hoch (`-lll`) | mittel (`-ll`): 1 Treffer B608 in `tests/datenbank/test_schema.py` (SQL-String im Test) |
| `shellcheck` | `-S error` | alle Hinweise |
| `abdeckung-cpp` | Host-Tests und Simulation (3 Tage) laufen instrumentiert | Abdeckung der Dateien unter `firmware/` (gcovr), Artefakt `abdeckung-cpp` |
| `abdeckung-js` | beide Formatter-Tests laufen | Abdeckung `formatter/` (c8), Artefakt `abdeckung-js` |
| `abdeckung-python` | `test_beelogger1_inventur.py`, Rechenmodelle, `eigen_anpassen.py` laufen | Abdeckung `hardware/` (ohne kicad, layout-auftrag) und `server/` (coverage), Artefakt `abdeckung-python` |

Noch ohne Mindestwerte: zuerst Baseline erheben, dann Schwellen und verpflichtende Regelsätze festlegen. Nicht erfasst: PHP-Abdeckung (kein Xdebug-Lauf), `tests/datenbank/test_schema.py` (braucht PostgreSQL), KiCad-Generator (braucht KiCad 10, siehe `kicad-schaltplan` in `tests.yml`). Lokal: `ruff check .`, `bandit -r hardware server tests -ll`, `shellcheck $(git ls-files '*.sh')`.

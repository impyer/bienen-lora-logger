# Tests

| Teil | Inhalt | Start |
|---|---|---|
| `host/` | Unit-Tests der Zeitlogik (`beelogger_zeitsync.h`) | `g++ -std=c++11 -O2 -o t host/test_zeitsync.cpp && ./t` |
| `sim/` | Simulation von 10 Loggern mit dem echten ZS-Code (Modell: Quarz, Temperatur, Funk, Gateway) | `g++ -std=c++17 -O2 -DZEITSYNC_AKTIV=1 -o sim sim/sim_zeitsync.cpp && ./sim --hilfe` |
| `ttn_auswertung/` | Auswertung von TTN-Exporten: Sendezeiten, Slots, Uhrkorrekturen, verlorene Pakete | `python3 ttn_auswertung/ttn_zeitanalyse.py export.json` |
| `STM32_ZS_Selbsttest/` | Selbsttest-Sketch für die BlackPill (Unit-Tests + RTC-Tests auf der Hardware) | Arduino-IDE |
| `windows/` | `tests_starten.bat` für die Windows-Programme | Die Programme aus dem Actions-Lauf laden (Artefakt `windows-tests`) |

Alles auf einmal unter Linux, WSL oder macOS: `./alle_tests_linux.sh`.

`zs_testfaelle.h` und `zs_testvektoren.h` werden von den PC-Tests und vom Selbsttest gemeinsam genutzt.
Im Selbsttest-Ordner liegen Kopien, weil die Arduino-IDE keine Dateien außerhalb des Sketch-Ordners einbindet.
Der CI-Lauf prüft, dass die Kopien gleich bleiben.

# bienen-lora-logger

Stockwaagen und Sensoren für Bienenvölker mit LoRaWAN. Die Firmware baut auf der
**beelogger-STM32**-Firmware von [beelogger.de](https://beelogger.de) auf.
Dazu kommen eigene Erweiterungen, Tests, Dokumentation und später eine eigene, offene SMD-Platine.

> **Inoffizielles Projekt.** Es besteht keine Verbindung zu beelogger.de. „beelogger“ bezeichnet hier
> nur die Herkunft der Firmware. Die Platinen von beelogger.de sind **nicht** Teil dieses Repos:
> Ihre Fertigungsdaten sind nicht offen lizenziert.

## Stand

| Teil | Stand |
|---|---|
| Firmware `STM32_LORA_261008_ZS` (ZS + V2-Payload + optional FFT) | SiL-/CI-Prüfung vorhanden, **noch nicht am Logger/mit TTN validiert** |
| Tests (Unit-Tests, Simulation, TTN-Auswertung, Selbsttest auf dem STM32) | lauffähig |
| Eigene SMD-Platine | Lastenheft-Entwurf, siehe [`hardware/`](hardware/) |
| Waagenrahmen (Alu) | geplant, siehe [`mechanik/`](mechanik/) |
| Erweiterungen beelogger-Webserver | Eigener TTN-LoRa-Eingang implementiert und integriert getestet; siehe [`server/lora/`](server/lora/) |

## Aufbau des Systems

```
Logger (STM32F411 + RFM95, künftig SX1262; Waage, Sensoren) --LoRa--> Gateway (RAK7268V2) --> TTN
TTN --Webhook--> eigener beelogger-Webserver --> BEEP
Wetterstation SenseCAP S2120 --LoRa--> ... gleicher Weg, dient als Referenz
```

## Ordner

| Ordner | Inhalt | Lizenz |
|---|---|---|
| [`firmware/`](firmware/) | Arduino-Sketch für beelogger-STM32 (BlackPill F411CE) mit LoRaWAN | GPL-3.0-or-later |
| [`formatter/`](formatter/) | TTN-Payload-Formatter (beelogger-Format und Funkformat v2) | GPL-3.0-or-later |
| [`tests/`](tests/) | PC-Tests, Simulation, TTN-Auswertung, Selbsttest-Sketch | GPL-3.0-or-later |
| [`docs/`](docs/) | Einrichtung TTN, Zeitabgleich, BEEP-Anbindung | CC BY-SA 4.0 |
| [`hardware/`](hardware/) | eigene SMD-Platine (KiCad), Lastenheft | CERN-OHL-S-2.0 |
| [`mechanik/`](mechanik/) | Waagenrahmen, Halterungen | CERN-OHL-S-2.0 |
| [`server/`](server/) | Erweiterungen für den beelogger-Webserver | GPL-3.0-or-later |

Einzelheiten in [`LICENSE.md`](LICENSE.md).

## Schnellstart Firmware

1. Arduino-IDE mit STM32-Core (STMicroelectronics, getestet 2.6.0) und den Bibliotheken nach
   [`firmware/README.md`](firmware/README.md) einrichten.
2. `firmware/STM32_LORA_261008_ZS/Config_Geraet.beispiel.h` kopieren, die Kopie in
   `Config_Geraet.h` umbenennen und DevAddr und Schlüssel aus TTN eintragen. Diese Datei wird nie hochgeladen.
3. TTN-Einstellungen nach [`docs/ttn-einrichtung.md`](docs/ttn-einrichtung.md) vornehmen.
4. Übersetzen und auf die BlackPill spielen.

## Tests

Die Tests laufen bei jedem Push automatisch (GitHub Actions, siehe `.github/workflows/tests.yml`):

- Unit-Tests der Zeitlogik
- Simulation von 10 Loggern
- Testlauf der TTN-Auswertung
- Übersetzen der Firmware für die BlackPill
- Windows-Programme für die PC-Tests (als Download unter „Actions“)

Lokal: `tests/alle_tests_linux.sh` (Linux, WSL, macOS).

**Prüfberichte und offene Befunde:** [`docs/testberichte/README.md`](docs/testberichte/README.md). Für Coding-Agents gibt es zusätzlich [`CLAUDE.md`](CLAUDE.md). Die Berichte unterscheiden Code-Review, Host-/SiL-Tests, CI und ausstehende HiL-/Feldtests.

## Dank und Herkunft

- Firmware-Grundlage: beelogger-STM32 von R. Schick und dem beelogger-Team,
  [beelogger.de](https://beelogger.de), GPL v3 oder später. Die Originalhinweise stehen in den Dateien;
  Änderungen sind mit `ZS` und Datum markiert.
- LoRaWAN-Stack: [MCCI arduino-lmic](https://github.com/mcci-catena/arduino-lmic). Er wird nicht mitgeliefert,
  sondern über den Bibliotheksverwalter installiert.
- Die beelogger-Bibliotheken werden ebenfalls nicht mitgeliefert, sondern von beelogger.de geladen.

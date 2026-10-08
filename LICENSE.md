# Lizenzen

Dieses Repository enthält Teile unter verschiedenen Lizenzen. Maßgeblich ist der Ordner:

| Ordner | Lizenz | Text |
|---|---|---|
| `firmware/`, `tests/`, `server/` | GNU General Public License v3.0 oder später (GPL-3.0-or-later) | [`LICENSES/GPL-3.0-or-later.txt`](LICENSES/GPL-3.0-or-later.txt) |
| `hardware/`, `mechanik/` | CERN Open Hardware Licence v2 – Strongly Reciprocal (CERN-OHL-S-2.0) | [`LICENSES/CERN-OHL-S-2.0.txt`](LICENSES/CERN-OHL-S-2.0.txt) |
| `docs/` und die README-Dateien | Creative Commons Namensnennung – Weitergabe unter gleichen Bedingungen 4.0 (CC BY-SA 4.0) | [`LICENSES/CC-BY-SA-4.0.txt`](LICENSES/CC-BY-SA-4.0.txt) |

## Herkunft der Firmware

Die Dateien in `firmware/STM32_LORA_261008_ZS/` beruhen auf dem beelogger-STM32-Sketch `STM32_LORA_260705`
aus dem Paket `beelogger_STM32_202610` von beelogger.de:

    (C) 2024 R.Schick - beelogger.de
    This program is free software: you can redistribute it and/or modify it under the terms of the
    GNU General Public License as published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

Änderungen ab 08.10.2026 sind im Quelltext mit `ZS` gekennzeichnet:
Copyright (C) 2026 Philipp Schnabel, ebenfalls GPL-3.0-or-later.

## Nicht enthalten

- **Platinen von beelogger.de** (STM32, SMD, Universal): Ihre Fertigungsdaten sind nicht offen lizenziert.
  Die SMD-Platine steht laut beelogger.de unter dem Copyright von Thorsten Gurzan und ist nur für den privaten
  Gebrauch freigegeben. Eine eigene Platine entsteht in `hardware/` als Neuentwicklung. Übernommen wird nur die
  Pinbelegung, damit die Firmware passt.
- **Bibliotheken** (beelogger-Bibliotheken, MCCI LMIC, STM32duino): Sie werden aus ihren Quellen installiert
  und haben eigene Lizenzen.
- **Gerätedaten und Schlüssel** (`Config_Geraet.h`): stehen absichtlich in `.gitignore`.

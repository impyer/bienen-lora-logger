# Server

## `beelogger_M40_original/`

Unveränderte Webserver-Skripte von beelogger.de:

| Angabe | Wert |
|---|---|
| Datei | `M40_261004_ServerSkripte.zip` |
| Download | https://beelogger.de/?ddownload=215031, geladen am 08.10.2026 |
| SHA-256 | `fc8fc02b6ab6bb2377b95e5a360b28d6f45a2b26d2c8ea415102d61c9585de85` |
| Lizenz | GPL v3 oder später; © Jeremias Bruker, Rudi Schick, Thorsten Gurzan – beelogger.de |
| Enthalten | dygraphs mit eigener Lizenz (`dygraphs_LICENSE.txt`) |
| Im Ordner | alle Skripte (PHP, JS, CSS, Texte), 36 Dateien. Die 162 Bilder (`beelogger_icons/`) nur im Original-ZIP daneben |
| Original-ZIP | `server/M40_261004_ServerSkripte.zip` (unverändert) |

Die Dateien bleiben byte-genau (`.gitattributes`). So zeigt jeder Patch einen sauberen Unterschied zum Original.

Analyse: [`../docs/server-analyse.md`](../docs/server-analyse.md).

## `lora/`

Eigener LoRa-Eingang (Webhook-Ziel für TTN) mit richtiger Messzeit und Zusatzdatei; die beelogger-Skripte bleiben unverändert. Siehe [`lora/README.md`](lora/README.md).

## Geplant

- Werte der Wetterstation SenseCAP S2120 als Standreferenz
- Übertragung an BEEP mit Messzeitpunkt

Zugangsdaten gehören in nicht versionierte Dateien (siehe `.gitignore`).
Lizenz eigener Dateien: GPL-3.0-or-later.

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

## `beelogger_eigen/` – eigene Fassung mit UTC (eigen-utc-2)

Aus dem Original-ZIP erzeugt mit `python3 server/eigen_anpassen.py <ordner>`. Unterschied zum Original: `eigen_utc.patch`.

- Gespeichert wird maßgeblich der Unix-Zeitstempel (UTC, letzte CSV-Spalte). Die erste Spalte ist nur noch Anzeige in der eingestellten Zeitzone.
- Zeitzone wählbar in `beelogger_zeitzone.php` (Vorgabe `Europe/Berlin`). Ungültige Namen fallen auf `Europe/Berlin` zurück.
- Behebt den Verlust in der Nacht der Winterzeit-Umstellung (Test: 7 von 7 statt 5 von 7).

Details, Grenzen und Einspielen: [`../docs/server-utc.md`](../docs/server-utc.md).
Die CI erzeugt die Fassung bei jedem Lauf neu und vergleicht sie mit dem Ordner. Änderungen deshalb nur in `eigen_anpassen.py` machen, nicht direkt im Ordner.

## `eingang/`

Gemeinsame Eingangsschicht der beiden TTN-Webhooks (Bienen, Umwelt): Annahme mit Token, Rohprotokoll nach R-1 bis R-3, Kennung gegen Doppelzustellung, Sperren, CSV-Anhängen. Wird von `bienen/` und `umwelt/` eingebunden und muss auf dem Server daneben liegen. Siehe [`eingang/README.md`](eingang/README.md).

## Zwei Eingänge (seit 22.10.2026)

Es gibt genau zwei Webhook-Ziele, nicht eines je Sensor. Beide schreiben jeden Uplink ins Rohprotokoll; der Importer liest beide in die Datenbank. Was ein Feld bedeutet und wohin ein Gerät gehört, steht nur in der Datenbank (Kanalregister, Zuordnung). Ein neuer Sensor braucht einen Formatter in TTN und einen Eintrag in der Verwaltung, keinen Servercode.

| Eingang | Geräte | Messzeit | Zusatz |
|---|---|---|---|
| [`bienen/`](bienen/README.md) | Messwerte der Völker: beelogger, eigene Platine, BEEP Base | Regel des Importers, gleich für beide | Weiterleitung an beelogger M.40 nur für Geräte in `bienen_config.php` (solange M.40 parallel läuft) |
| [`umwelt/`](umwelt/README.md) | Umweltsensoren am Stand: S2120, LSN50v2-D23, weitere | Regel des Importers, gleich für beide | keiner |

Messzeit: Gerätezeit, wenn der Formatter sie als abgeglichen liefert (`Messzeit_unix`, `Status.zeit_ok`; mehrere Messungen als Liste `Eintraege`), höchstens 30 s vor und 30 Tage nach dem Empfang; sonst Empfangszeit. Die Zeitlogik hängt an den Daten, nicht am Eingang. Vertrag: [`datenbank/README.md`](datenbank/README.md).

Früher: LoRa-Eingang (`lora/`) und Wetter-Eingang (`wetter/`, S2120-CSV je Stand). Ihre Protokolle `lora_log/` und `wetter_log/` liest der Importer als Altbestand weiter.

## `plattform/`

Lese-API (FastAPI) und Oberfläche (Vue 3, Apache ECharts, ohne Build-Schritt) der eigenen Plattform, Phase B nur lesend: Übersicht, Volk-Cockpit, Umwelt, Datenquellen; Anmeldung mit einem Konto. Getestet mit synthetischen Daten (`plattform/synthetisch.py`). Siehe [`plattform/README.md`](plattform/README.md).

## Geplant

- Übertragung an BEEP mit Messzeitpunkt

Zugangsdaten gehören in nicht versionierte Dateien (siehe `.gitignore`).
Lizenz eigener Dateien: GPL-3.0-or-later.

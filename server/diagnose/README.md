# Nur lesende Diagnosen für den Datenmodell-Entwurf

**Status:** Entwurfs-Hilfswerkzeuge, nicht produktiv in den Datenfluss integriert.  
**Entwicklungs-/Änderungsklasse:** D1 (neues, nicht-invasives Hilfsskript) · **Prüfnachweis:** T0: Quellenabgleich; T1: Offline-Unit-Tests vorhanden, **von diesem Chat aus noch nicht ausgeführt**. **Kein T4/Feldtest**.

## beelogger1-Inventur

[`beelogger1_inventur.py`](beelogger1_inventur.py) prüft für ein Verzeichnis eines M.40-Single-Loggers **ausschließlich** bekannte CSV-Dateien und das Vorhandensein bestimmter PHP-Dateien. Es verändert nichts und führt keine PHP-Dateien aus.

Es gibt insbesondere **nicht** aus:

- CSV-Einzelwerte, Originalpayloads oder konkrete Datensatz-Zeitpunkte;
- Inhalte von `beelogger_config.php`, API-/Webhook-Tokens, LoRa-/BEEP-Schlüssel;
- Gerätekennungen oder private Standorte aus dem Datenbestand.

Die Ausgabe enthält **nur** Dateistatus, grobe Dateistatistiken, Anzahl untersuchter Zeilen, beobachtete Spaltenzahlen, Anzahl nichtleerer bekannter Feldpositionen und ggf. das Format-1/Format-2-Verhältnis der **Zusatzdatei**. **Nichtleer bedeutet nicht, dass der Sensor vorhanden, kalibriert oder aktiv ist.**

### Ausführung (kein sudo erforderlich, sofern Dateien lesbar)

```bash
cd /home/impy/bienen-lora-logger
python3 -m unittest discover -s tests/server -p 'test_beelogger1_inventur.py' -v
python3 server/diagnose/beelogger1_inventur.py \
  --root /var/www/bienen-logger/beelogger1 \
  > /home/impy/beelogger1_strukturinventur.json
```

**Sicherheitsgrenzen:** Keine Skripte als Root starten, nur weil Dateirechte nicht passen; zunächst Berechtigungen prüfen. Diagnosereports **außerhalb** des Webroots ablegen. Niemals den Inhalt einer geheimen Konfiguration oder roher TTN-Webhook-Logs öffentlich posten.

**Prüfprotokoll (Stand 12.10.2026):**
- **T0 – Quellenreview: ERFOLGT** anhand des bekannten M.40-Single-Layouts, `lora_funktionen.php` und der Inventur-Anforderungen.
- **T1 – Ausführung der Offline-Tests: NICHT GELAUFEN** in dieser Umgebung; Befehl oben steht bereit.
- **T4/HiL/Feld: NICHT GELAUFEN**.

Die tatsächliche Sensorhardware wird nicht automatisch erkannt: Sie muss anhand der **wirklich geflashten** Firmware-/Hardwarekonfiguration und Einbaupositionen ermittelt werden.

Fachliche Einordnung: [Ist-Inventur beelogger1](../../docs/architektur/ist-inventur-beelogger1.md).

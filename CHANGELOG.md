# Änderungen

## 2026-10-08 – TTN-Formatter

- `formatter/formatter.js`: FPort 1 (beelogger, gleiche Ausgabe wie das Original) und FPort 2 (Funkformat v2)
- `docs/funkformat-v2.md`: Spezifikation 1.0
- Tests: Vergleich mit dem Original-Formatter, Goldenes Paket, Fehlerfälle, Prüfung in goja
- `formatter/ttn_formatter.min.js` (3846 Byte) zum Einfügen in TTN

## 2026-10-08 – Server-Analyse, FFT-Konzept, Verbesserungsliste

- Server-Skripte M.40 unverändert in `server/beelogger_M40_original/`
- `docs/server-analyse.md`: LoRa-Eingang geprüft (u. a. Winterzeit-Fehler, Aux2 = RSSI, Aux3 = Sketch-ID)
- `docs/fft-konzept.md`: 4-Hz-Teilung, Anti-Aliasing, dBFS, Bandpegel
- `docs/verbesserungen.md`: Liste der Notbehelfe mit Prioritäten
- Lastenheft: Mikrofon-Filter A2/A7 neu

## 2026-10-08 – Datenformat

- `docs/datenformat.md`: Daten weiter an den beelogger-Webserver, neues Funkformat auf FPort 2, Formatter liefert beelogger-Feldnamen

## 2026-10-08 – Lastenheft Platine 0.3

- Ra-01SH festgelegt (Datenblatt ausgewertet: Quarz statt TCXO, HF-Schalter über DIO2)
- neue Firmware ohne beelogger-Kompatibilität, neue Pinbelegung, USB-C
- Platine 121 × 121 mm nach Camdenboss-Zeichnung CBHUB_02 Rev. N

## 2026-10-08 – Lastenheft Platine 0.2

- Funk SX1262-Modul (E22-900M22S oder Ra-01SH), Firmware-Folgen beschrieben (RadioLib)
- Mikrofon GY-MAX4466 mit Entstörung, Akku per Kabel, Gehäuse CBHUB-02-GY mit Reserve

## 2026-10-08 – Firmware STM32_LORA_261008_ZS (Testversion, Review-Stand 2)

Grundlage: beelogger `STM32_LORA_260705`.

- MCCI LoRaWAN LMIC library statt LMIC-Arduino 1.5.0
- Zeitabgleich per LoRaWAN `DeviceTimeReq` einmal täglich, RTC läuft in UTC
- Weckraster `k × Intervall + LOGGER_SLOT × 10 s + 1 s`, Nachtfenster in Ortszeit mit EU-Sommerzeit
- 8 Kanäle, ADR aus
- RTC-Lesen ohne veraltetes Datum nach Mitternacht (STM32RTC 1.3.7, Schattenregister)
- Bei LMIC-Fehler schlafen statt Endlosschleife
- Plausibilitätsprüfung der Uhr beim Wecken; Prüfwort für die Backup-Register
- Frame-Counter beim Sendeversuch fortschalten
- Sketch-ID nur in jedem 10. Paket (Fehler im Original)
- Gerätedaten in `Config_Geraet.h` ausgelagert (nicht im Repo)

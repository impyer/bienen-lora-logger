# Änderungen

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

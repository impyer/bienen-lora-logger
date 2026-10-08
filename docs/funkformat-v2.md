# Funkformat v2 (FPort 2) – Spezifikation 1.0 (08.10.2026)

Gilt für die verbesserte beelogger-Firmware und die neue Firmware der eigenen Platine.
Dekodiert wird es von `formatter/formatter.js`; die Referenz für die Kodierung ist `tests/formatter/kodierer_v2.js`.
Alle Mehrbyte-Werte sind **Big Endian**.

## Aufbau

| Byte | Inhalt |
|---|---|
| 0 | Formatversion, immer `0x02` |
| 1–4 | Kopf: 32-Bit-Feld (uint32). Bit k gesetzt = Wert k folgt |
| 5 … | Werte in aufsteigender Bitreihenfolge, ohne Lücken |

Ein fehlender Messwert wird nicht gesendet: Sein Bit bleibt 0. Es gibt keine Ersatzwerte wie −127 oder 85,0.

## Werte

| Bit | Wert | Typ | Einheit / Umrechnung | Bereich | JSON (Formatter) |
|---|---|---|---|---|---|
| 0 | Außentemperatur (BME280) | int16 | 0,01 °C | −327,68 … 327,67 | `TempOut` |
| 1 | Außenfeuchte | uint8 | 0,5 % | 0 … 100 (Rohwert 0–200) | `FeuchteOut` |
| 2 | Luftdruck | uint16 | 0,1 hPa | 0 … 6553,5 | `Aux1` |
| 3 | Innentemperatur 1 (DS18B20 Nr. 1, Brut) | int16 | 0,01 °C | | `TempIn` |
| 4 | Innentemperatur 2 (DS18B20 Nr. 2) | int16 | 0,01 °C | | `TempIn2` (Name in `NAME.tIn2` einstellbar) |
| 5 | Gewicht 1 | int24 | 1 g | ±8388 kg | `Gewicht` (kg) |
| 6 | Gewicht 2 | int24 | 1 g | | `Gewicht2` (kg) |
| 7 | Akkuspannung | uint16 | 1 mV | 0 … 65,535 V | `VBatt` (V) |
| 8 | Solarspannung | uint16 | 1 mV | | `VSolar` (V) |
| 9 | Licht | uint16 | 1 lx | 0 … 65535 | `Licht` |
| 10 | Innenfeuchte | uint8 | 0,5 % | 0 … 100 | `FeuchteIn` |
| 11 | FFT-Spitze | uint16 + uint8 | Frequenz 0,1 Hz; Pegel −0,5 dBFS je Schritt | 0 … 6553,5 Hz; 0 … −127,5 dBFS | `FFT_Hz`, `FFT_dB` |
| 12 | FFT-Gesamtpegel | uint8 | −0,5 dBFS je Schritt | | `FFT_Gesamt_dB` |
| 13 | FFT-Bandpegel | uint8 n + n × uint8 | −0,5 dBFS je Schritt | n = 0 … 255 | `FFT_Baender_dB` (Liste) |
| 14 | Service | uint8 | wie beelogger | 0 … 255 | `Service` |
| 15 | Zustand | uint8 Bits + uint8 Neustart-Grund | siehe unten | | `Status` (Objekt), `Neustart` |
| 16 | Messzeitpunkt | uint32 | Unix-Sekunden UTC | | `Messzeit_unix`, `Messzeit` (ISO 8601) |
| 17 | Firmware-ID | uint32 | z. B. 261008 | | `FirmwareID` |
| 18 | CPU-Temperatur STM32 | int16 | 0,01 °C | | `TempCPU` |
| 19–31 | reserviert | – | – | – | Der Formatter meldet einen Fehler. |

Zusätzlich gibt der Formatter immer `Format: 2` aus. **`Aux2` und `Aux3` gibt er bei v2 bewusst nicht aus**: Der beelogger-Server M.40 belegt sie bei LoRa anders (siehe `docs/server-analyse.md`, B3/B4).

Die Bandgrenzen der FFT legt die Firmware fest (Vorschlag in `docs/fft-konzept.md`). Das Paket enthält nur die Pegel.

### Zustand (Bit 15)

| Bit im ersten Byte | Bedeutung | JSON (`Status.…`) |
|---|---|---|
| 0 | Uhr abgeglichen, Messzeitpunkt gültig | `zeit_ok` |
| 1 | Außensensor ausgefallen | `fehler_aussen` |
| 2 | DS18B20 Nr. 1 ausgefallen | `fehler_ds1` |
| 3 | DS18B20 Nr. 2 ausgefallen | `fehler_ds2` |
| 4 | Waage 1 (HX711) ausgefallen | `fehler_waage1` |
| 5 | Waage 2 ausgefallen | `fehler_waage2` |
| 6 | Akku unter Warnschwelle | `akku_niedrig` |
| 7 | reserviert, 0 | – |

Zweites Byte, Neustart-Grund (`Neustart`):

| Wert | Grund |
|---|---|
| 0 | kein Neustart (planmäßiges Aufwachen aus dem Standby) oder unbekannt |
| 1 | Einschalten |
| 2 | Reset-Pin |
| 3 | Watchdog |
| 4 | Software |
| 5 | Unterspannung |
| 6 | Low-Power-Reset |

Warnungen des Formatters (TTN `warnings`): „Uhr des Loggers nicht abgeglichen“ (Bit 15 gesendet, `zeit_ok` = 0) und „Akku niedrig“.

## Regeln für die Firmware

- Werte vor dem Kodieren auf den Bereich begrenzen, nicht überlaufen lassen (wie im Referenz-Kodierer).
- Messzeitpunkt (Bit 16) nur senden, wenn die Uhr abgeglichen ist. Zustand (Bit 15) in jedem Paket.
- Firmware-ID (Bit 17) nach einem Neustart und dann in jedem 96. Paket (bei 15 min etwa einmal täglich), nicht in jedem Paket.
- Neue Werte nur über die reservierten Bits 19–31, und nur zusammen mit einer neuen Version des Formatters.

## Beispiel (Goldenes Paket der Tests, 51 Byte)

Werte:

- Außen −3,21 °C, 81,5 %, 1013,2 hPa
- Innen 34,56 °C und 18,07 °C
- Gewicht 45,678 kg und −0,123 kg
- Akku 3,912 V, Solar 5,432 V
- Licht 12345 lx, Innenfeuchte 55,5 %
- FFT: Spitze 247,3 Hz mit −23,5 dBFS, gesamt −18 dBFS; Bänder −40 / −22,5 / −30 / −45 / −60,5 / −70 dBFS
- Service 7
- Zustand: Uhr abgeglichen, Neustart-Grund 3 (Watchdog)
- Messzeitpunkt 08.10.2026 12:00:00 UTC
- Firmware 261008, CPU 21,5 °C

```
02 0007ffff febf a3 2794 0d80 070f 00b26e ffff85 0f48 1538 3039 6f 09a92f 24
06 50 2d 3c 5a 79 8c 07 0103 6ac785c0 0003fb90 0866
```

## Luftzeit

Mit allen Werten und 6 Bändern sind es 51 Byte, plus 13 Byte LoRaWAN-Rahmen.
Bei SF7/125 kHz sind das nach meiner Rechnung etwa 120 ms. Das gilt für unser Gateway in 5–8 m Entfernung.
**[P]** Mit dem TTN-Airtime-Rechner nachprüfen.

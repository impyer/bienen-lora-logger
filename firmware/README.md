# Firmware

`STM32_LORA_261008_ZS/` ist ein Arduino-Sketch für den beelogger-STM32 mit BlackPill STM32F411CE und RFM95W (LoRaWAN, ABP, TTN).
Er beruht auf beelogger `STM32_LORA_260705`. Alle Änderungen sind mit `ZS` markiert.

## Einrichtung Arduino-IDE

1. **Boardverwalter-URL:** `https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json`.
   Dann „STM32 MCU based boards“ installieren (getestet 2.6.0).
2. **Board-Einstellungen:**
   - Generic STM32F4 series, Board part number: BlackPill F411CE
   - U(S)ART support: Enabled (generic 'Serial')
   - USB support: None
   - Optimize: Smallest
   - C Runtime Library: Newlib Nano
3. **Bibliotheken:**

   | Bibliothek | Version (getestet) | Quelle |
   |---|---|---|
   | MCCI LoRaWAN LMIC library | 5.0.1 (6.0.1 übersetzt ebenfalls) | Bibliotheksverwalter |
   | STM32duino RTC | 1.3.7 | Bibliotheksverwalter oder beelogger-Paket |
   | STM32duino Low Power | 1.2.5 | Bibliotheksverwalter oder beelogger-Paket |
   | OneWire | 2.3.7 | beelogger-Paket |
   | HX711 Arduino Library | 0.7.4 | beelogger-Paket |
   | beeloggerEE und weitere beelogger-Bibliotheken je nach Sensoren | – | [beelogger-Bibliotheken](https://beelogger.de/?ddownload=200581) |

   **Achtung bei Updates:**
   - „STM32duino RTC“ ab 2.0.0 bricht mit STM32-Core 2.6.0 ab („not compatible with core version“); Version 2.0.0 braucht einen Core neuer als 2.12.
   - Wer „STM32duino Low Power“ über den Bibliotheksverwalter installiert, bekommt die neueste RTC-Bibliothek automatisch mit.
   - Deshalb Version 1.3.7 behalten oder die Bibliotheken aus dem beelogger-Paket nehmen.

4. **MCCI-Konfiguration:** In `libraries/MCCI_LoRaWAN_LMIC_library/project_config/lmic_project_config.h` diese zwei Zeilen ändern:
   ```
   #define CFG_eu868 1
   //#define CFG_us915 1
   ```
   Ein Update der Bibliothek überschreibt die Datei wieder. Der Sketch bricht dann mit einer klaren Meldung ab.
5. **Gerätedaten:** `Config_Geraet.beispiel.h` kopieren und die Kopie in `Config_Geraet.h` umbenennen.
   - Je Logger DevAddr, NwkSKey und AppSKey aus TTN eintragen.
   - Vor dem Aufspielen `GERAET` auf den Logger einstellen, der gerade programmiert wird.
   - `LOGGER_SLOT` ergibt sich daraus (`GERAET - 1`).
6. **Sensoren** wie gewohnt in `Config_MULTI.h` einstellen. Für den Feldbetrieb `myDEBUG 0` in `STM32_beelogger.h` setzen.

## Wichtige Schalter in `Config_LORA.h`

| Schalter | Standard | Bedeutung |
|---|---|---|
| `ZEITSYNC_aktiv` | 1 | Zeitabgleich und festes Weckraster; 0 = Weckraster wie im Original |
| `SLOT_ABSTAND_S` | 10 | Sekunden zwischen den Sendefenstern der Logger |
| `ZEITSYNC_INTERVALL_H` | 24 | Zeitabfrage höchstens alle x Stunden |
| `LORA_CHANNELS` | 8 | Anzahl der Kanäle; in TTN alle 8 als Factory preset eintragen |
| `LORA_ADR_aus` | 1 | ADR-Bit aus |
| `ZEITSYNC_TEST` | 0 | nur für den Tischtest: Abfrage bei jedem Senden, höchstens 1 Stunde |
| `FUNKFORMAT` | 2 | 2 = Funkformat v2 auf FPort 2 (braucht den neuen TTN-Formatter `formatter/ttn_formatter.min.js`); 1 = beelogger-Format wie im Original |
| `V2_ZEIT_GUELTIG_S` | 259200 | so lange nach dem letzten Zeitabgleich gilt die Uhr als genau (Messzeitpunkt wird gesendet) |
| `V2_FIRMWARE_JEDES_N` | 96 | Firmware-ID nach Neustart und in jedem n-ten Paket |
| `TEMP_IN2_SENSOR` | 9 bei 2 DS18B20, sonst 0 | Sensor-Nr. der 2. Innentemperatur (z. B. Deckel) |
| `MIC_PIN`, `MIC_ADC_KANAL` | PA1, 1 | Mikrofon; FFT einschalten mit `beelogger_Audio 1` in `Config_MULTI.h` |
| `MIC_ADC_DIREKT` | 1 | ADC über Register (schnell, gleichmäßig); 0 = `analogRead()` |

### Version 261009 (V2)

Änderungen gegen die ZS-Fassung sind mit `V2` markiert, der neue Teil steht in `STM32_LORA_v2.ino`, `funkformat_v2.h` und `bee_fft.h`.

- Funkformat v2 nach [`../docs/funkformat-v2.md`](../docs/funkformat-v2.md): Messwerte ohne Ersatzwerte, Zustandsbits, Messzeitpunkt, Neustart-Grund.
- FFT nach [`../docs/fft-konzept.md`](../docs/fft-konzept.md): Die Messung dauert etwa 1,25 s und verschiebt den Sendezeitpunkt bei allen Loggern gleich. Der Abstand der Sendefenster bleibt also erhalten.
- Mit `FUNKFORMAT 2` meldet ein ausgefallener Außensensor ein Zustandsbit. Früher sendete der Logger stattdessen die CPU-Temperatur. Ohne Außentemperatur korrigiert der Server das Gewicht nicht nach der Temperatur.
- **[P] Auf der Hardware ungeprüft:**
  - FFT-Abtastung (verpasste Abtastungen, Rauschpegel)
  - Neustart-Grund
  - Datensatz in TTN mit dem neuen Formatter

Hintergrund und Testablauf: [`../docs/zeitabgleich.md`](../docs/zeitabgleich.md).
TTN-Einstellungen: [`../docs/ttn-einrichtung.md`](../docs/ttn-einrichtung.md).

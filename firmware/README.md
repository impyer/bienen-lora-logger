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

Hintergrund und Testablauf: [`../docs/zeitabgleich.md`](../docs/zeitabgleich.md).
TTN-Einstellungen: [`../docs/ttn-einrichtung.md`](../docs/ttn-einrichtung.md).

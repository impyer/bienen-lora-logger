/****************************************************************/
// LORA Konfiguration
/****************************************************************/
// ZS 08.10.2026: MCCI LoRaWAN LMIC library (Bibliotheksverwalter, getestet mit 5.0.1)
// statt beelogger_arduino-lmic. <arduino_lmic.h> gibt es nur in der MCCI-Bibliothek,
// damit wählt die Arduino-IDE eindeutig diese aus, auch wenn die alte noch installiert ist.
// In der MCCI-Bibliothek project_config/lmic_project_config.h anpassen:
//   #define CFG_eu868 1          (CFG_us915 auskommentieren!)
//   #define CFG_sx1276_radio 1
#include <arduino_lmic.h>
#include <hal/hal.h>
#include <SPI.h>
#if !defined(CFG_eu868)
#error "MCCI-LMIC: in project_config/lmic_project_config.h CFG_eu868 setzen und CFG_us915 auskommentieren"
#endif

// Verbindungsparameter:
// Beispiel für LORA-http-Intergration Setting in der TTN config:
// https://community.beelogger.de/UserName/beelogger1/beelogger_log.php?Passwort=deinpasswort&LORA=1

// "################################################"
// "This code needs payloadformatter_220227.js"
// "################################################"

// Gerätedaten (DevAddr, Schlüssel, LOGGER_SLOT) stehen in Config_Geraet.h.
// Diese Datei ist im Repo absichtlich nicht enthalten (.gitignore), damit keine
// Schlüssel veröffentlicht werden. Vorlage: Config_Geraet.beispiel.h kopieren,
// in Config_Geraet.h umbenennen und die Werte aus der TTN-Konsole eintragen.
#if __has_include("Config_Geraet.h")
#include "Config_Geraet.h"
#else
#error "Config_Geraet.h fehlt: Config_Geraet.beispiel.h kopieren, umbenennen, Schluessel eintragen"
#endif

// LoRaWAN Network Prefix
static const uint16_t PREFIX =   0x13;     //   https://www.thethingsnetwork.org/docs/lorawan/prefix-assignments.html  
// example: 0x13 = TTN
//          0x01 = your own local Lora accesspoint


// number of LORA-Channels to be used  1, 3 or 8
// 1 = Single-Channel-Gateway, may be need to change frequency in STM32_LORA.ino
// 3 = three channels
// 8 = use all channels
#define LORA_CHANNELS 8     // ZS: 8 Kanäle (RAK7268V2). In TTN alle 8 Frequenzen als "Factory preset frequencies" eintragen

// turn LMIC-Lib Debug on/off.  "On" with this line commented out
#define NDEBUG 1


/****************************************************************/
// Allgemeine Konfiguration
/****************************************************************/
#define WeckIntervall       10          //  Weckintervall / Messzyklus

#define WeckIntervall_aktiv  1          // Manuelle Intervallsteuerung 0 = inaktiv, 1 = aktiv

#define WeckIntervall_Tag 10
#define WeckIntervall_Nacht 30
#define WeckIntervall_Nacht_Anfang 23
#define WeckIntervall_Nacht_Ende 6

#define WeckIntervall_Winter_aktiv  0   // Intervall Winter 0 = inaktiv, 1 = aktiv
#define WeckIntervall_Winter       60   // Intervall in Minuten
#define WeckIntervall_Winter_Anfang 9   // Monat Winterintervall Start
#define WeckIntervall_Winter_Ende   4   // Monat Winterintervall Ende

// alternative Messzyklusumschaltung
#define TEMP_ZYKLUS_aktiv    0            //  0 / 1 aktiviert Umschaltung Messzyklus Winter per Temperatur
const float Temperatur_Wintertag = 8.0;   // < = Wintertag
#define SOLAR_ZYKLUS_aktiv   0            //  0 / 1 aktiviert Umschaltung Messzyklus Tag/Nacht per Solarzellenspannung
const float SolarSpannung_Sommertag = 0.1;// < = Nacht



// 
#define AlternativIntervallMinuten  120  // Weckinterval, wenn VAlternativ erreicht


/****************************************************************/
// ZS: Zeitabgleich per LoRaWAN DeviceTimeReq und festes Weckraster
/****************************************************************/
#define ZEITSYNC_aktiv            1     // 0 = Verhalten wie Original (5-min-Raster auf eigener Uhr)
                                        // 1 = Uhr per Netz stellen, Raster in UTC, Versatz je Logger

// LOGGER_SLOT (0 ... 9, je Logger verschieden) steht in Config_Geraet.h
#define SLOT_ABSTAND_S            10    // Sekunden zwischen den Loggern (Slot 9 -> +90 s)

#define ZEITSYNC_INTERVALL_H      24    // Zeitabfrage höchstens alle x Stunden (TTN Fair Use: 10 Downlinks/Tag)
#define ZEITSYNC_WIEDERHOLUNG_MIN 60    // nach erfolgloser Abfrage frühestens nach x Minuten erneut
#define ZEITSYNC_MAX_SPRUNG_S     600   // größere Korrektur bei bereits synchroner Uhr erst beim 3. Mal annehmen
#define ZEIT_ZONE_STD_H           1     // MEZ = UTC+1, Sommerzeit nach EU-Regel automatisch
                                        // gilt für WeckIntervall_Nacht_Anfang/_Ende und Winter-Monate

#define LORA_ADR_aus              1     // 1 = ADR-Bit aus. Die MAC-Daten werden bei jedem Wecken zurückgesetzt,
                                        //     ADR-Befehle des Netzes kann der Logger ohnehin nicht behalten.
                                        // 0 = wie Original (ADR an)

// Nur für den Test am Musterlogger, danach wieder 0 setzen:
#define ZEITSYNC_TEST             0     // 1 = Zeitabfrage bei JEDEM Senden. Max. 1 Stunde betreiben (Fair Use)!
#define ZEITSYNC_TEST_VERSTELLEN_S 0    // nur mit ZEITSYNC_TEST 1: Uhr nach jedem Abgleich absichtlich um
                                        // x s verstellen (z.B. 5); der nächste Abgleich muss -x s korrigieren

/****************************************************************/
// V2: Funkformat v2 und FFT (docs/funkformat-v2.md, docs/fft-konzept.md)
/****************************************************************/
#define FUNKFORMAT                2     // 2 = Funkformat v2 auf FPort 2 (empfohlen, braucht formatter/ttn_formatter.min.js)
                                        // 1 = beelogger-Format auf FPort 1 wie im Original
#define V2_ZEIT_GUELTIG_S    259200UL   // Uhr gilt so lange nach dem letzten Abgleich als genau (3 Tage)
#define V2_FIRMWARE_JEDES_N       96    // Firmware-ID nach jedem Neustart und in jedem n-ten Paket senden
// #define TEMP_IN2_SENSOR         9    // Sensor-Nr. der 2. Innentemperatur (Vorgabe: 9 = DS18B20 Nr. 2,
                                        // wenn Anzahl_Sensoren_DS18B20 >= 2; 0 = keiner)
#define MIC_PIN                 PA1     // Mikrofon GY-MAX4466 (beelogger_Audio 1 in Config_MULTI.h)
#define MIC_EINSCHWINGEN_MS      100    // Wartezeit vor der Abtastung
#define MIC_ADC_DIREKT             1    // 1 = ADC1 direkt über Register (schnell, gleichmäßig); 0 = analogRead()
#define MIC_ADC_KANAL              1    // ADC1-Kanal von MIC_PIN: PA1 = IN1

#if (LOGGER_SLOT * SLOT_ABSTAND_S) > 240
#error "LOGGER_SLOT * SLOT_ABSTAND_S muss <= 240 s sein (kleinstes Intervall 5 min)"
#endif

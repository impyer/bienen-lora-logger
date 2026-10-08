/****************************************************************/
// Gerätedaten je Logger - VORLAGE
/****************************************************************/
// 1. Diese Datei kopieren und die Kopie in "Config_Geraet.h" umbenennen.
// 2. Je Logger einen Block mit den Werten aus der TTN-Konsole füllen
//    (End device -> Activation information: Device address, NwkSKey, AppSKey; MSB-Reihenfolge).
// 3. Vor dem Aufspielen GERAET auf den Logger einstellen, der gerade programmiert wird.
// Config_Geraet.h steht in .gitignore und wird nie veröffentlicht.

#define GERAET 1          // 1 ... 10 = beelogger-01 ... beelogger-10

#if GERAET == 1
static const u4_t DEVADDR = 0x00000000;
static const u1_t PROGMEM NWKSKEY[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
static const u1_t PROGMEM APPSKEY[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

#elif GERAET == 2
static const u4_t DEVADDR = 0x00000000;
static const u1_t PROGMEM NWKSKEY[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
static const u1_t PROGMEM APPSKEY[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

// #elif GERAET == 3 ... weitere Logger nach demselben Muster

#else
#error "GERAET: fuer diese Nummer ist kein Block eingetragen"
#endif

// Sendefenster: Logger 1 -> Slot 0, Logger 2 -> Slot 1, ... (je 10 s Abstand)
#define LOGGER_SLOT (GERAET - 1)

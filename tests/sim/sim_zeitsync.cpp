/*
   sim_zeitsync.cpp - Simulation mehrerer beelogger mit dem ECHTEN Zeitabgleich-Code des Sketches

   Eingebunden werden unverändert:
     ../../firmware/STM32_LORA_261008_ZS/beelogger_zeitsync.h     (Rechenlogik)
     ../../firmware/STM32_LORA_261008_ZS/STM32_LORA_zeitsync.ino  (Ablauf im Sketch)
   Nachgebildet (Modell, keine Messung!) werden: RTC mit Gangabweichung und Temperatur,
   MCCI-LMIC (Zeitabfrage/Antwort), Funkkanal mit Kollisionen, Gateway (Halbduplex),
   Netzserver-Latenz, Messdauer der Logger, optional die Wetterstation.

   Übersetzen (zwei Varianten, weil ZEITSYNC_aktiv eine Compile-Option ist):
     g++ -std=c++17 -O2 -DZEITSYNC_AKTIV=1 -o sim_sync sim_zeitsync.cpp
     g++ -std=c++17 -O2 -DZEITSYNC_AKTIV=0 -o sim_orig sim_zeitsync.cpp
   Aufruf z. B.:
     ./sim_sync --tage 30 --szenario herbst
     ./sim_sync --slots 0              (abgeglichen, aber alle Logger ohne Versatz)
     ./sim_orig --tage 30              (Original-Firmware)
   Alle Optionen: --hilfe
*/
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <ctime>
#include <string>
#include <vector>
#include <queue>
#include <random>
#include <algorithm>

#ifdef _WIN32
extern "C" __declspec(dllimport) int __stdcall SetConsoleOutputCP(unsigned int);
#endif
#ifndef ZEITSYNC_AKTIV
#define ZEITSYNC_AKTIV 1
#endif

/****************************************************************/
// Simulationszeit (wahre Zeit UTC in Mikrosekunden)
/****************************************************************/
static int64_t g_jetzt_us = 0;

/****************************************************************/
// Nachbildung MCCI-LMIC (nur was der ZS-Code benutzt)
/****************************************************************/
typedef int32_t ostime_t;
typedef uint32_t lmic_gpstime_t;
struct lmic_time_reference_s { ostime_t tLocal; lmic_gpstime_t tNetwork; };
typedef struct lmic_time_reference_s lmic_time_reference_t;
typedef void lmic_request_network_time_cb_t(void *pUserData, int flagSuccess);
#define OSTICKS_PER_SEC 62500
#define osticks2ms(os) ((int32_t)(((int64_t)(os) * 1000) / OSTICKS_PER_SEC))
#define ARDUINO_LMIC_VERSION 0x05000100
#define LMIC_ENABLE_DeviceTimeReq 1

static int64_t g_tick_basis_us = 0;   // Zeitpunkt des Weckens (Tick-Zähler startet beim Reset)
static int32_t g_tick_offset = 0;
static ostime_t ticks_bei(int64_t t_us) { return (ostime_t)((t_us - g_tick_basis_us) / 16 + g_tick_offset); }
[[maybe_unused]] static ostime_t os_getTime() { g_jetzt_us += 2; return ticks_bei(g_jetzt_us); }   // jeder Aufruf kostet 2 us

static lmic_request_network_time_cb_t *g_cb = nullptr;
static void *g_cb_ctx = nullptr;
static int g_ref_ok = 0;
static lmic_time_reference_t g_ref;
[[maybe_unused]] static void LMIC_requestNetworkTime(lmic_request_network_time_cb_t *cb, void *ctx) { g_cb = cb; g_cb_ctx = ctx; }
[[maybe_unused]] static int LMIC_getNetworkTimeReference(lmic_time_reference_t *r) { if (!g_ref_ok) return 0; *r = g_ref; return 1; }

/****************************************************************/
// Nachbildung STM32-RTC und Backup-Register
/****************************************************************/
static int g_vorteiler_reset = 0;   // 1: RTC beginnt beim Stellen eine neue Sekunde (unbestätigt)

struct SimRTC {
  double ms_bezug = 0;      // RTC-Stand in ms zum Zeitpunkt t_bezug_us
  int64_t t_bezug_us = 0;
  double ppm = 0;           // aktuelle Gangabweichung
  double stand_ms() const { return ms_bezug + (double)(g_jetzt_us - t_bezug_us) / 1000.0 * (1.0 + ppm * 1e-6); }
  void neuer_bezug() { ms_bezug = stand_ms(); t_bezug_us = g_jetzt_us; }
  // Nachbildung der Schattenregister (STM32F4, BYPSHAD=0): Lesen der Uhrzeit sperrt das
  // Datum, bis das Datum gelesen wird. STM32RTC 1.3.7 getEpoch(): erst Datum, dann Uhrzeit.
  bool dr_gesperrt = false;
  int64_t dr_tag = 0;
  long datum_veraltet = 0;   // Zähler: getEpoch() lieferte ein veraltetes Datum
  int64_t tag_jetzt() const { return (int64_t)std::floor(stand_ms() / 1000.0 / 86400.0); }
  int64_t datum_lesen() { int64_t d = dr_gesperrt ? dr_tag : tag_jetzt(); dr_gesperrt = false; return d; }
  time_t getEpoch(uint32_t *ss = nullptr) {
    int64_t tag = datum_lesen();                         // syncDate()
    double m = stand_ms();                               // syncTime() ...
    double s = std::floor(m / 1000.0);
    dr_gesperrt = true; dr_tag = tag_jetzt();            // ... sperrt das Datum
    if (ss) *ss = (uint32_t)(m - s * 1000.0);
    int64_t tageszeit = (int64_t)s % 86400;
    if (tag != (int64_t)s / 86400) datum_veraltet++;
    return (time_t)(tag * 86400 + tageszeit);
  }
  uint8_t getDay() { (void)datum_lesen(); return 1; }
  void setEpoch(time_t s, uint32_t sub = 0) {
    (void)sub;   // wie STM32RTC 1.3.7 auf F4: Bruchteil wird nicht übernommen
    double phase = std::fmod(stand_ms(), 1000.0);
    ms_bezug = (double)s * 1000.0 + (g_vorteiler_reset ? 0.0 : phase);
    t_bezug_us = g_jetzt_us;
    dr_gesperrt = false;
  }
};
static SimRTC rtc_stm;
static uint32_t g_bkp[20];
[[maybe_unused]] static uint32_t getBackupRegister(uint32_t i) { return g_bkp[i]; }
[[maybe_unused]] static void setBackupRegister(uint32_t i, uint32_t v) { g_bkp[i] = v; }
static void delayMicroseconds(uint32_t us) { g_jetzt_us += us; }
[[maybe_unused]] static uint32_t millis() { return (uint32_t)(g_jetzt_us / 1000); }

/****************************************************************/
// Debug-Ausgaben des Sketches
/****************************************************************/
static bool g_debug = false;
static void sim_p(const char *s) { if (g_debug) std::fputs(s, stdout); }
static void sim_p(char *s) { if (g_debug) std::fputs(s, stdout); }
[[maybe_unused]] static void sim_p(float v) { if (g_debug) std::printf("%.2f", v); }
[[maybe_unused]] static void sim_p(double v) { if (g_debug) std::printf("%.2f", v); }
template <typename T> static void sim_p(T v) { if (g_debug) std::printf("%s", std::to_string(v).c_str()); }
#define myDEBUG 1
#define debugprintF(x) sim_p(x)
#define debugprintlnF(x) do { sim_p(x); sim_p("\n"); } while (0)
#define debugprint(x) sim_p(x)
#define debugprintln(x) do { sim_p(x); sim_p("\n"); } while (0)
#define debugflush()

/****************************************************************/
// Konfiguration wie in Config_LORA.h (Slot/Abstand hier zur Laufzeit)
/****************************************************************/
#define ZEITSYNC_aktiv            ZEITSYNC_AKTIV
static uint8_t g_slot = 0, g_abstand = 10;
#define LOGGER_SLOT               (g_slot)
#define SLOT_ABSTAND_S            (g_abstand)
#define ZEITSYNC_INTERVALL_H      24
#define ZEITSYNC_WIEDERHOLUNG_MIN 60
#define ZEITSYNC_MAX_SPRUNG_S     600
#define ZEIT_ZONE_STD_H           1
#define ZEITSYNC_TEST             0
#define ZEITSYNC_TEST_VERSTELLEN_S 0
#define WeckIntervall_Tag 10
#define WeckIntervall_Nacht 30
#define WeckIntervall_Nacht_Anfang 23
#define WeckIntervall_Nacht_Ende 6

// Globale Variablen aus STM32_LORA_261008_ZS.ino
static uint32_t time_on = 0;
uint32_t zs_letzter_sync = 0;
uint32_t zs_letzter_versuch = 0;
uint8_t  zs_rtc_ist_utc = 0;
uint8_t  zs_fehler = 0;
uint8_t  zs_abgelehnt = 0;
int16_t  zs_letzte_korrektur_ds = 0;
uint32_t zs_geplante_weckzeit = 0;
int32_t  zs_vorige_korr_s = 0;
uint8_t  zs_hinweis = 0;

void zs_zeige_zeit(uint32_t t);
void zs_fehler_zaehlen(const char *grund);
void zs_ruecksetzen();
void zs_zeige_ms(int64_t ms);

/****************************************************************/
// Der echte Code
/****************************************************************/
#include "../../firmware/STM32_LORA_261008_ZS/beelogger_zeitsync.h"
#include "../../firmware/STM32_LORA_261008_ZS/STM32_LORA_zeitsync.ino"

/****************************************************************/
// Modell
/****************************************************************/
struct Optionen {
  int tage = 30;
  int logger = 10;
  int slots = 1;            // 1 = Versatz je Logger, 0 = alle Slot 0
  int abstand = 10;
  std::string szenario = "herbst";
  double p_antwort = 0.95;  // Netz antwortet und Logger empfängt
  double p_rx1 = 0.5;       // Antwort im RX1 (sonst RX2)
  double latenz_ms = 80;    // Netzzeit ist im Mittel um so viel zu spät (TTS ohne GPS-Gateway)
  double latenz_streu_ms = 40;
  int vorteiler_reset = 0;
  double messdauer_s = 10;  // Wecken bis Senden
  double messdauer_streu_s = 2;   // Unterschied zwischen den Loggern (+/-)
  double messdauer_jitter_s = 0.2;
  int station = 1;          // SenseCAP S2120 alle 10 min, eigener Takt
  int kanaele = 8;
  unsigned seed = 1;
  int debug_logger = -1;
  const char *csv = nullptr;
};

struct Logger {
  int nr;
  uint8_t slot;
  SimRTC rtc;
  uint32_t bkp[20];
  double ppm0, t_offset, messdauer_s;
  bool erster_start = true;
  // "RAM" zwischen den Schritten eines Weckvorgangs
  uint32_t r_time_on; uint32_t r_sync, r_vers; uint8_t r_utc, r_fehler, r_abgel; int16_t r_korr;
  uint32_t r_geplant; int32_t r_vorige; uint8_t r_hinweis;
  uint8_t r_antwort, r_laeuft; lmic_time_reference_t r_ref;
  int64_t r_tick_basis; int32_t r_tick_off;
  lmic_request_network_time_cb_t *r_cb; void *r_ctx;
  // Funk
  int64_t tx_start, tx_ende; int kanal; bool mit_abfrage;
  // Statistik
  long uplinks = 0, verloren = 0, abfragen = 0, antworten = 0, syncs = 0;
  double max_fehler_ms = 0;
  std::vector<double> fehler_ms;   // |RTC - UTC| beim Wecken (nach erstem Abgleich)
};

struct Ereignis { int64_t t; int logger; int schritt; bool operator<(const Ereignis &o) const { return t > o.t; } };
struct Funk { int64_t a, e; int kanal; int quelle; };

static Optionen O;
static std::mt19937_64 rng;
static double gleich(double a, double b) { return std::uniform_real_distribution<double>(a, b)(rng); }
static double normal(double m, double s) { return std::normal_distribution<double>(m, s)(rng); }

static double temperatur(const Logger &L, int64_t t_us) {
  double mittel = 10, amp = 6;
  if (O.szenario == "winter") { mittel = -2; amp = 5; }
  if (O.szenario == "sommer") { mittel = 22; amp = 10; }
  double h = std::fmod((double)t_us / 3.6e9 + 2.0, 24.0);   // grob Ortszeit
  return mittel + amp * std::sin(2 * 3.14159265358979 * (h - 9.0) / 24.0) + L.t_offset;
}
static double ppm_bei(const Logger &L, int64_t t_us) {
  double T = temperatur(L, t_us);
  return L.ppm0 - 0.034 * (T - 25.0) * (T - 25.0);   // typ. Uhrenquarz, Parabel um 25 °C
}

static double airtime_ms(int pl_bytes, int sf) {   // LoRa, BW125, CR4/5, Präambel 8, Header, CRC
  double tsym = std::pow(2.0, sf) / 125.0;
  int de = sf >= 11 ? 1 : 0;
  double n = 8 + std::max(std::ceil((8.0 * pl_bytes - 4 * sf + 28 + 16) / (4.0 * (sf - 2 * de))) * 5.0, 0.0);
  return (8 + 4.25) * tsym + n * tsym;
}

static void ram_rein(Logger &L) {
  rtc_stm = L.rtc; std::memcpy(g_bkp, L.bkp, sizeof(g_bkp)); g_slot = L.slot; g_abstand = (uint8_t)O.abstand;
  time_on = L.r_time_on; zs_letzter_sync = L.r_sync; zs_letzter_versuch = L.r_vers; zs_rtc_ist_utc = L.r_utc;
  zs_fehler = L.r_fehler; zs_abgelehnt = L.r_abgel; zs_letzte_korrektur_ds = L.r_korr;
  zs_geplante_weckzeit = L.r_geplant; zs_vorige_korr_s = L.r_vorige; zs_hinweis = L.r_hinweis;
  zs_antwort = L.r_antwort; zs_abfrage_laeuft = L.r_laeuft; zs_ref = L.r_ref;
  g_tick_basis_us = L.r_tick_basis; g_tick_offset = L.r_tick_off; g_cb = L.r_cb; g_cb_ctx = L.r_ctx;
  g_debug = (L.nr == O.debug_logger);
}
static void ram_raus(Logger &L) {
  L.rtc = rtc_stm; std::memcpy(L.bkp, g_bkp, sizeof(g_bkp));
  L.r_time_on = time_on; L.r_sync = zs_letzter_sync; L.r_vers = zs_letzter_versuch; L.r_utc = zs_rtc_ist_utc;
  L.r_fehler = zs_fehler; L.r_abgel = zs_abgelehnt; L.r_korr = zs_letzte_korrektur_ds;
  L.r_geplant = zs_geplante_weckzeit; L.r_vorige = zs_vorige_korr_s; L.r_hinweis = zs_hinweis;
  L.r_antwort = zs_antwort; L.r_laeuft = zs_abfrage_laeuft; L.r_ref = zs_ref;
  L.r_tick_basis = g_tick_basis_us; L.r_tick_off = g_tick_offset; L.r_cb = g_cb; L.r_ctx = g_cb_ctx;
  g_debug = false;
}

static void zeige_hilfe() {
  std::puts("Optionen: --tage N --logger N --slots 0|1 --abstand S --szenario herbst|winter|sommer\n"
            "          --p-antwort P --p-rx1 P --latenz-ms M --latenz-streu-ms M --vorteiler-reset 0|1\n"
            "          --messdauer S --messdauer-streu S --messdauer-jitter S --station 0|1 --kanaele N\n"
            "          --seed N --debug-logger N --csv DATEI");
}

int main(int argc, char **argv) {
#ifdef _WIN32
  SetConsoleOutputCP(65001);   // Umlaute in der Windows-Konsole
#endif
  for (int i = 1; i < argc; i++) {
    std::string a = argv[i];
    auto wert = [&](void) -> const char * { if (i + 1 >= argc) { zeige_hilfe(); std::exit(2); } return argv[++i]; };
    if (a == "--tage") O.tage = std::atoi(wert());
    else if (a == "--logger") O.logger = std::atoi(wert());
    else if (a == "--slots") O.slots = std::atoi(wert());
    else if (a == "--abstand") O.abstand = std::atoi(wert());
    else if (a == "--szenario") O.szenario = wert();
    else if (a == "--p-antwort") O.p_antwort = std::atof(wert());
    else if (a == "--p-rx1") O.p_rx1 = std::atof(wert());
    else if (a == "--latenz-ms") O.latenz_ms = std::atof(wert());
    else if (a == "--latenz-streu-ms") O.latenz_streu_ms = std::atof(wert());
    else if (a == "--vorteiler-reset") O.vorteiler_reset = std::atoi(wert());
    else if (a == "--messdauer") O.messdauer_s = std::atof(wert());
    else if (a == "--messdauer-streu") O.messdauer_streu_s = std::atof(wert());
    else if (a == "--messdauer-jitter") O.messdauer_jitter_s = std::atof(wert());
    else if (a == "--station") O.station = std::atoi(wert());
    else if (a == "--kanaele") O.kanaele = std::atoi(wert());
    else if (a == "--seed") O.seed = (unsigned)std::atoi(wert());
    else if (a == "--debug-logger") O.debug_logger = std::atoi(wert());
    else if (a == "--csv") O.csv = wert();
    else { zeige_hilfe(); return 2; }
  }
  rng.seed(O.seed);
  g_vorteiler_reset = O.vorteiler_reset;
  FILE *csv = O.csv ? std::fopen(O.csv, "w") : nullptr;
  if (csv) std::fprintf(csv, "device_id,tx_start_utc_s,tx_ende_utc_s,kanal,verloren,abfrage\n");

  const int64_t START = 1791460800LL * 1000000LL;   // 8.10.2026 12:00 UTC
  const int64_t ENDE = START + (int64_t)O.tage * 86400LL * 1000000LL;
  const double air_up = airtime_ms(13 + 18, 7);      // 18 Byte Nutzdaten
  const double air_dn1 = airtime_ms(18, 7), air_dn2 = airtime_ms(18, 9);

  std::vector<Logger> LG(O.logger);
  std::priority_queue<Ereignis> Q;
  for (int i = 0; i < O.logger; i++) {
    Logger &L = LG[i];
    L.nr = i; L.slot = (uint8_t)(O.slots ? i % 10 : 0);
    std::memset(L.bkp, 0, sizeof(L.bkp));
    L.ppm0 = gleich(-20, 20);                       // Toleranz bei 25 °C
    L.t_offset = gleich(-1.5, 1.5);
    L.messdauer_s = O.messdauer_s + gleich(-O.messdauer_streu_s, O.messdauer_streu_s);
    // System-Check: RTC = Compile-Zeit in MESZ, beim Flashen 20 ... 300 s alt
    L.rtc.ms_bezug = ((double)START / 1000.0) + 7200.0 * 1000.0 - gleich(20, 300) * 1000.0;
    L.rtc.t_bezug_us = START;
    L.r_cb = nullptr; L.r_ctx = nullptr;
    Q.push({START + (int64_t)(gleich(0, 600) * 1e6), i, 0});   // Akku eingelegt irgendwann in den ersten 10 min
  }
  std::vector<Funk> funk;          // Uplinks der Logger und Gateway-Downlinks (grob zeitlich sortiert)
  std::vector<Funk> station;       // Wetterstation (zeitlich sortiert)
  if (O.station) {
    double phase = gleich(0, 600), st_ppm = gleich(-20, 20);
    for (double t = phase; t < O.tage * 86400.0; t += 600.0 * (1 + st_ppm * 1e-6)) {
      int64_t a = START + (int64_t)(t * 1e6);
      station.push_back({a, a + (int64_t)(airtime_ms(13 + 40, 7) * 1000), (int)(rng() % O.kanaele), -1});
    }
  }
  auto station_ueberlappt = [&](int64_t a, int64_t e, int kanal) {
    auto it = std::lower_bound(station.begin(), station.end(), a - 1000000,
                               [](const Funk &f, int64_t t) { return f.a < t; });
    for (; it != station.end() && it->a < e; ++it)
      if (it->kanal == kanal && it->a < e && it->e > a) return true;
    return false;
  };

  long ul_gesamt = 0, ul_verl_koll = 0, ul_verl_gw = 0, downlinks = 0, st_verl = 0;
  std::vector<double> min_abst;    // Abstand zum nächsten fremden Uplink (s)
  std::vector<std::pair<int64_t, int>> weckzeiten;

  while (!Q.empty()) {
    Ereignis E = Q.top(); Q.pop();
    if (E.t >= ENDE) continue;
    Logger &L = LG[E.logger];
    g_jetzt_us = E.t;

    if (E.schritt == 0) {   // ---------------- Wecken (MCU-Reset) ----------------
      L.rtc.neuer_bezug(); L.rtc.ppm = ppm_bei(L, g_jetzt_us);
      ram_rein(L);
      g_tick_basis_us = g_jetzt_us; g_tick_offset = (int32_t)(rng() % 1000000);
      // RAM ist nach dem Reset leer
      time_on = 0; zs_letzter_sync = zs_letzter_versuch = 0; zs_rtc_ist_utc = zs_fehler = zs_abgelehnt = 0;
      zs_letzte_korrektur_ds = 0; zs_antwort = 0; zs_abfrage_laeuft = 0; g_cb = nullptr;
      zs_geplante_weckzeit = 0; zs_vorige_korr_s = 0; zs_hinweis = 0;
      rtc_stm.dr_gesperrt = false;   // nach dem Reset werden die Schattenregister neu geladen
      if (L.erster_start) { zs_ruecksetzen(); L.erster_start = false; }   // POR
      else zs_daten_holen();                                               // RST
      if (zs_rtc_ist_utc) {
        double f = std::fabs(rtc_stm.stand_ms() - (double)g_jetzt_us / 1000.0);
        L.fehler_ms.push_back(f);
        L.max_fehler_ms = std::max(L.max_fehler_ms, f);
      }
      weckzeiten.push_back({g_jetzt_us, L.nr});
      time_on = (uint32_t)rtc_stm.getEpoch();
      // Messung
      double md = L.messdauer_s + normal(0, O.messdauer_jitter_s);
      g_jetzt_us += (int64_t)(std::max(1.0, md) * 1e6);
      // Daten_Senden(): setup_LORA, prep_payload
      g_jetzt_us += 50000;
      zs_abfrage_vorbereiten();
      L.mit_abfrage = zs_abfrage_laeuft;
      L.tx_start = g_jetzt_us;
      L.tx_ende = g_jetzt_us + (int64_t)(air_up * 1000);
      L.kanal = (int)(rng() % O.kanaele);
      funk.push_back({L.tx_start, L.tx_ende, L.kanal, L.nr});
      ram_raus(L);
      Q.push({L.tx_ende + 2500000, L.nr, 1});   // EV_TXCOMPLETE nach RX2 + Reserve
    } else {                // ---------------- nach dem Senden ----------------
      ram_rein(L);
      // Uplink verloren? (gleicher Kanal überlappend oder Gateway sendet gerade)
      bool koll = false, gw = false;
      for (auto it = funk.rbegin(); it != funk.rend(); ++it) {
        if (it->a < L.tx_start - 60000000LL) break;   // Liste ist grob zeitlich sortiert (+/- Messdauer)
        if (it->quelle == L.nr && it->a == L.tx_start) continue;
        bool ueber = it->a < L.tx_ende && it->e > L.tx_start;
        if (!ueber) continue;
        if (it->quelle == -2) gw = true;
        else if (it->kanal == L.kanal) koll = true;
      }
      if (station_ueberlappt(L.tx_start, L.tx_ende, L.kanal)) koll = true;
      bool verloren = koll || gw;
      ul_gesamt++; L.uplinks++;
      if (koll) ul_verl_koll++;
      if (gw) ul_verl_gw++;
      if (verloren) L.verloren++;
      if (csv) std::fprintf(csv, "beelogger-%d,%.6f,%.6f,%d,%d,%d\n", L.nr, L.tx_start / 1e6, L.tx_ende / 1e6, L.kanal, verloren ? 1 : 0, L.mit_abfrage ? 1 : 0);

      if (L.mit_abfrage) {
        L.abfragen++;
        g_ref_ok = 0;
        if (!verloren && gleich(0, 1) < O.p_antwort) {
          // Netzserver: Zeit des Uplink-Endes, etwas zu spät (Latenz), GPS-Sekunden + 1/256
          double lat = std::max(0.0, normal(O.latenz_ms, O.latenz_streu_ms));
          int64_t netz_us = L.tx_ende + (int64_t)(lat * 1000);
          int64_t gps_us = netz_us - (int64_t)(ZS_GPS_UNIX_OFFSET - ZS_SCHALTSEKUNDEN) * 1000000LL;
          uint32_t gps_s = (uint32_t)(gps_us / 1000000LL);
          uint8_t frac = (uint8_t)(((gps_us % 1000000LL) * 256) / 1000000LL);
          g_ref.tNetwork = gps_s;
          g_ref.tLocal = ticks_bei(L.tx_ende) - (ostime_t)((int64_t)frac * OSTICKS_PER_SEC / 256);
          g_ref_ok = 1;
          // Downlink belegt das Gateway (Halbduplex)
          bool rx1 = gleich(0, 1) < O.p_rx1;
          int64_t da = L.tx_ende + (rx1 ? 1000000 : 2000000);
          funk.push_back({da, da + (int64_t)((rx1 ? air_dn1 : air_dn2) * 1000), -1, -2});
          downlinks++; L.antworten++;
          if (g_cb) g_cb(g_cb_ctx, 1);
        } else {
          if (g_cb) g_cb(g_cb_ctx, 0);
        }
      }
      uint32_t sync_vorher = zs_letzter_sync;
      zs_abfrage_auswerten();
      if (zs_letzter_sync != sync_vorher) L.syncs++;
      // System_ShutDown -> Alarm_konfigurieren (Tag/Nacht wie im Sketch)
      g_jetzt_us += 300000;
      uint32_t ttim = zs_rtc_jetzt(nullptr) + 1;   // wie Alarm_konfigurieren() im Sketch
      uint32_t t_ort = zs_ortszeit_rtc(ttim);
      uint8_t h = zs_stunde(t_ort);
      uint8_t I = ((h >= WeckIntervall_Nacht_Anfang) || (h < WeckIntervall_Nacht_Ende)) ? WeckIntervall_Nacht : WeckIntervall_Tag;
      uint32_t tt = zs_weckzeit(ttim, I);
      zs_daten_sichern();
      // wann erreicht die RTC tt? (Gang während des Schlafs)
      rtc_stm.neuer_bezug();
      rtc_stm.ppm = ppm_bei(L, g_jetzt_us + 300000000LL);
      double rest_ms = (double)tt * 1000.0 - rtc_stm.stand_ms();
      int64_t weck = g_jetzt_us + (int64_t)(rest_ms * 1000.0 / (1.0 + rtc_stm.ppm * 1e-6));
      ram_raus(L);
      if (weck <= g_jetzt_us) weck = g_jetzt_us + 1000000;
      Q.push({weck, L.nr, 0});
    }
  }

  // Abstand jedes Uplinks zum nächsten fremden Uplink
  std::vector<Funk> ups;
  for (auto &f : funk) if (f.quelle >= 0) ups.push_back(f);
  std::sort(ups.begin(), ups.end(), [](const Funk &x, const Funk &y) { return x.a < y.a; });
  // Wetterstation: Pakete, die ein Logger-Uplink oder ein Downlink stört
  std::vector<Funk> dns;
  for (auto &f : funk) if (f.quelle == -2) dns.push_back(f);
  std::sort(dns.begin(), dns.end(), [](const Funk &x, const Funk &y) { return x.a < y.a; });
  for (auto &s : station) {
    bool gest = false;
    auto it = std::lower_bound(ups.begin(), ups.end(), s.a - 1000000, [](const Funk &f, int64_t t) { return f.a < t; });
    for (; it != ups.end() && it->a < s.e; ++it) if (it->kanal == s.kanal && it->e > s.a) { gest = true; break; }
    auto jt = std::lower_bound(dns.begin(), dns.end(), s.a - 1000000, [](const Funk &f, int64_t t) { return f.a < t; });
    for (; !gest && jt != dns.end() && jt->a < s.e; ++jt) if (jt->e > s.a) gest = true;
    if (gest) st_verl++;
  }
  long unter1s = 0;
  for (size_t i = 1; i < ups.size(); i++) if (ups[i].quelle != ups[i - 1].quelle) {
    double d = (ups[i].a - ups[i - 1].a) / 1e6;
    min_abst.push_back(d);
    if (d < 1.0) unter1s++;
  }
  // Streuung der Messzeitpunkte: Weckzeiten innerhalb jedes 10-min-Fensters (tagsüber)
  std::sort(weckzeiten.begin(), weckzeiten.end());
  std::vector<double> streu;
  size_t j = 0;
  for (int64_t w = START + 3600LL * 1000000 - 30LL * 1000000; w < ENDE; w += 600LL * 1000000) {
    while (j < weckzeiten.size() && weckzeiten[j].first < w) j++;
    int64_t lo = INT64_MAX, hi = INT64_MIN; int n = 0;
    for (size_t k = j; k < weckzeiten.size() && weckzeiten[k].first < w + 600LL * 1000000; k++) {
      lo = std::min(lo, weckzeiten[k].first); hi = std::max(hi, weckzeiten[k].first); n++;
    }
    if (n == O.logger) streu.push_back((hi - lo) / 1e6);
  }
  std::sort(streu.begin(), streu.end());
  std::vector<double> alle_f;
  for (auto &L : LG) alle_f.insert(alle_f.end(), L.fehler_ms.begin(), L.fehler_ms.end());
  std::sort(alle_f.begin(), alle_f.end());
  auto quant = [](const std::vector<double> &v, double q) { return v.empty() ? NAN : v[(size_t)(q * (v.size() - 1))]; };

  std::printf("\n=== beelogger Zeitabgleich-Simulation (Modell, keine Messung) ===\n");
  std::printf("Firmware: %s | Versatz je Logger: %s (%d s) | %d Logger | %d Tage | Szenario %s\n",
              ZEITSYNC_AKTIV ? "ZS (Zeitabgleich)" : "Original", (O.slots && ZEITSYNC_AKTIV) ? "ja" : "nein", O.abstand,
              O.logger, O.tage, O.szenario.c_str());
  std::printf("Annahmen: Antwortquote %.0f %%, RX1-Anteil %.0f %%, Netzlatenz %.0f +/- %.0f ms, Messdauer %.0f +/- %.0f s,\n"
              "          Quarz +/-20 ppm bei 25 °C, Temperaturkoeffizient -0,034 ppm/°C², Vorteiler-Reset beim Stellen: %s\n",
              O.p_antwort * 100, O.p_rx1 * 100, O.latenz_ms, O.latenz_streu_ms, O.messdauer_s, O.messdauer_streu_s,
              O.vorteiler_reset ? "ja" : "nein (bis 1 s Fehler)");
  std::printf("\nUplinks gesamt:            %ld\n", ul_gesamt);
  std::printf("verloren durch Kollision:  %ld (%.3f %%)\n", ul_verl_koll, 100.0 * ul_verl_koll / std::max(1L, ul_gesamt));
  std::printf("verloren, Gateway sendet:  %ld (%.3f %%)\n", ul_verl_gw, 100.0 * ul_verl_gw / std::max(1L, ul_gesamt));
  std::printf("Downlinks (Zeitantworten): %ld  = %.2f pro Logger und Tag\n", downlinks, (double)downlinks / O.logger / O.tage);
  if (O.station) std::printf("Wetterstation (eigener 10-min-Takt): Pakete gestört: %ld von %lu\n", st_verl, (unsigned long)station.size());
  if (!min_abst.empty()) {
    std::sort(min_abst.begin(), min_abst.end());
    std::printf("Abstand aufeinanderfolgender Uplinks verschiedener Logger: min %.3f s, 1%%-Quantil %.3f s, unter 1 s: %ld\n",
                min_abst.front(), quant(min_abst, 0.01), unter1s);
  }
  if (!alle_f.empty())
    std::printf("Uhrfehler |RTC-UTC| beim Wecken: Median %.0f ms, 99%% %.0f ms, max %.0f ms\n",
                quant(alle_f, 0.5), quant(alle_f, 0.99), alle_f.back());
  if (!streu.empty())
    std::printf("Streuung der Weckzeiten aller Logger je 10-min-Fenster: Median %.1f s, max %.1f s\n",
                quant(streu, 0.5), streu.back());
  long veraltet = 0;
  for (auto &L : LG) veraltet += L.rtc.datum_veraltet;
  std::printf("RTC-Lesungen mit veraltetem Datum (Schattenregister): %ld\n", veraltet);
  std::printf("\nje Logger: Nr Slot  Uplinks verloren Abfragen Antworten Syncs  max|RTC-UTC|[ms]  Quarz[ppm@25°C]\n");
  for (auto &L : LG)
    std::printf("           %2d %4d  %7ld %8ld %8ld %9ld %5ld  %17.0f  %+8.1f\n", L.nr, L.slot, L.uplinks, L.verloren,
                L.abfragen, L.antworten, L.syncs, L.max_fehler_ms, L.ppm0);
  if (csv) std::fclose(csv);
  return 0;
}

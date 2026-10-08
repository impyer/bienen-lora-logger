/*
  V2: Funkformat v2 (FPort 2), FFT des Mikrofons, Zustand und Neustart-Grund
  Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later

  - prep_payload_v2(): Werte nach docs/funkformat-v2.md; keine Ersatzwerte, fehlende Werte werden nicht gesendet
  - Sensor_FFT(): Mikrofon an MIC_PIN mit 8192 Hz abtasten (DWT-Zyklenzähler), Auswertung in bee_fft.h
  - v2_neustart_lesen(): Grund des letzten Neustarts aus RCC->CSR, vor dem Löschen der Flags
*/
#include "funkformat_v2.h"
#include "bee_fft.h"

uint8_t  v2_neustart = FF2_NS_KEINER;   // Grund des letzten Neustarts (0 = Aufwachen aus Standby)
float    v2_temp_cpu = No_Val;          // CPU-Temperatur aus CPU_Sensors()
uint32_t v2_messzeit = 0;               // RTC-Zeit zu Beginn der Messung (UTC, wenn abgeglichen)

// FFT wird nur mit Mikrofon und Funkformat v2 gemessen (mit FUNKFORMAT 1 würde sie nicht gesendet)
#define V2_FFT_AKTIV (beelogger_Audio && (FUNKFORMAT == 2))

#if V2_FFT_AKTIV
static BfArbeit v2_fft_arbeit;
static uint16_t v2_roh[BF_ROH];         // 18,7 KB, nur während der Messung genutzt
#endif
#if beelogger_Audio
BfErgebnis v2_fft = { false, false, 0, 0, 0, 0, { 0 } };
uint32_t v2_fft_ueberlaeufe = 0;
#endif


/**
  @brief v2_neustart_lesen() – ganz am Anfang von System_Init() aufrufen,
  vor LowPower.begin() (löscht das Standby-Flag) und vor __HAL_RCC_CLEAR_RESET_FLAGS().
  Bei jedem Reset zieht der STM32 auch NRST, deshalb ist PINRST zuletzt geprüft.
*/
void v2_neustart_lesen() {
  if (__HAL_RCC_GET_FLAG(RCC_FLAG_PORRST)) v2_neustart = FF2_NS_EINSCHALTEN;
  else if (__HAL_RCC_GET_FLAG(RCC_FLAG_BORRST)) v2_neustart = FF2_NS_UNTERSPANNUNG;
  else if (__HAL_RCC_GET_FLAG(RCC_FLAG_IWDGRST) || __HAL_RCC_GET_FLAG(RCC_FLAG_WWDGRST)) v2_neustart = FF2_NS_WATCHDOG;
  else if (__HAL_RCC_GET_FLAG(RCC_FLAG_SFTRST)) v2_neustart = FF2_NS_SOFTWARE;
  else if (__HAL_RCC_GET_FLAG(RCC_FLAG_LPWRRST)) v2_neustart = FF2_NS_LOWPOWER;
  else if (__HAL_PWR_GET_FLAG(PWR_FLAG_SB) != RESET) v2_neustart = FF2_NS_KEINER;   // planmäßiges Aufwachen
  else if (__HAL_RCC_GET_FLAG(RCC_FLAG_PINRST)) v2_neustart = FF2_NS_PIN;
  else v2_neustart = FF2_NS_KEINER;
}


/**
  @brief Sensor_FFT() – Mikrofon abtasten und auswerten (nur mit beelogger_Audio 1)
  Takt über den DWT-Zyklenzähler: Abtastzeitpunkt i = Start + i · SystemCoreClock / 8192.
  Liegt eine Abtastung mehr als eine Periode zu spät, zählt sie als Überlauf; über 1 % wird verworfen.
*/
#if V2_FFT_AKTIV && MIC_ADC_DIREKT
// ADC1 direkt über Register: einmal einstellen, dann je Abtastung nur Start, Warten, Lesen (ca. 4 µs).
// analogRead() stellt den ADC bei jedem Aufruf neu ein und ist dafür zu langsam bzw. zu ungleichmäßig.
// Kanal: PA1 = ADC1_IN1 (STM32F411, Datenblatt Tabelle „Pin definitions“). Nach der Messung wird der ADC
// wieder abgeschaltet; analogRead() stellt ihn beim nächsten Aufruf selbst neu ein.
static void v2_adc_ein() {
  pinMode(MIC_PIN, INPUT_ANALOG);
  __HAL_RCC_ADC1_CLK_ENABLE();
  ADC->CCR = (ADC->CCR & ~ADC_CCR_ADCPRE) | ADC_CCR_ADCPRE_0;   // PCLK2 / 4 (96 MHz → 24 MHz, max. 36 MHz)
  ADC1->CR1 = 0;                                                // 12 Bit, keine Scan-Gruppe
  ADC1->CR2 = 0;                                                // Einzelwandlung, rechtsbündig
  ADC1->SMPR2 = (ADC1->SMPR2 & ~ADC_SMPR2_SMP1) | (ADC_SMPR2_SMP1_2);   // Kanal 1: 84 Takte Abtastzeit
  ADC1->SQR1 = 0;                                               // eine Wandlung
  ADC1->SQR3 = MIC_ADC_KANAL;
  ADC1->CR2 |= ADC_CR2_ADON;
  delayMicroseconds(10);                                        // Stabilisierung (Datenblatt: tSTAB 3 µs)
}
// Wandlung dauert ca. 4 µs (84 + 12 Takte bei 24 MHz). Kommt nach V2_ADC_TIMEOUT_US kein EOC,
// wird v2_adc_fehler gesetzt, die Messung abgebrochen und als ungültig verworfen (kein Hängenbleiben).
#define V2_ADC_TIMEOUT_US 50
static bool v2_adc_fehler = false;
static inline uint16_t v2_adc_lesen() {
  ADC1->SR = 0;
  ADC1->CR2 |= ADC_CR2_SWSTART;
  const uint32_t t0 = DWT->CYCCNT, grenze = (SystemCoreClock / 1000000u) * V2_ADC_TIMEOUT_US;
  while (!(ADC1->SR & ADC_SR_EOC)) {
    if ((DWT->CYCCNT - t0) > grenze) { v2_adc_fehler = true; return 0; }
  }
  return (uint16_t)ADC1->DR;
}
static void v2_adc_aus() {
  ADC1->CR2 &= ~ADC_CR2_ADON;
}
#endif

void Sensor_FFT() {
#if V2_FFT_AKTIV
  CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
  DWT->CYCCNT = 0;
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

#if MIC_ADC_DIREKT
  v2_adc_fehler = false;
  v2_adc_ein();
  (void)v2_adc_lesen();
#else
  analogReadResolution(12);
  (void)analogRead(MIC_PIN);
#endif
  delay(MIC_EINSCHWINGEN_MS);  // Mikrofon-Modul nach dem Einschalten stabilisieren

  const uint32_t periode = SystemCoreClock / BF_FS_ADC;
  uint32_t ueber = 0;
  uint32_t start = DWT->CYCCNT + periode;
  for (uint32_t i = 0; i < BF_ROH; i++) {
    uint32_t ziel = start + (uint32_t)(((uint64_t)i * SystemCoreClock) / BF_FS_ADC);
    if ((int32_t)(DWT->CYCCNT - ziel) > (int32_t)periode) ueber++;
    while ((int32_t)(DWT->CYCCNT - ziel) < 0) {}
#if MIC_ADC_DIREKT
    v2_roh[i] = v2_adc_lesen();
    if (v2_adc_fehler) break;
#else
    v2_roh[i] = (uint16_t)analogRead(MIC_PIN);
#endif
  }
#if MIC_ADC_DIREKT
  v2_adc_aus();
#endif
  v2_fft_ueberlaeufe = ueber;
#if MIC_ADC_DIREKT
  if (v2_adc_fehler) {
    BfErgebnis leer = { false, false, 0, 0, 0, 0, { 0 } };
    v2_fft = leer;
    debugprintlnF("FFT: ADC antwortet nicht, Messung verworfen");
    debugflush();
    return;
  }
#endif
  v2_fft = bf_auswerten(&v2_fft_arbeit, v2_roh, ueber);

  debugprintF("FFT [Hz/dBFS]: ");
  debugprint(v2_fft.spitze_hz);
  debugprint(" / ");
  debugprint(v2_fft.spitze_db);
  debugprintF(" gesamt ");
  debugprint(v2_fft.gesamt_db);
  debugprintF(" SNR ");
  debugprint(v2_fft.snr_db);
  debugprintF(v2_fft.spitze_gueltig ? " (Spitze ok)" : " (keine deutliche Spitze)");
  debugprintF(" Ueberlaeufe ");
  debugprintln(ueber);
  debugflush();
#endif
}


/**
  @brief prep_payload_v2() – Datensatz im Funkformat v2 in payload[] schreiben
  @return Länge in Byte; sizeof(payload) bei Fehler (Daten_Senden() sendet dann nicht)
*/
byte prep_payload_v2() {
  FunkWerteV2 w;
  ff2_leeren(&w);
  uint8_t zustand = 0;

  uint32_t jetzt = zs_rtc_jetzt(NULL);
  bool zeit_ok = zs_rtc_ist_utc && zs_letzter_sync != 0 && jetzt >= zs_letzter_sync
                 && (jetzt - zs_letzter_sync) <= V2_ZEIT_GUELTIG_S;
  if (zeit_ok) zustand |= FF2_Z_ZEIT_OK;

#if (Aussenwerte > 0)
  if (SensorTemp[Aussenwerte] != No_Val) { w.t_aussen = SensorTemp[Aussenwerte]; ff2_setze(&w, FF2_T_AUSSEN); }
  else zustand |= FF2_Z_FEHLER_AUSSEN;
#if (Aussenwerte < 8)   // nur Sensoren mit Feuchte (1–7); 8–11 sind DS18B20
  if (SensorFeuchte[Aussenwerte] != No_Value) { w.h_aussen = SensorFeuchte[Aussenwerte]; ff2_setze(&w, FF2_H_AUSSEN); }
#endif
#endif
  if (Aux[0] != No_Value) { w.druck_hpa = Aux[0]; ff2_setze(&w, FF2_DRUCK); }

#if (Beute1 > 0)
  if (SensorTemp[Beute1] != No_Val) { w.t_innen1 = SensorTemp[Beute1]; ff2_setze(&w, FF2_T_INNEN1); }
  else zustand |= FF2_Z_FEHLER_DS1;
#if (Beute1 < 8)
  if (SensorFeuchte[Beute1] != No_Value) { w.h_innen = SensorFeuchte[Beute1]; ff2_setze(&w, FF2_H_INNEN); }
#endif
#endif
#if (TEMP_IN2_SENSOR > 0)
  if (SensorTemp[TEMP_IN2_SENSOR] != No_Val) { w.t_innen2 = SensorTemp[TEMP_IN2_SENSOR]; ff2_setze(&w, FF2_T_INNEN2); }
  else zustand |= FF2_Z_FEHLER_DS2;
#endif

  // Taragewicht 10 = Waage nicht kalibriert (so in Config_MULTI.h vorbelegt): Sensor_Gewicht() misst dann nicht,
  // Gewicht[] behält den Startwert 0,01. Nicht senden und nicht als Ausfall melden.
  if (Taragewicht[0] != 10) {
    if (Gewicht[0] != No_Value) { w.gewicht1_kg = Gewicht[0]; ff2_setze(&w, FF2_GEWICHT1); }
    else zustand |= FF2_Z_FEHLER_WAAGE1;
  }
#if (Anzahl_Sensoren_Gewicht > 1)
  if (Taragewicht[1] != 10) {
    if (Gewicht[1] != No_Value) { w.gewicht2_kg = Gewicht[1]; ff2_setze(&w, FF2_GEWICHT2); }
    else zustand |= FF2_Z_FEHLER_WAAGE2;
  }
#endif

  if (Batteriespannung != No_Value) { w.vbatt_v = Batteriespannung; ff2_setze(&w, FF2_VBATT); }
  if (Solarspannung != No_Value) { w.vsolar_v = Solarspannung; ff2_setze(&w, FF2_VSOLAR); }
  if (Licht != No_Value) { w.licht_lx = Licht; ff2_setze(&w, FF2_LICHT); }
  if (akku_save) zustand |= FF2_Z_AKKU_NIEDRIG;

#if beelogger_Audio
  if (v2_fft.gueltig) {
    if (v2_fft.spitze_gueltig) { w.fft_hz = v2_fft.spitze_hz; w.fft_db = v2_fft.spitze_db; ff2_setze(&w, FF2_FFT_SPITZE); }
    w.fft_gesamt_db = v2_fft.gesamt_db; ff2_setze(&w, FF2_FFT_GESAMT);
    w.fft_anzahl = BF_BAENDER;
    for (uint8_t b = 0; b < BF_BAENDER; b++) w.fft_baender_db[b] = v2_fft.band_db[b];
    ff2_setze(&w, FF2_FFT_BAENDER);
  }
#endif

  if (Service != No_Value) { w.service = Service; ff2_setze(&w, FF2_SERVICE); }
  w.zustand = zustand; w.neustart = v2_neustart; ff2_setze(&w, FF2_ZUSTAND);
  if (zeit_ok && v2_messzeit != 0) { w.messzeit = v2_messzeit; ff2_setze(&w, FF2_MESSZEIT); }
  if (v2_neustart != FF2_NS_KEINER || (LoRaSeqCounter % V2_FIRMWARE_JEDES_N) == 0) { w.firmware = (uint32_t)l_ID; ff2_setze(&w, FF2_FIRMWARE); }
  if (v2_temp_cpu != No_Val) { w.t_cpu = v2_temp_cpu; ff2_setze(&w, FF2_T_CPU); }

  size_t n = ff2_kodiere(&w, payload, sizeof(payload) - 1);
  if (n == 0) return sizeof(payload);
  return (byte)n;
}

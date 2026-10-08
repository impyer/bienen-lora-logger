// TTN-Payload-Formatter (Uplink) für bienen-lora-logger
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
//
// FPort 1: beelogger-Format (STM32_LORA_*, payloadformatter_220227.js), Ausgabe unverändert.
// FPort 2: Funkformat v2, siehe docs/funkformat-v2.md.
// Ausgabe-Feldnamen wie beim beelogger-Webserver (beelogger_log.php, LORA=1); neue Werte mit eigenen Namen.
// Bewusst ES5 (Laufzeit der The Things Stack).

// Feldnamen für Werte, die der beelogger nicht kennt: hier frei anpassbar.
var NAME = {
  tIn2: "TempIn2",        // 2. Innentemperatur (DS18B20 Nr. 2)
  fftHz: "FFT_Hz",        // Frequenz der stärksten Spitze
  fftDb: "FFT_dB",        // Pegel der Spitze, dBFS
  fftSum: "FFT_Gesamt_dB",
  fftBand: "FFT_Baender_dB",
  zeit: "Messzeit",       // ISO-8601 UTC
  zeitU: "Messzeit_unix",
  fw: "FirmwareID",
  tCpu: "TempCPU",
  status: "Status",
  reset: "Neustart"
};

function u16(b, i) { return (b[i] << 8) | b[i + 1]; }
function s16(b, i) { var v = u16(b, i); return v & 0x8000 ? v - 0x10000 : v; }
function s24(b, i) { var v = (b[i] << 16) | (b[i + 1] << 8) | b[i + 2]; return v & 0x800000 ? v - 0x1000000 : v; }
function u32(b, i) { return ((b[i] << 24) >>> 0) + (b[i + 1] << 16) + (b[i + 2] << 8) + b[i + 3]; }

// ---------- FPort 1: beelogger ----------
// Länge je Bit (Bytes), Name, Umrechnung; wie payloadformatter_220227.js
var V1 = [
  [2, "TempOut", function (b, i) { return s16(b, i) / 100; }],
  [1, "FeuchteOut", function (b, i) { return b[i]; }],
  [2, "VBatt", function (b, i) { return u16(b, i) / 1000; }],
  [2, "VSolar", function (b, i) { return u16(b, i) / 1000; }],
  [2, "Licht", function (b, i) { return u16(b, i); }],
  [2, "Gewicht", function (b, i) { return s16(b, i) / 100; }],
  [2, "TempIn", function (b, i) { return s16(b, i) / 100; }],
  [1, "FeuchteIn", function (b, i) { return b[i]; }],
  [2, "Gewicht2", function (b, i) { return s16(b, i) / 100; }],
  [2, "TempIn2", function (b, i) { return s16(b, i) / 100; }],
  [1, "FeuchteIn2", function (b, i) { return b[i]; }],
  [2, "Gewicht3", function (b, i) { return s16(b, i) / 100; }],
  [2, "Gewicht4", function (b, i) { return s16(b, i) / 100; }],
  [2, "Aux1", function (b, i) { return s16(b, i) / 10; }],
  [1, "Service", function (b, i) { return b[i]; }],
  [4, "Aux3", function (b, i) { return (b[i] << 24) | (b[i + 1] << 16) | (b[i + 2] << 8) | b[i + 3]; }]
];

function dekodiereV1(b, res) {
  if (b.length < 2) { res.errors.push("beelogger: zu kurz"); return; }
  var kopf = u16(b, b.length - 2), i = 0, k, f;
  for (k = 0; k < 16; k++) {
    if (!(kopf & (1 << k))) continue;
    f = V1[k];
    if (i + f[0] > b.length - 2) { res.errors.push("beelogger: Daten zu kurz für Bit " + k); return; }
    res.data[f[1]] = f[2](b, i);
    i += f[0];
  }
  if (i !== b.length - 2) res.errors.push("beelogger: Länge passt nicht zum Kopf (" + i + " statt " + (b.length - 2) + " Byte)");
  res.data.Format = 1;
}

// ---------- FPort 2: Funkformat v2 ----------
function db(v) { return v ? -v / 2 : 0; }   // Pegel: 0..255 → 0 .. −127,5 dBFS

// Bit, Länge (Bytes; 0 = variabel), Auswertung
var V2 = [
  [2, function (b, i, d) { d.TempOut = s16(b, i) / 100; }],                                   // 0
  [1, function (b, i, d) { d.FeuchteOut = b[i] / 2; }],                                       // 1
  [2, function (b, i, d) { d.Aux1 = u16(b, i) / 10; }],                                       // 2 Luftdruck hPa
  [2, function (b, i, d) { d.TempIn = s16(b, i) / 100; }],                                    // 3
  [2, function (b, i, d) { d[NAME.tIn2] = s16(b, i) / 100; }],                                // 4
  [3, function (b, i, d) { d.Gewicht = s24(b, i) / 1000; }],                                  // 5 g → kg
  [3, function (b, i, d) { d.Gewicht2 = s24(b, i) / 1000; }],                                 // 6
  [2, function (b, i, d) { d.VBatt = u16(b, i) / 1000; }],                                    // 7
  [2, function (b, i, d) { d.VSolar = u16(b, i) / 1000; }],                                   // 8
  [2, function (b, i, d) { d.Licht = u16(b, i); }],                                           // 9
  [1, function (b, i, d) { d.FeuchteIn = b[i] / 2; }],                                        // 10
  [3, function (b, i, d) { d[NAME.fftHz] = u16(b, i) / 10; d[NAME.fftDb] = db(b[i + 2]); }],  // 11
  [1, function (b, i, d) { d[NAME.fftSum] = db(b[i]); }],                                     // 12
  [0, function (b, i, d) {                                                                    // 13
    var n = b[i], a = [], k;
    for (k = 1; k <= n; k++) a.push(db(b[i + k]));
    d[NAME.fftBand] = a;
    return n + 1;
  }],
  [1, function (b, i, d) { d.Service = b[i]; }],                                              // 14
  [2, function (b, i, d) {                                                                    // 15
    var s = b[i];
    d[NAME.status] = {
      zeit_ok: !!(s & 1), fehler_aussen: !!(s & 2), fehler_ds1: !!(s & 4), fehler_ds2: !!(s & 8),
      fehler_waage1: !!(s & 16), fehler_waage2: !!(s & 32), akku_niedrig: !!(s & 64)
    };
    d[NAME.reset] = b[i + 1];
  }],
  [4, function (b, i, d) { var t = u32(b, i); d[NAME.zeitU] = t; d[NAME.zeit] = new Date(t * 1000).toISOString(); }], // 16
  [4, function (b, i, d) { d[NAME.fw] = u32(b, i); }],                                        // 17
  [2, function (b, i, d) { d[NAME.tCpu] = s16(b, i) / 100; }]                                 // 18
];

function dekodiereV2(b, res) {
  if (b.length < 5) { res.errors.push("v2: zu kurz"); return; }
  if (b[0] !== 2) { res.errors.push("v2: unbekannte Formatversion " + b[0]); return; }
  var kopf = u32(b, 1), i = 5, k, f, n;
  for (k = 0; k < 32; k++) {
    if (!(kopf & (1 << k))) continue;
    f = V2[k];
    if (!f) { res.errors.push("v2: Bit " + k + " ist reserviert"); return; }
    if (f[0] === 0) {
      if (i >= b.length || i + 1 + b[i] > b.length) { res.errors.push("v2: Daten zu kurz für Bit " + k); return; }
      n = f[1](b, i, res.data);
    } else {
      if (i + f[0] > b.length) { res.errors.push("v2: Daten zu kurz für Bit " + k); return; }
      f[1](b, i, res.data);
      n = f[0];
    }
    i += n;
  }
  if (i !== b.length) { res.errors.push("v2: " + (b.length - i) + " Byte zu viel"); return; }
  res.data.Format = 2;
  var st = res.data[NAME.status];
  if (st && !st.zeit_ok) res.warnings.push("Uhr des Loggers nicht abgeglichen");
  if (st && st.akku_niedrig) res.warnings.push("Akku niedrig");
}

function decodeUplink(input) {
  var res = { data: {}, warnings: [], errors: [] };
  if (input.fPort === 1) dekodiereV1(input.bytes, res);
  else if (input.fPort === 2) dekodiereV2(input.bytes, res);
  else res.errors.push("unbekannter FPort " + input.fPort);
  if (res.errors.length) delete res.data;
  return res;
}

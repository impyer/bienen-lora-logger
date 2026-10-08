// Tests für formatter/formatter.js (und die verkleinerte Fassung für TTN)
// Aufruf: node tests/formatter/test_formatter.js [pfad/zum/formatter.js]
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");
const { kodiere } = require("./kodierer_v2");

const wurzel = path.join(__dirname, "..", "..");
const datei = process.argv[2] || path.join(wurzel, "formatter", "formatter.js");

function lade(p) {
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(p, "utf8"), ctx, { filename: p });
  return ctx;
}
const neu = lade(datei);
const alt = lade(path.join(__dirname, "referenz", "payloadformatter_220227.js"));

let anzahl = 0, fehler = 0;
function test(name, fn) {
  anzahl++;
  try { fn(); } catch (e) { fehler++; console.log("FEHLER: " + name + "\n  " + e.message.split("\n").join("\n  ")); }
}
const protokoll = [];
function dek(port, bytes) {
  const r = JSON.parse(JSON.stringify(neu.decodeUplink({ fPort: port, bytes: bytes })));
  if (protokoll.length < 5000) protokoll.push({ fPort: port, bytes: bytes.slice(), erwartet: JSON.parse(JSON.stringify(r)) });
  return r;
}
function nah(a, b, tol, was) { if (Math.abs(a - b) > tol) throw new Error(was + ": " + a + " statt " + b); }

// Zufall mit festem Startwert, damit Läufe wiederholbar sind
let saat = 12345;
function zufall() { saat = (saat * 1103515245 + 12345) & 0x7fffffff; return saat / 0x7fffffff; }
function zz(lo, hi) { return Math.floor(lo + zufall() * (hi - lo + 1)); }

// ---------- FPort 1: wie STM32_LORA prep_payload() ----------
const LEN1 = [2, 1, 2, 2, 2, 2, 2, 1, 2, 2, 1, 2, 2, 2, 1, 4];
function beeloggerPaket(bits) {
  const d = []; let kopf = 0;
  for (let k = 0; k < 16; k++) {
    if (!(bits & (1 << k))) continue;
    kopf |= 1 << k;
    for (let j = 0; j < LEN1[k]; j++) d.push(zz(0, 255));
  }
  d.push((kopf >> 8) & 0xFF, kopf & 0xFF);
  return d;
}

test("FPort 1: gleiche Ausgabe wie payloadformatter_220227.js (2000 Zufallspakete)", () => {
  for (let n = 0; n < 2000; n++) {
    const b = beeloggerPaket(zz(0, 0xFFFF));
    const r = dek(1, b);
    assert.deepStrictEqual(r.errors, [], "Fehler bei " + JSON.stringify(b));
    const erwartet = JSON.parse(JSON.stringify(alt.Decoder(b, 1)));
    delete r.data.Format;
    assert.deepStrictEqual(r.data, erwartet, "Paket " + JSON.stringify(b));
  }
});

test("FPort 1: typisches Paket Musterlogger", () => {
  // TempOut 12,34 °C; FeuchteOut 67 %; VBatt 3,912 V; VSolar 5,1 V; Gewicht 45,67 kg; TempIn 34,56 °C; Aux1 1013,2 hPa; Service 0
  const b = [0x04, 0xD2, 67, 0x0F, 0x48, 0x13, 0xEC, 0x11, 0xD7, 0x0D, 0x80, 0x27, 0x94, 0x00, 0x60, 0x6F];
  const r = dek(1, b);
  assert.deepStrictEqual(r.errors, []);
  assert.deepStrictEqual(r.data, { TempOut: 12.34, FeuchteOut: 67, VBatt: 3.912, VSolar: 5.1, Gewicht: 45.67,
    TempIn: 34.56, Aux1: 1013.2, Service: 0, Format: 1 });
});

test("FPort 1: negative Temperatur und Gewicht", () => {
  const b = [0xFE, 0x0C, 0xFF, 0x9C, 0x00, 0x21];   // TempOut −5,00; Gewicht −1,00
  assert.deepStrictEqual(dek(1, b).data, { TempOut: -5, Gewicht: -1, Format: 1 });
});

test("FPort 1: zu kurz bzw. Länge passt nicht → Fehler statt NaN", () => {
  assert.ok(dek(1, [0x01]).errors.length);
  assert.ok(dek(1, [0x12, 0x00, 0x01]).errors.length);        // Bit 0 braucht 2 Byte
  assert.ok(dek(1, [0x12, 0x34, 0x56, 0x00, 0x01]).errors.length);
  assert.strictEqual(dek(1, [0x12, 0x00, 0x01]).data, undefined);
});

// ---------- FPort 2: Funkformat v2 ----------
const VOLL = { tOut: -3.21, hOut: 81.5, p: 1013.2, tIn1: 34.56, tIn2: 18.07, g1: 45.678, g2: -0.123,
  vBatt: 3.912, vSolar: 5.432, licht: 12345, hIn: 55.5, fftHz: 247.3, fftDb: -23.5, fftSum: -18,
  baender: [-40, -22.5, -30, -45, -60.5, -70], service: 7, status: 0x01, reset: 3, zeit: 1791460800,
  fw: 261008, tCpu: 21.5 };

test("FPort 2: Goldenes Paket (Hexwert steht in docs/funkformat-v2.md)", () => {
  const hex = Buffer.from(kodiere(VOLL)).toString("hex");
  assert.strictEqual(hex,
    "020007ffff" + "febf" + "a3" + "2794" + "0d80" + "070f" + "00b26e" + "ffff85" + "0f48" + "1538" + "3039" + "6f" +
    "09a92f" + "24" + "06502d3c5a798c" + "07" + "0103" + "6ac785c0" + "0003fb90" + "0866");
});

test("FPort 2: alle Werte zurückgelesen", () => {
  const r = dek(2, kodiere(VOLL));
  assert.deepStrictEqual(r.errors, []);
  assert.deepStrictEqual(r.warnings, []);
  assert.deepStrictEqual(r.data, {
    TempOut: -3.21, FeuchteOut: 81.5, Aux1: 1013.2, TempIn: 34.56, TempIn2: 18.07, Gewicht: 45.678, Gewicht2: -0.123,
    VBatt: 3.912, VSolar: 5.432, Licht: 12345, FeuchteIn: 55.5, FFT_Hz: 247.3, FFT_dB: -23.5, FFT_Gesamt_dB: -18,
    FFT_Baender_dB: [-40, -22.5, -30, -45, -60.5, -70], Service: 7,
    Status: { zeit_ok: true, fehler_aussen: false, fehler_ds1: false, fehler_ds2: false, fehler_waage1: false,
      fehler_waage2: false, akku_niedrig: false },
    Neustart: 3, Messzeit_unix: 1791460800, Messzeit: "2026-10-08T12:00:00.000Z", FirmwareID: 261008, TempCPU: 21.5,
    Format: 2 });
});

test("FPort 2: kein Aux2/Aux3 in der Ausgabe (beim beelogger-Server doppelt belegt)", () => {
  const d = dek(2, kodiere(VOLL)).data;
  assert.ok(!("Aux2" in d) && !("Aux3" in d));
});

test("FPort 2: nur Pflichtteil (leerer Kopf)", () => {
  assert.deepStrictEqual(dek(2, [2, 0, 0, 0, 0]), { data: { Format: 2 }, warnings: [], errors: [] });
});

test("FPort 2: Zufallspakete zurückgelesen (1000 Stück, Auflösung beachtet)", () => {
  for (let n = 0; n < 1000; n++) {
    const w = {};
    if (zufall() < .7) w.tOut = zz(-4000, 6000) / 100;
    if (zufall() < .7) w.tIn2 = zz(-4000, 6000) / 100;
    if (zufall() < .7) w.g1 = zz(-500000, 300000) / 1000;
    if (zufall() < .7) w.vBatt = zz(0, 65535) / 1000;
    if (zufall() < .5) { w.fftHz = zz(0, 6553) / 10; w.fftDb = -zz(0, 255) / 2; }
    if (zufall() < .5) w.baender = Array.from({ length: zz(0, 12) }, () => -zz(0, 255) / 2);
    if (zufall() < .5) { w.status = zz(0, 127); w.reset = zz(0, 6); }
    if (zufall() < .5) w.zeit = zz(1735689600, 2051222400);
    const r = dek(2, kodiere(w));
    assert.deepStrictEqual(r.errors, [], JSON.stringify(w));
    const d = r.data;
    if (w.tOut !== undefined) nah(d.TempOut, w.tOut, 0.005, "TempOut");
    if (w.tIn2 !== undefined) nah(d.TempIn2, w.tIn2, 0.005, "TempIn2");
    if (w.g1 !== undefined) nah(d.Gewicht, w.g1, 0.0005, "Gewicht");
    if (w.vBatt !== undefined) nah(d.VBatt, w.vBatt, 0.0005, "VBatt");
    if (w.fftHz !== undefined) { nah(d.FFT_Hz, w.fftHz, 0.05, "FFT_Hz"); nah(d.FFT_dB, w.fftDb, 0.25, "FFT_dB"); }
    if (w.baender !== undefined) assert.deepStrictEqual(d.FFT_Baender_dB, w.baender.map((x) => x || 0));
    if (w.zeit !== undefined) assert.strictEqual(d.Messzeit_unix, w.zeit);
    if (w.status !== undefined) assert.strictEqual(d.Status.zeit_ok, !!(w.status & 1));
  }
});

test("FPort 2: Warnungen bei Uhr nicht abgeglichen und Akku niedrig", () => {
  const r = dek(2, kodiere({ status: 0x40, reset: 1 }));
  assert.deepStrictEqual(r.warnings, ["Uhr des Loggers nicht abgeglichen", "Akku niedrig"]);
});

test("FPort 2: jedes Zustandsbit einzeln", () => {
  const namen = ["zeit_ok", "fehler_aussen", "fehler_ds1", "fehler_ds2", "fehler_waage1", "fehler_waage2", "akku_niedrig"];
  namen.forEach((n, k) => {
    const st = dek(2, kodiere({ status: 1 << k, reset: 5 })).data.Status;
    namen.forEach((m, j) => assert.strictEqual(st[m], j === k, n + " gesetzt, " + m + " geprüft"));
  });
});

test("FPort 2: Fehlerfälle", () => {
  const ok = kodiere(VOLL);
  assert.ok(dek(2, [2, 0, 0]).errors.length, "zu kurz");
  assert.ok(dek(2, [3, 0, 0, 0, 0]).errors.length, "falsche Version");
  assert.ok(dek(2, [2, 0, 8, 0, 0]).errors.length, "reserviertes Bit 19");
  assert.ok(dek(2, [2, 0x80, 0, 0, 0]).errors.length, "reserviertes Bit 31");
  assert.ok(dek(2, ok.slice(0, ok.length - 1)).errors.length, "ein Byte fehlt");
  assert.ok(dek(2, ok.concat([0])).errors.length, "ein Byte zu viel");
  assert.ok(dek(2, [2, 0, 0, 0x20, 0, 5, 1, 2]).errors.length, "Bandliste zu kurz");
  assert.strictEqual(dek(2, [3, 0, 0, 0, 0]).data, undefined, "keine Daten bei Fehler");
});

test("Unbekannter FPort → Fehler", () => {
  assert.ok(dek(3, [1, 2, 3]).errors.length);
});

test("Werte werden begrenzt statt überzulaufen (Kodierer)", () => {
  const d = dek(2, kodiere({ tOut: 400, vBatt: -1, fftDb: 10, fftHz: 100 })).data;
  assert.strictEqual(d.TempOut, 327.67);
  assert.strictEqual(d.VBatt, 0);
  assert.strictEqual(d.FFT_dB, 0);
});

if (process.env.VEKTOREN) fs.writeFileSync(process.env.VEKTOREN, JSON.stringify(protokoll));
console.log(path.relative(wurzel, datei) + ": " + (anzahl - fehler) + " von " + anzahl + " Tests bestanden");
process.exit(fehler ? 1 : 0);

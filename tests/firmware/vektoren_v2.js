// Erzeugt C-Testvektoren aus dem Referenz-Kodierer (tests/formatter/kodierer_v2.js)
// Aufruf: node tests/firmware/vektoren_v2.js > <ausgabe.h>
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"use strict";
const { kodiere } = require("../formatter/kodierer_v2");
const f = Math.fround;

let saat = 4711;
function zufall() { saat = (saat * 1103515245 + 12345) & 0x7fffffff; return saat / 0x7fffffff; }
function zz(lo, hi) { return Math.floor(lo + zufall() * (hi - lo + 1)); }

// Feld im Kodierer -> [Bit, C-Feld]
const FELDER = [
  ["tOut", 0, "t_aussen"], ["hOut", 1, "h_aussen"], ["p", 2, "druck_hpa"], ["tIn1", 3, "t_innen1"], ["tIn2", 4, "t_innen2"],
  ["g1", 5, "gewicht1_kg"], ["g2", 6, "gewicht2_kg"], ["vBatt", 7, "vbatt_v"], ["vSolar", 8, "vsolar_v"], ["licht", 9, "licht_lx"],
  ["hIn", 10, "h_innen"], ["fftSum", 12, "fft_gesamt_db"], ["service", 14, "service"], ["tCpu", 18, "t_cpu"]
];

const faelle = [];
// Goldenes Paket aus den Formatter-Tests
faelle.push({ tOut: -3.21, hOut: 81.5, p: 1013.2, tIn1: 34.56, tIn2: 18.07, g1: 45.678, g2: -0.123, vBatt: 3.912, vSolar: 5.432,
  licht: 12345, hIn: 55.5, fftHz: 247.3, fftDb: -23.5, fftSum: -18, baender: [-40, -22.5, -30, -45, -60.5, -70], service: 7,
  status: 1, reset: 3, zeit: 1791460800, fw: 261008, tCpu: 21.5 });
faelle.push({});
// Grenzwerte: Begrenzen statt Überlaufen
faelle.push({ tOut: 400, tIn1: -400, hOut: 120, hIn: -3, p: 7000, g1: 9000, g2: -9000, vBatt: -1, vSolar: 70, licht: 70000,
  fftHz: 7000, fftDb: 10, fftSum: -200, service: 300, tCpu: -1000 });
for (let n = 0; n < 300; n++) {
  const w = {};
  for (const [k] of FELDER) if (zufall() < 0.6) {
    const bereich = { tOut: [-40, 60], hOut: [0, 100], p: [900, 1100], tIn1: [-40, 60], tIn2: [-40, 60], g1: [-5, 200], g2: [-5, 200],
      vBatt: [2.5, 4.3], vSolar: [0, 7], licht: [0, 65535], hIn: [0, 100], fftSum: [-127, 0], service: [0, 255], tCpu: [-20, 70] }[k];
    w[k] = bereich[0] + zufall() * (bereich[1] - bereich[0]);
  }
  if (zufall() < 0.5) { w.fftHz = zufall() * 1024; w.fftDb = -zufall() * 127; }
  if (zufall() < 0.4) w.baender = Array.from({ length: zz(0, 12) }, () => -zufall() * 127.5);
  if (zufall() < 0.5) { w.status = zz(0, 127); w.reset = zz(0, 6); }
  if (zufall() < 0.5) w.zeit = zz(1735689600, 2051222400);
  if (zufall() < 0.2) w.fw = zz(0, 4294967295);
  faelle.push(w);
}

// Werte auf float runden, damit C (float) und JS (double) von derselben Zahl ausgehen
for (const w of faelle) {
  for (const k of Object.keys(w)) if (typeof w[k] === "number" && !["status", "reset", "zeit", "fw"].includes(k)) w[k] = f(w[k]);
  if (w.baender) w.baender = w.baender.map(f);
}

function cf(x) { return Number.isFinite(x) ? x.toPrecision(9) + "f" : "0.0f"; }
const out = ["// Erzeugt von tests/firmware/vektoren_v2.js – nicht von Hand ändern", "struct Ff2Testfall { FunkWerteV2 w; uint8_t n; uint8_t b[64]; };",
  "static Ff2Testfall ff2_faelle[" + faelle.length + "];", "static void ff2_faelle_fuellen() {", "  FunkWerteV2 *w;"];
faelle.forEach((t, i) => {
  const bytes = kodiere(t);
  out.push(`  w = &ff2_faelle[${i}].w; ff2_leeren(w);`);
  for (const [k, bit, c] of FELDER) if (t[k] !== undefined) out.push(`  w->${c} = ${cf(t[k])}; ff2_setze(w, ${bit});`);
  if (t.fftHz !== undefined) out.push(`  w->fft_hz = ${cf(t.fftHz)}; w->fft_db = ${cf(t.fftDb)}; ff2_setze(w, 11);`);
  if (t.baender !== undefined) {
    out.push(`  w->fft_anzahl = ${t.baender.length}; ff2_setze(w, 13);`);
    t.baender.forEach((b, j) => out.push(`  w->fft_baender_db[${j}] = ${cf(b)};`));
  }
  if (t.status !== undefined) out.push(`  w->zustand = ${t.status}; w->neustart = ${t.reset || 0}; ff2_setze(w, 15);`);
  if (t.zeit !== undefined) out.push(`  w->messzeit = ${t.zeit}UL; ff2_setze(w, 16);`);
  if (t.fw !== undefined) out.push(`  w->firmware = ${t.fw}UL; ff2_setze(w, 17);`);
  out.push(`  ff2_faelle[${i}].n = ${bytes.length};`);
  out.push(`  { static const uint8_t e[] = {${bytes.join(",")}}; for (unsigned j = 0; j < sizeof(e); j++) ff2_faelle[${i}].b[j] = e[j]; }`);
});
out.push("}");
process.stdout.write(out.join("\n") + "\n");

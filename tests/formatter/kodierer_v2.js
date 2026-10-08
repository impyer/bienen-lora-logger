// Referenz-Kodierer für Funkformat v2 (docs/funkformat-v2.md).
// Dient den Tests und als Vorlage für die C-Umsetzung in der Firmware.
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"use strict";

function rund(x) { return Math.round(x); }
function begrenze(x, lo, hi) { return Math.min(hi, Math.max(lo, x)); }
function i16(x) { x = begrenze(rund(x), -32768, 32767) & 0xFFFF; return [x >> 8, x & 0xFF]; }
function u16(x) { x = begrenze(rund(x), 0, 65535); return [x >> 8, x & 0xFF]; }
function i24(x) { x = begrenze(rund(x), -8388608, 8388607) & 0xFFFFFF; return [x >> 16, (x >> 8) & 0xFF, x & 0xFF]; }
function u32(x) { x = begrenze(rund(x), 0, 4294967295); return [(x >>> 24) & 0xFF, (x >>> 16) & 0xFF, (x >>> 8) & 0xFF, x & 0xFF]; }
function pegel(dbfs) { return begrenze(rund(-dbfs * 2), 0, 255); }   // 0 .. −127,5 dBFS
function feuchte(p) { return begrenze(rund(p * 2), 0, 200); }

// w: Objekt mit optionalen Werten in physikalischen Einheiten
function kodiere(w) {
  var kopf = 0, d = [];
  function setze(bit, bytes) { kopf |= (1 << bit); d.push.apply(d, bytes); }
  if (w.tOut !== undefined) setze(0, i16(w.tOut * 100));
  if (w.hOut !== undefined) setze(1, [feuchte(w.hOut)]);
  if (w.p !== undefined) setze(2, u16(w.p * 10));
  if (w.tIn1 !== undefined) setze(3, i16(w.tIn1 * 100));
  if (w.tIn2 !== undefined) setze(4, i16(w.tIn2 * 100));
  if (w.g1 !== undefined) setze(5, i24(w.g1 * 1000));
  if (w.g2 !== undefined) setze(6, i24(w.g2 * 1000));
  if (w.vBatt !== undefined) setze(7, u16(w.vBatt * 1000));
  if (w.vSolar !== undefined) setze(8, u16(w.vSolar * 1000));
  if (w.licht !== undefined) setze(9, u16(w.licht));
  if (w.hIn !== undefined) setze(10, [feuchte(w.hIn)]);
  if (w.fftHz !== undefined) setze(11, u16(w.fftHz * 10).concat([pegel(w.fftDb)]));
  if (w.fftSum !== undefined) setze(12, [pegel(w.fftSum)]);
  if (w.baender !== undefined) setze(13, [w.baender.length].concat(w.baender.map(pegel)));
  if (w.service !== undefined) setze(14, [begrenze(rund(w.service), 0, 255)]);
  if (w.status !== undefined) setze(15, [w.status & 0xFF, (w.reset || 0) & 0xFF]);
  if (w.zeit !== undefined) setze(16, u32(w.zeit));
  if (w.fw !== undefined) setze(17, u32(w.fw));
  if (w.tCpu !== undefined) setze(18, i16(w.tCpu * 100));
  return [2].concat(u32(kopf >>> 0), d);
}

module.exports = { kodiere: kodiere };

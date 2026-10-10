// Tests für formatter/s2120_beep_formatter.js (Wetterstation SenseCAP S2120)
// Aufruf: node tests/formatter/test_s2120_formatter.js [formatter.js]
// Mit VEKTOREN=<datei.json> werden die Ergebnisse für den goja-Vergleich (tests/formatter/goja) geschrieben.
// Erwartete Werte: von Hand nach dem Seeed-Decoder (SenseCAP-Decoder, S2120/TTN) gerechnet; die ersten beiden
// Nutzdaten sind echte Uplinks der Station am Hauptstand vom 10.10.2026.
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const datei = process.argv[2] || path.join(__dirname, "..", "..", "formatter", "s2120_beep_formatter.js");
const quelle = fs.readFileSync(datei, "utf8");
let anz = 0, fehler = 0;
function pruefe(name, ok, info) {
  anz++;
  if (!ok) { fehler++; console.log("FEHL - " + name + (info ? "\n       " + info : "")); }
}

// Vorsicht nach „Unexpected token ILLEGAL“ beim Einfügen in die TTN-Konsole (10.10.2026; Ursache nicht geklärt,
// goja selbst übersetzt UTF-8-Kommentare): Quelle nur ASCII, damit Kopieren über Editoren nichts verfälscht
pruefe("Quelle nur ASCII-Zeichen", /^[\x00-\x7F]*$/.test(quelle));

const ctx = {};
vm.createContext(ctx);
vm.runInContext(quelle, ctx);
const dek = (hex, fPort) => ctx.decodeUplink({ fPort: fPort || 3, bytes: Array.from(Buffer.from(hex, "hex")) });

const faelle = [
  { name: "echter Uplink 10.10. 04:51 (4A+4B+4C)",
    hex: "4A008045000004E60000004B013200000AA126794C0000000002FA",
    data: { t: 12.8, h: 69, l: 1254, uv: 0, wind_ms: 0, wind_dir_deg: 306, rain_mmh: 2.721, p: 98490, p_hpa: 984.9, gust_ms: 0, rain_mm: 0.762 }, warnings: [] },
  { name: "echter Uplink nach Join mit Block 04 davor",
    hex: "046401010201000505A04A006E59000000000000004B01030000000026594C000000000FE0",
    data: { battery_pct: 100, interval_min: 5, t: 11, h: 89, l: 0, uv: 0, wind_ms: 0, wind_dir_deg: 259, rain_mmh: 0, p: 98170, p_hpa: 981.7, gust_ms: 0, rain_mm: 4.064 }, warnings: [] },
  { name: "negative Temperatur −10,0 °C",
    hex: "4AFF9C45000004E6000000",
    data: { t: -10, h: 69, l: 1254, uv: 0, wind_ms: 0 }, warnings: [] },
  { name: "Grenzwerte: −0,1 °C, 200000 lx, UV 1,5, Wind 12,3 m/s",
    hex: "4AFFFF6400030D400F007B",
    data: { t: -0.1, h: 100, l: 200000, uv: 1.5, wind_ms: 12.3 }, warnings: [] },
  { name: "ältere Firmware ohne 4C",
    hex: "4A008045000004E60000004B013200000AA12679",
    data: { t: 12.8, h: 69, l: 1254, uv: 0, wind_ms: 0, wind_dir_deg: 306, rain_mmh: 2.721, p: 98490, p_hpa: 984.9 }, warnings: [] },
  { name: "Batterieblock 03 allein (keine Messwerte)",
    hex: "0364", data: { battery_pct: 100 }, warnings: [] },
  { name: "leer", hex: "", data: {}, warnings: [] },
  { name: "unbekannter Block",
    hex: "FF0102", data: {}, warnings: ["unknown block or too short at byte 0"] },
  { name: "abgeschnittener 4B nach gültigem 4A",
    hex: "4A008045000004E60000004B0132",
    data: { t: 12.8, h: 69, l: 1254, uv: 0, wind_ms: 0 }, warnings: ["unknown block or too short at byte 11"] },
];

const vektoren = [];
for (const f of faelle) {
  let r;
  try { r = dek(f.hex); } catch (e) { pruefe(f.name, false, "Laufzeitfehler: " + e.message); continue; }
  const ist = JSON.stringify({ data: r.data, warnings: r.warnings });
  const soll = JSON.stringify({ data: f.data, warnings: f.warnings });
  // Reihenfolge der Schlüssel ist egal
  const sortiert = (o) => JSON.stringify(o, Object.keys(o).sort());
  pruefe(f.name, sortiert(r.data) === sortiert(f.data) && JSON.stringify(r.warnings) === JSON.stringify(f.warnings),
    "soll: " + soll + "\n       ist:  " + ist);
  vektoren.push({ fPort: 3, bytes: Array.from(Buffer.from(f.hex, "hex")), erwartet: r });
}

// BEEP speichert nur t, h, p, l: diese Schlüssel müssen bei vollständigen Uplinks da sein
const voll = dek(faelle[0].hex).data;
pruefe("BEEP-Schlüssel t, h, p, l vorhanden", ["t", "h", "p", "l"].every((k) => typeof voll[k] === "number"));
// BEEP teilt p durch 100 und zeigt hPa (beobachtet 10.10.2026: 982.6 hPa gesendet -> 9.826 hPa angezeigt); p also in Pa
pruefe("p in Pa für BEEP, p_hpa in hPa", voll.p === 98490 && voll.p_hpa === 984.9, "p=" + voll.p + " p_hpa=" + voll.p_hpa);

if (process.env.VEKTOREN) fs.writeFileSync(process.env.VEKTOREN, JSON.stringify(vektoren));
console.log((fehler ? "FEHLER" : "OK") + ": S2120-Formatter " + (anz - fehler) + " von " + anz + " Prüfungen bestanden (" + path.basename(datei) + ")");
process.exit(fehler ? 1 : 0);

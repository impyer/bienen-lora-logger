// Tests für formatter/lsn50v2_d23_formatter.js (Bodensonde Dragino LSN50v2-D23)
// Aufruf: node tests/formatter/test_lsn50v2_d23_formatter.js [formatter.js]
// Erster Vektor: echter Uplink vom 14.10.2026 (Hauptstand). Der alte Boden-Eingang hat daraus mit dem Dragino-
// Decoder temp_5cm 12,4 / temp_20cm 12,3 gemacht – vertauscht; richtig ist weiß (C1) 12,3, rot (C2) 12,4.
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const datei = process.argv[2] || path.join(__dirname, "..", "..", "formatter", "lsn50v2_d23_formatter.js");
const quelle = fs.readFileSync(datei, "utf8");
let anz = 0, fehler = 0;
function pruefe(name, ok, info) {
  anz++;
  if (!ok) { fehler++; console.log("FEHL - " + name + (info ? "\n       " + info : "")); }
}
pruefe("Quelle nur ASCII-Zeichen (TTN-Konsole)", /^[\x00-\x7F]*$/.test(quelle));
const ctx = {};
vm.createContext(ctx);
vm.runInContext(quelle, ctx);
const dek = (hex, port = 2) => JSON.parse(JSON.stringify(ctx.decodeUplink({ fPort: port, bytes: Array.from(Buffer.from(hex, "hex")) })));
const gleich = (name, ist, soll) => pruefe(name, JSON.stringify(ist) === JSON.stringify(soll), "ist  " + JSON.stringify(ist) + "\n       soll " + JSON.stringify(soll));

gleich("echter Uplink 14.10.: Farben nach Dragino-Handbuch (C1 weiß, C2 rot, C3 schwarz)", dek("0E28007B00000C007C0083"),
  { data: { Work_mode: "DS18B20", BatV: 3.624, ALARM_status: "FALSE", temp_weiss: 12.3, temp_rot: 12.4, temp_schwarz: 13.1 } });
gleich("gleiches Payload als Base64 aus dem alten Boden-Protokoll", dek(Buffer.from("DigAewAADAB8AIM=", "base64").toString("hex")).data.temp_weiss, 12.3);
gleich("Frost: negative Temperaturen (FF3F = -19,3 °C wie im Handbuch)", dek("0E28FF3F00000CFF3FFFF6").data,
  { Work_mode: "DS18B20", BatV: 3.624, ALARM_status: "FALSE", temp_weiss: -19.3, temp_rot: -19.3, temp_schwarz: -1 });
gleich("fehlender Fühler (FFFF) → null, nicht -0,1 °C", dek("0E28FFFF00000D007CFFFF").data,
  { Work_mode: "DS18B20", BatV: 3.624, ALARM_status: "TRUE", temp_weiss: null, temp_rot: 12.4, temp_schwarz: null });
gleich("Alarmabfrage (Modus 31): nur Grenzwerte", dek("0E280000F61E7CF61E1E0A").data,
  { Work_mode: "ALARM", temp_weiss_min: -10, temp_weiss_max: 30, temp_rot_min: -10, temp_rot_max: 30, temp_schwarz_min: 30, temp_schwarz_max: 10 });
gleich("falscher FPort", dek("0E28007B00000C007C0083", 3), { errors: ["unknown FPort 3"] });
gleich("falsche Länge", dek("0E28007B"), { errors: ["expected 11 bytes, got 4"] });
gleich("unbekannter Modus", dek("0E28007B000004007C0083"), { errors: ["unknown mode 1"] });
pruefe("keine alten, vertauschten Namen", !/Temp_Red|Temp_White/.test(JSON.stringify(dek("0E28007B00000C007C0083"))));

console.log((fehler ? "FEHLER" : "OK") + ": LSN50v2-D23-Formatter " + (anz - fehler) + " von " + anz + " Prüfungen bestanden");
process.exit(fehler ? 1 : 0);

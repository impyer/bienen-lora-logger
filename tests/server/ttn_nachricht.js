// Erzeugt eine TTN-Uplink-Nachricht (wie Webhook "uplink_message") mit dem echten Formatter.
// Aufruf: node ttn_nachricht.js '<json-parameter>'
//   { "geraet": "beelogger-01", "fport": 2, "werte": {...Kodierer-Werte...} | "hex": "...",
//     "empfang": "2026-10-08T12:00:05.123456789Z", "f_cnt": 1, "rssi": [-80, -95] }
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { kodiere } = require("../formatter/kodierer_v2");

const p = JSON.parse(process.argv[2]);
const ctx = {};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "..", "formatter", "formatter.js"), "utf8"), ctx);

const bytes = p.hex ? Array.from(Buffer.from(p.hex, "hex")) : kodiere(p.werte || {});
const dek = ctx.decodeUplink({ fPort: p.fport, bytes: bytes });
const up = {
  f_port: p.fport,
  f_cnt: p.f_cnt || 1,
  frm_payload: Buffer.from(bytes).toString("base64"),
  rx_metadata: (p.rssi || [-80]).map((r, i) => ({ gateway_ids: { gateway_id: "gw-" + i }, rssi: r, snr: 9.5 - i })),
  settings: { data_rate: { lora: { bandwidth: 125000, spreading_factor: 7, coding_rate: "4/5" } }, frequency: "868100000" },
  received_at: p.empfang
};
if (!dek.errors.length) up.decoded_payload = dek.data;
if (dek.warnings.length) up.decoded_payload_warnings = dek.warnings;
if (p.ohne_decoded) delete up.decoded_payload;
process.stdout.write(JSON.stringify({
  end_device_ids: { device_id: p.geraet, application_ids: { application_id: "beelog-de-sn" } },
  received_at: p.empfang,
  uplink_message: up
}));

// SPDX-License-Identifier: GPL-3.0-or-later
const assert = require('node:assert/strict');
const { beepOriginalRoute } = require('../../integrations/beep-stockkarte/stockkarte_urls');
assert.equal(beepOriginalRoute(42), 'https://app.beep.nl/hives/42/inspections/');
assert.equal(beepOriginalRoute('42','hiveEdit'), 'https://app.beep.nl/hives/42/edit');
assert.equal(beepOriginalRoute(42,'newInspection'), 'https://app.beep.nl/inspect?hiveId=42');
assert.equal(beepOriginalRoute(42,'inspections','https://stockkarte.example.org'), 'https://stockkarte.example.org/hives/42/inspections/');
for (const bad of ['',null,0,-1,'../admin','123?token=abc','1/2','01']) assert.equal(beepOriginalRoute(bad),null);
for (const base of ['http://app.beep.nl','https://user:pass@app.beep.nl','https://app.beep.nl/private/','https://app.beep.nl?token=abc']) assert.equal(beepOriginalRoute(42,'inspections',base),null);
assert.equal(beepOriginalRoute(42,'unknown'),null);
console.log('BEEP-Original-Stockkartenrouten: PASS');

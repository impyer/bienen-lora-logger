// SPDX-License-Identifier: GPL-3.0-or-later
// Tests der Diagrammlogik der Oberfläche (server/plattform/web/diagramm.js), ohne Browser.
// Aufruf: node tests/plattform/test_diagramm.mjs
import assert from 'node:assert/strict';
import { achsenText, bilanzOptionen, ereignisMarken, ortstag, verlaufOptionen } from '../../server/plattform/web/diagramm.js';
import { bilanzVergleichOptionen, ereignisListe, milbenTage, referenzOptionen, stapelOptionen, summenOptionen } from '../../server/plattform/web/stapel.js';

let anz = 0, fehler = 0;
function test(name, fn) {
  anz++;
  try { fn(); console.log('bestanden  ' + name); } catch (e) { fehler++; console.log('FEHLER     ' + name + ': ' + e.message); }
}

const katalog = [
  { code: 'gewicht', name: 'Gewicht', einheit: 'kg', achse: 'gewicht', darstellung: 'linie', farbe: '#8a5a00' },
  { code: 'temperatur', name: 'Temperatur', einheit: '°C', achse: 'temperatur', darstellung: 'linie' },
  { code: 'windrichtung', name: 'Windrichtung', einheit: '°', achse: 'richtung', darstellung: 'pfeile' },
  { code: 'regen_summe', name: 'Niederschlag', einheit: 'mm', achse: 'regen', darstellung: 'balken' },
];
const antwort = {
  von: '2026-10-24T22:00:00+00:00', bis: '2026-10-25T04:00:00+00:00', raster_s: 60,
  reihen: [
    { messgroesse: 'gewicht', messstelle_id: 1, zone: 'waage', punkte: [['2026-10-24T23:30:00+00:00', 30], ['2026-10-25T00:30:00+00:00', null], ['2026-10-25T02:30:00+00:00', 29.5]] },
    { messgroesse: 'temperatur', messstelle_id: 2, zone: 'brutnest', punkte: [['2026-10-24T23:30:00+00:00', 33]] },
    { messgroesse: 'temperatur', messstelle_id: 3, zone: 'aussen', punkte: [['2026-10-24T23:30:00+00:00', 5]] },
  ],
};

test('je Katalog-Achse eine y-Achse, Reihen derselben Größe teilen sie', () => {
  const o = verlaufOptionen(antwort, katalog);
  assert.equal(o.yAxis.length, 2);
  assert.deepEqual(o.series.map((s) => s.yAxisIndex), [0, 1, 1]);
  assert.deepEqual(o.series.map((s) => s.name), ['Gewicht – Waage', 'Temperatur – Brutnest', 'Temperatur – außen']);
});

test('Lücken werden nicht verbunden, null bleibt null (keine 0)', () => {
  const s = verlaufOptionen(antwort, katalog).series[0];
  assert.equal(s.connectNulls, false);
  assert.equal(s.data[1][1], null);
});

test('relatives Gewicht: Abstand zum ersten Wert, Temperatur unverändert', () => {
  const o = verlaufOptionen(antwort, katalog, { relativ: true });
  assert.deepEqual(o.series[0].data.map((p) => p[1]), [0, null, -0.5]);
  assert.equal(o.series[1].data[0][1], 33);
  assert.equal(o.yAxis[0].name, 'Δ kg');
});

test('Auswahl blendet Reihen aus', () => {
  const o = verlaufOptionen(antwort, katalog, { sichtbar: new Set(['gewicht|1']) });
  assert.equal(o.series.length, 1);
  assert.equal(o.yAxis.length, 1);
});

test('Winterzeit: Achse beschriftet 02:30 zweimal (MESZ und MEZ)', () => {
  assert.equal(achsenText(Date.parse('2026-10-25T00:30:00Z')), '02:30');
  assert.equal(achsenText(Date.parse('2026-10-25T01:30:00Z')), '02:30');
  assert.match(achsenText(Date.parse('2026-10-24T22:00:00Z')), /25\.10\./);
});

test('Ortstag: Mitternacht in MESZ und am Umstellungstag (25 h)', () => {
  const [a, b] = ortstag('2026-10-07T10:00:00Z');
  assert.equal(a.toISOString(), '2026-10-06T22:00:00.000Z');
  assert.equal(b.toISOString(), '2026-10-07T22:00:00.000Z');
  const [c, d] = ortstag('2026-10-25T12:00:00Z');
  assert.equal(c.toISOString(), '2026-10-24T22:00:00.000Z');
  assert.equal(d.toISOString(), '2026-10-25T23:00:00.000Z');
});

test('Ereignisse: Behandlung als Band, Tarieren als Linie, Durchsicht nur_datum als Tagesband (K-03/K-04)', () => {
  const m = ereignisMarken({
    massnahmen: [{ art: 'behandlung', von: '2026-10-01T08:00:00Z', bis: '2026-10-11T08:00:00Z', zeitgenauigkeit: 'exakt' },
                 { art: 'tarieren', von: '2026-10-22T08:59:00Z', bis: '2026-10-22T09:01:00Z', zeitgenauigkeit: 'exakt' }],
    durchsichten: [{ zeit: '2026-10-07T10:00:00Z', zeitgenauigkeit: 'nur_datum' }, { zeit: '2026-10-02T12:30:00Z', zeitgenauigkeit: 'exakt' }],
  });
  assert.equal(m.flaechen.length, 2);
  assert.equal(m.flaechen[0][0].name, 'Behandlung');
  assert.equal(m.flaechen[0][1].xAxis, Date.parse('2026-10-11T08:00:00Z'));
  assert.match(m.flaechen[1][0].name, /Uhrzeit übernommen/);
  assert.equal(m.flaechen[1][0].xAxis, Date.parse('2026-10-06T22:00:00Z'));
  assert.deepEqual(m.linien.map((l) => l.name), ['Tarieren', 'Durchsicht']);
  assert.equal(m.linien[0].xAxis, Date.parse('2026-10-22T09:00:00Z'));
});

test('Pfeile für Windrichtung, Balken für Regen, Richtungsachse 0–360°', () => {
  const o = verlaufOptionen({ von: antwort.von, bis: antwort.bis, reihen: [
    { messgroesse: 'windrichtung', messstelle_id: 9, zone: 'luft_stand', punkte: [['2026-10-25T00:00:00Z', 350]] },
    { messgroesse: 'regen_summe', messstelle_id: 9, zone: 'luft_stand', punkte: [['2026-10-25T00:00:00Z', 1.2]] }] }, katalog);
  assert.equal(o.series[0].symbol, 'arrow');
  assert.equal(o.series[0].symbolRotate([0, 350]), -170);
  assert.equal(o.yAxis[0].max, 360);
  assert.equal(o.series[1].type, 'bar');
});

test('Tagesbilanz: Eingriffstage grau, sonst grün/rot', () => {
  const o = bilanzOptionen([{ tag: '2026-10-22', bilanz_kg: 0.1, mit_eingriff: false }, { tag: '2026-10-23', bilanz_kg: -30, mit_eingriff: true },
                            { tag: '2026-10-24', bilanz_kg: -0.2, mit_eingriff: false }, { tag: '2026-10-25', bilanz_kg: null, mit_eingriff: false }]);
  assert.deepEqual(o.series[0].data.map((d) => d.itemStyle.color), ['#2e7d32', '#b3b3b3', '#c62828']);
  assert.match(o.tooltip.formatter({ value: ['2026-10-23', -30], data: { eingriff: true } }), /nicht biologisch deuten/);
});

test('leere Antwort ergibt ein gültiges, leeres Diagramm', () => {
  const o = verlaufOptionen({ von: antwort.von, bis: antwort.bis, reihen: [] }, []);
  assert.equal(o.series.length, 0);
  assert.equal(o.yAxis.length, 1);
});

const ereignisse = {
  massnahmen: [{ id: 1, art: 'behandlung', von: '2026-10-20T08:00:00Z', bis: '2026-10-26T08:00:00Z', zeitgenauigkeit: 'exakt' }],
  durchsichten: [{ id: 2, zeit: '2026-10-25T10:00:00Z', zeitgenauigkeit: 'nur_datum' }],
  varroa: [{ id: 3, von: '2026-10-21T10:00:00Z', bis: '2026-10-24T10:00:00Z', milben: 30, milben_pro_tag: 10 }, { id: 4, von: '2026-10-25T00:00:00Z', bis: '2026-10-25T00:20:00Z', milben: 3, milben_pro_tag: null }],
};

test('Gestapelt: ein Feld je Achse, Milbenfall-Feld, Ereignisleiste; gemeinsame Zeitachse', () => {
  const o = stapelOptionen(antwort, katalog, { ereignisse });
  assert.equal(o.grid.length, 4);                                    // Gewicht, Temperatur, Milbenfall, Leiste
  assert.deepEqual(o.series.map((s) => s.xAxisIndex), [0, 1, 1, 2, 3]);
  assert.equal(new Set(o.xAxis.map((x) => `${x.min}-${x.max}`)).size, 1);
  assert.deepEqual(o.dataZoom[0].xAxisIndex, [0, 1, 2, 3]);
  assert.equal(o.series.find((s) => s.name === 'Milbenfall').type, 'bar');
  assert.ok(o.grid[1].top > o.grid[0].top + o.grid[0].height, 'Felder überlappen');
  assert.ok(o.hoehe > o.grid[2].top + o.grid[2].height);
});

test('Gestapelt: Temperatur nach Messstelle gefärbt, Gewicht im Entwurfsblau, Lücken nicht verbunden', () => {
  const o = stapelOptionen(antwort, katalog);
  assert.deepEqual(o.series.map((s) => s.color), ['#1f4e79', '#c2410c', '#8a918c']);
  assert.equal(o.series[0].connectNulls, false);
  assert.equal(o.series[0].data[1][1], null);
});

test('Gestapelt: Vorher/Nachher-Fenster als zusätzliche Bänder in jedem Feld', () => {
  const fenster = { vorher: { von: '2026-10-24T22:00:00Z', bis: '2026-10-25T00:00:00Z' }, nachher: { von: '2026-10-25T02:00:00Z', bis: '2026-10-25T04:00:00Z' } };
  const ohne = stapelOptionen(antwort, katalog, { ereignisse });
  const mit = stapelOptionen(antwort, katalog, { ereignisse, fenster });
  assert.equal(mit.series[0].markArea.data.length, ohne.series[0].markArea.data.length + 2);
  assert.equal(mit.series[1].markArea.data.length, ohne.series[1].markArea.data.length + 2);
});

test('Milbenfall: ein Balken je Ortstag der Liegedauer, Puderzucker ohne pro Tag weggelassen', () => {
  const t = milbenTage(ereignisse.varroa).map((p) => new Date(p[0]).toISOString().slice(0, 10));
  assert.deepEqual(t, ['2026-10-21', '2026-10-22', '2026-10-23']);
  assert.ok(milbenTage(ereignisse.varroa).every((p) => p[1] === 10));
});

test('Ereignisleiste: Buchstaben B/D/V, „nur Datum“ markiert; Behandlung vor dem Zeitraum steht am linken Rand', () => {
  const l = ereignisListe(ereignisse);
  assert.deepEqual(l.map((e) => e.buchstabe), ['B', 'V', 'V', 'D']);
  assert.equal(l.find((e) => e.buchstabe === 'D').nurDatum, true);
  const o = stapelOptionen(antwort, katalog, { ereignisse });
  const leiste = o.series.find((s) => s.name === 'Stockkarte');
  const b = leiste.data.find((d) => d.label.formatter === 'B');
  assert.equal(b.value[0], Date.parse(antwort.von));
});

const voelker = [
  { id: 1, name: 'A', tagesreferenz: [{ tag: '2026-10-01', referenz_kg: 30 }, { tag: '2026-10-02', referenz_kg: 31 }, { tag: '2026-10-03', referenz_kg: 20 }],
    tagesbilanz: [{ tag: '2026-10-02', bilanz_kg: 1, mit_eingriff: false }, { tag: '2026-10-03', bilanz_kg: -11, mit_eingriff: true }] },
  { id: 2, name: 'B', tagesreferenz: [{ tag: '2026-10-02', referenz_kg: 40 }], tagesbilanz: [] },
];

test('Vergleich: Nachtmedian relativ zum ersten Tag, Summen ohne Eingriffstage, Eingriff grau', () => {
  assert.deepEqual(referenzOptionen(voelker).series[0].data.map((p) => p[1]), [0, 1, -10]);
  assert.deepEqual(referenzOptionen(voelker, { relativ: false }).series[0].data.map((p) => p[1]), [30, 31, 20]);
  assert.deepEqual(summenOptionen(voelker).series[0].data.map((p) => p[1]), [1, 1]);
  assert.deepEqual(summenOptionen(voelker, { ohneEingriff: false }).series[0].data.map((p) => p[1]), [1, -10]);
  const b = bilanzVergleichOptionen(voelker);
  assert.deepEqual(b.xAxis.data, ['2026-10-02', '2026-10-03']);
  assert.equal(b.series[0].data[1].itemStyle.color, '#b3b3b3');
  assert.equal(b.series[1].data[0], null);
});

test('Tooltips maskieren Notizen und Namen (kein HTML aus Eingaben)', () => {
  const o = stapelOptionen(antwort, katalog, { ereignisse: { durchsichten: [{ id: 9, zeit: '2026-10-25T00:00:00Z', zeitgenauigkeit: 'exakt', notiz: '<img src=x onerror=alert(1)>' }] } });
  const leiste = o.series.find((s) => s.name === 'Stockkarte');
  const html = leiste.tooltip.formatter({ name: leiste.data[0].name, value: leiste.data[0].value, data: leiste.data[0] });
  assert.ok(!html.includes('<img') && html.includes('&lt;img'), html);
  const b = bilanzVergleichOptionen([{ id: 1, name: '<b>Volk</b>', tagesreferenz: [], tagesbilanz: [{ tag: '2026-10-02', bilanz_kg: 1, mit_eingriff: false }] }]);
  const t = b.tooltip.formatter([{ axisValue: '2026-10-02', marker: '', seriesName: '<b>Volk</b>', value: 1, data: {} }]);
  assert.ok(!t.includes('<b>') && t.includes('&lt;b&gt;'), t);
});

console.log(`${anz - fehler} von ${anz} bestanden`);
process.exit(fehler ? 1 : 0);

// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// ECharts-Optionen aus den Antworten der Lese-API bauen. Reine Funktionen ohne DOM (Test: tests/plattform/test_diagramm.mjs).
// Die Oberfläche kennt keine festen Sensorfelder: Achse, Farbe und Darstellung kommen aus dem Messgrößen-Katalog.

export const ZONE = 'Europe/Berlin';

const ZONEN = {
  brutnest: 'Brutnest', deckel: 'Deckel', aussen: 'außen', waage: 'Waage', flugloch: 'Flugloch', boden: 'Boden',
  luft_stand: 'Luft am Stand', elektronik: 'Elektronik', funk: 'Funk',
};
const MASSNAHMEN = {
  behandlung: 'Behandlung', fuetterung: 'Fütterung', ernte: 'Ernte', zarge_auf: 'Zarge auf', zarge_ab: 'Zarge ab',
  umsetzen: 'Umsetzen', tarieren: 'Tarieren', sonstiges: 'Maßnahme',
};
const KURZ_MS = 3600 * 1000;      // Maßnahmen kürzer als 1 h als Linie statt Band

const fmtZeit = new Intl.DateTimeFormat('de-DE', {
  timeZone: ZONE, day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
});
const fmtTag = new Intl.DateTimeFormat('de-DE', { timeZone: ZONE, weekday: 'short', day: '2-digit', month: '2-digit' });
const fmtStunde = new Intl.DateTimeFormat('de-DE', { timeZone: ZONE, hour: '2-digit', minute: '2-digit' });

// Text für HTML-Tooltips von ECharts maskieren: eigene Formatierer geben HTML zurück, Notizen und Namen sind Eingaben
export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// Dunkles Schema (M-07): Die Optionen nutzen die hellen Farben des Entwurfs. Für das dunkle Schema ersetzt
// farbenAnpassen() genau diese Werte durch die CSS-Farben der Seite; Datenfarben bleiben, außer dem dunklen Blau.
const HELL = { '#1a1f1c': 'text', '#3d4540': 'text', '#5b635e': 'leise', '#eef1ec': 'gitter', '#cdd3cb': 'linie', '#1f4e79': 'blau' };

export function farbenAnpassen(option, palette) {
  if (!palette || !palette.dunkel) return option;
  const tausch = (w) => {
    if (typeof w === 'string') { const k = HELL[w.toLowerCase()]; return k && palette[k] ? palette[k] : w; }
    if (Array.isArray(w)) return w.map(tausch);
    if (w && typeof w === 'object' && !(w instanceof Date)) return Object.fromEntries(Object.entries(w).map(([k, v]) => [k, tausch(v)]));
    return w;                                         // Zahlen, Funktionen (Formatierer) unverändert
  };
  const o = tausch(option);
  o.textStyle = { color: palette.leise, ...(o.textStyle || {}) };
  if (o.legend && !Array.isArray(o.legend)) o.legend = { ...o.legend, textStyle: { color: palette.text, ...(o.legend.textStyle || {}) } };
  return o;
}

export function zeitText(t) { return t ? fmtZeit.format(new Date(t)) : '–'; }

export function zahl(w, stellen = 1) {
  return w === null || w === undefined ? '–' : Number(w).toLocaleString('de-DE', { maximumFractionDigits: stellen, minimumFractionDigits: stellen });
}

// Achsenbeschriftung in Ortszeit: Mitternacht als Tag, sonst Uhrzeit (die doppelte Stunde der Winterzeit erscheint zweimal)
export function achsenText(ms) {
  const d = new Date(ms);
  const s = fmtStunde.format(d);
  return s === '00:00' ? fmtTag.format(d) : s;
}

export function reihenName(r, katalog) {
  const g = katalog[r.messgroesse];
  const ort = r.bezeichnung || ZONEN[r.zone] || r.zone || '';
  return (g ? g.name : r.messgroesse) + (ort ? ' – ' + ort : '');
}

export function reihenSchluessel(r) { return r.messgroesse + '|' + (r.messstelle_id ?? ''); }

// Mitternacht Ortszeit des Tages von t und des Folgetages (für Einträge mit zeitgenauigkeit 'nur_datum')
const fmtOrt = new Intl.DateTimeFormat('en-US', {
  timeZone: ZONE, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});
function ortText(ms) {   // "2026-10-25T00:00" in der Zone; formatToParts, weil die Reihenfolge je nach ICU-Fassung wechselt
  const t = Object.fromEntries(fmtOrt.formatToParts(new Date(ms)).map((p) => [p.type, p.value]));
  return `${t.year}-${t.month}-${t.day}T${t.hour}:${t.minute}`;
}

function mitternacht(tag) {
  // Zeitpunkt, an dem in der Zone tag 00:00 ist: Versatz der Zone durchprobieren (MEZ +1 h, MESZ +2 h usw.)
  const basis = Date.parse(tag + 'T00:00:00Z');
  for (let h = -14; h <= 14; h++) {
    const ms = basis - h * 3600000;
    if (ortText(ms) === tag + 'T00:00') return new Date(ms);
  }
  return new Date(basis);
}

// Eingabe aus <input type="datetime-local"> ("2026-10-20T14:30") als Ortszeit Europe/Berlin → ISO in UTC.
// In der doppelten Stunde der Winterzeit-Umstellung gilt die erste (Sommerzeit); eine Zeit in der übersprungenen
// Stunde (Frühjahr) gibt es nicht und ergibt null.
export function ortszeitNachUtc(text) {
  if (!/^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(text || '')) return null;
  const basis = Date.parse(text + ':00Z');
  for (let h = 14; h >= -14; h--) {
    const ms = basis - h * 3600000;
    if (ortText(ms) === text) return new Date(ms).toISOString();
  }
  return null;
}

// Jetzt als Wert für <input type="datetime-local"> in Ortszeit
export function jetztOrtszeit(ms = Date.now()) { return ortText(ms); }

// Ende des Ortstags tag ("2026-10-31") als ISO in UTC: Mitternacht des Folgetags in Europe/Berlin (exklusiv)
export function tagesEnde(tag) {
  if (!/^\d{4}-\d\d-\d\d$/.test(tag || '')) return '';
  return mitternacht(new Date(Date.parse(tag + 'T00:00:00Z') + 86400000).toISOString().slice(0, 10)).toISOString();
}

// Ortstag, zu dem ein exklusives Zeitraumende gehört (Ende 01.11. 00:00 → "2026-10-31"), für das Datumsfeld
export function bisTag(bis) { return bis ? ortText(Date.parse(bis) - 1).slice(0, 10) : ''; }

// Zeitraum aus der Adresse (?tage=14&bis=ISO): von/bis in UTC; ohne bis gilt jetzt
export function zeitraum(query, vorgabeTage = 14, jetzt = Date.now()) {
  const tage = Number(query.tage || vorgabeTage);
  const bisMs = query.bis ? Date.parse(query.bis) : jetzt;
  return { tage, bis: query.bis || '', von: new Date(bisMs - tage * 86400000).toISOString(), bisIso: new Date(bisMs).toISOString() };
}

export function ortstag(t) {
  const tag = ortText(Date.parse(t)).slice(0, 10);
  const morgen = new Date(Date.parse(tag + 'T00:00:00Z') + 86400000).toISOString().slice(0, 10);
  return [mitternacht(tag), mitternacht(morgen)];
}

function serienTyp(darstellung) {
  return { linie: 'line', stufe: 'line', balken: 'bar', punkte: 'scatter', pfeile: 'scatter' }[darstellung] || 'line';
}

// Ereignisse der Stockkarte als Bänder und Linien (markArea/markLine an der ersten Reihe)
export function ereignisMarken(ereignisse) {
  const flaechen = [], linien = [];
  for (const m of ereignisse?.massnahmen || []) {
    const name = MASSNAHMEN[m.art] || m.art;
    const von = Date.parse(m.von), bis = m.bis ? Date.parse(m.bis) : null;
    if (m.zeitgenauigkeit === 'nur_datum') {
      const [a, b] = ortstag(m.von);
      flaechen.push([{ name: name + ' (Uhrzeit übernommen)', xAxis: a.getTime(), itemStyle: { color: 'rgba(150,150,150,0.18)' } }, { xAxis: b.getTime() }]);
    } else if (bis !== null && bis - von >= KURZ_MS) {
      flaechen.push([{ name, xAxis: von, itemStyle: { color: m.art === 'behandlung' ? 'rgba(192,57,43,0.10)' : 'rgba(41,128,185,0.10)' } }, { xAxis: bis }]);
    } else {
      linien.push({ name, xAxis: bis !== null ? (von + bis) / 2 : von, lineStyle: { color: '#8e44ad', type: 'solid' } });
    }
  }
  for (const d of ereignisse?.durchsichten || []) {
    if (d.zeitgenauigkeit === 'nur_datum') {
      const [a, b] = ortstag(d.zeit);
      flaechen.push([{ name: 'Durchsicht (Uhrzeit übernommen)', xAxis: a.getTime(), itemStyle: { color: 'rgba(39,174,96,0.12)' } }, { xAxis: b.getTime() }]);
    } else {
      linien.push({ name: 'Durchsicht', xAxis: Date.parse(d.zeit), lineStyle: { color: '#27ae60', type: 'dashed' } });
    }
  }
  return { flaechen, linien };
}

// Hauptdiagramm: eine y-Achse je Katalog-Achse, Lücken (null) werden nicht verbunden
export function verlaufOptionen(antwort, katalogListe, { sichtbar = null, relativ = false, ereignisse = null } = {}) {
  const katalog = Object.fromEntries((katalogListe || []).map((g) => [g.code, g]));
  const reihen = (antwort?.reihen || []).filter((r) => !sichtbar || sichtbar.has(reihenSchluessel(r)));
  const achsen = [];
  for (const r of reihen) {
    const a = katalog[r.messgroesse]?.achse || r.messgroesse;
    if (!achsen.includes(a)) achsen.push(a);
  }
  const yAxis = achsen.map((a, i) => {
    const g = Object.values(katalog).find((k) => k.achse === a);
    const einheit = g?.einheit || '';
    return {
      type: 'value', name: (relativ && a === 'gewicht' ? 'Δ ' : '') + (einheit || a), position: i % 2 ? 'right' : 'left',
      offset: Math.floor(i / 2) * 52, scale: true, alignTicks: false, splitLine: { show: i === 0 },
      ...(a === 'richtung' ? { min: 0, max: 360, interval: 90 } : {}),
    };
  });
  const marken = ereignisMarken(ereignisse);
  const series = reihen.map((r, i) => {
    const g = katalog[r.messgroesse] || {};
    let punkte = r.punkte.map(([t, w]) => [Date.parse(t), w]);
    if (relativ && g.achse === 'gewicht') {
      const erster = punkte.find((p) => p[1] !== null);
      if (erster) punkte = punkte.map(([t, w]) => [t, w === null ? null : Math.round((w - erster[1]) * 1000) / 1000]);
    }
    const s = {
      name: reihenName(r, katalog), type: serienTyp(g.darstellung), yAxisIndex: achsen.indexOf(g.achse || r.messgroesse),
      data: punkte, connectNulls: false, showSymbol: g.darstellung === 'punkte' || g.darstellung === 'pfeile',
      symbolSize: 6, sampling: 'lttb', emphasis: { focus: 'series' },
    };
    if (g.farbe && !reihen.slice(0, i).some((x) => x.messgroesse === r.messgroesse)) s.color = g.farbe;
    if (g.darstellung === 'stufe') s.step = 'end';
    if (g.darstellung === 'pfeile') {
      s.symbol = 'arrow';
      s.symbolSize = 11;
      s.symbolRotate = (wert) => 180 - (Array.isArray(wert) ? wert[1] : wert);   // Pfeil zeigt, wohin der Wind weht
    }
    if (g.darstellung === 'balken') s.barMaxWidth = 8;
    if (i === 0) {
      s.markArea = { silent: true, label: { show: true, position: 'insideTop', fontSize: 10 }, data: marken.flaechen };
      s.markLine = { silent: true, symbol: 'none', label: { show: true, formatter: '{b}', fontSize: 10 }, data: marken.linien };
    }
    return s;
  });
  return {
    animation: false,
    grid: { left: 16 + 52 * Math.ceil(achsen.length / 2), right: 16 + 52 * Math.floor(achsen.length / 2), top: 40, bottom: 70, containLabel: false },
    legend: { type: 'scroll', top: 0 },
    tooltip: { trigger: 'axis', valueFormatter: (w) => (w === null || w === undefined ? 'keine Messung' : zahl(w, 2)),
               axisPointer: { label: { formatter: (p) => zeitText(p.value) } } },
    xAxis: { type: 'time', min: antwort ? Date.parse(antwort.von) : undefined, max: antwort ? Date.parse(antwort.bis) : undefined,
             axisLabel: { formatter: achsenText, hideOverlap: true } },
    yAxis: yAxis.length ? yAxis : [{ type: 'value' }],
    // Mausrad scrollt die Seite; Zoomen mit Strg + Mausrad, Ziehen oder dem Schieber
    dataZoom: [{ type: 'inside', zoomOnMouseWheel: 'ctrl', moveOnMouseWheel: false }, { type: 'slider', bottom: 10 }],
    series,
  };
}

// Tagesbilanz als Balken; Tage mit Eingriff grau und ausdrücklich gekennzeichnet (Leitplanke L8: nicht biologisch deuten)
// Achse der Tagesbilanz nach den Tagen ohne Eingriff (M-09): Ein Tarieren (−30 kg) soll die normalen Tage (±0,1 kg)
// nicht unsichtbar machen. Symmetrisch, mindestens ±0,5 kg, 20 % Rand. null = automatisch (keine Tage ohne Eingriff).
export function bilanzBereich(tage) {
  const w = (tage || []).filter((t) => t.bilanz_kg !== null && !t.mit_eingriff).map((t) => Math.abs(t.bilanz_kg));
  if (!w.length) return null;
  const r = Math.ceil(Math.max(0.5, ...w) * 1.2 * 10) / 10;
  return { min: -r, max: r };
}

// Eingriffsbalken außerhalb des Bereichs: abgeschnitten, Wert als Beschriftung
export function eingriffLabel(wert, bereich) {
  if (!bereich || (wert >= bereich.min && wert <= bereich.max)) return undefined;
  return { show: true, position: wert < 0 ? 'insideBottom' : 'insideTop', formatter: () => zahl(wert, 1), fontSize: 10, color: '#3d4540' };
}

export function bilanzOptionen(tage) {
  const bereich = bilanzBereich(tage);
  const daten = (tage || []).filter((t) => t.bilanz_kg !== null).map((t) => ({
    value: [t.tag, Math.round(t.bilanz_kg * 1000) / 1000],
    eingriff: t.mit_eingriff,
    itemStyle: { color: t.mit_eingriff ? '#b3b3b3' : (t.bilanz_kg >= 0 ? '#2e7d32' : '#c62828') },
    label: eingriffLabel(t.bilanz_kg, bereich),
  }));
  return {
    animation: false,
    grid: { left: 56, right: 16, top: 24, bottom: 40 },
    tooltip: { trigger: 'item', formatter: (p) => `${p.value[0]}: ${zahl(p.value[1], 2)} kg` + (p.data.eingriff ? '<br>Eingriff an diesem Tag – Sprung nicht biologisch deuten' : '') },
    xAxis: { type: 'category', data: daten.map((d) => d.value[0]), axisLabel: { formatter: (t) => t.slice(8, 10) + '.' + t.slice(5, 7) + '.' } },
    yAxis: { type: 'value', name: 'kg/Tag', ...(bereich || {}) },
    series: [{ type: 'bar', name: 'Tagesbilanz', data: daten, encode: { x: 0, y: 1 }, clip: true }],
  };
}

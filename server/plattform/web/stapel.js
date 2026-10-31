// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Diagramme nach dem Designentwurf (16.10.2026): übereinander gestapelte Felder mit gemeinsamer Zeitachse
// (Gewicht, Temperatur, Milbenfall …), Ereignisleiste mit Buchstabenmarken, Vorher/Nachher-Fenster, Völkervergleich.
// Reine Funktionen ohne DOM (Test: tests/plattform/test_diagramm.mjs).
import { achsenText, bilanzBereich, datenBeginn, eingriffLabel, ereignisMarken, esc, ortstag, reihenName, reihenSchluessel, zahl, zeitText } from './diagramm.js';

// Farben des Entwurfs; Temperaturen nach Messstelle, damit Brutnest, Deckel und außen unterscheidbar bleiben
export const FARBEN = {
  gewicht: '#1f4e79', milbenfall: '#9f1239', vorher: 'rgba(37, 99, 235, 0.08)', nachher: 'rgba(199, 119, 0, 0.10)',
};
const ZONENFARBEN = { brutnest: '#c2410c', deckel: '#e3a15a', aussen: '#8a918c', luft_stand: '#8a918c', boden: '#7c5c3b',
                      flugloch: '#b45309', waage: '#6b726d', elektronik: '#5b635e' };
// Völkervergleich: gut unterscheidbare Farben in fester Reihenfolge
export const VOLKFARBEN = ['#1f4e79', '#c2410c', '#2e7d32', '#7b3fa0', '#9a5b00', '#0f766e', '#b42318', '#475569', '#be185d', '#4d7c0f'];

// Ereignismarken: Buchstabe, Farbe und Name je Art (Legende unter dem Diagramm)
export const MARKEN = {
  durchsicht: ['D', '#1f4e79', 'Durchsicht'], behandlung: ['B', '#b42318', 'Behandlung'], fuetterung: ['F', '#9a5b00', 'Fütterung'],
  ernte: ['E', '#2e7d32', 'Ernte'], zarge_auf: ['Z', '#475569', 'Zarge auf'], zarge_ab: ['Z', '#475569', 'Zarge ab'],
  umsetzen: ['U', '#7b3fa0', 'Umsetzen'], tarieren: ['T', '#5b635e', 'Tarieren'], sonstiges: ['M', '#5b635e', 'Maßnahme'],
  varroa: ['V', '#9f1239', 'Varroa'], vereinigung: ['E', '#0f766e', 'Volk-Ereignis'], aufloesung: ['E', '#0f766e', 'Volk-Ereignis'],
};
const FELDHOEHE = { gewicht: 150, milbenfall: 110 };

export function reihenFarbe(r, g) {
  if (r.messgroesse === 'temperatur' && ZONENFARBEN[r.zone]) return ZONENFARBEN[r.zone];
  if (r.messgroesse === 'gewicht') return FARBEN.gewicht;
  return g?.farbe || undefined;
}

// Milbenfall pro Tag als Tagesbalken über die Liegedauer der Windel (Mitte jedes Ortstags)
export function milbenTage(varroa) {
  const aus = [];
  for (const v of varroa || []) {
    if (v.milben_pro_tag === null || v.milben_pro_tag === undefined) continue;
    // ein Balken je Ortstag der Liegedauer (Windel 12.10. 10 Uhr bis 15.10. 10 Uhr: 12., 13., 14.), mindestens einer
    const ende = Date.parse(v.bis);
    let [tag, morgen] = ortstag(v.von);
    do {
      aus.push([tag.getTime() + (morgen.getTime() - tag.getTime()) / 2, Number(v.milben_pro_tag)]);
      tag = morgen;
      morgen = ortstag(new Date(morgen.getTime() + 3600000).toISOString())[1];
    } while (morgen.getTime() <= ende);
  }
  return aus;
}

// Ereignisse als Marken für die Leiste über den Feldern: [{zeit, art, buchstabe, farbe, name, text, nurDatum}]
export function ereignisListe(e) {
  const aus = [];
  const nimm = (art, zeit, text, nurDatum = false, schluessel = '', bis = null) => {
    const [b, farbe, name] = MARKEN[art] || MARKEN.sonstiges;
    aus.push({ art, zeit: Date.parse(zeit), bis: bis ? Date.parse(bis) : null, buchstabe: b, farbe, name, text, nurDatum, schluessel });
  };
  for (const d of e?.durchsichten || []) nimm('durchsicht', d.zeit, d.notiz || '', d.zeitgenauigkeit === 'nur_datum', 'durchsicht:' + d.id);
  for (const m of e?.massnahmen || []) nimm(m.art, m.von, [m.mittel, m.notiz].filter(Boolean).join(' · '), m.zeitgenauigkeit === 'nur_datum', 'massnahme:' + m.id, m.bis);
  for (const v of e?.varroa || []) nimm('varroa', v.bis, `${v.milben} Milben`, v.zeitgenauigkeit === 'nur_datum', 'varroa:' + v.id);
  for (const v of e?.volk_ereignisse || []) nimm(v.art, v.zeit, v.art);
  return aus.sort((a, b) => a.zeit - b.zeit);
}

// Felder: eine Gruppe je Katalog-Achse in fester Reihenfolge, Milbenfall als eigenes Feld
function felder(reihen, katalog, milben) {
  const reihenfolge = ['gewicht', 'temperatur', 'feuchte', 'regenmenge', 'druck', 'licht', 'spannung'];
  const gruppen = new Map();
  for (const r of reihen) {
    const a = katalog[r.messgroesse]?.achse || r.messgroesse;
    if (!gruppen.has(a)) gruppen.set(a, []);
    gruppen.get(a).push(r);
  }
  const achsen = [...gruppen.keys()].sort((a, b) => (reihenfolge.indexOf(a) + 1 || 99) - (reihenfolge.indexOf(b) + 1 || 99));
  const aus = achsen.map((a) => {
    const g = Object.values(katalog).find((k) => k.achse === a);
    return { achse: a, titel: g ? (a === 'temperatur' ? 'Temperatur' : g.name) : a, einheit: g?.einheit || '', reihen: gruppen.get(a) };
  });
  if (milben.length) aus.push({ achse: 'milbenfall', titel: 'Milbenfall', einheit: 'Milben/Tag', reihen: [], milben });
  return aus;
}

export function stapelOptionen(antwort, katalogListe, { sichtbar = null, relativ = false, ereignisse = null, fenster = null } = {}) {
  const katalog = Object.fromEntries((katalogListe || []).map((g) => [g.code, g]));
  const reihen = (antwort?.reihen || []).filter((r) => !sichtbar || sichtbar.has(reihenSchluessel(r)));
  const milben = sichtbar && !sichtbar.has('milbenfall') ? [] : milbenTage(ereignisse?.varroa);
  const fs = felder(reihen, katalog, milben);
  const liste = ereignisListe(ereignisse);
  const marken = ereignisMarken(ereignisse);
  const max = antwort ? Date.parse(antwort.bis) : undefined;
  // Zeitachse beginnt beim ersten Wert im Zeitraum (alle Reihen, auch ausgeblendete), nicht vor den Daten:
  // sonst stehen bei 90 Tagen oder 1 Jahr zwei Wochen Daten als schmaler Streifen am rechten Rand
  const beginn = datenBeginn(antwort?.reihen, [...milbenTage(ereignisse?.varroa).map((p) => p[0] - 43200000),
                                               ...liste.map((e) => e.zeit)]);
  const min = antwort ? Math.max(Date.parse(antwort.von), beginn !== null ? beginn : -Infinity) : undefined;
  const links = 56, rechts = 18, leiste = liste.length ? 34 : 8, titel = 22, abstand = 18;
  let oben = 8 + leiste;
  const grid = [], xAxis = [], yAxis = [], series = [], graphic = [];
  fs.forEach((f, i) => {
    const hoehe = FELDHOEHE[f.achse] || 120;
    // Feldtitel über dem Feld (wie im Entwurf: „Gewicht  kg“), nicht neben der Achsenbeschriftung
    graphic.push({ type: 'text', left: 8, top: oben, style: { text: f.titel, fontSize: 12, fontWeight: 600, fill: '#1a1f1c' } },
                 { type: 'text', left: 12 + f.titel.length * 7.2, top: oben + 1,
                   style: { text: (relativ && f.achse === 'gewicht' ? 'Δ ' : '') + f.einheit, fontSize: 11, fill: '#5b635e' } });
    oben += titel;
    grid.push({ left: links, right: rechts, top: oben, height: hoehe });
    xAxis.push({ type: 'time', gridIndex: i, min, max, axisLabel: { show: i === fs.length - 1, formatter: achsenText, hideOverlap: true, color: '#5b635e' },
                 axisTick: { show: i === fs.length - 1 }, axisLine: { lineStyle: { color: '#cdd3cb' } }, splitLine: { show: true, lineStyle: { color: '#eef1ec' } } });
    yAxis.push({ type: 'value', gridIndex: i, scale: !['milbenfall', 'regenmenge'].includes(f.achse), splitNumber: 3, axisLabel: { color: '#5b635e', fontSize: 11 },
                 splitLine: { lineStyle: { color: '#eef1ec' } }, ...(f.achse === 'richtung' ? { min: 0, max: 360, interval: 90, scale: false } : {}) });
    // Namen nur im obersten Feld (für Tooltip und Tests); die Bänder laufen über alle Felder
    const baender = { silent: true, label: { show: false }, data: [...marken.flaechen.map(([a, b]) => [{ ...a, name: i === 0 ? a.name : '' }, b]),
      ...(fenster ? [[{ xAxis: Date.parse(fenster.vorher.von), itemStyle: { color: FARBEN.vorher } }, { xAxis: Date.parse(fenster.vorher.bis) }],
                     [{ xAxis: Date.parse(fenster.nachher.von), itemStyle: { color: FARBEN.nachher } }, { xAxis: Date.parse(fenster.nachher.bis) }]] : [])] };
    const linien = { silent: true, symbol: 'none', label: { show: false }, data: marken.linien.map((l) => ({ ...l, name: '' })) };
    if (f.milben) {
      series.push({ name: 'Milbenfall', type: 'bar', xAxisIndex: i, yAxisIndex: i, data: f.milben, color: FARBEN.milbenfall, barMaxWidth: 14,
                    markArea: baender, markLine: linien });
      return (oben += hoehe + abstand);
    }
    f.reihen.forEach((r, j) => {
      const g = katalog[r.messgroesse] || {};
      let punkte = r.punkte.map(([t, w]) => [Date.parse(t), w]);
      if (relativ && f.achse === 'gewicht') {
        const erster = punkte.find((p) => p[1] !== null);
        if (erster) punkte = punkte.map(([t, w]) => [t, w === null ? null : Math.round((w - erster[1]) * 1000) / 1000]);
      }
      const s = { name: reihenName(r, katalog), type: g.darstellung === 'balken' ? 'bar' : g.darstellung === 'punkte' || g.darstellung === 'pfeile' ? 'scatter' : 'line',
                  xAxisIndex: i, yAxisIndex: i, data: punkte, connectNulls: false, showSymbol: g.darstellung === 'punkte' || g.darstellung === 'pfeile',
                  symbolSize: 5, sampling: 'lttb', lineStyle: { width: 1.6 }, color: reihenFarbe(r, g), emphasis: { focus: 'series' } };
      if (g.darstellung === 'stufe') s.step = 'end';
      if (j === 0) { s.markArea = baender; s.markLine = linien; }
      series.push(s);
    });
    oben += hoehe + abstand;
  });
  // Ereignisleiste: Buchstabenmarken über dem obersten Feld (eigenes, unsichtbares Raster)
  if (liste.length) {
    const n = grid.length;
    grid.push({ left: links, right: rechts, top: 4, height: 24 });
    xAxis.push({ type: 'time', gridIndex: n, min, max, show: false });
    yAxis.push({ type: 'value', gridIndex: n, show: false, min: 0, max: 1 });
    series.push({ name: 'Stockkarte', type: 'scatter', xAxisIndex: n, yAxisIndex: n, symbol: 'roundRect', symbolSize: [18, 18], z: 5,
                  // Ereignisse, die vor dem Zeitraum beginnen und hineinreichen (z. B. Behandlung), stehen am linken Rand
                  data: liste.filter((e) => (!min || e.zeit >= min || (e.bis && e.bis > min)) && (!max || e.zeit <= max)).map((e) => ({
                    value: [min ? Math.max(e.zeit, min) : e.zeit, 0.5], name: e.name, schluessel: e.schluessel, text: e.text, nurDatum: e.nurDatum,
                    itemStyle: { color: e.farbe, opacity: e.nurDatum ? 0.55 : 1, borderType: e.nurDatum ? 'dashed' : 'solid' },
                    label: { show: true, formatter: e.buchstabe, color: '#fff', fontSize: 10, fontWeight: 700 } })),
                  tooltip: { trigger: 'item', formatter: (p) => `${esc(p.name)} · ${zeitText(p.value[0])}${p.data.nurDatum ? ' (nur Datum)' : ''}${p.data.text ? '<br>' + esc(p.data.text) : ''}` } });
  }
  const achsenIndizes = fs.map((_, i) => i);
  return {
    animation: false, grid, xAxis, yAxis, series, graphic,
    hoehe: oben + 40,
    legend: { show: false },
    axisPointer: { link: [{ xAxisIndex: 'all' }], label: { formatter: (p) => (p.axisDimension === 'x' ? zeitText(p.value) : zahl(p.value, 1)) } },
    tooltip: { trigger: 'axis', valueFormatter: (w) => (w === null || w === undefined ? 'keine Messung' : zahl(w, 2)) },
    dataZoom: [{ type: 'inside', xAxisIndex: [...achsenIndizes, ...(liste.length ? [grid.length - 1] : [])], zoomOnMouseWheel: 'ctrl', moveOnMouseWheel: false },
               { type: 'slider', xAxisIndex: [...achsenIndizes, ...(liste.length ? [grid.length - 1] : [])], bottom: 4, height: 18 }],
  };
}

// ---------------------------------------------------------------- Völkervergleich (Vorbild beelogger)

function tagMs(tag) { const [a, b] = ortstag(tag + 'T12:00:00Z'); return a.getTime() + (b.getTime() - a.getTime()) / 2; }

// Nachtmedian je Volk (absolut oder relativ zum ersten Tag)
export function referenzOptionen(voelker, { relativ = true } = {}) {
  const series = voelker.map((v, i) => {
    let punkte = v.tagesreferenz.map((r) => [tagMs(r.tag), r.referenz_kg]);
    if (relativ && punkte.length) { const a = punkte[0][1]; punkte = punkte.map(([t, w]) => [t, Math.round((w - a) * 1000) / 1000]); }
    return { name: v.name, type: 'line', data: punkte, color: VOLKFARBEN[i % VOLKFARBEN.length], showSymbol: true, symbolSize: 4,
             connectNulls: false, lineStyle: { width: 1.8 } };
  });
  return { animation: false, grid: { left: 56, right: 18, top: 36, bottom: 30 }, legend: { top: 0, type: 'scroll' },
           tooltip: { trigger: 'axis', valueFormatter: (w) => zahl(w, 2) + ' kg' },
           xAxis: { type: 'time', axisLabel: { formatter: achsenText, hideOverlap: true } },
           yAxis: { type: 'value', scale: true, name: relativ ? 'Δ kg' : 'kg' }, series };
}

// Tagesbilanz je Volk als gruppierte Balken; Tage mit Eingriff grau schraffiert (nicht biologisch deuten, L8)
export function bilanzVergleichOptionen(voelker) {
  const tage = [...new Set(voelker.flatMap((v) => v.tagesbilanz.map((b) => b.tag)))].sort();
  const bereich = bilanzBereich(voelker.flatMap((v) => v.tagesbilanz));
  const series = voelker.map((v, i) => {
    const je = Object.fromEntries(v.tagesbilanz.map((b) => [b.tag, b]));
    return { name: v.name, type: 'bar', color: VOLKFARBEN[i % VOLKFARBEN.length], barMaxWidth: 12,
             clip: true,
             data: tage.map((t) => (je[t] ? { value: Math.round(je[t].bilanz_kg * 1000) / 1000, eingriff: je[t].mit_eingriff,
                                               label: eingriffLabel(je[t].bilanz_kg, bereich),
                                               itemStyle: je[t].mit_eingriff ? { color: '#b3b3b3', decal: { symbol: 'rect', dashArrayX: [1, 0], dashArrayY: [2, 3], rotation: -0.8 } } : undefined } : null)) };
  });
  return { animation: false, aria: { enabled: true, decal: { show: false } }, grid: { left: 56, right: 18, top: 36, bottom: 30 }, legend: { top: 0, type: 'scroll' },
           tooltip: { trigger: 'axis', formatter: (ps) => esc(ps[0].axisValue) + '<br>' + ps.filter((p) => p.value !== undefined && p.value !== null)
             .map((p) => `${p.marker}${esc(p.seriesName)}: ${zahl(p.value, 2)} kg${p.data && p.data.eingriff ? ' (Eingriff)' : ''}`).join('<br>') },
           xAxis: { type: 'category', data: tage, axisLabel: { formatter: (t) => t.slice(8, 10) + '.' + t.slice(5, 7) + '.' } },
           yAxis: { type: 'value', name: 'kg/Tag', ...(bereich || {}) }, series };
}

// Summe der Tagesbilanzen je Volk (beelogger „Summen“); ohne Eingriffstage, wenn gewünscht
export function summenOptionen(voelker, { ohneEingriff = true } = {}) {
  const series = voelker.map((v, i) => {
    let s = 0;
    const punkte = v.tagesbilanz.map((b) => { if (!(ohneEingriff && b.mit_eingriff)) s += b.bilanz_kg; return [tagMs(b.tag), Math.round(s * 1000) / 1000]; });
    return { name: v.name, type: 'line', step: 'end', data: punkte, color: VOLKFARBEN[i % VOLKFARBEN.length], showSymbol: false, lineStyle: { width: 1.8 } };
  });
  return { animation: false, grid: { left: 56, right: 18, top: 36, bottom: 30 }, legend: { top: 0, type: 'scroll' },
           tooltip: { trigger: 'axis', valueFormatter: (w) => zahl(w, 2) + ' kg' },
           xAxis: { type: 'time', axisLabel: { formatter: achsenText, hideOverlap: true } },
           yAxis: { type: 'value', name: ohneEingriff ? 'Σ kg ohne Eingriffe' : 'Σ kg' }, series };
}

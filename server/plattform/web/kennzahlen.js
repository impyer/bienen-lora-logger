// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Rechenteile der Seiten ohne DOM und ohne Vue: Kennzahlen des Cockpits, Stockkarten-Chronik, Hinweise im
// Völkervergleich, „veraltet“ in der Übersicht. Getrennt, damit test_diagramm.mjs sie mit Sollwerten prüft (PLT26-16).
import { zahl, zeitText } from './diagramm.js';
import { MARKEN } from './stapel.js';

export const ARTEN = { behandlung: 'Behandlung', fuetterung: 'Fütterung', ernte: 'Ernte', zarge_auf: 'Zarge auf',
                       zarge_ab: 'Zarge ab', umsetzen: 'Umsetzen', tarieren: 'Tarieren', sonstiges: 'Maßnahme' };
export const METHODEN = { windel: 'Windel', puderzucker: 'Puderzucker', auswaschung: 'Auswaschung' };
export const VERALTET_MS = 3 * 3600 * 1000;    // keine Messung seit 3 h: Kachel als veraltet markieren
export const MASSNAHME_ZEITPUNKT_MS = 60000;   // Maßnahme ohne Ende wird als 1-Minuten-Zeitraum gespeichert

// Vorzeichen immer zeigen; Werte unter 0,005 als ±0,00 (kein „-0,00“)
export function vorzeichen(w) { return Math.abs(w) < 0.005 ? '±0,00' : (w > 0 ? '+' : '') + zahl(w, 2); }

// Merkmalswert einer Durchsicht als kurzer Text, z. B. „Brutwaben 6 Waben“, „Königin gesehen: ja“
export function wertText(w) {
  if (w.eingabetyp === 'janein') return `${w.name}: ${w.wert ? 'ja' : 'nein'}`;
  if (w.eingabetyp === 'bewertung') return `${w.name} ${w.wert}/5`;
  return `${w.name} ${typeof w.wert === 'number' ? zahl(w.wert, 0) : w.wert}${w.einheit ? ' ' + w.einheit : ''}`;
}

// letzter Punkt mit Wert (Lücken am Ende überspringen)
export function letzterWert(punkte) {
  for (let i = punkte.length - 1; i >= 0; i--) if (punkte[i][1] !== null) return punkte[i];
  return null;
}

// Kacheln des Cockpits: jüngster Gewichts- und Brutnestwert, jüngste Tagesbilanz, jüngste Varroa- und Durchsicht
export function cockpitKennzahlen(reihen, bilanz, ereignisse) {
  const r = reihen || [];
  const gew = r.find((x) => x.messgroesse === 'gewicht');
  const brut = r.find((x) => x.messgroesse === 'temperatur' && x.zone === 'brutnest');
  const e = ereignisse || {};
  const juengste = (liste, feld) => [...(liste || [])].sort((a, b) => Date.parse(b[feld]) - Date.parse(a[feld]))[0] || null;
  return { gewicht: gew ? letzterWert(gew.punkte) : null, brut: brut ? letzterWert(brut.punkte) : null,
           bilanz: bilanz && bilanz.length ? bilanz[bilanz.length - 1] : null,
           varroa: juengste(e.varroa, 'bis'), durchsicht: juengste(e.durchsichten, 'zeit') };
}

// Stockkarte als Chronik, neueste zuerst: [{schluessel, bearbeiten, t, zeit, nurDatum, art, buchstabe, farbe, text}]
export function chronik(ereignisse) {
  const e = ereignisse || {};
  const tag = (t) => zeitText(t).slice(0, 6);
  const marke = (art) => MARKEN[art] || MARKEN.sonstiges;
  const z = [];
  for (const d of e.durchsichten || []) {
    z.push({ schluessel: 'd' + d.id, bearbeiten: 'durchsicht&id=' + d.id, t: d.zeit, nurDatum: d.zeitgenauigkeit === 'nur_datum',
             zeit: d.zeitgenauigkeit === 'nur_datum' ? tag(d.zeit) : zeitText(d.zeit), art: 'Durchsicht',
             buchstabe: marke('durchsicht')[0], farbe: marke('durchsicht')[1],
             text: [...(d.werte || []).map(wertText), d.notiz].filter(Boolean).join(' · ') });
  }
  for (const m of e.massnahmen || []) {
    const band = m.bis && Date.parse(m.bis) - Date.parse(m.von) > 2 * MASSNAHME_ZEITPUNKT_MS;
    z.push({ schluessel: 'm' + m.id, bearbeiten: 'massnahme&id=' + m.id, t: m.von, nurDatum: m.zeitgenauigkeit === 'nur_datum',
             zeit: zeitText(m.von) + (band ? ' – ' + zeitText(m.bis) : ''), art: ARTEN[m.art] || m.art,
             buchstabe: marke(m.art)[0], farbe: marke(m.art)[1],
             text: [m.mittel, m.menge !== null && m.menge !== undefined ? zahl(m.menge, 1) + ' ' + (m.einheit || '') : '', m.notiz].filter(Boolean).join(' · ') });
  }
  for (const v of e.varroa || []) {
    const proTag = v.milben_pro_tag !== null && v.milben_pro_tag !== undefined;
    z.push({ schluessel: 'v' + v.id, bearbeiten: 'varroa&id=' + v.id, t: v.von, nurDatum: v.zeitgenauigkeit === 'nur_datum',
             zeit: zeitText(v.von) + ' – ' + zeitText(v.bis), art: `Varroa (${METHODEN[v.methode] || v.methode})`,
             buchstabe: 'V', farbe: marke('varroa')[1],
             text: `${v.milben} Milben` + (proTag ? `, ${zahl(v.milben_pro_tag, 1)} pro Tag` : '') + (v.anmerkung ? ' · ' + v.anmerkung : '') });
  }
  for (const v of e.volk_ereignisse || []) {
    z.push({ schluessel: 'e' + v.id, t: v.zeit, zeit: zeitText(v.zeit), art: v.art[0].toUpperCase() + v.art.slice(1),
             buchstabe: 'E', farbe: marke(v.art)[1], text: (v.beteiligte || []).map((b) => `${b.name} (${b.rolle})`).join(', ') });
  }
  return z.sort((a, b) => Date.parse(b.t) - Date.parse(a.t));
}

// Völkervergleich: Mittel der jeweils letzten Tagesbilanz ohne Eingriff; null ohne Werte
export function letzteBilanzMittel(voelker) {
  const w = voelker.map((v) => [...v.tagesbilanz].reverse().find((b) => !b.mit_eingriff)).filter(Boolean).map((b) => b.bilanz_kg);
  return w.length ? w.reduce((a, b) => a + b, 0) / w.length : null;
}

// Plausibilitätshinweise aus der Vergleichsantwort (Sprünge ohne Eingriff, Sensor-Fehlercodes); keine Deutung
export function vergleichHinweise(voelker) {
  const h = [];
  for (const v of voelker) {
    for (const t of v.spruenge) {
      const b = v.tagesbilanz.find((x) => x.tag === t);
      h.push(`${v.name}: Sprung ${b ? vorzeichen(b.bilanz_kg) : '?'} kg am ${t.slice(8, 10)}.${t.slice(5, 7)}. ohne erfassten Eingriff – Maßnahme nachtragen oder Messung prüfen`);
    }
    if (v.fehlcodes) h.push(`${v.name}: ${v.fehlcodes} Temperaturwert(e) mit Sensor-Fehlercode (−127 / 85 °C) – Sensor prüfen (PLT26-11)`);
  }
  return h;
}

// Übersicht: keine Messung oder die letzte älter als VERALTET_MS vor dem Bezugszeitpunkt
export function veraltet(letzteMessung, bezugMs) {
  return !letzteMessung || bezugMs - Date.parse(letzteMessung) > VERALTET_MS;
}

// Maßnahme ohne eigenes Ende (Zeitpunkt): Ende im Formular leer lassen
export function istZeitpunkt(von, bis) { return !bis || Date.parse(bis) - Date.parse(von) <= MASSNAHME_ZEITPUNKT_MS; }

// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Bienenstand-Dashboard nach Designentwurf v0.3 (Seite 1) und Konzept 0.2 §6: Standleiste (Wetter, Boden),
// Handlungsbedarf, Völker als Kacheln oder Liste (umschaltbar, sortierbar, Kennzahlen wählbar), Beutensymbol mit
// Zargen und Königinnenfarbe (Vorbild BEEP), drei getrennte Status je Volk: Stockkarte, Technik, Varroa.
// „Keine Messquelle“ ist grau, nie rot. Gerätenamen erscheinen hier nicht (nur auf der Seite Datenquellen).
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { zahl, zeitText } from '../diagramm.js';
import { veraltet } from '../kennzahlen.js';
import { Zustand } from './komponenten.js';

const KOENIGIN = { 'weiß': '#f4f4f4', weiss: '#f4f4f4', gelb: '#f4d03f', rot: '#e74c3c', 'grün': '#27ae60', gruen: '#27ae60', blau: '#2e86de' };
const RICHTUNG = ['N', 'NO', 'O', 'SO', 'S', 'SW', 'W', 'NW'];
const TAG = 86400000;
const KENNZAHLEN = [['gewicht', 'Gewicht'], ['bilanz', 'Tagesbilanz'], ['varroa', 'Varroa'], ['durchsicht', 'Durchsicht'], ['aufgaben', 'Aufgaben']];
const SORTIERUNG = [['platz', 'Platz am Stand'], ['name', 'Name'], ['gewicht', 'Gewicht'], ['varroa', 'Milbenfall'], ['durchsicht', 'letzte Durchsicht']];

function speicher(schluessel, vorgabe) {
  try { const w = localStorage.getItem('bienenstand.' + schluessel); return w === null ? vorgabe : JSON.parse(w); } catch { return vorgabe; }
}
function merken(schluessel, wert) { try { localStorage.setItem('bienenstand.' + schluessel, JSON.stringify(wert)); } catch { /* privat */ } }

// Varroa-Ampel (vereinfacht nach LWG, natürlicher Milbenfall pro Tag): < 5 grün, 5–10 gelb, > 10 rot
export function varroaStatus(v) {
  if (!v || v.milben_pro_tag === null || v.milben_pro_tag === undefined) return ['grau', 'keine Zählung'];
  const m = v.milben_pro_tag;
  return [m > 10 ? 'rot' : m >= 5 ? 'warn' : 'ok', `${zahl(m, 1)} Milben/Tag`];
}

export default defineComponent({
  components: { Zustand },
  props: { route: Object },
  emits: ['fehler'],
  data: () => ({ staende: [], meldungen: [], laden: true, fehler: '', ansicht: speicher('ansicht', 'kacheln'),
                 sortierung: speicher('sortierung', 'platz'), kennzahlen: speicher('kennzahlen', KENNZAHLEN.map(([k]) => k)),
                 KENNZAHLEN, SORTIERUNG }),
  template: `
    <section>
      <div class="kopfzeile"><h1>Bienenstand</h1>
        <div class="zeile steuerung">
          <span class="segmente" role="group" aria-label="Ansicht">
            <button :class="{ aktiv: ansicht === 'kacheln' }" @click="setze('ansicht', 'kacheln')">Kacheln</button>
            <button :class="{ aktiv: ansicht === 'liste' }" @click="setze('ansicht', 'liste')">Liste</button></span>
          <label class="klein">Sortieren <select :value="sortierung" @change="setze('sortierung', $event.target.value)" aria-label="Sortierung">
            <option v-for="[k, t] in SORTIERUNG" :key="k" :value="k">{{ t }}</option></select></label>
          <details class="kennzahlwahl"><summary class="klein">Kennzahlen</summary>
            <label v-for="[k, t] in KENNZAHLEN" :key="k" class="klein"><input type="checkbox" :checked="kennzahlen.includes(k)" @change="kennzahl(k)"> {{ t }}</label></details>
        </div></div>
      <Zustand :laden="laden" :fehler="fehler" />
      <p v-if="meldungen.length" class="klein technik-hinweis">Technik: <a href="#/datenquellen">{{ meldungen.join(' · ') }}</a></p>
      <p v-if="!laden && !fehler && !staende.length" class="leer">
        Noch keine Stände angelegt. Sobald Stände, Völker und Geräte in den Stammdaten stehen und der Importer läuft, erscheinen sie hier.
      </p>
      <article v-for="s in staende" :key="s.id" class="stand">
        <header><h2>{{ s.name }}</h2> <a :href="'#/stand/' + s.id + '/umwelt' + abfrage">Umwelt</a></header>

        <div class="standleiste" v-if="leiste(s).length">
          <a v-for="w in leiste(s)" :key="w.titel" :href="'#/stand/' + s.id + '/umwelt' + abfrage" class="wert-kurz" :title="w.zeit ? 'Stand ' + zeitText(w.zeit) : ''">
            <span class="klein">{{ w.titel }}</span><strong>{{ w.wert }}</strong><span v-if="w.unter" class="klein">{{ w.unter }}</span></a>
        </div>
        <p v-else class="leer klein">Keine aktuellen Umweltwerte (Wetterstation oder Bodensonde ohne Meldung in den letzten 3 Stunden).</p>

        <div v-if="handlungsbedarf(s).length" class="karte handlungsbedarf">
          <h3>Handlungsbedarf</h3>
          <ul><li v-for="h in handlungsbedarf(s)" :key="h.schluessel"><span class="chip" :class="h.stufe">{{ h.art }}</span>&nbsp;<a :href="'#/volk/' + h.volk.id + abfrage">{{ h.volk.name }}</a>: {{ h.text }}</li></ul>
        </div>

        <p v-if="!s.voelker.length" class="leer">Keine Völker an diesem Stand.</p>
        <div v-else-if="ansicht === 'kacheln'" class="kacheln">
          <a v-for="v in sortiert(s.voelker)" :key="v.id" :href="'#/volk/' + v.id + abfrage" class="kachel volkkachel" :class="{ veraltet: technik(v)[0] === 'warn' }">
            <div class="kachelkopf">
              <svg class="beute" :viewBox="'0 0 40 ' + beutenHoehe(v)" width="34" :height="beutenHoehe(v) * 0.85" role="img" :aria-label="beutenText(v)">
                <title>{{ beutenText(v) }}</title>
                <rect v-for="(z, i) in zargen(v)" :key="i" x="2" :y="4 + i * 12" width="36" height="11" rx="1.5" :class="z" />
                <circle v-if="v.koenigin" cx="31" :cy="beutenHoehe(v) - 6" r="5" :fill="koeniginFarbe(v)" stroke="#1a1f1c" stroke-width="1" />
              </svg>
              <div><strong>{{ v.name }}</strong><div class="klein">{{ beutenText(v) }}</div></div>
            </div>
            <template v-if="kennzahlen.includes('gewicht')">
              <span v-if="v.messquellen" class="gross">{{ zahl(v.gewicht_kg, 1) }} kg</span>
            </template>
            <span v-if="kennzahlen.includes('bilanz') && v.tagesbilanz" :class="{ plus: v.tagesbilanz.bilanz_kg >= 0, minus: v.tagesbilanz.bilanz_kg < 0 }">
              {{ v.tagesbilanz.bilanz_kg >= 0 ? '+' : '' }}{{ zahl(v.tagesbilanz.bilanz_kg, 2) }} kg am {{ tag(v.tagesbilanz.tag) }}
              <em v-if="v.tagesbilanz.mit_eingriff" title="Maßnahme an diesem Tag: Sprung nicht biologisch deuten">Eingriff</em></span>
            <div class="status">
              <span class="chip" :class="stockkarte(v)[0]" title="Stockkarte: letzte Durchsicht">{{ stockkarte(v)[1] }}</span>
              <span class="chip" :class="technik(v)[0]" title="Technik: Messquelle">{{ technik(v)[1] }}</span>
              <span v-if="kennzahlen.includes('varroa')" class="chip" :class="varroa(v.varroa)[0]" title="Varroa: letzte Windelzählung (Ampel vereinfacht nach LWG)">{{ varroa(v.varroa)[1] }}</span>
            </div>
            <span v-if="kennzahlen.includes('aufgaben') && v.aufgaben_offen.length" class="klein" :class="{ warnung: v.aufgaben_faellig }">
              {{ v.aufgaben_offen.length }} Aufgabe(n), nächste {{ datum(v.aufgaben_offen[0].faellig_am) }}</span>
          </a>
        </div>
        <table v-else class="tabelle volkliste">
          <thead><tr><th>Volk</th><th>Beute</th><th>Königin</th>
            <th v-if="kennzahlen.includes('gewicht')" class="zahl">Gewicht</th><th v-if="kennzahlen.includes('bilanz')" class="zahl">Tagesbilanz</th>
            <th>Stockkarte</th><th>Technik</th><th v-if="kennzahlen.includes('varroa')">Varroa</th><th v-if="kennzahlen.includes('aufgaben')">Aufgaben</th></tr></thead>
          <tbody><tr v-for="v in sortiert(s.voelker)" :key="v.id">
            <td><a :href="'#/volk/' + v.id + abfrage">{{ v.name }}</a></td><td>{{ beutenText(v) }}</td>
            <td><span v-if="v.koenigin" class="punkt" :style="{ background: koeniginFarbe(v) }"></span> {{ v.koenigin ? (v.koenigin.farbe || '') + ' ' + (v.koenigin.jahrgang || '') : '–' }}</td>
            <td v-if="kennzahlen.includes('gewicht')" class="zahl">{{ v.messquellen ? zahl(v.gewicht_kg, 1) + ' kg' : '–' }}</td>
            <td v-if="kennzahlen.includes('bilanz')" class="zahl">{{ v.tagesbilanz ? (v.tagesbilanz.bilanz_kg >= 0 ? '+' : '') + zahl(v.tagesbilanz.bilanz_kg, 2) : '–' }}</td>
            <td><span class="chip" :class="stockkarte(v)[0]">{{ stockkarte(v)[1] }}</span></td>
            <td><span class="chip" :class="technik(v)[0]">{{ technik(v)[1] }}</span></td>
            <td v-if="kennzahlen.includes('varroa')"><span class="chip" :class="varroa(v.varroa)[0]">{{ varroa(v.varroa)[1] }}</span></td>
            <td v-if="kennzahlen.includes('aufgaben')">{{ v.aufgaben_offen.length ? v.aufgaben_offen.length + ', nächste ' + datum(v.aufgaben_offen[0].faellig_am) : '–' }}</td>
          </tr></tbody>
        </table>
      </article>
    </section>`,
  computed: {
    abfrage() { return this.route.query.zeit ? '?bis=' + encodeURIComponent(this.route.query.zeit) : ''; },
    bezug() { return this.route.query.zeit ? Date.parse(this.route.query.zeit) : Date.now(); },
  },
  methods: {
    zahl, zeitText,
    setze(feld, wert) { this[feld] = wert; merken(feld, wert); },
    kennzahl(k) { this.setze('kennzahlen', this.kennzahlen.includes(k) ? this.kennzahlen.filter((x) => x !== k) : [...this.kennzahlen, k]); },
    tag(t) { return t.slice(8, 10) + '.' + t.slice(5, 7) + '.'; },
    datum(t) { return t ? String(t).slice(8, 10) + '.' + String(t).slice(5, 7) + '.' : '–'; },
    zargen(v) {
      const b = v.beute || {};
      return [...Array(Math.min(b.honigzargen || 0, 4)).fill('honig'), ...Array(Math.min(Math.max(b.brutzargen ?? 1, 1), 4)).fill('brut')];
    },
    beutenHoehe(v) { return 8 + this.zargen(v).length * 12 + (v.koenigin ? 6 : 0); },
    beutenText(v) {
      const b = v.beute;
      if (!b) return 'Beute unbekannt';
      const teile = [b.beutentyp || b.bezeichnung];
      if (b.brutzargen !== null && b.brutzargen !== undefined) teile.push(b.brutzargen + ' Brut');
      if (b.honigzargen) teile.push(b.honigzargen + ' Honig');
      if (b.rahmen) teile.push(b.rahmen + ' Rähmchen');
      return teile.filter(Boolean).join(' · ');
    },
    koeniginFarbe(v) { return KOENIGIN[(v.koenigin?.farbe || '').toLowerCase()] || '#9aa19c'; },
    stockkarte(v) {
      if (!v.letzte_durchsicht) return ['grau', 'keine Durchsicht'];
      const tage = Math.floor((this.bezug - Date.parse(v.letzte_durchsicht)) / TAG);
      return [tage > 30 ? 'warn' : 'ok', tage <= 0 ? 'Durchsicht heute' : `Durchsicht vor ${tage} T`];
    },
    technik(v) {
      if (!v.messquellen) return ['grau', 'keine Messquelle'];
      return veraltet(v.letzte_messung, this.bezug) ? ['warn', 'Messung ' + (v.letzte_messung ? zeitText(v.letzte_messung).slice(0, 6) : 'fehlt')] : ['ok', 'Messung aktuell'];
    },
    varroa: varroaStatus,
    sortiert(voelker) {
      const s = this.sortierung, w = (v) => ({ name: v.name, gewicht: -(v.gewicht_kg ?? -1e9), varroa: -(v.varroa?.milben_pro_tag ?? -1),
        durchsicht: v.letzte_durchsicht ? Date.parse(v.letzte_durchsicht) : 0, platz: v.platz ?? 1e9 })[s];
      return [...voelker].sort((a, b) => (w(a) < w(b) ? -1 : w(a) > w(b) ? 1 : a.name.localeCompare(b.name, 'de', { numeric: true })));
    },
    // Standleiste: kurze Werte aus api/staende (umwelt.werte); Boden je Tiefe
    leiste(s) {
      const u = s.umwelt || {}, werte = u.werte || [];
      const finde = (code, f = () => true) => werte.find((w) => w.messgroesse === code && f(w));
      const aus = [];
      const t = finde('temperatur', (w) => w.zone !== 'boden'), h = finde('feuchte');
      if (t) aus.push({ titel: 'Luft', wert: zahl(t.wert, 1) + ' °C', unter: h ? zahl(h.wert, 0) + ' % Feuchte' : '', zeit: t.zeit });
      const p = finde('luftdruck');
      if (p) {
        const d = u.druck_vor_3h !== null && u.druck_vor_3h !== undefined ? p.wert - u.druck_vor_3h : null;
        aus.push({ titel: 'Luftdruck', wert: zahl(p.wert, 0) + ' hPa',
                   unter: d === null ? '' : (d > 1 ? '↗ steigt' : d < -1 ? '↘ fällt' : '→ gleich') + ' (3 h: ' + (d >= 0 ? '+' : '') + zahl(d, 1) + ')', zeit: p.zeit });
      }
      const wi = finde('wind'), b = finde('windboe'), r = finde('windrichtung');
      if (wi) aus.push({ titel: 'Wind', wert: zahl(wi.wert, 1) + ' m/s', zeit: wi.zeit,
                         unter: [r ? 'aus ' + RICHTUNG[Math.round(((r.wert % 360) + 360) % 360 / 45) % 8] : '', b ? 'Böe ' + zahl(b.wert, 1) : ''].filter(Boolean).join(' · ') });
      if (u.regen_heute !== null && u.regen_heute !== undefined) aus.push({ titel: 'Regen', wert: zahl(u.regen_heute, 1) + ' mm heute', unter: zahl(u.regen_24h, 1) + ' mm in 24 h' });
      for (const w of werte.filter((x) => x.messgroesse === 'temperatur' && x.zone === 'boden').sort((a, c) => (a.tiefe_cm ?? 0) - (c.tiefe_cm ?? 0)))
        aus.push({ titel: 'Boden ' + (w.tiefe_cm !== null ? zahl(w.tiefe_cm, 0) + ' cm' : (w.bezeichnung || '')), wert: zahl(w.wert, 1) + ' °C', zeit: w.zeit });
      return aus;
    },
    // Handlungsbedarf: fällige Aufgaben, Varroa rot, Messquelle ohne aktuelle Messung, lange keine Durchsicht
    handlungsbedarf(s) {
      const heute = new Date(this.bezug).toISOString().slice(0, 10), aus = [];
      for (const v of s.voelker) {
        for (const a of v.aufgaben_offen) if (String(a.faellig_am) <= heute) aus.push({ schluessel: v.id + 'a' + a.text, stufe: 'warn', art: 'Aufgabe', volk: v, text: `${a.text} (fällig ${this.datum(a.faellig_am)})` });
        const [st, txt] = varroaStatus(v.varroa);
        if (st === 'rot') aus.push({ schluessel: v.id + 'v', stufe: 'rot', art: 'Varroa', volk: v, text: `${txt} am ${zeitText(v.varroa.bis).slice(0, 6)}` });
        const [tk, ttxt] = this.technik(v);
        if (tk === 'warn') aus.push({ schluessel: v.id + 't', stufe: 'warn', art: 'Technik', volk: v, text: 'keine aktuelle Messung, letzte: ' + ttxt.replace('Messung ', '') });
      }
      return aus;
    },
  },
  async mounted() {
    try {
      const [staende, p] = await Promise.all([holen('staende', { zeit: this.route.query.zeit }), holen('pruefungen')]);
      this.staende = staende;
      const n = (zahl, eins, mehr) => (zahl ? [`${zahl} ${zahl === 1 ? eins : mehr}`] : []);
      this.meldungen = [...n(p.geraete_ohne_ziel.length, 'Gerät ohne Zuordnung', 'Geräte ohne Zuordnung'),
                        ...n(p.unbenannt.length, 'unbenanntes Feld', 'unbenannte Felder'),
                        ...n(p.zuordnung.length, 'Auffälligkeit bei Zuordnungen', 'Auffälligkeiten bei Zuordnungen')];
    } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

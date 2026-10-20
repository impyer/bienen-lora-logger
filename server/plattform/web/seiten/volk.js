// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Volk-Cockpit: frei wählbare Kurven (Vorbild beelogger), Stockkarten-Ereignisse im Diagramm, Tagesbilanz
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { bilanzOptionen, reihenName, reihenSchluessel, verlaufOptionen, zahl, zeitText } from '../diagramm.js';
import { Diagramm, Zeitraum, Zustand, zeitraumParameter } from './komponenten.js';

const ARTEN = { behandlung: 'Behandlung', fuetterung: 'Fütterung', ernte: 'Ernte', zarge_auf: 'Zarge auf',
                zarge_ab: 'Zarge ab', umsetzen: 'Umsetzen', tarieren: 'Tarieren', sonstiges: 'Maßnahme' };
const VORWAHL = ['gewicht', 'temperatur'];

export default defineComponent({
  components: { Diagramm, Zeitraum, Zustand },
  props: { route: Object, id: Number },
  emits: ['fehler', 'navigieren'],
  data: () => ({ volk: null, katalog: [], reihen: null, bilanz: [], ereignisse: null, sichtbar: null,
                 relativ: false, laden: true, fehler: '' }),
  template: `
    <section>
      <p><a href="#/">← Übersicht</a></p>
      <Zustand :laden="laden" :fehler="fehler" />
      <template v-if="volk">
        <h1>{{ volk.name }} <small v-if="volk.aufgeloest_am" class="klein">aufgelöst {{ zeitText(volk.aufgeloest_am) }}</small></h1>
        <p class="stammdaten">
          <span v-if="volk.stand">Stand: {{ volk.stand.name }}</span>
          <span v-if="volk.beute">Beute: {{ volk.beute.bezeichnung }} ({{ volk.beute.beutentyp }}, {{ volk.beute.brutzargen ?? '?' }} Brut-, {{ volk.beute.honigzargen ?? '?' }} Honigzargen)</span>
          <span v-if="volk.koenigin">Königin: {{ volk.koenigin.jahrgang }} {{ volk.koenigin.farbe }} {{ volk.koenigin.rasse }}</span>
          <span v-for="g in volk.geraete" :key="g.name + g.von">Gerät {{ g.name }} ab {{ zeitText(g.von) }}<template v-if="g.bis"> bis {{ zeitText(g.bis) }}</template></span>
        </p>
        <Zeitraum :tage="zr.tage" :bis="zr.bis" @wahl="$emit('navigieren', { tage: $event.tage, bis: $event.bis })" />
        <fieldset v-if="reihen && reihen.reihen.length" class="auswahl">
          <legend>Kurven</legend>
          <label v-for="r in reihen.reihen" :key="schluessel(r)"><input type="checkbox" :checked="!sichtbar || sichtbar.has(schluessel(r))" @change="umschalten(r)"> {{ name(r) }}
            <small v-if="r.ohne_geraetezeit" class="klein" title="Zeit vom Empfang, nicht vom Gerät">({{ r.ohne_geraetezeit }} ohne Gerätezeit)</small></label>
          <label><input type="checkbox" v-model="relativ"> Gewicht relativ zum Beginn</label>
        </fieldset>
        <p v-if="reihen && !reihen.reihen.length" class="leer">Keine Messwerte in diesem Zeitraum.</p>
        <Diagramm v-if="reihen && reihen.reihen.length" :optionen="verlauf" name="verlauf" />
        <h2>Tagesbilanz <small class="klein">Gewicht 00–04 Uhr, Vortag abgezogen</small></h2>
        <p v-if="!bilanz.length" class="leer">Keine Tagesbilanz in diesem Zeitraum.</p>
        <Diagramm v-else :optionen="bilanzDiagramm" hoehe="220px" name="bilanz" />
        <h2>Stockkarte</h2>
        <p v-if="ereignisse && !anzahlEreignisse" class="leer">Keine Einträge in diesem Zeitraum.</p>
        <table v-if="anzahlEreignisse" class="tabelle">
          <thead><tr><th>Zeit</th><th>Art</th><th>Angaben</th></tr></thead>
          <tbody>
            <tr v-for="e in liste" :key="e.schluessel">
              <td>{{ e.zeit }}<em v-if="e.nurDatum" title="Uhrzeit aus BEEP übernommen, nicht erfasst"> Uhrzeit übernommen</em></td>
              <td>{{ e.art }}</td><td>{{ e.text }}</td>
            </tr>
          </tbody>
        </table>
      </template>
    </section>`,
  computed: {
    zr() { return zeitraumParameter(this.route); },
    verlauf() { return verlaufOptionen(this.reihen, this.katalog, { sichtbar: this.sichtbar, relativ: this.relativ, ereignisse: this.ereignisse }); },
    bilanzDiagramm() { return bilanzOptionen(this.bilanz); },
    liste() {
      const e = this.ereignisse || {};
      const tag = (t) => zeitText(t).slice(0, 6);
      const z = [];
      for (const d of e.durchsichten || []) z.push({ schluessel: 'd' + d.id, t: d.zeit, zeit: d.zeitgenauigkeit === 'nur_datum' ? tag(d.zeit) : zeitText(d.zeit), nurDatum: d.zeitgenauigkeit === 'nur_datum', art: 'Durchsicht', text: d.notiz || '' });
      for (const m of e.massnahmen || []) z.push({ schluessel: 'm' + m.id, t: m.von, zeit: zeitText(m.von) + (m.bis ? ' – ' + zeitText(m.bis) : ''), nurDatum: m.zeitgenauigkeit === 'nur_datum', art: ARTEN[m.art] || m.art, text: [m.mittel, m.menge !== null ? zahl(m.menge, 1) + ' ' + (m.einheit || '') : '', m.notiz].filter(Boolean).join(' · ') });
      for (const v of e.varroa || []) z.push({ schluessel: 'v' + v.id, t: v.von, zeit: zeitText(v.von) + ' – ' + zeitText(v.bis), nurDatum: v.zeitgenauigkeit === 'nur_datum', art: 'Varroa (Windel)', text: `${v.milben} Milben, ${zahl(v.milben_pro_tag, 1)} pro Tag` });
      for (const v of e.volk_ereignisse || []) z.push({ schluessel: 'e' + v.id, t: v.zeit, zeit: zeitText(v.zeit), art: v.art[0].toUpperCase() + v.art.slice(1), text: (v.beteiligte || []).map((b) => `${b.name} (${b.rolle})`).join(', ') });
      return z.sort((a, b) => Date.parse(a.t) - Date.parse(b.t));
    },
    anzahlEreignisse() { return this.liste.length; },
  },
  methods: {
    zeitText,
    schluessel: reihenSchluessel,
    name(r) { return reihenName(r, Object.fromEntries(this.katalog.map((g) => [g.code, g]))); },
    umschalten(r) {
      const alle = new Set(this.reihen.reihen.map(reihenSchluessel));
      const s = new Set(this.sichtbar || alle);
      const k = reihenSchluessel(r);
      s.has(k) ? s.delete(k) : s.add(k);
      this.sichtbar = s;
    },
  },
  async mounted() {
    const p = { von: this.zr.von, bis: this.zr.bisIso };
    try {
      [this.volk, this.katalog, this.reihen, this.bilanz, this.ereignisse] = await Promise.all([
        holen(`voelker/${this.id}`, { zeit: this.zr.bisIso }), holen('messgroessen'),
        holen(`voelker/${this.id}/messreihen`, p), holen(`voelker/${this.id}/tagesbilanz`, p),
        holen(`voelker/${this.id}/ereignisse`, p)]);
      // Zu Beginn nur Gewicht und Temperaturen zeigen (wie beelogger); weitere Kurven über die Auswahl
      const start = this.reihen.reihen.filter((r) => VORWAHL.includes(r.messgroesse)).map(reihenSchluessel);
      this.sichtbar = start.length ? new Set(start) : null;
    } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

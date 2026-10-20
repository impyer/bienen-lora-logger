// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Umwelt eines Stands: Wetterstation und weitere Geräte am Stand (Wind als Pfeile, Regenzähler ohne Summe)
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { verlaufOptionen } from '../diagramm.js';
import { Diagramm, Zeitraum, Zustand, zeitraumParameter } from './komponenten.js';

export default defineComponent({
  components: { Diagramm, Zeitraum, Zustand },
  props: { route: Object, id: Number },
  emits: ['fehler', 'navigieren'],
  data: () => ({ stand: null, katalog: [], reihen: null, laden: true, fehler: '' }),
  template: `
    <section>
      <p><a href="#/">← Übersicht</a></p>
      <h1>Umwelt <span v-if="stand">– {{ stand.name }}</span></h1>
      <Zustand :laden="laden" :fehler="fehler" />
      <Zeitraum :tage="zr.tage" :bis="zr.bis" @wahl="$emit('navigieren', { tage: $event.tage, bis: $event.bis })" />
      <p v-if="reihen && !reihen.reihen.length" class="leer">Keine Umweltdaten in diesem Zeitraum. Ist dem Stand ein Gerät zugeordnet?</p>
      <Diagramm v-for="g in gruppen" :key="g.titel" :optionen="g.optionen" :name="'umwelt_' + g.name" hoehe="300px" />
      <p class="klein">Regen: Zählerstand der Station; er beginnt nach einem Neustart wieder bei 0 und wird deshalb nicht aufsummiert.</p>
    </section>`,
  computed: {
    zr() { return zeitraumParameter(this.route); },
    gruppen() {
      if (!this.reihen) return [];
      const k = Object.fromEntries(this.katalog.map((g) => [g.code, g]));
      const teil = (name, achsen) => {
        const r = this.reihen.reihen.filter((x) => achsen.includes(k[x.messgroesse]?.achse));
        return r.length ? { name, titel: name, optionen: verlaufOptionen({ ...this.reihen, reihen: r }, this.katalog) } : null;
      };
      const bekannt = ['temperatur', 'feuchte', 'druck', 'wind', 'richtung', 'regen', 'regenrate'];
      const rest = [...new Set(this.reihen.reihen.map((x) => k[x.messgroesse]?.achse))].filter((a) => !bekannt.includes(a));
      return [teil('klima', ['temperatur', 'feuchte', 'druck']), teil('wind', ['wind', 'richtung']),
              teil('regen', ['regen', 'regenrate']), rest.length ? teil('weitere', rest) : null].filter(Boolean);
    },
  },
  async mounted() {
    try {
      const staende = await holen('staende');
      this.stand = staende.find((s) => s.id === this.id) || null;
      [this.katalog, this.reihen] = await Promise.all([holen('messgroessen'),
        holen(`staende/${this.id}/umwelt`, { von: this.zr.von, bis: this.zr.bisIso })]);
    } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Übersicht: Stände mit ihren Völkern als Kacheln (Vorbild BEEP), Kurzwerte aus der Lese-API
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { zahl, zeitText } from '../diagramm.js';
import { Zustand } from './komponenten.js';

const VERALTET_MS = 3 * 3600 * 1000;    // keine Messung seit 3 h: Kachel als veraltet markieren

export default defineComponent({
  components: { Zustand },
  props: { route: Object },
  emits: ['fehler'],
  data: () => ({ staende: [], meldungen: 0, laden: true, fehler: '' }),
  template: `
    <section>
      <h1>Übersicht</h1>
      <Zustand :laden="laden" :fehler="fehler" />
      <p v-if="!laden && !fehler && !staende.length" class="leer">
        Noch keine Stände angelegt. Sobald Stände, Völker und Geräte in den Stammdaten stehen und der Importer läuft, erscheinen sie hier.
      </p>
      <p v-if="meldungen" class="warnung"><a href="#/datenquellen">{{ meldungen }} Hinweis(e) zu Datenquellen</a></p>
      <article v-for="s in staende" :key="s.id" class="stand">
        <header><h2>{{ s.name }}</h2> <a :href="'#/stand/' + s.id + '/umwelt' + abfrage">Umwelt</a></header>
        <p v-if="!s.voelker.length" class="leer">Keine Völker an diesem Stand.</p>
        <div class="kacheln">
          <a v-for="v in s.voelker" :key="v.id" :href="'#/volk/' + v.id + abfrage" class="kachel" :class="{ veraltet: veraltet(v) }">
            <strong>{{ v.name }}</strong>
            <span class="gross">{{ zahl(v.gewicht_kg, 1) }} kg</span>
            <span v-if="v.tagesbilanz" :class="{ plus: v.tagesbilanz.bilanz_kg >= 0, minus: v.tagesbilanz.bilanz_kg < 0 }">
              {{ v.tagesbilanz.bilanz_kg >= 0 ? '+' : '' }}{{ zahl(v.tagesbilanz.bilanz_kg, 2) }} kg am {{ tag(v.tagesbilanz.tag) }}
              <em v-if="v.tagesbilanz.mit_eingriff" title="Maßnahme an diesem Tag: Sprung nicht biologisch deuten">Eingriff</em>
            </span>
            <span v-else class="klein">keine Tagesbilanz</span>
            <span class="klein">letzte Messung {{ zeitText(v.letzte_messung) }}</span>
          </a>
        </div>
      </article>
    </section>`,
  computed: {
    abfrage() { return this.route.query.zeit ? '?bis=' + encodeURIComponent(this.route.query.zeit) : ''; },
    bezug() { return this.route.query.zeit ? Date.parse(this.route.query.zeit) : Date.now(); },
  },
  methods: {
    zahl, zeitText,
    tag(t) { return t.slice(8, 10) + '.' + t.slice(5, 7) + '.'; },
    veraltet(v) { return !v.letzte_messung || this.bezug - Date.parse(v.letzte_messung) > VERALTET_MS; },
  },
  async mounted() {
    try {
      const [staende, p] = await Promise.all([holen('staende', { zeit: this.route.query.zeit }), holen('pruefungen')]);
      this.staende = staende;
      this.meldungen = p.zuordnung.length + p.unbenannt.length + p.geraete_ohne_ziel.length;
    } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

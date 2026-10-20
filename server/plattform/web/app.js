// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Oberfläche der Bienen-Plattform (Phase B lesend, Phase C Teil 1 Stammdaten). Hash-Router ohne Build-Schritt:
//   #/                      Übersicht (?zeit= Bezugszeitpunkt, ISO)
//   #/volk/<id>             Volk-Cockpit (?tage=14&bis=ISO)
//   #/stand/<id>/umwelt     Umwelt eines Stands
//   #/datenquellen          unbenannte Felder, Zuordnungen, Import
//   #/verwaltung            Stammdaten pflegen: Stände, Völker, Beuten, Geräte, Kanäle (Phase C, Teil 1)
import { createApp, defineComponent, reactive } from './vendor/vue.esm-browser.prod.js';
import { NichtAngemeldet, csrfSetzen, holen, senden } from './api.js';
import Anmelden from './seiten/anmelden.js';
import Datenquellen from './seiten/datenquellen.js';
import Uebersicht from './seiten/uebersicht.js';
import Verwaltung from './seiten/verwaltung.js';
import Umwelt from './seiten/umwelt.js';
import Volk from './seiten/volk.js';

function routeLesen() {
  const [pfad, abfrage = ''] = (location.hash.replace(/^#/, '') || '/').split('?');
  return { pfad, query: Object.fromEntries(new URLSearchParams(abfrage)), schluessel: location.hash };
}

const route = reactive(routeLesen());
window.addEventListener('hashchange', () => Object.assign(route, routeLesen()));

const Wurzel = defineComponent({
  components: { Anmelden, Datenquellen, Uebersicht, Umwelt, Verwaltung, Volk },
  data: () => ({ route, angemeldet: null }),
  template: `
    <header class="kopf">
      <a href="#/" class="marke">Bienen-Plattform</a>
      <nav v-if="angemeldet"><a href="#/">Übersicht</a><a href="#/verwaltung">Verwaltung</a><a href="#/datenquellen">Datenquellen</a><button class="link" @click="abmelden">Abmelden</button></nav>
    </header>
    <main>
      <p v-if="angemeldet === null" class="hinweis">Lädt …</p>
      <Anmelden v-else-if="!angemeldet" @angemeldet="sitzungLaden" />
      <component v-else :is="seite.komponente" v-bind="seite.props" :key="route.schluessel" :route="route"
                 @fehler="fehler" @navigieren="navigieren" />
    </main>`,
  computed: {
    seite() {
      const p = this.route.pfad;
      let m;
      if ((m = p.match(/^\/volk\/(\d+)$/))) return { komponente: 'Volk', props: { id: Number(m[1]) } };
      if ((m = p.match(/^\/stand\/(\d+)\/umwelt$/))) return { komponente: 'Umwelt', props: { id: Number(m[1]) } };
      if (p === '/datenquellen') return { komponente: 'Datenquellen', props: {} };
      if (p === '/verwaltung') return { komponente: 'Verwaltung', props: {} };
      return { komponente: 'Uebersicht', props: {} };
    },
  },
  methods: {
    fehler(e) { if (e instanceof NichtAngemeldet) this.angemeldet = false; },
    navigieren(q) {
      const neu = { ...this.route.query, ...q };
      Object.keys(neu).forEach((k) => (neu[k] === '' || neu[k] === undefined) && delete neu[k]);
      location.hash = this.route.pfad + (Object.keys(neu).length ? '?' + new URLSearchParams(neu) : '');
    },
    async abmelden() { await senden('abmelden', {}); csrfSetzen(''); this.angemeldet = false; },
    async sitzungLaden() {
      try { csrfSetzen((await holen('sitzung')).csrf); this.angemeldet = true; } catch { this.angemeldet = false; }
    },
  },
  mounted() { this.sitzungLaden(); },
});

createApp(Wurzel).mount('#app');

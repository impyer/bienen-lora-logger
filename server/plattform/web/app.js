// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Oberfläche der Bienen-Plattform (Phase B lesend, Phase C Stammdaten und Stockkarte). Hash-Router ohne Build-Schritt:
//   #/                      Übersicht (?zeit= Bezugszeitpunkt, ISO)
//   #/volk/<id>             Volk-Cockpit (?tage=14&bis=ISO)
//   #/stand/<id>/umwelt     Umwelt eines Stands
//   #/datenquellen          unbenannte Felder, Zuordnungen, Import
//   #/verwaltung            Stammdaten pflegen: Stände, Völker, Beuten, Geräte, Kanäle (Phase C, Teil 1)
//   #/stockkarte            Durchsicht, Maßnahme, Varroa, Aufgabe erfassen und bearbeiten (Phase C, Teil 2)
//   #/analysen              Analysen & Völkervergleich (Nachtmedian, Tagesbilanz, Summen; Vorbild beelogger)
import { createApp, defineComponent, reactive } from './vendor/vue.esm-browser.prod.js';
import { NichtAngemeldet, csrfSetzen, holen, senden } from './api.js';
import Anmelden from './seiten/anmelden.js';
import Datenquellen from './seiten/datenquellen.js';
import Analysen from './seiten/analysen.js';
import Uebersicht from './seiten/uebersicht.js';
import Stockkarte from './seiten/stockkarte.js';
import Verwaltung from './seiten/verwaltung.js';
import Umwelt from './seiten/umwelt.js';
import Volk from './seiten/volk.js';

function routeLesen() {
  const [pfad, abfrage = ''] = (location.hash.replace(/^#/, '') || '/').split('?');
  return { pfad, query: Object.fromEntries(new URLSearchParams(abfrage)), schluessel: location.hash };
}

const route = reactive(routeLesen());
const NAVIGATION = [['/', 'Bienenstand'], ['/analysen', 'Analysen & Vergleich'], ['/stockkarte', 'Stockkarte'],
                    ['/datenquellen', 'Datenquellen'], ['/verwaltung', 'Verwaltung']];
window.addEventListener('hashchange', () => Object.assign(route, routeLesen()));

const Wurzel = defineComponent({
  components: { Analysen, Anmelden, Datenquellen, Stockkarte, Uebersicht, Umwelt, Verwaltung, Volk },
  data: () => ({ route, angemeldet: null, navigation: NAVIGATION }),
  template: `
    <header class="kopf">
      <a href="#/" class="marke"><svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5 20.2 7.25v9.5L12 21.5 3.8 16.75v-9.5Z" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="1.8"/></svg>Bienenlogger</a>
      <nav v-if="angemeldet" aria-label="Hauptnavigation">
        <a v-for="[ziel, text] in navigation" :key="ziel" :href="'#' + ziel" :class="{ aktiv: aktiv(ziel) }">{{ text }}</a>
        <button class="link rechts" @click="abmelden">Abmelden</button>
      </nav>
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
      if (p === '/stockkarte') return { komponente: 'Stockkarte', props: {} };
      if (p === '/analysen') return { komponente: 'Analysen', props: {} };
      return { komponente: 'Uebersicht', props: {} };
    },
  },
  methods: {
    aktiv(ziel) { const p = this.route.pfad; return ziel === '/' ? (p === '/' || p.startsWith('/volk/') || p.startsWith('/stand/')) : p.startsWith(ziel); },
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

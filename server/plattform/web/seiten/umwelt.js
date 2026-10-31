// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Umwelt & Tracht eines Stands (Design v0.3, Seite 3; Anforderungen: „Regen als Balken, Windrichtung als Windrose“,
// „Einheiten werden nie auf einer Achse gemischt“). Je Thema ein Diagramm: Luft, Luftdruck, Boden, Wind + Windrose,
// Regen, Licht/UV. Gerätewerte (Spannung, Funk) gehören auf die Seite Datenquellen und erscheinen hier nicht.
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { datenBeginn, regenMengen, verlaufOptionen, windrose, windroseOptionen, zahl } from '../diagramm.js';
import { Diagramm, Zeitraum, Zustand, zeitraumParameter } from './komponenten.js';

const GERAETEZONEN = ['elektronik', 'funk'];
const REGEN = { code: 'regen_menge', name: 'Regen', einheit: 'mm', achse: 'regenmenge', darstellung: 'balken', farbe: '#1f618d' };

export default defineComponent({
  components: { Diagramm, Zeitraum, Zustand },
  props: { route: Object, id: Number },
  emits: ['fehler', 'navigieren'],
  data: () => ({ stand: null, katalog: [], reihen: null, laden: true, fehler: '' }),
  template: `
    <section>
      <p><a href="#/">← Bienenstand</a></p>
      <h1>Umwelt <span v-if="stand">– {{ stand.name }}</span></h1>
      <Zustand :laden="laden" :fehler="fehler" />
      <Zeitraum :tage="zr.tage" :bis="zr.bis" @wahl="$emit('navigieren', { tage: $event.tage, bis: $event.bis })" />
      <p v-if="reihen && !umwelt.length" class="leer">Keine Umweltdaten in diesem Zeitraum. Ist dem Stand ein Gerät zugeordnet?</p>
      <div v-for="g in gruppen" :key="g.name" class="karte">
        <h2>{{ g.titel }} <small v-if="g.hinweis" class="klein">{{ g.hinweis }}</small></h2>
        <Diagramm :optionen="g.optionen" :name="'umwelt_' + g.name" :hoehe="g.hoehe || '260px'" />
      </div>
      <div v-if="reihen && umwelt.length" class="karte">
        <h2>Flugkreise und Saison</h2>
        <p class="leer">Flugkreise 1 / 3 / 5 km und Saisonkennzahlen (Trachtbeginn, Regentage, Flugwetterstunden) folgen.</p>
      </div>
    </section>`,
  computed: {
    zr() { return zeitraumParameter(this.route); },
    // Umweltreihen ohne Gerätewerte
    umwelt() { return (this.reihen?.reihen || []).filter((r) => !GERAETEZONEN.includes(r.zone)); },
    gruppen() {
      if (!this.reihen) return [];
      const k = Object.fromEntries(this.katalog.map((g) => [g.code, g]));
      const beginn = datenBeginn(this.umwelt);
      const von = beginn !== null ? new Date(Math.max(Date.parse(this.reihen.von), beginn)).toISOString() : this.reihen.von;
      const antwort = (reihen) => ({ ...this.reihen, von, reihen });
      const nimm = (f) => this.umwelt.filter(f);
      const g = [];
      const luft = nimm((r) => (r.messgroesse === 'temperatur' && r.zone !== 'boden') || r.messgroesse === 'feuchte');
      if (luft.length) g.push({ name: 'luft', titel: 'Luft: Temperatur und Feuchte', optionen: verlaufOptionen(antwort(luft), this.katalog) });
      const druck = nimm((r) => r.messgroesse === 'luftdruck');
      if (druck.length) g.push({ name: 'druck', titel: 'Luftdruck', hoehe: '200px', optionen: verlaufOptionen(antwort(druck), this.katalog) });
      const boden = nimm((r) => r.zone === 'boden').sort((a, b) => (a.tiefe_cm ?? 0) - (b.tiefe_cm ?? 0));
      if (boden.length) g.push({ name: 'boden', titel: 'Bodentemperatur', optionen: verlaufOptionen(antwort(boden), this.katalog) });
      const wind = nimm((r) => r.messgroesse === 'wind' || r.messgroesse === 'windboe');
      if (wind.length) g.push({ name: 'wind', titel: 'Wind', hoehe: '220px', optionen: verlaufOptionen(antwort(wind), this.katalog) });
      const richtung = nimm((r) => r.messgroesse === 'windrichtung')[0];
      const geschw = nimm((r) => r.messgroesse === 'wind')[0];
      if (richtung && geschw) {
        const rose = windrose(richtung.punkte, geschw.punkte);
        if (rose.n) g.push({ name: 'windrose', titel: 'Windrose', hinweis: `Anteil der Zeit je Herkunftsrichtung, ${rose.n} Werte`, hoehe: '340px', optionen: windroseOptionen(rose) });
      }
      const zaehler = nimm((r) => r.messgroesse === 'regen_summe')[0];
      if (zaehler) {
        const jeTag = this.zr.tage > 14;
        const mengen = regenMengen(zaehler.punkte, jeTag ? 'tag' : 'stunde');
        const summe = mengen.reduce((s, [, mm]) => s + mm, 0);
        const reihe = { messgroesse: REGEN.code, zone: 'luft_stand', bezeichnung: null, punkte: mengen.map(([t, mm]) => [new Date(t).toISOString(), mm]) };
        g.push({ name: 'regen', titel: `Regen je ${jeTag ? 'Tag' : 'Stunde'}`, hinweis: `${zahl(summe, 1)} mm im Zeitraum · aus dem Zählerstand der Station, Neustarts berücksichtigt`,
                 hoehe: '200px', optionen: verlaufOptionen(antwort([reihe]), [...this.katalog, REGEN]) });
      }
      const licht = nimm((r) => r.messgroesse === 'licht' || r.messgroesse === 'uv');
      if (licht.length) g.push({ name: 'licht', titel: 'Licht und UV', hoehe: '220px', optionen: verlaufOptionen(antwort(licht), this.katalog) });
      const bekannt = ['temperatur', 'feuchte', 'luftdruck', 'wind', 'windboe', 'windrichtung', 'regen_summe', 'regen_rate', 'licht', 'uv'];
      const rest = nimm((r) => !bekannt.includes(r.messgroesse));
      for (const achse of [...new Set(rest.map((r) => k[r.messgroesse]?.achse || r.messgroesse))]) {
        const teil = rest.filter((r) => (k[r.messgroesse]?.achse || r.messgroesse) === achse);
        g.push({ name: 'weitere_' + achse, titel: k[teil[0].messgroesse]?.name || achse, optionen: verlaufOptionen(antwort(teil), this.katalog) });
      }
      return g;
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

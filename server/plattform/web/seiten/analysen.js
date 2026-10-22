// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Analysen & Völkervergleich nach dem Designentwurf (Vorbild beelogger): Nachtmedian 00–04 Uhr, Tagesbilanz,
// Summen, Plausibilitätshinweise, Tabelle je Tag. Gleicher Berechnungsstandard für alle Völker (berechnung@version).
//   #/analysen?stand=1&tage=30&bis=ISO&voelker=1,2
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { zahl } from '../diagramm.js';
import { VOLKFARBEN, bilanzVergleichOptionen, referenzOptionen, summenOptionen } from '../stapel.js';
import { Diagramm, Zeitraum, Zustand, zeitraumParameter } from './komponenten.js';

export default defineComponent({
  components: { Diagramm, Zeitraum, Zustand },
  props: { route: Object },
  emits: ['fehler', 'navigieren'],
  data: () => ({ staende: [], daten: null, relativ: true, ohneEingriff: true, laden: true, fehler: '', farben: VOLKFARBEN }),
  template: `
    <section>
      <p class="klein" style="text-transform: uppercase; letter-spacing: .06em; font-weight: 600">Bienenlogger / Analyse</p>
      <h1>Analysen & Völkervergleich</h1>
      <p class="hinweis">beelogger-orientiert: Median der Nachtwerte, Tagesbilanz, Summen, Plausibilitätsprüfung und Eingriffsbezug.</p>
      <Zustand :laden="laden" :fehler="fehler" />
      <template v-if="!laden">
        <p v-if="!staende.length" class="leer">Noch keine Völker. In der <a href="#/verwaltung">Verwaltung</a> anlegen.</p>
        <div v-else class="kopfzeile">
          <div class="zeile">
            <label class="klein">Stand <select :value="standId" @change="$emit('navigieren', { stand: $event.target.value, voelker: '' })" aria-label="Stand">
              <option v-for="s in staende" :key="s.id" :value="s.id">{{ s.name }}</option></select></label>
            <span class="klein">Völker</span>
            <button v-for="v in voelkerAmStand" :key="v.id" :class="{ aktiv: gewaehlt.includes(v.id) }" @click="umschalten(v.id)">{{ v.name }}</button>
          </div>
          <Zeitraum :tage="zr.tage" :bis="zr.bis" @wahl="$emit('navigieren', { tage: $event.tage, bis: $event.bis })" />
        </div>

        <template v-if="daten && daten.voelker.length">
          <div class="kennzahlen">
            <div class="kennzahl"><div class="titel">Nacht-Referenzwerte</div><div class="wert">{{ summe('tagesreferenz') }}</div>
              <div class="unter">Median 00:00–04:00 Uhr, Europe/Berlin</div></div>
            <div class="kennzahl"><div class="titel">Mittlere letzte Tagesbilanz</div><div class="wert">{{ letzteBilanz === null ? '–' : vorzeichen(letzteBilanz) }}<small>kg</small></div>
              <div class="unter">über {{ daten.voelker.length }} Völker, Tage mit Eingriff ausgenommen</div></div>
            <div class="kennzahl"><div class="titel">Plausibilitäts-Hinweise</div><div class="wert" :class="{ minus: hinweise.length }">{{ hinweise.length }}</div>
              <div class="unter">Sprung |Δ| > 1 kg ohne Eingriff, Sensor-Fehlercodes; keine biologische Diagnose</div></div>
            <div class="kennzahl"><div class="titel">Messpunkte Gewicht</div><div class="wert">{{ daten.voelker.reduce((s, v) => s + v.messpunkte, 0).toLocaleString('de-DE') }}</div>
              <div class="unter">im gewählten Zeitraum</div></div>
          </div>

          <div class="cockpit">
            <div>
              <div class="karte">
                <div class="kopfzeile"><h2 style="margin: 0">Nachtmedian (Tagesreferenz)</h2>
                  <label class="klein"><input type="checkbox" v-model="relativ"> relativ zum ersten Tag</label></div>
                <Diagramm :optionen="referenzDiagramm" hoehe="300px" name="referenz" />
                <p class="klein">Unterschiedliche Beutenmasse und Kalibrierung: Für den Vergleich zählt die Veränderung, nicht die absolute Masse.</p>
              </div>
              <div class="karte" style="margin-top: 16px">
                <h2>Tagesbilanz je Volk <small class="klein">grau schraffiert = Tag mit Eingriff, nicht biologisch deuten</small></h2>
                <Diagramm :optionen="bilanzDiagramm" hoehe="260px" name="bilanzvergleich" />
              </div>
              <div class="karte" style="margin-top: 16px">
                <div class="kopfzeile"><h2 style="margin: 0">Summe der Tagesbilanzen</h2>
                  <label class="klein"><input type="checkbox" v-model="ohneEingriff"> Tage mit Eingriff auslassen</label></div>
                <Diagramm :optionen="summenDiagramm" hoehe="260px" name="summen" />
              </div>
            </div>
            <aside class="seitenleiste">
              <div class="karte">
                <h2>Berechnungsmethodik</h2>
                <table class="tabelle klein"><tbody>
                  <tr><td>Referenz</td><td class="zahl"><b>Median 00–04 Uhr</b></td></tr>
                  <tr><td>Tagesbilanz</td><td class="zahl"><b>Tag t − Vortag</b></td></tr>
                  <tr><td>Zeitbasis</td><td class="zahl"><b>Europe/Berlin</b></td></tr>
                  <tr><td>Eingriffe</td><td class="zahl"><b>separat markiert</b></td></tr>
                  <tr><td>Berechnung</td><td class="zahl"><code>{{ berechnung }}</code></td></tr></tbody></table>
                <p class="warnung klein">Gewichtsänderungen können durch Tracht, Wetter oder Eingriffe verursacht sein. Keine automatische Schwarm- oder Varroa-Diagnose aus diesen Kennzahlen.</p>
              </div>
              <div class="karte">
                <h2>Tagesreferenz · letzte Nacht</h2>
                <div v-for="(v, i) in daten.voelker" :key="v.id" style="margin: 8px 0">
                  <div class="kopfzeile klein"><span>{{ v.name }}</span><b class="zahl">{{ v.letzte_referenz ? zahl(v.letzte_referenz.referenz_kg, 2) + ' kg' : '–' }}</b></div>
                  <div class="balken"><span :style="{ width: balken(v) + '%', background: farben[i % farben.length] }"></span></div>
                </div>
              </div>
              <div class="karte">
                <h2>Summen im Zeitraum</h2>
                <table class="tabelle klein"><thead><tr><th>Volk</th><th class="zahl">Σ alle</th><th class="zahl">Σ ohne Eingriff</th></tr></thead>
                  <tbody><tr v-for="v in daten.voelker" :key="v.id"><td>{{ v.name }}</td>
                    <td class="zahl">{{ v.summe_kg === null ? '–' : vorzeichen(v.summe_kg) }}</td><td class="zahl">{{ v.summe_ohne_eingriff_kg === null ? '–' : vorzeichen(v.summe_ohne_eingriff_kg) }}</td></tr></tbody></table>
              </div>
              <div class="karte">
                <h2>Hinweise</h2>
                <p v-if="!hinweise.length" class="leer">Keine.</p>
                <ul class="chronik"><li v-for="h in hinweise" :key="h.text"><span class="marke" style="background: #c77700">!</span><div class="klein">{{ h.text }}</div></li></ul>
              </div>
            </aside>
          </div>

          <div class="karte" style="margin-top: 16px">
            <h2>Tagesbilanzen und Maßnahmen</h2>
            <div style="overflow-x: auto">
              <table class="tabelle tagestabelle">
                <thead><tr><th>Tag</th><template v-for="v in daten.voelker" :key="v.id"><th class="zahl">{{ v.name }} Median</th><th class="zahl">Δ kg</th></template></tr></thead>
                <tbody><tr v-for="t in tage" :key="t">
                  <td>{{ t.slice(8, 10) }}.{{ t.slice(5, 7) }}.</td>
                  <template v-for="v in daten.voelker" :key="v.id">
                    <td class="zahl">{{ median(v, t) }}</td>
                    <td class="zahl" :class="klasse(v, t)">{{ bil(v, t) }}<em v-if="eingriff(v, t)">Eingriff</em></td></template></tr></tbody>
              </table>
            </div>
          </div>
        </template>
        <p v-else-if="daten" class="leer">Keine Gewichtsdaten für die gewählten Völker in diesem Zeitraum.</p>
      </template>
    </section>`,
  computed: {
    zr() { return zeitraumParameter(this.route, 30); },
    standId() { return Number(this.route.query.stand) || this.staende[0]?.id; },
    voelkerAmStand() { return this.staende.find((s) => s.id === this.standId)?.voelker || []; },
    gewaehlt() {
      const q = (this.route.query.voelker || '').split(',').filter(Boolean).map(Number);
      return q.length ? q : this.voelkerAmStand.map((v) => v.id);
    },
    referenzDiagramm() { return referenzOptionen(this.daten.voelker, { relativ: this.relativ }); },
    bilanzDiagramm() { return bilanzVergleichOptionen(this.daten.voelker); },
    summenDiagramm() { return summenOptionen(this.daten.voelker, { ohneEingriff: this.ohneEingriff }); },
    tage() { return [...new Set(this.daten.voelker.flatMap((v) => v.tagesreferenz.map((r) => r.tag)))].sort().reverse(); },
    berechnung() { return this.daten.voelker.find((v) => v.tagesbilanz.length)?.tagesbilanz[0].berechnung || 'gewicht_tagesbilanz@1'; },
    letzteBilanz() {
      const w = this.daten.voelker.map((v) => [...v.tagesbilanz].reverse().find((b) => !b.mit_eingriff)).filter(Boolean).map((b) => b.bilanz_kg);
      return w.length ? w.reduce((a, b) => a + b, 0) / w.length : null;
    },
    hinweise() {
      const h = [];
      for (const v of this.daten.voelker) {
        for (const t of v.spruenge) h.push({ text: `${v.name}: Sprung ${this.vorzeichen(v.tagesbilanz.find((b) => b.tag === t).bilanz_kg)} kg am ${t.slice(8, 10)}.${t.slice(5, 7)}. ohne erfassten Eingriff – Maßnahme nachtragen oder Messung prüfen` });
        if (v.fehlcodes) h.push({ text: `${v.name}: ${v.fehlcodes} Temperaturwert(e) mit Sensor-Fehlercode (−127 / 85 °C) – Sensor prüfen (PLT26-11)` });
      }
      return h;
    },
  },
  methods: {
    zahl,
    vorzeichen(w) { return Math.abs(w) < 0.005 ? '±0,00' : (w > 0 ? '+' : '') + zahl(w, 2); },
    summe(feld) { return this.daten.voelker.reduce((s, v) => s + v[feld].length, 0); },
    balken(v) {
      const max = Math.max(...this.daten.voelker.map((x) => x.letzte_referenz?.referenz_kg || 0));
      return v.letzte_referenz && max ? Math.round(100 * v.letzte_referenz.referenz_kg / max) : 0;
    },
    zeile(v, t) { return v.tagesbilanz.find((b) => b.tag === t); },
    median(v, t) { const r = v.tagesreferenz.find((x) => x.tag === t); return r ? zahl(r.referenz_kg, 2) : '–'; },
    bil(v, t) { const b = this.zeile(v, t); return b ? this.vorzeichen(b.bilanz_kg) : '–'; },
    eingriff(v, t) { return this.zeile(v, t)?.mit_eingriff; },
    klasse(v, t) { const b = this.zeile(v, t); return b && !b.mit_eingriff ? (b.bilanz_kg >= 0 ? 'plus' : 'minus') : ''; },
    umschalten(id) {
      const s = new Set(this.gewaehlt);
      s.has(id) ? s.delete(id) : s.add(id);
      if (s.size) this.$emit('navigieren', { voelker: [...s].join(',') });
    },
  },
  async mounted() {
    try {
      this.staende = (await holen('staende', { zeit: this.zr.bisIso })).filter((s) => s.voelker.length);
      if (this.gewaehlt.length) {
        this.daten = await holen('vergleich', { volk_ids: this.gewaehlt.join(','), von: this.zr.von, bis: this.zr.bisIso });
        const reihenfolge = this.gewaehlt;
        this.daten.voelker.sort((a, b) => reihenfolge.indexOf(a.id) - reihenfolge.indexOf(b.id));
      }
    } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

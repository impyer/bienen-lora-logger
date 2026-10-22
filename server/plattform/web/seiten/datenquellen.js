// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Datenquellen: was der Importer nicht zuordnen konnte und wie aktuell die Geräte sind (K-06, HB-09)
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { zeitText } from '../diagramm.js';
import { Zustand } from './komponenten.js';

export default defineComponent({
  components: { Zustand },
  emits: ['fehler'],
  data: () => ({ p: null, laden: true, fehler: '' }),
  template: `
    <section>
      <h1>Datenquellen</h1>
      <Zustand :laden="laden" :fehler="fehler" />
      <template v-if="p">
        <h2>Unbenannte Felder <small class="klein">ohne Kanal, nicht als Messwert übernommen</small></h2>
        <p v-if="!p.unbenannt.length" class="leer">Keine.</p>
        <table v-else class="tabelle"><thead><tr><th>Gerät</th><th>Quellfeld</th><th>zuerst</th><th>zuletzt</th><th>Anzahl</th></tr></thead>
          <tbody><tr v-for="u in p.unbenannt" :key="u.geraet + u.quellfeld"><td>{{ u.geraet }}</td><td><code>{{ u.quellfeld }}</code></td><td>{{ zeitText(u.zuerst) }}</td><td>{{ zeitText(u.zuletzt) }}</td><td>{{ u.anzahl }}</td></tr></tbody></table>
        <p v-if="p.steuerfelder && p.steuerfelder.length" class="klein">Steuerfelder des Funkformats (kein Messwert, kein Handlungsbedarf):
          <span v-for="s in steuerNamen" :key="s"><code>{{ s }}</code> </span></p>
        <h2>Geräte ohne aktuelle Zuordnung</h2>
        <p v-if="!p.geraete_ohne_ziel.length" class="leer">Keine.</p>
        <table v-else class="tabelle"><thead><tr><th>Gerät</th><th>Art</th><th>letzte Nachricht</th></tr></thead>
          <tbody><tr v-for="g in p.geraete_ohne_ziel" :key="g.name"><td>{{ g.name }}</td><td>{{ g.art }}</td><td>{{ zeitText(g.letzte) }}</td></tr></tbody></table>
        <h2>Zuordnungsprüfung <small class="klein">Waage einem aufgelösten oder beutelosen Volk zugeordnet</small></h2>
        <p v-if="!p.zuordnung.length" class="leer">Keine Auffälligkeiten.</p>
        <table v-else class="tabelle"><thead><tr><th>Gerät</th><th>Volk</th><th>Befund</th></tr></thead>
          <tbody><tr v-for="z in p.zuordnung" :key="z.zuordnung_id" class="warnung"><td>{{ z.geraet }}</td><td>{{ z.volk }}</td><td>{{ z.befund }}</td></tr></tbody></table>
        <h2>Geräte</h2>
        <p v-if="!p.geraete.length" class="leer">Noch keine Nachrichten importiert.</p>
        <table v-else class="tabelle"><thead><tr><th>Gerät</th><th>letzte Nachricht</th><th>Nachrichten</th></tr></thead>
          <tbody><tr v-for="g in p.geraete" :key="g.name"><td>{{ g.name }}</td><td>{{ zeitText(g.letzte) }}</td><td>{{ g.nachrichten }}</td></tr></tbody></table>
        <h2>Import</h2>
        <p v-if="!p.importe.length" class="leer">Der Importer ist noch nicht gelaufen.</p>
        <table v-else class="tabelle"><thead><tr><th>Datei</th><th>Zeilen</th><th>zuletzt</th></tr></thead>
          <tbody><tr v-for="i in p.importe" :key="i.datei"><td><code>{{ i.datei }}</code></td><td>{{ i.zeilen }}</td><td>{{ zeitText(i.aktualisiert) }}</td></tr></tbody></table>
      </template>
    </section>`,
  computed: { steuerNamen() { return [...new Set((this.p.steuerfelder || []).map((s) => s.quellfeld))].sort(); } },
  methods: { zeitText },
  async mounted() {
    try { this.p = await holen('pruefungen'); } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

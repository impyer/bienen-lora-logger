// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Volk-Cockpit nach dem Designentwurf (16.10.2026): Kennzahlen, gestapelte Diagramme mit gemeinsamer Zeitachse und
// Stockkarten-Marken (Vorbild beelogger + BEEP), Messwerte-Auswahl, Vorher/Nachher zu einem Ereignis, Chronik.
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen } from '../api.js';
import { bilanzOptionen, reihenName, reihenSchluessel, zahl, zeitText } from '../diagramm.js';
import { MARKEN, ereignisListe, reihenFarbe, stapelOptionen } from '../stapel.js';
import { METHODEN, chronik, cockpitKennzahlen, vorzeichen } from '../kennzahlen.js';
import { Diagramm, Zeitraum, Zustand, zeitraumParameter } from './komponenten.js';

const VORWAHL = ['gewicht', 'temperatur'];
const ZONEN = { brutnest: 'Brutnest', deckel: 'Deckel', aussen: 'außen', luft_stand: 'Luft am Stand', waage: 'Waage',
                boden: 'Boden', flugloch: 'Flugloch', elektronik: 'Elektronik', funk: 'Funk' };

export default defineComponent({
  components: { Diagramm, Zeitraum, Zustand },
  props: { route: Object, id: Number },
  emits: ['fehler', 'navigieren'],
  data: () => ({ volk: null, katalog: [], reihen: null, bilanz: [], ereignisse: null, sichtbar: null, relativ: false,
                 vergleich: null, vergleichWahl: '', fensterTage: 3, laden: true, fehler: '', marken: MARKEN, zonen: ZONEN }),
  template: `
    <section>
      <p class="klein"><a href="#/">← Bienenstand</a></p>
      <Zustand :laden="laden" :fehler="fehler" />
      <template v-if="volk">
        <div class="kopfzeile">
          <div>
            <h1>{{ volk.name }} <small v-if="volk.aufgeloest_am">aufgelöst {{ zeitText(volk.aufgeloest_am) }}</small></h1>
            <p class="stammdaten">
              <span v-if="volk.koenigin">Königin {{ volk.koenigin.farbe }} {{ volk.koenigin.jahrgang }}<template v-if="volk.koenigin.rasse"> · {{ volk.koenigin.rasse }}</template></span>
              <span v-if="volk.beute">{{ volk.beute.beutentyp || volk.beute.bezeichnung }} · {{ volk.beute.brutzargen ?? '?' }} Brutzarge(n){{ volk.beute.honigzargen ? ' · ' + volk.beute.honigzargen + ' Honigraum' : '' }}</span>
              <span v-if="volk.stand">{{ volk.stand.name }}</span>
              <span v-for="g in volk.geraete.filter((x) => !x.bis)" :key="g.name">{{ g.name }}</span>
            </p>
          </div>
          <a :href="'#/stockkarte?volk=' + id" class="knopf">Eintrag erfassen</a>
        </div>

        <div class="kennzahlen">
          <div class="kennzahl"><div class="titel">Gewicht</div>
            <div class="wert">{{ kz.gewicht ? zahl(kz.gewicht[1], 1) : '–' }}<small>kg</small></div>
            <div class="unter">{{ kz.bilanz ? 'Tagesbilanz ' + vorzeichen(kz.bilanz.bilanz_kg) + ' kg' + (kz.bilanz.mit_eingriff ? ' · Eingriff' : '') : 'keine Tagesbilanz' }}</div></div>
          <div class="kennzahl"><div class="titel">Brutnest</div>
            <div class="wert">{{ kz.brut ? zahl(kz.brut[1], 1) : '–' }}<small>°C</small></div>
            <div class="unter">{{ kz.brut ? zeitText(kz.brut[0]) : 'keine Messung' }}</div></div>
          <div class="kennzahl"><div class="titel">Milbenfall</div>
            <div class="wert">{{ kz.varroa && kz.varroa.milben_pro_tag !== null ? zahl(kz.varroa.milben_pro_tag, 1) : (kz.varroa ? kz.varroa.milben : '–') }}<small>{{ kz.varroa && kz.varroa.milben_pro_tag !== null ? '/Tag' : (kz.varroa ? 'Milben' : '') }}</small></div>
            <div class="unter">{{ kz.varroa ? zeitText(kz.varroa.bis).slice(0, 6) + ' · ' + (methoden[kz.varroa.methode] || kz.varroa.methode) : 'keine Messung im Zeitraum' }}</div></div>
          <div class="kennzahl"><div class="titel">Durchsicht</div>
            <div class="wert">{{ kz.durchsicht ? zeitText(kz.durchsicht.zeit).slice(0, 6) : '–' }}</div>
            <div class="unter">{{ kz.durchsicht ? (kz.durchsicht.werte.length + ' Merkmale' + (kz.durchsicht.zeitgenauigkeit === 'nur_datum' ? ' · ohne Uhrzeit' : '')) : 'keine im Zeitraum' }}</div></div>
        </div>

        <div class="cockpit">
          <div>
            <div class="karte">
              <div class="kopfzeile">
                <div><h2 style="margin: 0">Messdaten und Stockkarte</h2>
                  <span class="klein">{{ zeitText(zr.von).slice(0, 6) }}–{{ zeitText(Date.parse(zr.bisIso) - 1).slice(0, 6) }} · Ortszeit Europe/Berlin, gespeichert in UTC</span></div>
                <Zeitraum :tage="zr.tage" :bis="zr.bis" @wahl="$emit('navigieren', { tage: $event.tage, bis: $event.bis })" />
              </div>
              <p v-if="reihen && !reihen.reihen.length && !hatMilben" class="leer">Keine Messwerte in diesem Zeitraum.</p>
              <Diagramm v-else-if="reihen" :optionen="verlauf" :hoehe="verlaufHoehe" name="verlauf" />
              <p class="klein legende"><span v-for="[art, b] in sichtbareMarken" :key="art" class="chip"><b :style="{ color: b[1] }">{{ b[0] }}</b> {{ b[2] }}</span>
                <span v-if="hatNurDatum" class="chip">Tagesband = Eintrag ohne Uhrzeit</span>
                <span v-if="vergleich" class="chip" style="background: rgba(37,99,235,.10)">vorher</span><span v-if="vergleich" class="chip warn">nachher</span></p>
            </div>
            <div class="karte" style="margin-top: 16px">
              <h2>Tagesbilanz <small class="klein">Median 00–04 Uhr, Vortag abgezogen · gewicht_tagesbilanz@1</small></h2>
              <p v-if="!bilanz.length" class="leer">Keine Tagesbilanz in diesem Zeitraum.</p>
              <Diagramm v-else :optionen="bilanzDiagramm" hoehe="200px" name="bilanz" />
            </div>
          </div>

          <aside class="seitenleiste">
            <div class="karte messwahl">
              <h2>Messwerte</h2>
              <template v-for="(gruppe, titel) in gruppen" :key="titel">
                <h3>{{ titel }}</h3>
                <label v-for="r in gruppe" :key="schluessel(r)"><input type="checkbox" :checked="!sichtbar || sichtbar.has(schluessel(r))" @change="umschalten(schluessel(r))">
                  <span class="farbe" :style="{ background: farbe(r) }"></span>{{ zonen[r.zone] || r.bezeichnung || name(r) }}
                  <small v-if="r.ohne_geraetezeit" class="klein" title="Zeit vom Empfang, nicht vom Gerät">({{ r.ohne_geraetezeit }} ohne Gerätezeit)</small></label>
              </template>
              <template v-if="hatMilben"><h3>Milbenfall</h3>
                <label><input type="checkbox" :checked="!sichtbar || sichtbar.has('milbenfall')" @change="umschalten('milbenfall')"><span class="farbe" style="background: #9f1239"></span>Windel, pro Tag</label></template>
              <label style="margin-top: 10px"><input type="checkbox" v-model="relativ"> Gewicht relativ zum Beginn</label>
              <p class="klein">Nur Messwerte mit Daten im gewählten Zeitraum. Zoomen mit Strg + Mausrad oder dem Schieber.</p>
            </div>

            <div class="karte">
              <h2>Vorher / nachher</h2>
              <p v-if="!vergleichsZiele.length" class="leer">Keine Stockkarten-Einträge im Zeitraum.</p>
              <template v-else>
                <select v-model="vergleichWahl" aria-label="Ereignis für den Vergleich" style="width: 100%">
                  <option v-for="e in vergleichsZiele" :key="e.schluessel" :value="e.schluessel">{{ zeitText(e.zeit).slice(0, 6) }} · {{ e.name }}{{ e.text ? ' – ' + e.text.slice(0, 30) : '' }}</option></select>
                <div class="zeile"><span class="klein">Fenster</span>
                  <span class="segmente"><button v-for="t in [1, 3, 7]" :key="t" :class="{ aktiv: fensterTage === t }" @click="fensterTage = t">± {{ t }} T</button></span></div>
                <table v-if="vergleich" class="tabelle klein vergleich">
                  <thead><tr><th>Kennzahl</th><th class="zahl">vorher</th><th class="zahl">nachher</th><th class="zahl">Δ</th></tr></thead>
                  <tbody><tr v-for="k in vergleich.kennzahlen" :key="k.name">
                    <td>{{ kennzahlName(k) }} <small>({{ k.einheit }})</small></td>
                    <td class="zahl">{{ k.vorher === null ? '–' : zahl(k.vorher, 2) }}</td><td class="zahl">{{ k.nachher === null ? '–' : zahl(k.nachher, 2) }}</td>
                    <td class="zahl">{{ k.delta === null ? '–' : vorzeichen(k.delta) }}</td></tr></tbody></table>
                <p v-if="eingriffstage" class="klein">Tagesbilanz ohne {{ eingriffstage }} Tag(e) mit Eingriff.</p>
                <p class="klein">Mittelwerte aus den Messwerten. Erst Wetter und Eingriff prüfen, dann deuten.</p>
              </template>
            </div>

            <div class="karte">
              <h2>Stockkarte <small class="klein">neueste zuerst</small></h2>
              <p v-if="offeneAufgaben.length" class="warnung klein">Aufgaben: <span v-for="a in offeneAufgaben" :key="a.id">{{ a.faellig_am.slice(8, 10) }}.{{ a.faellig_am.slice(5, 7) }}. {{ a.text }}; </span></p>
              <p v-if="ereignisse && !liste.length" class="leer">Keine Einträge in diesem Zeitraum.</p>
              <ul class="chronik">
                <li v-for="e in liste" :key="e.schluessel">
                  <span class="marke" :style="{ background: e.farbe }">{{ e.buchstabe }}</span>
                  <div><div class="klein">{{ e.zeit }}<em v-if="e.nurDatum" title="Uhrzeit aus BEEP übernommen, nicht erfasst"> Uhrzeit übernommen</em> · {{ e.art }}</div>
                    <div>{{ e.text }}</div>
                    <a v-if="e.bearbeiten" :href="'#/stockkarte?art=' + e.bearbeiten" class="klein">bearbeiten</a></div>
                </li>
              </ul>
            </div>
          </aside>
        </div>
      </template>
    </section>`,
  computed: {
    zr() { return zeitraumParameter(this.route); },
    katalogMap() { return Object.fromEntries(this.katalog.map((g) => [g.code, g])); },
    verlaufRoh() {
      return stapelOptionen(this.reihen, this.katalog, { sichtbar: this.sichtbar, relativ: this.relativ, ereignisse: this.ereignisse,
                                                       fenster: this.vergleich ? { vorher: this.vergleich.vorher, nachher: this.vergleich.nachher } : null });
    },
    verlauf() { const { hoehe, ...o } = this.verlaufRoh; return o; },
    verlaufHoehe() { return this.verlaufRoh.hoehe + 'px'; },
    hatMilben() { return (this.ereignisse?.varroa || []).some((v) => v.milben_pro_tag !== null && v.milben_pro_tag !== undefined); },
    hatNurDatum() { return ereignisListe(this.ereignisse).some((e) => e.nurDatum); },
    sichtbareMarken() {
      const arten = new Set(ereignisListe(this.ereignisse).map((e) => e.art));
      const gesehen = new Set();
      return Object.entries(MARKEN).filter(([a, b]) => arten.has(a) && !gesehen.has(b[0] + b[2]) && gesehen.add(b[0] + b[2]));
    },
    bilanzDiagramm() { return bilanzOptionen(this.bilanz); },
    gruppen() {
      const g = {};
      for (const r of this.reihen?.reihen || []) (g[this.katalogMap[r.messgroesse]?.name || r.messgroesse] ||= []).push(r);
      return g;
    },
    kz() { return cockpitKennzahlen(this.reihen?.reihen, this.bilanz, this.ereignisse); },
    vergleichsZiele() {
      return ereignisListe(this.ereignisse).filter((e) => e.schluessel).reverse();
    },
    liste() { return chronik(this.ereignisse); },
    eingriffstage() {
      const g = (this.vergleich?.kennzahlen || []).find((k) => k.berechnung === 'gewicht_tagesbilanz@1');
      return g ? (g.eingriff_vorher || 0) + (g.eingriff_nachher || 0) : 0;
    },
    offeneAufgaben() { return (this.ereignisse?.aufgaben || []).filter((a) => !a.erledigt_am); },
    methoden: () => METHODEN,
  },
  watch: {
    vergleichWahl() { this.vergleichLaden(); },
    fensterTage() { this.vergleichLaden(); },
  },
  methods: {
    zeitText, zahl,
    vorzeichen,
    schluessel: reihenSchluessel,
    name(r) { return reihenName(r, this.katalogMap); },
    farbe(r) { return reihenFarbe(r, this.katalogMap[r.messgroesse]) || '#5b635e'; },
    kennzahlName(k) { return k.name.replace(/brutnest|deckel|aussen|luft_stand/g, (z) => ZONEN[z] || z); },
    umschalten(k) {
      const alle = new Set([...(this.reihen?.reihen || []).map(reihenSchluessel), 'milbenfall']);
      const s = new Set(this.sichtbar || alle);
      s.has(k) ? s.delete(k) : s.add(k);
      this.sichtbar = s;
    },
    async vergleichLaden() {
      if (!this.vergleichWahl) { this.vergleich = null; return; }
      const [art, eid] = this.vergleichWahl.split(':');
      try {
        this.vergleich = await holen(`voelker/${this.id}/vorher_nachher`, { art, ereignis_id: eid, tage: this.fensterTage });
      } catch (e) { this.$emit('fehler', e); this.vergleich = null; }
    },
  },
  async mounted() {
    const p = { von: this.zr.von, bis: this.zr.bisIso };
    try {
      [this.volk, this.katalog, this.reihen, this.bilanz, this.ereignisse] = await Promise.all([
        holen(`voelker/${this.id}`, { zeit: this.zr.bisIso }), holen('messgroessen'),
        holen(`voelker/${this.id}/messreihen`, p), holen(`voelker/${this.id}/tagesbilanz`, p),
        holen(`voelker/${this.id}/ereignisse`, p)]);
      // Zu Beginn Gewicht, Temperaturen und Milbenfall zeigen (wie im Entwurf); weitere Kurven über die Auswahl
      const start = this.reihen.reihen.filter((r) => VORWAHL.includes(r.messgroesse)).map(reihenSchluessel);
      this.sichtbar = start.length ? new Set([...start, 'milbenfall']) : null;
      // Vorher/Nachher zuerst für die jüngste Maßnahme, sonst den jüngsten Eintrag
      const ziele = this.vergleichsZiele;
      this.vergleichWahl = (ziele.find((e) => e.schluessel.startsWith('massnahme:')) || ziele[0] || {}).schluessel || '';
    } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

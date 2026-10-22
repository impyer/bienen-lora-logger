// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Stockkarte erfassen am Handy (Phase C, Teil 2; Vorbild BEEP): Durchsicht mit Checkliste, Maßnahme, Varroa, Aufgabe –
// für mehrere Völker zugleich, mit Uhrzeit (Ortszeit, vorbelegt mit jetzt).
//   #/stockkarte?volk=3                    neu, Volk 3 vorgewählt
//   #/stockkarte?art=durchsicht&id=12      bestehenden Eintrag bearbeiten oder löschen
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen, senden } from '../api.js';
import { jetztOrtszeit, ortszeitNachUtc, zeitText } from '../diagramm.js';
import { istZeitpunkt } from '../kennzahlen.js';
import { Zustand } from './komponenten.js';

const ARTEN = [['durchsicht', 'Durchsicht'], ['massnahme', 'Maßnahme'], ['varroa', 'Varroa'], ['aufgabe', 'Aufgabe']];
const MASSNAHMEN = { behandlung: 'Behandlung', fuetterung: 'Fütterung', ernte: 'Ernte', zarge_auf: 'Zarge auf',
                     zarge_ab: 'Zarge ab', umsetzen: 'Umsetzen', tarieren: 'Waage tarieren', sonstiges: 'Sonstiges' };
const GENAU = { exakt: 'Uhrzeit genau', geschaetzt: 'Uhrzeit geschätzt', nur_datum: 'nur Datum bekannt' };

const heute = (tage = 0) => jetztOrtszeit(Date.now() + tage * 86400000).slice(0, 10);
const ortszeit = (iso) => (iso ? jetztOrtszeit(Date.parse(iso)) : '');

function leer(art = 'durchsicht') {
  const jetzt = jetztOrtszeit();
  return { art, zeit: jetzt, vorgabe: jetzt, genau: 'exakt', notiz: '', werte: {},
           massnahme: { art: 'behandlung', bis: '', mittel: '', menge: '', einheit: '' },
           varroa: { methode: 'windel', von: jetztOrtszeit(Date.now() - 3 * 86400000), milben: '' },
           aufgabe: { faellig: heute(7), text: '' } };
}

export default defineComponent({
  components: { Zustand },
  props: { route: Object },
  emits: ['fehler'],
  data: () => ({ staende: [], liste: null, aufgaben: [], gewaehlt: [], f: leer(), bearbeiten: null, laden: true,
                 fehler: '', meldung: '', laeuft: false, arten: ARTEN, massnahmen: MASSNAHMEN, genauigkeiten: GENAU }),
  template: `
    <section class="stockkarte">
      <h1>{{ bearbeiten ? 'Eintrag bearbeiten' : 'Stockkarte' }}</h1>
      <Zustand :laden="laden" :fehler="fehler" />
      <p v-if="meldung" class="ok" role="status">{{ meldung }}</p>
      <template v-if="!laden">
        <div v-if="!bearbeiten" class="reiter" role="tablist">
          <button v-for="[a, t] in arten" :key="a" role="tab" :aria-selected="f.art === a" :class="{ aktiv: f.art === a }" @click="f.art = a">{{ t }}</button>
        </div>
        <fieldset v-if="!bearbeiten" class="voelker">
          <legend>Völker</legend>
          <p v-if="!staende.length" class="leer">Noch keine Völker. In der <a href="#/verwaltung">Verwaltung</a> anlegen.</p>
          <div v-for="s in staende" :key="s.id"><strong>{{ s.name }}</strong>
            <label v-for="v in s.voelker" :key="v.id" class="volkwahl"><input type="checkbox" :value="v.id" v-model="gewaehlt"> {{ v.name }}</label>
            <button v-if="s.voelker.length > 1" class="link" @click="alleAmStand(s)">alle</button>
          </div>
        </fieldset>
        <p v-else class="hinweis">{{ bearbeiten.volk || ('Volk ' + bearbeiten.volk_id) }}</p>

        <form @submit.prevent="speichern" class="eingabe">
          <template v-if="f.art !== 'aufgabe'">
            <label>{{ f.art === 'varroa' ? 'Ende (Auszählen)' : f.art === 'massnahme' ? 'Beginn' : 'Zeit' }}
              <input type="datetime-local" v-model="f.zeit" required></label>
            <label>Genauigkeit <select v-model="f.genau"><option v-for="(t, g) in genauigkeiten" :value="g">{{ t }}</option></select></label>
          </template>

          <template v-if="f.art === 'durchsicht'">
            <p v-if="!liste" class="leer">Noch keine Checkliste. <button type="button" @click="checklisteUebernehmen">Standard-Checkliste übernehmen</button></p>
            <template v-else>
              <template v-for="(gruppe, gname) in gruppen" :key="gname">
                <h2>{{ gname }}</h2>
                <div v-for="m in gruppe" :key="m.code" class="merkmal">
                  <span class="name">{{ m.name }}<small v-if="m.einheit" class="klein"> ({{ m.einheit }})</small></span>
                  <span v-if="m.eingabetyp === 'janein'" class="knoepfe">
                    <button type="button" :class="{ aktiv: f.werte[m.code] === true }" @click="setzen(m.code, true)">ja</button>
                    <button type="button" :class="{ aktiv: f.werte[m.code] === false }" @click="setzen(m.code, false)">nein</button></span>
                  <span v-else-if="m.eingabetyp === 'bewertung'" class="knoepfe">
                    <button v-for="n in 5" :key="n" type="button" :class="{ aktiv: f.werte[m.code] === n }" @click="setzen(m.code, n)">{{ n }}</button></span>
                  <select v-else-if="m.eingabetyp === 'liste'" v-model="f.werte[m.code]" :aria-label="m.name"><option :value="undefined">–</option><option v-for="o in m.optionen" :value="o">{{ o }}</option></select>
                  <input v-else-if="m.eingabetyp === 'zahl' || m.eingabetyp === 'ganzzahl'" type="number" inputmode="decimal" min="0" :step="m.eingabetyp === 'zahl' ? 'any' : 1" v-model.number="f.werte[m.code]" :aria-label="m.name">
                  <input v-else-if="m.eingabetyp === 'datum'" type="date" v-model="f.werte[m.code]" :aria-label="m.name">
                  <textarea v-else v-model="f.werte[m.code]" rows="2" :aria-label="m.name"></textarea>
                </div>
              </template>
            </template>
          </template>

          <template v-if="f.art === 'massnahme'">
            <label>Art <select v-model="f.massnahme.art" aria-label="Art der Maßnahme"><option v-for="(t, a) in massnahmen" :value="a">{{ t }}</option></select></label>
            <label>Ende <small class="klein">(leer = Zeitpunkt)</small> <input type="datetime-local" v-model="f.massnahme.bis" aria-label="Ende"></label>
            <label>Mittel <input v-model.trim="f.massnahme.mittel" placeholder="z. B. Ameisensäure 60 %" aria-label="Mittel"></label>
            <label>Menge <input type="number" inputmode="decimal" min="0" step="any" v-model.number="f.massnahme.menge" aria-label="Menge">
              <input v-model.trim="f.massnahme.einheit" placeholder="Einheit" size="5" aria-label="Einheit"></label>
          </template>

          <template v-if="f.art === 'varroa'">
            <label>Methode <select v-model="f.varroa.methode" aria-label="Methode"><option value="windel">Windel</option><option value="puderzucker">Puderzucker</option><option value="auswaschung">Auswaschung</option></select></label>
            <label>Beginn (Windel eingelegt bzw. Probe) <input type="datetime-local" v-model="f.varroa.von" required aria-label="Beginn"></label>
            <label>Milben <input type="number" inputmode="numeric" min="0" step="1" v-model.number="f.varroa.milben" required aria-label="Milben"></label>
          </template>

          <template v-if="f.art === 'aufgabe'">
            <label>Fällig am <input type="date" v-model="f.aufgabe.faellig" required aria-label="Fällig am"></label>
            <label>Aufgabe <input v-model.trim="f.aufgabe.text" required placeholder="z. B. Windel auszählen" aria-label="Aufgabe"></label>
          </template>

          <label v-if="f.art !== 'aufgabe'">Notiz <textarea v-model="f.notiz" rows="3" aria-label="Notiz"></textarea></label>
          <div class="zeile">
            <button type="submit" class="haupt" :disabled="laeuft || (!bearbeiten && !gewaehlt.length)">Speichern{{ !bearbeiten && gewaehlt.length > 1 ? ' (' + gewaehlt.length + ' Völker)' : '' }}</button>
            <button v-if="bearbeiten" type="button" class="gefahr" @click="loeschen">Löschen</button>
            <a v-if="bearbeiten" :href="'#/volk/' + bearbeiten.volk_id">zum Volk</a>
          </div>
        </form>

        <h2>Offene Aufgaben</h2>
        <p v-if="!aufgaben.length" class="leer">Keine.</p>
        <ul class="aufgaben">
          <li v-for="a in aufgaben" :key="a.id" :class="{ faellig: a.faellig_am <= heute }">
            <label><input type="checkbox" @change="erledigt(a)"> {{ datum(a.faellig_am) }} · {{ a.volk || a.stand }}: {{ a.text }}</label>
          </li>
        </ul>
      </template>
    </section>`,
  computed: {
    heute: () => heute(),
    gruppen() {
      const g = {};
      for (const m of this.liste?.merkmale || []) (g[m.gruppe || 'Weitere'] ||= []).push(m);
      return g;
    },
  },
  methods: {
    zeitText,
    datum(t) { return t.slice(8, 10) + '.' + t.slice(5, 7) + '.'; },
    setzen(code, wert) { this.f.werte[code] = this.f.werte[code] === wert ? undefined : wert; },
    alleAmStand(s) { this.gewaehlt = [...new Set([...this.gewaehlt, ...s.voelker.map((v) => v.id)])]; },
    utc(text, name) {
      // unveränderte Vorgabe „jetzt“: sekundengenau, damit ein eben angelegtes Volk schon besteht
      if (!this.bearbeiten && text === this.f.vorgabe) return new Date().toISOString();
      const t = ortszeitNachUtc(text);
      if (!t) throw new Error(`${name}: Zeit ungültig (Umstellungsstunde?)`);
      return t;
    },
    nutzlast() {
      const f = this.f;
      const werte = Object.fromEntries(Object.entries(f.werte).filter(([, w]) => w !== undefined && w !== null && w !== ''));
      if (f.art === 'durchsicht') {
        return { zeit: this.utc(f.zeit, 'Zeit'), zeitgenauigkeit: f.genau, notiz: f.notiz || null, werte,
                 ...(this.bearbeiten ? {} : { checkliste_version_id: this.liste?.version_id ?? null }) };
      }
      if (f.art === 'massnahme') {
        const m = f.massnahme;
        return { art: m.art, von: this.utc(f.zeit, 'Beginn'), bis: m.bis ? this.utc(m.bis, 'Ende') : null, zeitgenauigkeit: f.genau,
                 mittel: m.mittel || null, menge: m.menge === '' ? null : m.menge, einheit: m.einheit || null, notiz: f.notiz || null };
      }
      if (f.art === 'varroa') {
        const v = f.varroa;
        return { methode: v.methode, von: this.utc(v.von, 'Beginn'), bis: this.utc(f.zeit, 'Ende'), milben: v.milben,
                 anmerkung: f.notiz || null, zeitgenauigkeit: f.genau };
      }
      return { faellig_am: f.aufgabe.faellig, text: f.aufgabe.text };
    },
    pfad() { return { durchsicht: 'durchsichten', massnahme: 'massnahmen', varroa: 'varroa', aufgabe: 'aufgaben' }[this.f.art]; },
    async speichern() {
      this.fehler = ''; this.meldung = ''; this.laeuft = true;
      try {
        const daten = this.nutzlast();
        if (this.bearbeiten) {
          await senden(`stockkarte/${this.pfad()}/${this.bearbeiten.id}`, daten, 'PUT');
          this.meldung = 'Geändert.';
        } else {
          const r = await senden(`stockkarte/${this.pfad()}`, { ...daten, volk_ids: this.gewaehlt });
          this.meldung = `Gespeichert (${r.ids.length} ${r.ids.length === 1 ? 'Eintrag' : 'Einträge'}).`;
          const art = this.f.art;
          this.f = leer(art);
        }
        this.aufgaben = await holen('stockkarte/aufgaben');
      } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laeuft = false; }
    },
    async loeschen() {
      if (!window.confirm('Eintrag endgültig löschen?')) return;
      try {
        await senden(`stockkarte/${this.pfad()}/${this.bearbeiten.id}`, {}, 'DELETE');
        location.hash = '#/volk/' + this.bearbeiten.volk_id;
      } catch (e) { this.$emit('fehler', e); this.fehler = e.message; }
    },
    async erledigt(a) {
      try {
        await senden(`stockkarte/aufgaben/${a.id}/erledigt`, { zeit: new Date().toISOString(), erledigt: true });
        this.aufgaben = await holen('stockkarte/aufgaben');
      } catch (e) { this.$emit('fehler', e); this.fehler = e.message; }
    },
    async checklisteUebernehmen() {
      try {
        await senden('stockkarte/checkliste/standard', { zeit: new Date().toISOString() });
        this.liste = (await holen('stockkarte/checklisten'))[0] || null;
      } catch (e) { this.$emit('fehler', e); this.fehler = e.message; }
    },
    eintragLaden(art, e) {
      const f = leer(art);
      f.genau = e.zeitgenauigkeit;
      if (art === 'durchsicht') {
        f.zeit = ortszeit(e.zeit); f.notiz = e.notiz || '';
        for (const w of e.werte) f.werte[w.code] = w.wert;
      } else if (art === 'massnahme') {
        f.zeit = ortszeit(e.von); f.notiz = e.notiz || '';
        Object.assign(f.massnahme, { art: e.art, bis: istZeitpunkt(e.von, e.bis) ? '' : ortszeit(e.bis), mittel: e.mittel || '', menge: e.menge ?? '', einheit: e.einheit || '' });
      } else {
        f.zeit = ortszeit(e.bis); f.notiz = e.anmerkung || '';
        Object.assign(f.varroa, { methode: e.methode, von: ortszeit(e.von), milben: e.milben });
      }
      this.f = f;
    },
  },
  async mounted() {
    try {
      const q = this.route.query;
      const [staende, listen, aufgaben] = await Promise.all([holen('staende'), holen('stockkarte/checklisten'), holen('stockkarte/aufgaben')]);
      this.staende = staende.filter((s) => s.voelker.length);
      this.liste = listen[0] || null;
      this.aufgaben = aufgaben;
      if (q.art && q.id) {
        this.bearbeiten = await holen(`stockkarte/eintrag/${q.art}/${q.id}`);
        this.eintragLaden(q.art, this.bearbeiten);
      } else {
        if (q.volk) this.gewaehlt = [Number(q.volk)];
        if (q.art) this.f.art = q.art;
      }
    } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

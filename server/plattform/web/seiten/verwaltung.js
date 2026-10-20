// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Verwaltung der Stammdaten (Phase C, Teil 1): Messgrößen, Stände, Völker mit Beute, Geräte und Kanäle.
// Jede Änderung gilt ab dem oben gewählten Zeitpunkt (Ortszeit); die Datenbank beendet die alte Angabe und legt eine
// neue an, Historie wird nie überschrieben.
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { holen, senden } from '../api.js';
import { jetztOrtszeit, ortszeitNachUtc, zeitText } from '../diagramm.js';
import { Zustand } from './komponenten.js';

const ZONEN = { waage: 'Waage', brutnest: 'Brutnest', deckel: 'Deckel', aussen: 'außen', flugloch: 'Flugloch',
                boden: 'Boden', luft_stand: 'Luft am Stand', elektronik: 'Elektronik', funk: 'Funk' };
const ARTEN = { stockwaage: 'Stockwaage', beep_base: 'BEEP Base', wetter: 'Wetterstation', boden: 'Bodensonde', sonstiges: 'sonstiges' };

const leer = () => ({
  stand: { name: '', ort_oeffentlich: '' },
  volk: { name: '', stand_id: '', platz: '', beute: { bezeichnung: '', beutentyp: '', brutzargen: 1, honigzargen: 0 } },
  geraet: { name: '', art: 'stockwaage', modell: '', dev_eui: '' },
});

export default defineComponent({
  components: { Zustand },
  emits: ['fehler'],
  data: () => ({ d: null, laden: true, fehler: '', meldung: '', ab: jetztOrtszeit(), neu: leer(), aktion: {}, laeuft: false,
                 zonen: ZONEN, arten: ARTEN }),
  template: `
    <section class="verwaltung">
      <h1>Verwaltung</h1>
      <Zustand :laden="laden" :fehler="fehler" />
      <p v-if="meldung" class="ok" role="status">{{ meldung }}</p>
      <label class="ab">Änderungen gelten ab <input type="datetime-local" v-model="ab"> <small class="klein">Ortszeit</small></label>
      <template v-if="d">
        <h2>Messgrößen <small class="klein">{{ d.messgroessen.length }} im Katalog</small></h2>
        <p v-if="!d.messgroessen.length" class="leer">Der Katalog ist leer. Ohne Messgrößen gibt es keine Kanäle und keine Kurven.</p>
        <button @click="los('verwaltung/katalog/standard', {})">Standardkatalog übernehmen</button>
        <span class="klein"> legt nur fehlende Messgrößen an (Gewicht, Temperatur, Feuchte, Spannung, Wetter …)</span>

        <h2>Stände</h2>
        <table v-if="d.staende.length" class="tabelle"><tbody>
          <tr v-for="s in d.staende" :key="s.id"><td>{{ s.name }}</td><td class="klein">{{ s.ort_oeffentlich }}</td></tr>
        </tbody></table>
        <form class="zeile" @submit.prevent="los('verwaltung/staende', neu.stand, 'POST', () => neu.stand = leer().stand)">
          <input v-model.trim="neu.stand.name" placeholder="Name des Stands" required aria-label="Name des Stands">
          <input v-model.trim="neu.stand.ort_oeffentlich" placeholder="Ort (öffentlich, grob)" aria-label="Ort öffentlich">
          <button type="submit">Stand anlegen</button>
        </form>

        <h2>Völker</h2>
        <table v-if="d.voelker.length" class="tabelle">
          <thead><tr><th>Volk</th><th>Stand / Platz</th><th>Beute</th><th>Aktionen</th></tr></thead>
          <tbody><tr v-for="v in d.voelker" :key="v.id" :class="{ aufgeloest: v.aufgeloest_am }">
            <td><a :href="'#/volk/' + v.id">{{ v.name }}</a><small v-if="v.aufgeloest_am" class="klein"> aufgelöst {{ zeitText(v.aufgeloest_am) }}</small></td>
            <td>{{ standName(v.stand_id) }}<template v-if="v.platz !== null"> / {{ v.platz }}</template></td>
            <td>{{ v.beute || '–' }} <small class="klein" v-if="v.beute">{{ v.beutentyp }} · {{ v.brutzargen ?? '?' }} Brut, {{ v.honigzargen ?? '?' }} Honig</small></td>
            <td>
              <details v-if="!v.aufgeloest_am"><summary>ändern</summary>
                <form class="zeile" @submit.prevent="los('verwaltung/beuten/' + v.beute_id + '/konfiguration', { zeit: zeit(), brutzargen: f(v, 'brut', v.brutzargen), honigzargen: f(v, 'honig', v.honigzargen) })">
                  Zargen: <input type="number" min="0" max="9" v-model.number="feld(v, 'brut', v.brutzargen).wert" aria-label="Brutzargen"> Brut
                  <input type="number" min="0" max="9" v-model.number="feld(v, 'honig', v.honigzargen).wert" aria-label="Honigzargen"> Honig
                  <button type="submit">Zargen speichern</button></form>
                <form class="zeile" @submit.prevent="los('verwaltung/beuten/' + v.beute_id + '/aufstellen', { zeit: zeit(), stand_id: +f(v, 'stand', v.stand_id), platz: f(v, 'platz', v.platz) })">
                  Stand: <select v-model="feld(v, 'stand', v.stand_id).wert" aria-label="Stand"><option v-for="s in d.staende" :value="s.id">{{ s.name }}</option></select>
                  Platz <input type="number" min="0" v-model.number="feld(v, 'platz', v.platz).wert" aria-label="Platz">
                  <button type="submit">Beute versetzen</button></form>
                <form class="zeile" @submit.prevent="los('verwaltung/voelker/' + v.id + '/umsetzen', { zeit: zeit(), beute: { bezeichnung: f(v, 'neubeute', ''), beutentyp: v.beutentyp, brutzargen: v.brutzargen, honigzargen: v.honigzargen } })">
                  In neue Beute umsetzen: <input v-model.trim="feld(v, 'neubeute', '').wert" placeholder="Bezeichnung" required aria-label="Neue Beute">
                  <button type="submit">Umsetzen</button></form>
                <form class="zeile" @submit.prevent="aufloesen(v)">
                  <select v-model="feld(v, 'ziel', '').wert" aria-label="Auflösen oder vereinigen"><option value="">auflösen</option>
                    <option v-for="z in d.voelker.filter((x) => x.id !== v.id && !x.aufgeloest_am)" :value="z.id">vereinigen mit {{ z.name }}</option></select>
                  <button type="submit" class="gefahr">Ausführen</button></form>
              </details>
            </td></tr></tbody></table>
        <form class="block" @submit.prevent="volkAnlegen">
          <strong>Volk mit neuer Beute anlegen</strong>
          <div class="zeile">
            <input v-model.trim="neu.volk.name" placeholder="Name, z. B. Volk 8" required aria-label="Name des Volks">
            <select v-model="neu.volk.stand_id" required aria-label="Stand"><option value="" disabled>Stand wählen</option><option v-for="s in d.staende" :value="s.id">{{ s.name }}</option></select>
            <input type="number" min="0" v-model.number="neu.volk.platz" placeholder="Platz" aria-label="Platz">
          </div>
          <div class="zeile">
            <input v-model.trim="neu.volk.beute.bezeichnung" placeholder="Beute, z. B. Beute 8" required aria-label="Bezeichnung der Beute">
            <input v-model.trim="neu.volk.beute.beutentyp" placeholder="Beutentyp, z. B. Segeberger 1,5" aria-label="Beutentyp">
            <input type="number" min="0" max="9" v-model.number="neu.volk.beute.brutzargen" aria-label="Brutzargen"> Brut
            <input type="number" min="0" max="9" v-model.number="neu.volk.beute.honigzargen" aria-label="Honigzargen"> Honig
            <button type="submit" :disabled="!d.staende.length">Volk anlegen</button>
          </div>
          <p v-if="!d.staende.length" class="klein">Zuerst einen Stand anlegen.</p>
        </form>

        <h2>Geräte <small class="klein">Geräte, die schon gesendet haben, legt der Importer selbst an</small></h2>
        <article v-for="g in d.geraete" :key="g.id" class="geraet">
          <header><strong>{{ g.name }}</strong> <span class="klein">{{ arten[g.art] }} · letzte Nachricht {{ zeitText(g.letzte) }}</span>
            <span :class="g.volk_id || g.stand_id ? 'ok' : 'warnung'">{{ zielText(g) }}</span></header>
          <table v-if="g.kanaele.length" class="tabelle klein">
            <thead><tr><th>Quellfeld</th><th>Messgröße</th><th>Messstelle</th><th>gültig</th><th></th></tr></thead>
            <tbody><tr v-for="k in g.kanaele" :key="k.id" :class="{ beendet: k.bis }">
              <td><code>{{ k.quellfeld }}</code></td><td>{{ k.messgroesse_code }}<template v-if="k.versatz || k.faktor !== 1"> ({{ k.faktor }}·x{{ k.versatz >= 0 ? '+' : '' }}{{ k.versatz }})</template></td>
              <td>{{ zonen[k.zone] || k.zone }} {{ k.bezeichnung || '' }}</td><td>{{ zeitText(k.von) }}<template v-if="k.bis"> – {{ zeitText(k.bis) }}</template></td>
              <td><button v-if="!k.bis" class="link" @click="los('verwaltung/kanaele/' + k.id + '/beenden', { zeit: zeit() })">beenden</button></td></tr></tbody></table>
          <p v-if="g.unbenannt.length" class="warnung klein">Unbenannte Felder: <span v-for="u in g.unbenannt" :key="u.quellfeld"><code>{{ u.quellfeld }}</code> ({{ u.anzahl }}) </span></p>
          <details><summary>ändern</summary>
            <form class="zeile" @submit.prevent="zuordnen(g)">
              Zuordnen: <select v-model="feld(g, 'ziel', zielWert(g)).wert" aria-label="Ziel">
                <option value="">keine Zuordnung</option>
                <optgroup label="Volk (Stockwaage)"><option v-for="v in d.voelker.filter((x) => !x.aufgeloest_am)" :value="'v' + v.id">{{ v.name }}</option></optgroup>
                <optgroup label="Stand (Umwelt)"><option v-for="s in d.staende" :value="'s' + s.id">{{ s.name }}</option></optgroup></select>
              <button type="submit">Zuordnung speichern</button></form>
            <form class="zeile" @submit.prevent="los('verwaltung/geraete/' + g.id + '/vorlage', { zeit: zeit(), vorlage: f(g, 'vorlage', 'beelogger') })">
              Vorlage: <select v-model="feld(g, 'vorlage', g.stand_id ? 's2120' : 'beelogger').wert" aria-label="Vorlage"><option v-for="(v, k) in d.vorlagen" :value="k">{{ v.name }}</option></select>
              <button type="submit">Kanäle anlegen</button></form>
            <form class="zeile" @submit.prevent="kanalAnlegen(g)">
              Kanal: <input v-model.trim="feld(g, 'quellfeld', g.unbenannt[0]?.quellfeld || '').wert" placeholder="Quellfeld" required :list="'felder' + g.id" aria-label="Quellfeld">
              <datalist :id="'felder' + g.id"><option v-for="u in g.unbenannt" :value="u.quellfeld" /></datalist>
              <select v-model="feld(g, 'messgroesse', '').wert" required aria-label="Messgröße"><option value="" disabled>Messgröße</option><option v-for="m in d.messgroessen" :value="m.code">{{ m.name }}</option></select>
              <select v-model="feld(g, 'zone', g.stand_id ? 'luft_stand' : 'brutnest').wert" aria-label="Zone"><option v-for="(t, z) in zonen" :value="z">{{ t }}</option></select>
              Versatz <input type="number" step="0.01" v-model.number="feld(g, 'versatz', 0).wert" aria-label="Versatz">
              <button type="submit">Kanal anlegen</button></form>
            <form class="zeile" @submit.prevent="los('verwaltung/geraete/' + g.id, { art: f(g, 'art', g.art), modell: g.modell, dev_eui: g.dev_eui }, 'PUT')">
              Art: <select v-model="feld(g, 'art', g.art).wert" aria-label="Art"><option v-for="(t, a) in arten" :value="a">{{ t }}</option></select>
              <button type="submit">Art speichern</button></form>
            <p class="zeile"><button @click="los('verwaltung/geraete/' + g.id + '/nachtragen', {})">Werte nachtragen</button>
              <small class="klein">übernimmt ältere Nachrichten für neu angelegte Kanäle aus den Rohprotokollen</small></p>
          </details>
        </article>
        <form class="zeile" @submit.prevent="los('verwaltung/geraete', { ...neu.geraet, dev_eui: neu.geraet.dev_eui || null }, 'POST', () => neu.geraet = leer().geraet)">
          <input v-model.trim="neu.geraet.name" placeholder="TTN-Gerätename" required pattern="[A-Za-z0-9_.\\-]+" aria-label="TTN-Gerätename">
          <select v-model="neu.geraet.art" aria-label="Art"><option v-for="(t, a) in arten" :value="a">{{ t }}</option></select>
          <input v-model.trim="neu.geraet.modell" placeholder="Modell" aria-label="Modell">
          <button type="submit">Gerät anlegen</button>
        </form>
      </template>
    </section>`,
  methods: {
    zeitText,
    zeit() { return ortszeitNachUtc(this.ab); },
    standName(id) { return this.d.staende.find((s) => s.id === id)?.name || '–'; },
    zielText(g) {
      if (g.volk_id) return 'an ' + (this.d.voelker.find((v) => v.id === g.volk_id)?.name || 'Volk ' + g.volk_id);
      if (g.stand_id) return 'am ' + this.standName(g.stand_id);
      return 'nicht zugeordnet';
    },
    zielWert(g) { return g.volk_id ? 'v' + g.volk_id : g.stand_id ? 's' + g.stand_id : ''; },
    // Formularwerte je Zeile (Objekt + Name), mit Vorbelegung aus den aktuellen Daten
    feld(obj, name, start) {
      const k = (obj.beute_id !== undefined ? 'v' : 'g') + obj.id + name;
      if (!this.aktion[k]) this.aktion[k] = { wert: start ?? '' };
      return this.aktion[k];
    },
    f(obj, name, start) { return this.feld(obj, name, start).wert; },
    async los(pfad, daten, methode = 'POST', danach = null) {
      this.fehler = ''; this.meldung = '';
      if (daten && 'zeit' in daten && !daten.zeit) { this.fehler = 'Zeitpunkt ungültig (in der Umstellungsstunde nicht vorhanden?)'; return; }
      this.laeuft = true;
      try {
        const r = await senden(pfad, daten, methode);
        this.meldung = 'Gespeichert.' + (r && r.messwerte !== undefined ? ` ${r.messwerte} Messwerte nachgetragen.` : '')
          + (r && r.kanaele ? ` ${r.kanaele.length} Kanäle angelegt.` : '') + (r && r.neu !== undefined ? ` ${r.neu} Messgrößen neu.` : '');
        if (danach) danach();
        this.aktion = {};
        await this.laden_();
      } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laeuft = false; }
    },
    volkAnlegen() {
      const v = this.neu.volk;
      this.los('verwaltung/voelker', { ...v, zeit: this.zeit(), stand_id: +v.stand_id, platz: v.platz === '' ? null : v.platz },
               'POST', () => { this.neu.volk = leer().volk; });
    },
    aufloesen(v) {
      const ziel = this.f(v, 'ziel', '');
      const text = ziel ? `${v.name} mit dem Zielvolk vereinigen?` : `${v.name} auflösen?`;
      if (!window.confirm(text + ' Belegung und Waagenzuordnung enden zum gewählten Zeitpunkt.')) return;
      this.los(`verwaltung/voelker/${v.id}/aufloesen`, { zeit: this.zeit(), art: ziel ? 'vereinigung' : 'aufloesung', ziel_volk_id: ziel ? +ziel : null });
    },
    zuordnen(g) {
      const w = this.f(g, 'ziel', this.zielWert(g));
      this.los(`verwaltung/geraete/${g.id}/zuordnen`, { zeit: this.zeit(), volk_id: w[0] === 'v' ? +w.slice(1) : null, stand_id: w[0] === 's' ? +w.slice(1) : null });
    },
    kanalAnlegen(g) {
      this.los(`verwaltung/geraete/${g.id}/kanaele`, { zeit: this.zeit(), quellfeld: this.f(g, 'quellfeld', ''), messgroesse: this.f(g, 'messgroesse', ''),
                                                      zone: this.f(g, 'zone', 'brutnest'), versatz: this.f(g, 'versatz', 0) || 0 });
    },
    async laden_() { this.d = await holen('verwaltung'); },
  },
  async mounted() {
    try { await this.laden_(); } catch (e) { this.$emit('fehler', e); this.fehler = e.message; } finally { this.laden = false; }
  },
});

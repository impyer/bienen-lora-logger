// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Anmeldung mit dem einen Konto (ADR-0003 Nr. 10)
import { defineComponent } from '../vendor/vue.esm-browser.prod.js';
import { senden } from '../api.js';

export default defineComponent({
  emits: ['angemeldet'],
  data: () => ({ passwort: '', fehler: '', laeuft: false }),
  template: `
    <section class="anmelden">
      <h1>Anmelden</h1>
      <form @submit.prevent="anmelden">
        <label>Passwort <input type="password" v-model="passwort" autocomplete="current-password" required autofocus></label>
        <button type="submit" :disabled="laeuft">Anmelden</button>
        <p v-if="fehler" class="fehler" role="alert">{{ fehler }}</p>
      </form>
    </section>`,
  methods: {
    async anmelden() {
      this.laeuft = true;
      this.fehler = '';
      try {
        await senden('anmelden', { passwort: this.passwort });
        this.passwort = '';
        this.$emit('angemeldet');
      } catch (e) { this.fehler = e.message; } finally { this.laeuft = false; }
    },
  },
});

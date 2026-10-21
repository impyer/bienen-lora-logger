// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Gemeinsame Bausteine: Diagramm (ECharts), Zeitraumwahl, Lade- und Fehleranzeige
import { defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from '../vendor/vue.esm-browser.prod.js';

// ECharts-Diagramm; "name" macht es für Tests unter window.bienenDiagramme[name] erreichbar
export const Diagramm = defineComponent({
  props: { optionen: Object, hoehe: { type: String, default: '420px' }, name: String },
  setup(props) {
    const el = ref(null);
    let chart = null;
    const groesse = () => chart && chart.resize();
    const zeichnen = () => { if (chart && props.optionen) chart.setOption(props.optionen, { notMerge: true }); };
    onMounted(() => {
      chart = window.echarts.init(el.value, null, { renderer: 'canvas' });
      if (props.name) (window.bienenDiagramme ||= {})[props.name] = chart;
      zeichnen();
      window.addEventListener('resize', groesse);
    });
    watch(() => props.optionen, zeichnen);
    watch(() => props.hoehe, () => nextTick(groesse));   // gestapelte Felder ändern die Höhe
    onBeforeUnmount(() => {
      window.removeEventListener('resize', groesse);
      if (props.name && window.bienenDiagramme) delete window.bienenDiagramme[props.name];
      chart && chart.dispose();
    });
    return () => h('div', { ref: el, class: 'diagramm', style: { height: props.hoehe } });
  },
});

export const ZEITRAEUME = [['2 Tage', 2], ['7 Tage', 7], ['14 Tage', 14], ['30 Tage', 30], ['90 Tage', 90], ['1 Jahr', 365]];

// Zeitraum als [von, bis] (ISO); bis = Ende des gewählten Tages bzw. jetzt
export const Zeitraum = defineComponent({
  props: { tage: Number, bis: String },
  emits: ['wahl'],
  template: `
    <div class="zeitraum" role="group" aria-label="Zeitraum">
      <button v-for="[text, t] in liste" :key="t" :class="{ aktiv: t === tage }" @click="$emit('wahl', { tage: t, bis })">{{ text }}</button>
      <label>bis <input type="date" :value="bis ? bis.slice(0, 10) : ''" @change="$emit('wahl', { tage, bis: $event.target.value ? $event.target.value + 'T23:59:59Z' : '' })"></label>
    </div>`,
  setup() { return { liste: ZEITRAEUME }; },
});

export const Zustand = defineComponent({
  props: { laden: Boolean, fehler: String },
  template: `<p v-if="laden" class="hinweis">Lädt …</p><p v-else-if="fehler" class="fehler" role="alert">{{ fehler }}</p>`,
});

export function zeitraumParameter(route) {
  const tage = Number(route.query.tage || 14);
  const bisT = route.query.bis ? new Date(route.query.bis) : new Date();
  return { tage, bis: route.query.bis || '', von: new Date(bisT.getTime() - tage * 86400000).toISOString(), bisIso: bisT.toISOString() };
}

# Fremdbibliotheken der Oberfläche

Unverändert übernommen, damit die Oberfläche ohne Build-Schritt und ohne Internetzugriff läuft. Neue Fassungen nur zusammen mit einem Lauf von `tests/plattform/oberflaeche_testen.sh` einspielen.

| Datei | Bibliothek | Fassung | Quelle (geladen 20.10.2026) | Lizenz | SHA-256 |
|---|---|---|---|---|---|
| `vue.esm-browser.prod.js` | Vue.js (© 2018–present Yuxi (Evan) You and Vue contributors) | 3.5.42 | `https://cdn.jsdelivr.net/npm/vue@3.5.42/dist/vue.esm-browser.prod.js` | MIT, `LICENSE-vue` | `f175f7993cae4ad615bef4d32baa37da3bc2d6d6642dd357d35c935e91583830` |
| `echarts.min.js` | Apache ECharts (The Apache Software Foundation) | 6.1.0 | `https://cdn.jsdelivr.net/npm/echarts@6.1.0/dist/echarts.min.js` | Apache-2.0, `LICENSE-echarts`, `NOTICE-echarts` | `b66b25aeb4df84e33199dc21694014d336d222cbd9deb0e5a7c14bd6aa0d0fd0` |

Beide Prüfsummen stimmen mit den von jsDelivr veröffentlichten Werten des npm-Pakets überein (geprüft am 20.10.2026).

Prüfen: `sha256sum server/plattform/web/vendor/*.js`

/* SPDX-License-Identifier: GPL-3.0-or-later
 * Navigation zu den UNVERÄNDERTEN BEEP-Vue-Routen.
 * Quelle der Routen: beepnl/beep-vue-app/src/router/routes.js
 * Keine Zugangsdaten, kein API-Client, keine impliziten Schreibvorgänge.
 */
'use strict';
function beepOriginalRoute(hiveId, view = 'inspections', base = 'https://app.beep.nl') {
  if (!/^[1-9][0-9]*$/.test(String(hiveId ?? ''))) return null;
  let root;
  try { root = new URL(base); } catch { return null; }
  if (root.protocol !== 'https:' || root.username || root.password || root.search || root.hash || root.pathname !== '/') return null;
  const id = String(hiveId);
  const routes = {
    inspections: `/hives/${id}/inspections/`,
    hiveEdit: `/hives/${id}/edit`,
    newInspection: `/inspect?hiveId=${id}`,
  };
  if (!Object.prototype.hasOwnProperty.call(routes, view)) return null;
  return root.origin + routes[view];
}
if (typeof module !== 'undefined' && module.exports) module.exports = { beepOriginalRoute };

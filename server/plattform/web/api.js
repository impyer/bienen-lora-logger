// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Zugriff auf die Lese-API. Relative Pfade, damit die Oberfläche auch hinter einem Präfix (z. B. /bienen/) läuft.

export class NichtAngemeldet extends Error {}

// FastAPI meldet Prüffehler als Liste [{loc, msg}]; als eine lesbare Zeile ausgeben
function fehlerText(detail) {
  if (Array.isArray(detail)) return detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ');
  return detail;
}

export async function holen(pfad, parameter = {}) {
  const q = new URLSearchParams(Object.entries(parameter).filter(([, v]) => v !== undefined && v !== null && v !== ''));
  const antwort = await fetch('api/' + pfad + (q.toString() ? '?' + q : ''), { credentials: 'same-origin' });
  if (antwort.status === 401) throw new NichtAngemeldet();
  const daten = await antwort.json().catch(() => ({}));
  if (!antwort.ok) throw new Error(fehlerText(daten.detail) || `Fehler ${antwort.status}`);
  return daten;
}

// CSRF-Token der Sitzung (von GET api/sitzung); geht bei jeder schreibenden Anfrage im Header mit
let csrf = '';
export function csrfSetzen(t) { csrf = t || ''; }

export async function senden(pfad, daten, methode = 'POST') {
  const antwort = await fetch('api/' + pfad, {
    method: methode, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRF-Token': csrf } : {}) }, body: JSON.stringify(daten),
  });
  const inhalt = await antwort.json().catch(() => ({}));
  if (antwort.status === 401 && pfad !== 'anmelden') throw new NichtAngemeldet();
  if (!antwort.ok) throw new Error(fehlerText(inhalt.detail) || `Fehler ${antwort.status}`);
  return inhalt;
}

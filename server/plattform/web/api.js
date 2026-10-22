// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Zugriff auf die Lese-API. Relative Pfade, damit die Oberfläche auch hinter einem Präfix (z. B. /bienen/) läuft.

export class NichtAngemeldet extends Error {}

// FastAPI meldet Prüffehler als Liste [{loc, msg}]; als eine lesbare Zeile ausgeben
function fehlerText(detail) {
  if (Array.isArray(detail)) return detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ');
  return detail;
}

// Stand der Schnittstelle, den diese Oberfläche erwartet (api/app.py API_STAND); siehe standPruefen()
export const API_STAND = 4;

// Sitzung abgelaufen: Die Oberfläche fragt das Passwort über der Seite ab (anmeldungAnfordernSetzen) und wiederholt
// die Anfrage einmal; Eingaben auf der Seite bleiben so erhalten (PLT26-15)
let anmeldungAnfordern = null;
export function anmeldungAnfordernSetzen(f) { anmeldungAnfordern = f; }

// Netzfehler (Server aus, WLAN weg) als deutsche Meldung statt „Failed to fetch“
async function versuchen(machen) {
  try { return await machen(); } catch (e) {
    if (e instanceof TypeError) throw new Error('Server nicht erreichbar – Verbindung prüfen und erneut versuchen. Eingaben bleiben auf der Seite.');
    throw e;
  }
}

async function anfragen(pfad, machen) {
  let antwort = await versuchen(machen);
  if (antwort.status === 401 && !['anmelden', 'sitzung', 'abmelden'].includes(pfad) && anmeldungAnfordern) {
    await anmeldungAnfordern();               // wirft NichtAngemeldet, wenn abgebrochen
    antwort = await versuchen(machen);
  }
  if (antwort.status === 401 && pfad !== 'anmelden') throw new NichtAngemeldet();
  const daten = await antwort.json().catch(() => ({}));
  if (!antwort.ok) {
    if (antwort.status === 404 && daten.detail === 'unbekannter Endpunkt') {
      throw new Error('Der Server kennt diese Funktion nicht – er läuft vermutlich noch mit älterem Code. Server neu starten, dann die Seite neu laden.');
    }
    throw new Error(fehlerText(daten.detail) || `Fehler ${antwort.status}`);
  }
  return daten;
}

export async function holen(pfad, parameter = {}) {
  const q = new URLSearchParams(Object.entries(parameter).filter(([, v]) => v !== undefined && v !== null && v !== ''));
  return anfragen(pfad, () => fetch('api/' + pfad + (q.toString() ? '?' + q : ''), { credentials: 'same-origin' }));
}

// Passt der Server zur Oberfläche? Liefert null oder einen Hinweistext (z. B. Server nach Update nicht neu gestartet)
export async function standPruefen() {
  try {
    const g = await fetch('api/gesundheit', { credentials: 'same-origin' }).then((a) => a.json());
    if (g.api_stand === API_STAND) return null;
    return `Oberfläche und Server passen nicht zusammen (Oberfläche Stand ${API_STAND}, Server Stand ${g.api_stand ?? 'alt'}). `
      + (g.api_stand === undefined || g.api_stand < API_STAND ? 'Bitte den Server neu starten.' : 'Bitte die Seite neu laden (Strg+F5).');
  } catch { return null; }                    // Server nicht erreichbar: zeigen die Seiten selbst an
}

// CSRF-Token der Sitzung (von GET api/sitzung); geht bei jeder schreibenden Anfrage im Header mit
let csrf = '';
export function csrfSetzen(t) { csrf = t || ''; }

export async function senden(pfad, daten, methode = 'POST') {
  // Header bei jedem Versuch neu: nach erneuter Anmeldung gilt ein neues CSRF-Token
  return anfragen(pfad, () => fetch('api/' + pfad, {
    method: methode, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRF-Token': csrf } : {}) }, body: JSON.stringify(daten),
  }));
}

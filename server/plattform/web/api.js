// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 Philipp Schnabel
// Zugriff auf die Lese-API. Relative Pfade, damit die Oberfläche auch hinter einem Präfix (z. B. /bienen/) läuft.

export class NichtAngemeldet extends Error {}

export async function holen(pfad, parameter = {}) {
  const q = new URLSearchParams(Object.entries(parameter).filter(([, v]) => v !== undefined && v !== null && v !== ''));
  const antwort = await fetch('api/' + pfad + (q.toString() ? '?' + q : ''), { credentials: 'same-origin' });
  if (antwort.status === 401) throw new NichtAngemeldet();
  const daten = await antwort.json().catch(() => ({}));
  if (!antwort.ok) throw new Error(daten.detail || `Fehler ${antwort.status}`);
  return daten;
}

export async function senden(pfad, daten) {
  const antwort = await fetch('api/' + pfad, {
    method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(daten),
  });
  const inhalt = await antwort.json().catch(() => ({}));
  if (!antwort.ok) throw new Error(inhalt.detail || `Fehler ${antwort.status}`);
  return inhalt;
}

// SPDX-License-Identifier: GPL-3.0-or-later
// Oberfläche der Plattform im echten Browser (Chromium über Playwright) gegen die laufende Lese-API.
// Aufruf: node tests/plattform/test_oberflaeche.mjs <basis-url> <passwort> leer|verwaltung|voll [volk-id] [stand-id]
//   leer: Datenbank ohne Stammdaten → Leerzustände, keine Fehler
//   verwaltung: leerer Start, alles über die Oberfläche anlegen (Katalog, Stand, Volk, Gerät, Zuordnung, Vorlage)
//   voll: synthetischer Oktober 2026 (server/plattform/synthetisch.py) → Kacheln, Diagramme, Bänder, Lücken
// Braucht: npm install --no-save playwright@1.56.1 && npx playwright install chromium
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const [basis, passwort, art, volk = '2', stand = '1'] = process.argv.slice(2);

let anz = 0, fehler = 0;
function pruefe(name, ok, info = '') {
  anz++;
  if (ok) { console.log('bestanden  ' + name); return; }
  fehler++;
  console.log(`FEHLER     ${name} ${info}`);
  if (process.env.GITHUB_ACTIONS) console.log(`::error title=test_oberflaeche::${name} ${String(info).slice(0, 400)}`);
}

const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
const seite = await browser.newPage({ timezoneId: 'America/New_York', viewport: { width: 1200, height: 900 } });
const jsFehler = [];
seite.on('pageerror', (e) => jsFehler.push(String(e)));
// API-Fehlerantworten (401, 404 …) zeigt die Oberfläche selbst an; der Browser meldet sie zusätzlich als „Failed to load
// resource“. Als Fehler zählen Skriptfehler, andere Konsolenfehler und fehlgeschlagene Dateien außerhalb von /api/.
seite.on('console', (m) => { if (m.type() === 'error' && !m.text().startsWith('Failed to load resource')) jsFehler.push(m.text()); });
seite.on('response', (r) => { if (r.status() >= 400 && !new URL(r.url()).pathname.startsWith('/api/')) jsFehler.push(`${r.status()} ${r.url()}`); });

let schritt = 'Start';
async function oeffnen(hash) {
  await seite.goto(basis + '/' + hash, { waitUntil: 'load' });
  await seite.waitForFunction(() => !document.querySelector('main')?.innerText.includes('Lädt'), null, { timeout: 15000 });
}

try {
  await seite.goto(basis + '/', { waitUntil: 'load' });
  await seite.fill('input[type=password]', 'falsch-falsch');
  await seite.click('button[type=submit]');
  await seite.waitForSelector('.fehler', { timeout: 5000 });
  pruefe('falsches Passwort wird abgelehnt', (await seite.textContent('.fehler')).includes('Passwort falsch'));
  await seite.fill('input[type=password]', passwort);
  await seite.click('button[type=submit]');
  await seite.waitForSelector('h1:has-text("Übersicht")', { timeout: 10000 });
  pruefe('Anmeldung führt zur Übersicht', true);

  if (art === 'leer') {
    await oeffnen('#/');
    pruefe('Leerzustand Übersicht', (await seite.innerText('main')).includes('Noch keine Stände angelegt'));
    await oeffnen('#/datenquellen');
    pruefe('Leerzustand Datenquellen', (await seite.innerText('main')).includes('Der Importer ist noch nicht gelaufen'));
    await oeffnen('#/volk/1');
    pruefe('unbekanntes Volk zeigt Fehlermeldung statt leerer Seite', (await seite.innerText('main')).includes('Volk unbekannt'));
  } else if (art === 'verwaltung') {
    const meldung = async () => { await seite.waitForSelector('.ok[role=status], .fehler', { timeout: 10000 }); return seite.innerText('main'); };
    schritt = 'Verwaltung öffnen';
    await oeffnen('#/verwaltung');
    schritt = 'Standardkatalog';
    await seite.click('button:has-text("Standardkatalog übernehmen")');
    pruefe('Verwaltung: Standardkatalog', (await meldung()).includes('12 Messgrößen neu'), (await seite.innerText('main')).slice(0, 300));
    schritt = 'Stand anlegen';
    await seite.fill('input[aria-label="Name des Stands"]', 'Teststand');
    await seite.click('button:has-text("Stand anlegen")');
    await seite.waitForSelector('td:has-text("Teststand")', { timeout: 10000 });
    pruefe('Verwaltung: Stand angelegt', true);
    schritt = 'Volk anlegen';
    const volk = seite.locator('form.block');
    await volk.locator('input[aria-label="Name des Volks"]').fill('Testvolk');
    await volk.locator('select[aria-label="Stand"]').selectOption({ label: 'Teststand' });
    await volk.locator('input[aria-label="Bezeichnung der Beute"]').fill('Testbeute');
    await volk.locator('button[type=submit]').click();
    await seite.waitForSelector('a:has-text("Testvolk")', { timeout: 10000 });
    pruefe('Verwaltung: Volk mit Beute angelegt', (await seite.innerText('main')).includes('Testbeute'));
    schritt = 'Gerät anlegen';
    await seite.fill('input[aria-label="TTN-Gerätename"]', 'beelogger-07');
    await seite.click('button:has-text("Gerät anlegen")');
    const geraet = seite.locator('article.geraet', { hasText: 'beelogger-07' });
    await geraet.waitFor({ timeout: 10000 });
    schritt = 'Gerät zuordnen';
    await geraet.locator('details').evaluate((d) => { d.open = true; });
    await geraet.locator('select[aria-label="Ziel"]').selectOption({ label: 'Testvolk' });
    await geraet.locator('button:has-text("Zuordnung speichern")').click();
    await seite.waitForSelector('article.geraet:has-text("an Testvolk")', { timeout: 10000 });
    schritt = 'Vorlage anwenden';
    const g2 = seite.locator('article.geraet', { hasText: 'beelogger-07' });
    await g2.locator('details').evaluate((d) => { d.open = true; });
    await g2.locator('button:has-text("Kanäle anlegen")').click();
    await seite.waitForSelector('.ok:has-text("5 Kanäle angelegt")', { timeout: 10000 }).catch(() => null);
    pruefe('Verwaltung: Zuordnung und Vorlage (5 Kanäle)', (await seite.innerText('main')).includes('5 Kanäle angelegt'),
           (await seite.innerText('main')).slice(0, 300));
    await oeffnen('#/');
    const k = await seite.$$eval('.kachel strong', (e) => e.map((x) => x.textContent));
    pruefe('Verwaltung: Volk erscheint in der Übersicht', JSON.stringify(k) === '["Testvolk"]', JSON.stringify(k));

    // Stockkarte am Handy: Checkliste übernehmen, Durchsicht mit Werten, Maßnahme; danach im Cockpit sichtbar
    schritt = 'Stockkarte am Handy';
    await seite.setViewportSize({ width: 390, height: 844 });
    await oeffnen('#/stockkarte');
    await seite.click('button:has-text("Standard-Checkliste übernehmen")');
    await seite.waitForSelector('.merkmal', { timeout: 10000 });
    await seite.locator('label.volkwahl', { hasText: 'Testvolk' }).locator('input').check();
    await seite.locator('.merkmal', { hasText: 'Königin gesehen' }).locator('button:has-text("ja")').click();
    await seite.fill('input[aria-label="Brutwaben"]', '6');
    await seite.locator('.merkmal', { hasText: 'Sanftmut' }).locator('button:has-text("4")').click();
    await seite.click('button.haupt');
    await seite.waitForSelector('.ok:has-text("Gespeichert (1 Eintrag)")', { timeout: 10000 });
    pruefe('Stockkarte: Durchsicht gespeichert', true);
    const breit = await seite.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    pruefe('Stockkarte: kein waagrechtes Scrollen bei 390 px', breit <= 0, `${breit} px zu breit`);
    schritt = 'Stockkarte Maßnahme';
    await seite.click('.reiter button:has-text("Maßnahme")');
    await seite.locator('label.volkwahl', { hasText: 'Testvolk' }).locator('input').check();
    await seite.selectOption('select[aria-label="Art der Maßnahme"]', 'fuetterung');
    await seite.fill('input[aria-label="Menge"]', '5');
    await seite.fill('input[aria-label="Einheit"]', 'kg');
    await seite.click('button.haupt');
    await seite.waitForSelector('.ok:has-text("Gespeichert (1 Eintrag)")', { timeout: 10000 });
    await seite.setViewportSize({ width: 1200, height: 900 });
    schritt = 'Stockkarte im Cockpit';
    await oeffnen('#/');
    await seite.click('.kachel:has-text("Testvolk")');
    await seite.waitForSelector('.tabelle', { timeout: 10000 });
    const sk = await seite.innerText('.tabelle');
    pruefe('Cockpit: Durchsicht mit Werten und Fütterung', sk.includes('Königin gesehen: ja') && sk.includes('Brutwaben 6 Waben')
           && sk.includes('Sanftmut 4/5') && sk.includes('Fütterung') && sk.includes('5,0 kg'), sk.slice(0, 400));
    schritt = 'Stockkarte bearbeiten';
    await seite.click('.tabelle a:has-text("bearbeiten")');
    await seite.waitForSelector('h1:has-text("Eintrag bearbeiten")', { timeout: 10000 });
    pruefe('Bearbeiten: Werte vorbelegt', await seite.locator('input[aria-label="Brutwaben"]').inputValue() === '6');
  } else {
    await oeffnen('#/?zeit=2026-10-31T23:00:00Z');
    const kacheln = await seite.$$eval('.kachel strong', (e) => e.map((x) => x.textContent));
    pruefe('Übersicht: Völker nach Vereinigung', JSON.stringify(kacheln) === JSON.stringify(['Volk 1 (syn)', 'Volk 2 (syn)', 'Volk 4 (syn)']), JSON.stringify(kacheln));

    await oeffnen(`#/volk/${volk}?bis=2026-10-15T23:59:59Z&tage=14`);
    await seite.waitForFunction(() => window.bienenDiagramme?.verlauf, null, { timeout: 10000 });
    const o = await seite.evaluate(() => {
      const opt = window.bienenDiagramme.verlauf.getOption();
      const g = opt.series.find((s) => s.name.startsWith('Gewicht'));
      return { namen: opt.series.map((s) => s.name), nullen: g.data.filter((p) => p[1] === null).length,
               nullwerte: g.data.filter((p) => p[1] === 0).length, verbinden: g.connectNulls,
               flaechen: (opt.series[0].markArea?.data || []).map((a) => a[0].name),
               bilanz: !!window.bienenDiagramme.bilanz };
    });
    pruefe('Cockpit: Gewicht und Temperaturen vorgewählt', o.namen.length === 3 && o.namen.some((n) => n.startsWith('Gewicht')), JSON.stringify(o.namen));
    pruefe('Cockpit: Lücke als null, nicht verbunden, keine 0', o.nullen >= 1 && o.nullwerte === 0 && o.verbinden === false, JSON.stringify(o));
    pruefe('Cockpit: Behandlung als Band (K-04)', o.flaechen.includes('Behandlung'), JSON.stringify(o.flaechen));
    pruefe('Cockpit: Durchsicht ohne Uhrzeit als Tagesband (K-03)', o.flaechen.some((f) => f.includes('Uhrzeit übernommen')), JSON.stringify(o.flaechen));
    pruefe('Cockpit: Tagesbilanz-Diagramm', o.bilanz);
    const tabelle = await seite.innerText('.tabelle');
    pruefe('Cockpit: Stockkarte mit Varroa pro Tag', tabelle.includes('45 Milben, 15,0 pro Tag'), tabelle.slice(0, 300));
    // Zeitanzeige in Europe/Berlin, obwohl der Browser in New York steht
    pruefe('Cockpit: Zeiten in Europe/Berlin', tabelle.includes('01.10., 10:00'), tabelle.slice(0, 200));

    await oeffnen(`#/stand/${stand}/umwelt?bis=2026-10-31T23:59:59Z&tage=7`);
    await seite.waitForFunction(() => window.bienenDiagramme?.umwelt_wind, null, { timeout: 10000 });
    const w = await seite.evaluate(() => window.bienenDiagramme.umwelt_wind.getOption().series.map((s) => [s.name, s.type, s.symbol]));
    pruefe('Umwelt: Windrichtung als Pfeile', w.some(([n, t, s]) => n.startsWith('Windrichtung') && t === 'scatter' && s === 'arrow'), JSON.stringify(w));
    pruefe('Umwelt: Regenzähler als Balken', await seite.evaluate(() => window.bienenDiagramme.umwelt_regen.getOption().series.some((s) => s.type === 'bar')));

    await oeffnen('#/datenquellen');
    const d = await seite.innerText('main');
    pruefe('Datenquellen: unbenanntes Feld und Gerät ohne Ziel', d.includes('FeuchteIn') && d.includes('beelogger-99'));
  }
  pruefe('keine JavaScript-Fehler', jsFehler.length === 0, JSON.stringify(jsFehler.slice(0, 5)));
} catch (e) {
  const text = await seite.innerText('main').catch(() => '');
  pruefe('Ablauf ohne Abbruch', false, `Schritt „${schritt}“: ${String(e).split('\n')[0]} | Seite: ${text.replace(/\s+/g, ' ').slice(0, 300)} | JS: ${JSON.stringify(jsFehler.slice(0, 3))}`);
  console.log((await seite.innerText('body').catch(() => '')).slice(0, 1500));
} finally {
  await browser.close();
}
console.log(`${anz - fehler} von ${anz} bestanden`);
process.exit(fehler ? 1 : 0);

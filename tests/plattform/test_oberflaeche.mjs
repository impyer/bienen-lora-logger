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
// Sollwerte holt der Test bei der API selbst (gleiche Sitzung), die Anzeige muss sie wiedergeben
const api = (pfad) => seite.evaluate((p) => fetch('api/' + p).then((r) => r.json()), pfad);
const zahlDe = (t) => Number(String(t).replace(/\s/g, '').replace('−', '-').replace('±', '').replace(/\./g, '').replace(',', '.'));
const fmt = (w, n) => w.toLocaleString('de-DE', { minimumFractionDigits: n, maximumFractionDigits: n });
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
    // PLT26-17: Server mit altem Code (kein api_stand, neue Endpunkte 404) → verständlicher Hinweis statt „unbekannter Endpunkt“
    await seite.route('**/api/gesundheit', (r) => r.fulfill({ json: { datenbank: 'ok' } }));
    await seite.route('**/api/vergleich*', (r) => r.fulfill({ status: 404, json: { detail: 'unbekannter Endpunkt' } }));
    await seite.route('**/api/staende*', (r) => r.fulfill({ json: [{ id: 1, name: 'S', voelker: [{ id: 1, name: 'V' }] }] }));
    await seite.reload();
    await oeffnen('#/analysen');
    await seite.waitForSelector('.warnung[role=alert]', { timeout: 10000 });
    const alt = await seite.innerText('main');
    pruefe('Versionsprüfung: alter Server wird gemeldet', alt.includes('passen nicht zusammen') && alt.includes('Server neu starten'), alt.slice(0, 300));
    pruefe('Versionsprüfung: 404 eines neuen Endpunkts verständlich', alt.includes('älterem Code') && !alt.includes('unbekannter Endpunkt'), alt.slice(0, 300));
    await seite.unrouteAll();
    await seite.reload();
    await oeffnen('#/');
    pruefe('Versionsprüfung: passender Server ohne Hinweis', !(await seite.innerText('main')).includes('passen nicht zusammen'));
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
    await seite.waitForSelector('.chronik li', { timeout: 10000 });
    const sk = await seite.innerText('.chronik');
    pruefe('Cockpit: Durchsicht mit Werten und Fütterung', sk.includes('Königin gesehen: ja') && sk.includes('Brutwaben 6 Waben')
           && sk.includes('Sanftmut 4/5') && sk.includes('Fütterung') && sk.includes('5,0 kg'), sk.slice(0, 400));
    schritt = 'Stockkarte bearbeiten';
    await seite.click('.chronik a:has-text("bearbeiten")');
    await seite.waitForSelector('h1:has-text("Eintrag bearbeiten")', { timeout: 10000 });
    pruefe('Bearbeiten: Werte vorbelegt', await seite.locator('input[aria-label="Brutwaben"]').inputValue() === '6');

    // PLT26-15: Sitzung läuft während der Eingabe ab → Anmeldung über der Seite, Eingabe bleibt, Speichern wird wiederholt
    schritt = 'Sitzungsablauf';
    await oeffnen('#/stockkarte?art=massnahme');
    await seite.locator('label.volkwahl', { hasText: 'Testvolk' }).locator('input').check();
    await seite.fill('input[aria-label="Mittel"]', 'Ameisensäure 60 %');
    await seite.context().clearCookies();
    await seite.click('button.haupt');
    await seite.waitForSelector('.ueberlagerung', { timeout: 10000 });
    pruefe('Sitzungsablauf: Anmeldung über der Seite, Eingabe noch da',
           await seite.locator('input[aria-label="Mittel"]').inputValue() === 'Ameisensäure 60 %');
    await seite.fill('.ueberlagerung input[type=password]', passwort);
    await seite.click('.ueberlagerung button[type=submit]');
    await seite.waitForSelector('.ok:has-text("Gespeichert (1 Eintrag)")', { timeout: 10000 });
    pruefe('Sitzungsablauf: nach Anmeldung gespeichert', !(await seite.$('.ueberlagerung')));
  } else {
    await oeffnen('#/?zeit=2026-10-31T23:00:00Z');
    const kacheln = await seite.$$eval('.kachel strong', (e) => e.map((x) => x.textContent));
    pruefe('Übersicht: Völker nach Vereinigung', JSON.stringify(kacheln) === JSON.stringify(['Volk 1 (syn)', 'Volk 2 (syn)', 'Volk 4 (syn)']), JSON.stringify(kacheln));
    pruefe('Übersicht: aktuelle Kacheln nicht veraltet', await seite.locator('.kachel.veraltet').count() === 0);
    await oeffnen('#/?zeit=2026-11-02T12:00:00Z');
    pruefe('Übersicht: zwei Tage ohne Messung → alle veraltet', await seite.locator('.kachel.veraltet').count() === 3);

    await oeffnen(`#/volk/${volk}?bis=2026-10-15T23:59:59Z&tage=14`);
    await seite.waitForFunction(() => window.bienenDiagramme?.verlauf, null, { timeout: 10000 });
    const o = await seite.evaluate(() => {
      const opt = window.bienenDiagramme.verlauf.getOption();
      const g = opt.series.find((s) => s.name.startsWith('Gewicht'));
      return { namen: opt.series.filter((s) => s.type === 'line').map((s) => s.name), nullen: g.data.filter((p) => p[1] === null).length,
               felder: opt.grid.length, milben: (opt.series.find((s) => s.name === 'Milbenfall') || { data: [] }).data.length,
               marken: (opt.series.find((s) => s.name === 'Stockkarte') || { data: [] }).data.map((d) => d.label.formatter),
               achsenGleich: new Set(opt.xAxis.map((x) => String(x.min) + String(x.max))).size === 1,
               nullwerte: g.data.filter((p) => p[1] === 0).length, verbinden: g.connectNulls,
               flaechen: (opt.series[0].markArea?.data || []).map((a) => a[0].name),
               bilanz: !!window.bienenDiagramme.bilanz };
    });
    pruefe('Cockpit: Gewicht und Temperaturen vorgewählt', o.namen.length === 3 && o.namen.some((n) => n.startsWith('Gewicht')), JSON.stringify(o.namen));
    pruefe('Cockpit: Lücke als null, nicht verbunden, keine 0', o.nullen >= 1 && o.nullwerte === 0 && o.verbinden === false, JSON.stringify(o));
    pruefe('Cockpit: Behandlung als Band (K-04)', o.flaechen.includes('Behandlung'), JSON.stringify(o.flaechen));
    pruefe('Cockpit: Durchsicht ohne Uhrzeit als Tagesband (K-03)', o.flaechen.some((f) => f.includes('Uhrzeit übernommen')), JSON.stringify(o.flaechen));
    pruefe('Cockpit: Tagesbilanz-Diagramm', o.bilanz);
    pruefe('Cockpit: gestapelte Felder mit gemeinsamer Zeitachse', o.felder >= 4 && o.achsenGleich, JSON.stringify(o));
    pruefe('Cockpit: Milbenfall als Tagesbalken (Windel 3 Tage)', o.milben === 3, JSON.stringify(o.milben));
    pruefe('Cockpit: Stockkarten-Marken B, D, V', ['B', 'D', 'V'].every((b) => o.marken.includes(b)), JSON.stringify(o.marken));
    // Vorher/Nachher: jüngste Maßnahme ist vorgewählt, Tabelle mit Gewicht und Temperaturen
    await seite.waitForSelector('table.vergleich tbody tr', { timeout: 10000 });
    const vn = await seite.innerText('table.vergleich');
    pruefe('Cockpit: Vorher/Nachher-Tabelle', vn.includes('Gewicht, Tagesbilanz') && vn.includes('Brutnest'), vn.slice(0, 300));
    await seite.click('.segmente button:has-text("± 7 T")');
    await seite.waitForFunction(() => (window.bienenDiagramme.verlauf.getOption().series[0].markArea.data || []).length >= 4, null, { timeout: 10000 });
    pruefe('Cockpit: Vorher/Nachher-Fenster als Bänder', true);
    schritt = 'Kennzahlen des Cockpits';
    const p = `von=2026-10-01T23:59:59Z&bis=2026-10-15T23:59:59Z`;
    const mr = await api(`voelker/${volk}/messreihen?${p}`);
    const tb = await api(`voelker/${volk}/tagesbilanz?${p}`);
    const letzt = (r) => r.punkte.filter((x) => x[1] !== null).at(-1)[1];
    const kacheln2 = await seite.$$eval('.kennzahl', (e) => e.map((x) => x.innerText.replace(/\s+/g, ' ')));
    const gw = letzt(mr.reihen.find((r) => r.messgroesse === 'gewicht'));
    const bt = letzt(mr.reihen.find((r) => r.messgroesse === 'temperatur' && r.zone === 'brutnest'));
    const lb = tb.at(-1).bilanz_kg;
    pruefe('Kennzahl Gewicht = letzter Messwert', kacheln2[0].includes(fmt(gw, 1)), `${kacheln2[0]} / ${gw}`);
    pruefe('Kennzahl Tagesbilanz = letzter Tag', kacheln2[0].includes((lb > 0 ? '+' : '') + fmt(lb, 2)), `${kacheln2[0]} / ${lb}`);
    pruefe('Kennzahl Brutnest = Brutnest, nicht außen', kacheln2[1].includes(fmt(bt, 1)), `${kacheln2[1]} / ${bt}`);
    pruefe('Kennzahl Milbenfall = jüngste Windel', kacheln2[2].includes('15,0') && kacheln2[2].includes('Windel'), kacheln2[2]);
    const zeiten = await seite.$$eval('.chronik li', (e) => e.map((x) => x.querySelector('.klein').innerText.slice(0, 6)));
    const ms = zeiten.map((z) => Date.UTC(2026, Number(z.slice(3, 5)) - 1, Number(z.slice(0, 2))));
    pruefe('Chronik: neueste zuerst', ms.every((m, i) => i === 0 || ms[i - 1] >= m) && ms.length >= 3, JSON.stringify(zeiten));
    const tabelle = await seite.innerText('.chronik');
    pruefe('Cockpit: Stockkarte mit Varroa pro Tag', tabelle.includes('45 Milben, 15,0 pro Tag'), tabelle.slice(0, 300));
    // Zeitanzeige in Europe/Berlin, obwohl der Browser in New York steht
    pruefe('Cockpit: Zeiten in Europe/Berlin', tabelle.includes('01.10., 10:00'), tabelle.slice(0, 200));

    // PLT26-14: Datum „bis“ ist das Ende des Ortstags, auch in der Sommerzeit; Kopfzeile zeigt denselben Tag
    schritt = 'Zeitraum bis';
    await seite.fill('input[aria-label="Zeitraum bis"]', '2026-10-20');
    await seite.waitForFunction(() => location.hash.includes('bis='), null, { timeout: 10000 });
    await seite.waitForFunction(() => !document.querySelector('main')?.innerText.includes('Lädt'), null, { timeout: 15000 });
    const bis = new URLSearchParams(await seite.evaluate(() => location.hash.split('?')[1])).get('bis');
    pruefe('Zeitraum: bis = Mitternacht Ortszeit (MESZ)', bis === '2026-10-20T22:00:00.000Z', bis);
    pruefe('Zeitraum: Datumsfeld und Kopfzeile zeigen den 20.10.', await seite.inputValue('input[aria-label="Zeitraum bis"]') === '2026-10-20'
           && (await seite.innerText('.cockpit .kopfzeile')).includes('–20.10.'), await seite.innerText('.cockpit .kopfzeile'));

    // PLT26-13: Tarieren in Volk 1; der Eingriffstag zählt nicht als „nachher“
    schritt = 'Vorher/Nachher Tarieren';
    await oeffnen(`#/volk/1?bis=2026-10-26T23:00:00.000Z&tage=14`);
    await seite.waitForSelector('table.vergleich tbody tr', { timeout: 10000 });
    const tr = await seite.evaluate(() => [...document.querySelectorAll('table.vergleich tbody tr')].find((z) => z.innerText.includes('Tagesbilanz'))
      ?.innerText.split('	').map((x) => x.trim()));
    const zahl = (t) => Number(String(t).replace('−', '-').replace('±', '').replace(',', '.'));
    pruefe('Vorher/Nachher: Tarieren-Tag nicht als Wirkung', tr && Math.abs(zahl(tr[2])) < 0.2 && Math.abs(zahl(tr[3])) < 0.2, JSON.stringify(tr));
    pruefe('Vorher/Nachher: ausgelassener Eingriffstag genannt', (await seite.innerText('aside')).includes('ohne 1 Tag(e) mit Eingriff'));

    // Analysen & Vergleich: alle Völker des Stands, Nachtmedian, Tagesbilanz, Summen, Hinweise
    schritt = 'Analysen';
    await oeffnen('#/analysen?bis=2026-10-31T23:59:59Z&tage=30');
    await seite.waitForFunction(() => window.bienenDiagramme?.referenz && window.bienenDiagramme?.summen, null, { timeout: 10000 });
    const an = await seite.evaluate(() => ({ referenz: window.bienenDiagramme.referenz.getOption().series.map((s) => s.name),
                                             bilanz: window.bienenDiagramme.bilanzvergleich.getOption().series.length,
                                             zeilen: document.querySelectorAll('.tagestabelle tbody tr').length,
                                             text: document.querySelector('main').innerText }));
    pruefe('Analysen: Völker des Stands im Vergleich', JSON.stringify(an.referenz) === '["Volk 1 (syn)","Volk 2 (syn)"]' && an.bilanz === 2, JSON.stringify(an.referenz));
    pruefe('Analysen: Tagestabelle', an.zeilen >= 28, String(an.zeilen));
    pruefe('Analysen: Sprung ohne Eingriff und Fehlcodes als Hinweis', an.text.includes('Sprung') && an.text.includes('Fehlercode'), an.text.slice(0, 200));
    const vg = await api('vergleich?volk_ids=1,2&von=2026-10-01T23:59:59Z&bis=2026-10-31T23:59:59Z');
    const letzte = vg.voelker.map((v) => [...v.tagesbilanz].reverse().find((b) => !b.mit_eingriff).bilanz_kg);
    const mittel = letzte.reduce((a, b) => a + b, 0) / letzte.length;
    const kz = await seite.$$eval('.kennzahl', (e) => e.map((x) => x.innerText.replace(/\s+/g, ' ')));
    pruefe('Analysen: mittlere letzte Tagesbilanz ohne Eingriff', kz[1].includes(fmt(mittel, 2)), `${kz[1]} / ${mittel}`);
    const summen = await seite.$$eval('.seitenleiste table', (t) => t.find((x) => /ohne eingriff/i.test(x.innerText))
      .innerText.split('\n').slice(1).map((z) => z.split('\t')));
    const v1 = vg.voelker.find((v) => v.name === 'Volk 1 (syn)');
    const z1 = summen.find((z) => z[0].startsWith('Volk 1'));
    pruefe('Analysen: Summen je Volk wie die API', Math.abs(zahlDe(z1[1]) - v1.summe_kg) < 0.006 && Math.abs(zahlDe(z1[2]) - v1.summe_ohne_eingriff_kg) < 0.006,
           `${JSON.stringify(z1)} / ${v1.summe_kg} ${v1.summe_ohne_eingriff_kg}`);
    await seite.click('button:has-text("Volk 2 (syn)")');
    await seite.waitForFunction(() => window.bienenDiagramme?.referenz?.getOption().series.length === 1, null, { timeout: 10000 });
    pruefe('Analysen: Volk abwählen', true);

    schritt = 'Maßnahme-Band bearbeiten';
    const ev = await api(`voelker/${volk}/ereignisse?von=2026-09-01T00:00:00Z&bis=2026-11-01T00:00:00Z`);
    const beh = ev.massnahmen.find((m) => m.art === 'behandlung');
    await oeffnen(`#/stockkarte?art=massnahme&id=${beh.id}`);
    pruefe('Bearbeiten: Ende eines Bands bleibt erhalten', await seite.inputValue('input[aria-label="Ende"]') === '2026-10-11T10:00',
           await seite.inputValue('input[aria-label="Ende"]'));
    // Fehlerpfade: 409 vom Server und Netzfehler erscheinen als deutsche Meldung, die Eingabe bleibt
    await seite.fill('textarea[aria-label="Notiz"]', 'Test 409');
    await seite.route('**/api/stockkarte/massnahmen/*', (r) => r.fulfill({ status: 409, json: { detail: 'Ende vor Beginn' } }));
    await seite.click('button.haupt');
    await seite.waitForSelector('.fehler', { timeout: 10000 });
    pruefe('Fehlerpfad 409: Meldung des Servers, Eingabe bleibt', (await seite.innerText('.fehler')).includes('Ende vor Beginn')
           && await seite.inputValue('textarea[aria-label="Notiz"]') === 'Test 409');
    await seite.unrouteAll();
    await seite.route('**/api/stockkarte/massnahmen/*', (r) => r.abort('connectionrefused'));
    await seite.click('button.haupt');
    await seite.waitForFunction(() => document.querySelector('.fehler')?.innerText.includes('nicht erreichbar'), null, { timeout: 10000 });
    pruefe('Fehlerpfad Netz: „Server nicht erreichbar“ statt „Failed to fetch“', true);
    await seite.unrouteAll();

    schritt = 'Umwelt';
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

// Prüft die beelogger-Grafik im echten Browser (Chromium über Playwright):
// Dygraph hat alle Zeilen gelesen, die Zeitachse steigt streng an, keine JavaScript-Fehler.
// Aufruf: node grafik_pruefen.js <url> [zeitzone-des-browsers]
// Copyright (C) 2026 Philipp Schnabel – GPL-3.0-or-later
"use strict";
const { chromium } = require("playwright");
(async () => {
  const url = process.argv[2], tz = process.argv[3] || "Europe/Berlin";
  const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  const page = await browser.newPage({ timezoneId: tz });
  const fehler = [];
  page.on("pageerror", (e) => fehler.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") fehler.push(m.text()); });
  await page.goto(url, { waitUntil: "load" });
  await page.waitForFunction(() => typeof BL !== "undefined" && BL.numRows && BL.numRows() > 0, null, { timeout: 15000 });
  const r = await page.evaluate(() => {
    const n = BL.numRows(), xs = [];
    for (let i = 0; i < n; i++) xs.push(BL.getValue(i, 0));
    let steigend = true;
    for (let i = 1; i < n; i++) if (!(xs[i] > xs[i - 1])) steigend = false;
    return { zeilen: n, steigend, erste: new Date(xs[0]).toISOString(), letzte: new Date(xs[n - 1]).toISOString(),
      letzte7: xs.slice(-7).map((x) => x / 1000) };
  });
  r.fehler = fehler;
  console.log(JSON.stringify(r));
  await browser.close();
})().catch((e) => { console.log(JSON.stringify({ abbruch: String(e) })); process.exit(1); });

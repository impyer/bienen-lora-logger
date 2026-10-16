// SPDX-License-Identifier: GPL-3.0-or-later
// Chromium-Regression: Quellfassung UND tatsächlich ausgelieferte Einzeldatei.
// Die Designtests vergleichen die fachlich prägenden Elemente der Claude-Vorlage.
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../prototype/claude-ui');
const names=new Set(['/','/index.html','/app.js','/style.css','/stockkarte_native.js','/bienenlogger-claude-prototyp.html']);
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://localhost');
 if(!names.has(url.pathname)){res.writeHead(404);res.end();return;}
 const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
 res.writeHead(200,{'Content-Type':name.endsWith('.css')?'text/css':name.endsWith('.js')?'application/javascript':'text/html','Cache-Control':'no-store'});
 res.end(fs.readFileSync(path.join(root,name)));
});
async function verify(page,base,entry){
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+entry,{waitUntil:'load'});
 await page.locator('.colony').first().waitFor();
 assert.equal(await page.locator('.site-header nav .nav-link').count(),7,'horizontale Claude-Navigation');
 assert.equal(await page.locator('.side').count(),0,'keine Sidebar');
 assert.equal(await page.locator('.stand-metric').count(),8,'acht Claude-Standkennzahlen');
 assert.equal(await page.locator('.alert-card').count(),4,'vier Hinweisfelder');
 assert.equal(await page.locator('.colony').count(),11,'11 Völker aus Claude-Referenz');
 assert.equal(await page.locator('.colony .hive-mini').count(),11,'Beutensymbole');
 assert.match(await page.locator('main').innerText(),/31,419/,'reale Gewichtsprobe');
 assert.match(await page.locator('.colony[data-volk="1"]').innerText(),/Keine Messreihe/,'fehlende Messungen bleiben fehlend');
 await page.locator('[data-action="view-table"]').click();
 assert.equal(await page.locator('main table tbody tr').count(),11,'Listenansicht');
 await page.locator('[data-action="view-cards"]').click();
 await page.locator('[data-action="sort-gewicht"]').click();
 assert.equal(await page.locator('.colony').first().getAttribute('data-volk'),'8','Sortierung');
 await page.locator('[data-action="toggle-audio"]').click();
 assert.equal(await page.locator('.colony-audio').count(),0,'Akustik ausschalten');
 await page.locator('[data-action="toggle-audio"]').click();
 assert.equal(await page.locator('.colony-audio').count(),11,'Akustik einschalten');
 for(const view of ['volk','stockkarte','beute','analyse','umwelt','quellen','stand']){
  await page.locator('.site-nav [data-view="'+view+'"]').click();
  assert.equal(await page.locator('main h1').count(),1,'Ansicht '+view);
 }
 await page.locator('.colony[data-volk="5"]').click();
 assert.match(await page.locator('h1').first().innerText(),/Volk 5/);
 await page.locator('#colonyPicker').selectOption('8');
 assert.match(await page.locator('h1').first().innerText(),/Volk 8/);
 await page.locator('[data-action="new-inspection"]').first().click();
 await page.locator('#inspectionForm textarea[name="summary"]').fill('CI: Durchsicht am Volk');
 await page.locator('#inspectionForm button[type="submit"]').click();
 await page.locator('.site-nav [data-view="stockkarte"]').click();
 assert.match(await page.locator('main').innerText(),/CI: Durchsicht am Volk/);
 await page.locator('.site-nav [data-view="beute"]').click();
 await page.locator('#hiveForm input[name="honey"]').fill('1');
 await page.locator('#hiveForm button[type="submit"]').click();
 assert.match(await page.locator('main').innerText(),/lokaler Änderungsentwurf/);
 await page.locator('.site-nav [data-view="quellen"]').click();
 await page.locator('#channelForm input[name="key"]').fill('co2_ppm');
 await page.locator('#channelForm input[name="name"]').fill('CO2');
 await page.locator('#channelForm input[name="unit"]').fill('ppm');
 await page.locator('#channelForm button[type="submit"]').click();
 assert.equal(await page.locator('td code').filter({hasText:'co2_ppm'}).count(),1);
 await page.locator('#dataToggle').click();
 assert.match(await page.locator('#modeMark').innerText(),/SIMULATION/);
 await page.locator('#dataToggle').click();
 assert.doesNotMatch(await page.locator('#modeMark').innerText(),/SIMULATION/);
 for(const width of [320,360,390,768,1024,1440]){
  await page.setViewportSize({width,height:900});
  await page.locator('.site-nav [data-view="stand"]').click();
  const contentWidth=await page.evaluate(()=>document.documentElement.scrollWidth);
  assert.ok(contentWidth<=width+2,'horizontaler Überlauf bei '+width+': '+contentWidth);
 }
 assert.deepEqual(errors,[],'JavaScript-Fehler');
 console.log('PASS: '+entry+' · horizontales Claude-Design, 7 Ansichten, 11 Völker, Bearbeitung, Mobile');
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const base='http://127.0.0.1:'+server.address().port;
  for(const entry of ['/index.html','/bienenlogger-claude-prototyp.html']){
   const context=await browser.newContext();
   const page=await context.newPage();
   await verify(page,base,entry);
   await context.close();
  }
  const context=await browser.newContext({javaScriptEnabled:false});
  const page=await context.newPage();
  await page.goto(base+'/bienenlogger-claude-prototyp.html');
  assert.match(await page.locator('h1').innerText(),/Interaktive Ansicht benötigt JavaScript/);
  await context.close();
  console.log('PASS: HTML-Einzeldatei ohne JavaScript erklärt Einschränkung');
 }finally{await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
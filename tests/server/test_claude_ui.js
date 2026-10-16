// SPDX-License-Identifier: GPL-3.0-or-later
// Browser-Smoke-Test für die Claude-basierte Bienenlogger-Vorschau.
// Voraussetzung: npm install --no-save playwright und npx playwright install chromium.
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../prototype/claude-ui');
const names=new Set(['/','/index.html','/app.js','/style.css','/bienenlogger-claude-prototyp.html']);
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://localhost');
 if(!names.has(url.pathname)){res.writeHead(404);res.end();return;}
 const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
 const mime=name.endsWith('.css')?'text/css':name.endsWith('.js')?'text/javascript':'text/html';
 res.writeHead(200,{'Content-Type':mime+'; charset=utf-8','Cache-Control':'no-store'});
 res.end(fs.readFileSync(path.join(root,name)));
});
async function main(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
  for (const filename of ['/', '/bienenlogger-claude-prototyp.html']) {
  const page=await browser.newPage({viewport:{width:1365,height:900}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:'+server.address().port+filename);
  assert.match(await page.locator('h1').innerText(),/Teststand/);
  assert.equal(await page.locator('.colony').count(),2);
  assert.match(await page.locator('main').innerText(),/31,419 kg/);
  await page.locator('[data-view="stockkarte"]').click();
  await page.locator('#checklistForm input[name="item"]').fill('Königinnenzellen geprüft');
  await page.locator('#checklistForm button').click();
  assert.equal(await page.getByText('Königinnenzellen geprüft').count(),1);
  await page.locator('[data-action="new-inspection"]').click();
  await page.locator('#inspectionForm textarea[name="summary"]').fill('CI Testeintrag');
  await page.locator('#inspectionForm button[type="submit"]').click();
  assert.equal(await page.getByText('CI Testeintrag').count(),1);
  await page.locator('[data-view="beute"]').click();
  await page.locator('#hiveForm input[name="honey"]').fill('1');
  await page.locator('#hiveForm button[type="submit"]').click();
  assert.match(await page.locator('main').innerText(),/lokaler Änderungsentwurf/);
  await page.locator('[data-view="analyse"]').click();
  assert.match(await page.locator('main').innerText(),/Keine Messreihe|Keine Tagesbilanz|Nacht-Referenzwerte/);
  await page.locator('#dataToggle').click();
  assert.match(await page.locator('#modeMark').innerText(),/SIMULATION/);
  assert.equal(await page.locator('.kpi-number').last().innerText(),'161');
  await page.setViewportSize({width:390,height:844});
  await page.locator('#menuBtn').click();
  assert.equal(await page.locator('.side').evaluate(el=>el.classList.contains('open')),true);
  assert.deepEqual(errors,[]);
  console.log('Claude UI: Browser-Smoke-Test bestanden: '+filename);
  await page.close();
  }
  const noJs=await browser.newContext({javaScriptEnabled:false});
  const blocked=await noJs.newPage();
  await blocked.goto('http://127.0.0.1:'+server.address().port+'/bienenlogger-claude-prototyp.html');
  assert.match(await blocked.locator('h1').innerText(),/Interaktive Ansicht benötigt JavaScript/);
  await noJs.close();
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
}
main().catch(e=>{console.error(e);process.exitCode=1;server.close();});

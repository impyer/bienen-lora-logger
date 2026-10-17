// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const http=require('node:http'),path=require('node:path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../prototype/claude-ui');
const allowed=new Set(['index.html','app.js','style.css','stockkarte_native.js','stockkarte_live.js','stockkarte_edit.js','umwelt.js','bienenlogger-claude-prototyp.html']);
const server=http.createServer((req,res)=>{
 const name=(req.url||'/').split('?')[0].slice(1)||'index.html';
 if(!allowed.has(name)){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'Content-Type':name.endsWith('.css')?'text/css':name.endsWith('.js')?'text/javascript':'text/html'});
 res.end(fs.readFileSync(path.join(root,name)));
});
async function main(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  for(const filename of ['index.html','bienenlogger-claude-prototyp.html']){
   const page=await browser.newPage({viewport:{width:1024,height:768},acceptDownloads:true});
   const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error('PAGE ERROR:',e.stack||e.message);});page.on('console',m=>{if(m.type()==='error')console.error('BROWSER CONSOLE:',m.text());});
   await page.goto('http://127.0.0.1:'+server.address().port+'/'+filename);
   await page.locator('[data-view="stockkarte"]').first().click();
   await page.locator('[data-action="manage-catalog"]').click();
   await page.locator('#nativeGroupForm [name="label"]').fill('Lokale Prüfgruppe');
   await page.locator('#nativeGroupForm button[type="submit"]').click();
   await page.locator('#nativeFieldForm [name="parentId"]').selectOption({label:'Lokale Prüfgruppe'});
   await page.locator('#nativeFieldForm [name="label"]').fill('Prüfbehandlung');
   await page.locator('#nativeFieldForm [name="input"]').selectOption('select');
   await page.locator('#nativeFieldForm button[type="submit"]').click();
   await page.locator('#nativeOptionForm [name="parentId"]').selectOption({label:'Lokale Prüfgruppe > Prüfbehandlung'});
   await page.locator('#nativeOptionForm [name="label"]').fill('Oxalsäure');
   await page.locator('#nativeOptionForm button[type="submit"]').click();
   await page.locator('#nativeRenameForm [name="entryId"]').selectOption({label:'Lokale Prüfgruppe > Prüfbehandlung > Oxalsäure'});
   await page.locator('#nativeRenameForm [name="label"]').fill('Oxalsäurelösung');
   await page.locator('#nativeRenameForm button[type="submit"]').click();
   const state=await page.evaluate(()=>({href:location.href,modal:document.getElementById('modalRoot')?.innerText?.slice(0,300),forms:Array.from(document.forms).map(f=>f.id),exportButton:!!document.querySelector('[data-action="export-native-catalog"]'),toast:document.getElementById('statusToast')?.textContent}));
   
   assert.ok(state.exportButton,'Katalogfenster nach Optionsumbenennung verloren: '+JSON.stringify(state));
   await page.evaluate(()=>{
    window.__exportTrace=[];
    const original=URL.createObjectURL.bind(URL);
    URL.createObjectURL=(blob)=>{window.__exportTrace.push({size:blob.size,type:blob.type});return original(blob)};
   });
   const dl=page.waitForEvent('download',{timeout:4000}).catch(()=>null);
   await page.locator('[data-action="export-native-catalog"]').click();
   const download=await dl;
   if(!download){
    const trace=await page.evaluate(()=>({urls:window.__exportTrace,actions:document.querySelectorAll('[data-action="export-native-catalog"]').length}));
    throw Error('Katalogexport: kein Download. Browserfehler='+JSON.stringify(errors)+' Trace='+JSON.stringify(trace));
   }
   assert.match(download.suggestedFilename(),/bienenlogger-stockkarte-katalog\.json/);
   const catalog=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
   assert.ok(catalog.categories.some(x=>x.name==='Oxalsäurelösung'&&x.id.startsWith('bl:')));
   assert.ok(catalog.checklists.some(x=>x.category_ids.some(id=>id.startsWith('bl:'))));
   await page.locator('#modalRoot [data-action="close-modal"]').first().click();
   await page.locator('[data-action="new-inspection"]').first().click();
   await page.locator('#nativeFields select[data-native-category^="bl:"]').selectOption({label:'Oxalsäurelösung'});
   await page.locator('#inspectionForm textarea[name="summary"]').fill('Lokaler Katalogtest');
   await page.locator('#inspectionForm button[type="submit"]').click();
   assert.match(await page.locator('main').innerText(),/Lokaler Katalogtest/);
   await page.reload();
   await page.locator('[data-view="stockkarte"]').first().click();
   assert.match(await page.locator('main').innerText(),/Lokaler Katalogtest/);
   assert.deepEqual(errors,[]);
   console.log(filename+': Eigene Kategorien, Optionen, Rename, Export, Durchsicht und Reload PASS');
   await page.close();
  }
 }finally{await browser.close();await new Promise(r=>server.close(r));}
}
main().catch(err=>{console.error(err);process.exitCode=1;server.close();});

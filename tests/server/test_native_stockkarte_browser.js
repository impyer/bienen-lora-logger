// SPDX-License-Identifier: GPL-3.0-or-later
// Browser-Smoketest of *own* Bienenlogger UI; contains no private BEEP data.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const { chromium }=require('playwright');
const root=path.resolve(__dirname,'../../prototype/claude-ui'), names=new Set(['index.html','style.css','app.js','stockkarte_native.js','stockkarte_live.js','stockkarte_edit.js','bienenlogger-claude-prototyp.html']);
const server=http.createServer((req,res)=>{const n=decodeURIComponent((req.url||'/').split('?')[0]).slice(1)||'index.html';if(!names.has(n)){res.writeHead(404);res.end();return;}res.writeHead(200,{'Content-Type':n.endsWith('.js')?'text/javascript':n.endsWith('.css')?'text/css':'text/html'});res.end(fs.readFileSync(path.join(root,n)))});
async function test(){await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const browser=await chromium.launch({headless:true,args:['--no-sandbox']});try{
 for(const file of ['index.html','bienenlogger-claude-prototyp.html']){
 const page=await browser.newPage({viewport:{width:390,height:850}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:'+server.address().port+'/'+file);
 await page.locator('[data-view="stockkarte"]').first().click();
 assert.equal(await page.locator('[data-action="manage-templates"]').count(),1);
 await page.locator('[data-action="new-inspection"]').first().click();
 assert.equal(await page.locator('[data-native-category="demo-queen"]').count(),1);
 await page.locator('[data-native-category="demo-queen"]').selectOption('1');
 await page.locator('[data-native-category="demo-varroa"]').selectOption('demo-sugar');
 await page.locator('#inspectionForm textarea[name="summary"]').fill('Native-Engine-Test');
 await page.locator('#inspectionForm button[type="submit"]').click();
 assert.match(await page.locator('main').innerText(),/Native-Engine-Test/);
 assert.deepEqual(errors,[]);
 console.log(file,': PASS');await page.close();
 }
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}}
test().catch(e=>{console.error(e);process.exitCode=1;server.close();});

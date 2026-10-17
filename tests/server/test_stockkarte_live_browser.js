// SPDX-License-Identifier: GPL-3.0-or-later
// Verifiziert UI-Brücke mit simulierten Antworten, NICHT echte Authentifizierung.
// Echte Sessions/ACL werden unabhängig durch PostgreSQL-TestClient geprüft.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../prototype/claude-ui');
const files=new Set(['index.html','app.js','style.css','stockkarte_native.js',
 'stockkarte_live.js','stockkarte_edit.js','bienenlogger-claude-prototyp.html']);
let logins=0,logouts=0,created=0,corrected=0;
let inserted=[];
const json=(res,status,body,extra={})=>{
 res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store',...extra});
 res.end(JSON.stringify(body));
};
const server=http.createServer(async(req,res)=>{
 const url=new URL(req.url,'http://127.0.0.1');
 const file=url.pathname.slice(1)||'index.html';
 if(files.has(file)){
  res.writeHead(200,{'Content-Type':file.endsWith('.js')?'text/javascript':
      file.endsWith('.css')?'text/css':'text/html'});
  res.end(fs.readFileSync(path.join(root,file)));return;
 }
 const api='/api/v1/stockkarte';
 const logged=/bl_dev_session=fixture_session/.test(req.headers.cookie||'');
 if(url.pathname===api+'/session/login'&&req.method==='POST'){
  let raw='';for await(const chunk of req)raw+=chunk;
  const body=JSON.parse(raw);
  if(body.username!=='tester'||body.password!=='local-test-password')return json(res,401,{detail:'fail'});
  logins++;
  return json(res,200,{username:'tester',csrf_token:'example-csrf-value'},
   {'Set-Cookie':'bl_dev_session=fixture_session; Path=/api/v1/stockkarte; HttpOnly; SameSite=Strict'});
 }
 if(!logged)return json(res,401,{detail:'missing session'});
 if(url.pathname===api+'/session'&&req.method==='GET')return json(res,200,{username:'tester',csrf_token:'example-csrf-value'});
 if(url.pathname===api+'/session/logout'&&req.method==='POST'){
  if(req.headers['x-csrf-token']!=='example-csrf-value')return json(res,403,{detail:'csrf'});
  logouts++;return json(res,200,{signed_out:true},
   {'Set-Cookie':'bl_dev_session=; Max-Age=0; Path=/api/v1/stockkarte; HttpOnly'});
 }
 if(url.pathname===api+'/voelker')return json(res,200,[
   {id:123,name:'Fiktives Volk A',can_write:true},
   {id:456,name:'Fiktives Volk B',can_write:false}
 ]);
 if(url.pathname===api+'/katalog')return json(res,200,{
  categories:[
   {id:'bl:seen',name:'Königin gesehen',input:'boolean',required:false,meta:{}},
   {id:'bl:frames',name:'Brutwaben',input:'number_0_decimals',required:true,meta:{min:0,max:20}},
   {id:'bl:method',name:'Varroa-Methode',input:'select',required:false,meta:{}}
  ],
  options:[{id:'bl:oxal',category_id:'bl:method',name:'Oxalsäure',inactive:false}],
  checklists:[{id:1,version:1,name:'Testdurchsicht',fields:[
   {category_id:'bl:seen',position:1,required:false},
   {category_id:'bl:frames',position:2,required:true},
   {category_id:'bl:method',position:3,required:false}
  ]}]
 });
 if(url.pathname===api+'/voelker/123/durchsichten'&&req.method==='POST'){
  assert.equal(req.headers['x-csrf-token'],'example-csrf-value');
  let raw='';for await(const buf of req)raw+=buf;
  const body=JSON.parse(raw);
  assert.equal(body.values['bl:frames'],3);
  created++;
  inserted.push({id:44,event_date:body.event_date,accuracy:body.accuracy,event_time:null,note:body.note,revision:1,
    values:body.values,checklist_id:1,checklist_version:1});
  return json(res,201,{id:44,revision:1,created:true});
 }
 if(url.pathname===api+'/durchsichten/44/revisionen'&&req.method==='POST'){
  assert.equal(req.headers['x-csrf-token'],'example-csrf-value');
  let raw='';for await(const buf of req)raw+=buf;
  const body=JSON.parse(raw);
  assert.equal(body.expected_revision,1);
  assert.equal(body.values['bl:frames'],4);
  corrected++;
  inserted[0]={...inserted[0],revision:2,values:body.values,note:body.note};
  return json(res,201,{id:44,revision:2,created:true});
 }
 if(url.pathname===api+'/voelker/123/durchsichten')return json(res,200,[
  ...inserted,
   {id:33,event_date:'2026-10-16',accuracy:'nur_datum',event_time:null,note:'Brutkontrolle',revision:2,values:{'bl:frames':5}},
   {id:32,event_date:'2026-10-12',accuracy:'nur_datum',event_time:null,note:'Futterprüfung',revision:1,values:{}},
  {id:31,event_date:'2026-10-11',accuracy:'exakt',event_time:'2026-10-11T11:00:00+02:00',
   note:'Uhrzeit-Durchsicht',revision:1,values:{'bl:frames':2}},
  {id:30,event_date:'2026-10-10',accuracy:'nur_datum',event_time:null,
   note:'Ehemalige Auswahl',revision:1,checklist_id:1,checklist_version:1,
   values:{'bl:frames':3,'bl:method':'bl:retired'}}
 ]);
 if(url.pathname===api+'/durchsichten/33/revisionen')return json(res,200,[
   {revision:1,event_date:'2026-10-16',accuracy:'nur_datum',reason:'Erstanlage',author:'tester'},
   {revision:2,event_date:'2026-10-16',accuracy:'nur_datum',reason:'Korrektur',author:'tester'}
 ]);
 if(url.pathname===api+'/voelker/456/durchsichten')return json(res,200,[]);
 json(res,404,{detail:'not found'});
});
async function main(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  for(const filename of ['index.html','bienenlogger-claude-prototyp.html']){
   inserted=[];
   const page=await browser.newPage({viewport:{width:1024,height:800}});
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   const base='http://127.0.0.1:'+server.address().port;
   await page.goto(base+'/'+filename);
   await page.locator('.nav-link[data-view="stockkarte"]').click();
   await page.locator('[data-action="server-preview"]').click();
   await page.locator('#serverLoginForm [name="username"]').fill('tester');
   await page.locator('#serverLoginForm [name="password"]').fill('local-test-password');
   await page.locator('#serverLoginForm button[type="submit"]').click();
   await page.locator('#serverColonySelect').waitFor();
   assert.match(await page.locator('#serverColonySelect').innerText(),/Fiktives Volk A/);
   assert.match(await page.locator('#serverInspections').innerText(),/Brutkontrolle/);
   assert.match(await page.locator('#serverInspections').innerText(),/Futterprüfung/);
   await page.locator('#serverInspections .row-small button').filter({hasText:'Revisionen'}).first().click();
   await page.locator('#serverInspections .live-revisions').first().waitFor();
   assert.match(await page.locator('#serverInspections').innerText(),/Erstanlage/);
   assert.match(await page.locator('#serverInspections').innerText(),/Korrektur/);
   await page.locator('#serverInspections button').filter({hasText:'+ Durchsicht erfassen'}).click();
   await page.locator('#serverEntryForm').waitFor();
   await page.locator('#serverChecklist').selectOption('1:1');
   await page.locator('#serverEntryFields [data-category="bl:frames"]').fill('3');
   await page.locator('#serverEntryFields [data-category="bl:seen"]').selectOption('false');
   await page.locator('#serverEntryForm textarea').last().fill('Testdurchsicht neu');
   await page.locator('#serverEntryForm button[type="submit"]').click();
   await page.locator('#serverInspections').getByText('Testdurchsicht neu').waitFor();
   await page.locator('#serverInspections .row-small').filter({hasText:'Testdurchsicht neu'})
       .getByRole('button',{name:'Korrigieren'}).click();
   await page.locator('#serverEntryForm').waitFor();
   await page.locator('#serverEntryFields [data-category="bl:frames"]').fill('4');
   await page.locator('#serverEntryForm textarea').last().fill('Testdurchsicht korrigiert');
   await page.locator('#serverEntryForm button[type="submit"]').click();
   await page.locator('#serverInspections').getByText('Testdurchsicht korrigiert').waitFor();
   await page.locator('#serverInspections .row-small').filter({hasText:'Uhrzeit-Durchsicht'})
     .getByRole('button',{name:'Korrigieren'}).click();
   await page.waitForFunction(()=>document.querySelector('#liveError')?.textContent.includes('Uhrzeit'));
   assert.equal(await page.locator('#serverEntryForm').count(),0);
   await page.locator('#serverInspections .row-small').filter({hasText:'Ehemalige Auswahl'})
     .getByRole('button',{name:'Korrigieren'}).click();
   await page.locator('#serverEntryForm').waitFor();
   assert.equal(await page.locator('#serverEntryForm button[type="submit"]').isDisabled(),true);
   assert.match(await page.locator('#serverEntryFields').innerText(),/Historische Auswahl/);
   await page.locator('#serverEntryForm button').filter({hasText:'Abbrechen'}).click();
   await page.locator('#serverInspections').getByText('Futterprüfung').waitFor();

   const privacy=await page.evaluate(()=>({
    leaked:JSON.stringify(localStorage).includes('local-test-password') ||
       JSON.stringify(localStorage).includes('example-csrf-value'),
    cookie:document.cookie
   }));
   assert.equal(privacy.leaked,false);
   assert.ok(!privacy.cookie.includes('bl_dev_session'));
   await page.locator('#liveBody button').filter({hasText:'Abmelden'}).click();
   await page.locator('#serverLoginForm').waitFor();
   assert.deepEqual(errors,[]);
   console.log(filename+': Login, Völkerwahl, Durchsichten, Revisionen, Logout PASS');
   await page.close();
  }

  // Schmaler Handy-Bildschirm: Anmeldung und Eingabefeld müssen ohne
  // horizontales Abschneiden benutzbar sein.
  const phone=await browser.newPage({viewport:{width:390,height:844}});
  const base='http://127.0.0.1:'+server.address().port;
  await phone.goto(base+'/index.html');
  await phone.locator('[data-view="stockkarte"]').first().click();
  await phone.locator('[data-action="server-preview"]').click();
  await phone.locator('#serverLoginForm [name="username"]').fill('tester');
  await phone.locator('#serverLoginForm [name="password"]').fill('local-test-password');
  await phone.locator('#serverLoginForm button[type="submit"]').click();
  await phone.locator('#serverInspections button').filter({hasText:'+ Durchsicht erfassen'}).click();
  await phone.locator('#serverEntryForm').waitFor();
  const sizes=await phone.evaluate(()=>{
    const modal=document.querySelector('#modalRoot .modal'),form=document.querySelector('#serverEntryForm');
    return {width:innerWidth,modal:modal?.getBoundingClientRect().width,form:form?.getBoundingClientRect().width};
  });
  assert.ok(sizes.modal<=sizes.width&&sizes.form<=sizes.width,JSON.stringify(sizes));
  await phone.locator('#serverEntryForm button').filter({hasText:'Abbrechen'}).click();
  await phone.locator('#liveBody button').filter({hasText:'Abmelden'}).click();
  await phone.locator('#serverLoginForm').waitFor();
  await phone.close();
  assert.equal(logins,3);assert.equal(logouts,3);
  assert.equal(created,2);assert.equal(corrected,2);
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
}
main().catch(err=>{console.error(err);process.exitCode=1;server.close();});

// SPDX-License-Identifier: GPL-3.0-or-later
// Real HTTPS, FastAPI, PostgreSQL and CSV import. No intercepted API responses.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),cp=require('node:child_process');
const {chromium}=require('playwright');
const config=JSON.parse(process.env.R1_BROWSER_INPUT);
(async()=>{
 const browser=await chromium.launch({...(process.env.PW_CHROMIUM?{executablePath:process.env.PW_CHROMIUM}:{}),args:['--ignore-certificate-errors-spki-list='+config.ca_pins]});
 const context=await browser.newContext({viewport:{width:1440,height:1000},timezoneId:'Europe/Berlin'});
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(config.origin);
  await page.locator('.site-nav [data-view="umwelt"]').click();
  await page.locator('#umLogin input[name="username"]').fill(config.username);
  await page.locator('#umLogin input[name="password"]').fill(config.password);
  await page.locator('#umLogin button[type="submit"]').click();
  await page.locator('.um-chart[aria-label*="Bodentemperatur"]').waitFor();
  assert.match(await page.locator('#umMode').innerText(),/SYNTHETISCHE TESTDATEN/);
  let snapshot=await page.locator('.um-chart[aria-label*="Bodentemperatur"]').evaluate(node=>window.echarts.getInstanceByDom(node).getOption());
  assert.equal(snapshot.series.length,3);
  assert.deepEqual(snapshot.series.map(s=>s.name).sort(),['Bodentemperatur 20 cm','Bodentemperatur 5 cm','Bodentemperatur 50 cm'].sort());
  assert.ok(snapshot.series.find(s=>s.name.includes('20 cm')).data.some(p=>p.value[1]===null));
  assert.equal(snapshot.series[0].connectNulls,false);
  assert.equal(snapshot.yAxis[0].name,'°C');
  const dst=await page.locator('.um-chart[aria-label*="Bodentemperatur"]').evaluate(node=>{
   const f=window.echarts.getInstanceByDom(node).getOption().tooltip[0].formatter;
   return ['2026-10-25T00:30:00Z','2026-10-25T01:30:00Z'].map(time=>f([{seriesName:'synthetic',data:{meta:{time,value:1,source:'fixture',synthetic:true,time_quality:'unbekannt',revision:1,quality:[]}}}]));
  });
  assert.match(dst[0],/\+2/);assert.match(dst[1],/\+1/);
  const weather=await context.request.get(config.origin+'/api/v1/umwelt/messreihen?'+new URLSearchParams({stand_id:config.stand_id,von:config.from,bis:config.to}));
  assert.equal(weather.status(),200);
  const api=await weather.json();
  const temperature=api.series.find(s=>s.channel.field==='t');
  assert.equal(temperature.points.length,2); // duplicate removed, invalid time rejected
  assert.equal(temperature.points[0].value,-2.5);
  assert.equal(temperature.points[1].value,null);
  assert.ok(temperature.points[1].quality.includes('ungueltige_zahl:t'));
  assert.equal(temperature.points[0].time_quality,'empfang');
  const humidity=api.series.find(s=>s.channel.field==='h');
  assert.equal(humidity.points[0].value,null);
  assert.equal(humidity.points[1].value,0);
  assert.equal(api.series.find(s=>s.channel.field==='rain_mm').channel.semantics,'unbekannte_summe');
  const weatherPlot=await page.locator('.um-chart[aria-label*="Lufttemperatur"]').evaluate(node=>window.echarts.getInstanceByDom(node).getOption());
  assert.deepEqual(weatherPlot.series[0].data.map(p=>p.value[1]),[-2.5,null]);
  // The regular 30-second browser poll must display a real newly imported row.
  fs.appendFileSync(config.soil_file,config.new_row);
  // The independently running 5-second CSV watcher performs the actual import.
  const started=Date.now();
  await page.waitForFunction(()=>{
   const element=document.querySelector('.um-chart[aria-label*="Bodentemperatur"]');
   return element&&window.echarts.getInstanceByDom(element)?.getOption().series.some(s=>s.data.some(p=>p.value[1]===29.5));
  },null,{timeout:40000});
  const latency=Date.now()-started;
  const duplicate=cp.execFileSync(process.env.R1_PYTHON,['-m','umwelt.cli','import','--source-id',String(config.soil_source)],{env:{...process.env,PYTHONPATH:config.python_path},encoding:'utf8'});
  assert.equal(JSON.parse(duplicate).neue_revisionen,0);
  // An authorized empty apiary is an actual empty state, never a zero curve.
  await page.locator('#umStand').selectOption(String(config.empty_stand));
  await page.getByText('Keine ausgewählten Messkanäle.',{exact:true}).waitFor();
  assert.equal(await page.locator('.um-chart').count(),0);
  await page.locator('#umStand').selectOption(String(config.stand_id));
  await page.locator('.um-chart[aria-label*="Bodentemperatur"]').waitFor();
  // The same cookie opens the existing real server stockcard without login.
  await page.locator('.site-nav [data-view="stockkarte"]').click();
  await page.locator('[data-action="server-preview"]').click();
  await page.locator('#serverColonySelect').waitFor();
  assert.equal(await page.locator('#serverLoginForm').count(),0);
  const colonyIds=await page.locator('#serverColonySelect option').evaluateAll(nodes=>nodes.map(n=>n.value));
  assert.equal(colonyIds.length,2);
  await page.locator('#serverColonySelect').selectOption(colonyIds[1]);
  await page.locator('#serverInspections h3').waitFor();
  await page.locator('#modalRoot [data-action="close-modal"]').click();
  await page.locator('.site-nav [data-view="umwelt"]').click();
  await page.locator('#umLogout').waitFor();
  assert.equal(await page.locator('#umLogin').count(),0);
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2));
  await page.screenshot({path:config.screenshot,fullPage:true});
  await page.locator('#umLogout').click();
  await page.locator('#umLogin').waitFor();
  assert.equal((await context.request.get(config.origin+'/api/v1/umwelt/staende')).status(),401);
  await page.locator('#umLogin input[name="username"]').fill(config.username);
  await page.locator('#umLogin input[name="password"]').fill(config.password);
  await page.locator('#umLogin button[type="submit"]').click();
  await page.locator('.um-chart[aria-label*="Bodentemperatur"]').waitFor();
  assert.equal((await context.request.get(config.origin+'/api/v1/umwelt/kanaele?stand_id='+config.secret_stand)).status(),404);
  cp.execFileSync(process.env.R1_PYTHON,['-c',"import os,psycopg; c=psycopg.connect(os.environ['BIENEN_TEST_DSN'],autocommit=True); c.execute('UPDATE bienen.sk_benutzer_stand SET darf_lesen=false WHERE benutzer_id=%s AND stand_id=%s',("+config.user_id+','+config.stand_id+')); c.close()'],{env:process.env});
  assert.equal((await context.request.get(config.origin+'/api/v1/umwelt/kanaele?stand_id='+config.stand_id)).status(),404);
  await page.getByRole('button',{name:'24 h',exact:true}).click();
  await page.getByText('Keine Datenanzeige nach fehlgeschlagener Abfrage.',{exact:true}).waitFor();
  assert.equal(await page.locator('.um-chart').count(),0);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({result:'PASS',live_update_ms:latency,browser:browser.version(),checks:['weather-values','three-depths','null-gap','regular-poll','idempotence','apiary-switch','shared-login','colony-switch','mobile','logout-login','live-revocation','https-ca-pin']}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

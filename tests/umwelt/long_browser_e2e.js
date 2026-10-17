/* SPDX-License-Identifier: GPL-3.0-or-later */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
const config=JSON.parse(process.env.R1_BROWSER_INPUT);
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PW_CHROMIUM||undefined,args:['--ignore-certificate-errors-spki-list='+config.ca_pins]});
 try{
  const context=await browser.newContext();
  const page=await context.newPage();
  const replies=[],errors=[];
  page.on('response',response=>{if(response.url().includes('/zeitreihen?')&&response.ok())replies.push(response.json());});
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(config.origin);
  await page.locator('.site-nav [data-view="umwelt"]').click();
  await page.locator('#umLogin input[name="username"]').fill(config.username);
  await page.locator('#umLogin input[name="password"]').fill(config.password);
  await page.locator('#umLogin button[type="submit"]').click();
  await page.locator('.um-chart[aria-label*="Bodentemperatur"]').waitFor();
  async function complete(action){await action();try{await page.waitForFunction(()=>document.querySelector('#umStatus')?.textContent.startsWith('Vollständig geladen'));}catch(error){console.error('Chart status:',await page.locator('#umStatus').textContent());console.error('Page errors:',errors);throw error;}}
  async function newest(range){
   const values=await page.locator('.um-chart[aria-label*="Bodentemperatur"]').evaluate(node=>window.echarts.getInstanceByDom(node).getOption().series.flatMap(s=>s.data.map(p=>p.value[1])));
   assert.ok(values.includes(config.last_value),range+': newest temperature missing from actual ECharts ('+values.length+' displayed soil points)');
   return values;
  }
  for(const range of ['24 h','7 Tage','30 Tage','Saison']){
   await complete(()=>page.getByRole('button',{name:range,exact:true}).click());
   await newest(range);
  }
  await complete(()=>page.getByRole('button',{name:'7 Tage',exact:true}).click());
  await complete(()=>page.locator('#umResolution').selectOption('raw'));
  assert.ok((await newest('raw-7d')).length>3000);
  // Real requests remain abortable during fast changes; no response interception.
  await page.getByRole('button',{name:'7 Tage',exact:true}).click();
  await complete(()=>page.getByRole('button',{name:'30 Tage',exact:true}).click());
  await newest('rapid-30d');
  const from=new Date(Date.parse(config.last_known)-2*86400000).toISOString().slice(0,16);
  await page.locator('.um-range input[name="from"]').fill(from);
  await page.locator('.um-range input[name="to"]').fill(config.to.slice(0,16));
  await complete(()=>page.getByRole('button',{name:'Zeitraum anwenden',exact:true}).click());
  await newest('free');
  await page.locator('#umStand').selectOption(String(config.empty_stand));
  await page.getByText('Keine ausgewählten Messkanäle.',{exact:true}).waitFor();
  assert.equal(await page.locator('.um-chart').count(),0);
  await complete(()=>page.locator('#umStand').selectOption(String(config.stand_id)));
  await newest('apiary-return');
  const started=Date.now();fs.appendFileSync(config.soil_file,config.new_row);
  await page.waitForFunction(()=>{
   const node=document.querySelector('.um-chart[aria-label*="Bodentemperatur"]');
   return node&&window.echarts.getInstanceByDom(node)?.getOption().series.some(s=>s.data.some(p=>p.value[1]===29.5));
  },null,{timeout:70000});
  const liveUpdate=Date.now()-started;
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
  await page.screenshot({path:config.screenshot,fullPage:true});
  const pages=await Promise.all(replies),snapshots=new Map();
  for(const result of pages){
   assert.ok(result.returned_points<=5000);assert.ok(result.total_points<=40000);
   snapshots.set(result.snapshot,(snapshots.get(result.snapshot)||0)+1);
  }
  assert.ok([...snapshots.values()].some(n=>n>1),'real browser must request multiple pages');
  assert.ok(pages.some(p=>p.source_points>5000));
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({result:'PASS',checks:['long-7d','long-30d','season-latest','raw-pages','free-window','rapid-change','apiary-switch','microsecond-order','live-poll','mobile'],live_update_ms:liveUpdate,browser:browser.version()}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});

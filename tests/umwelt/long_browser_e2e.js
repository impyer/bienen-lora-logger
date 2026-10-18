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
  const replies=[],errors=[],windows=[],heapSamples=[];
  page.on('request',r=>{if(r.url().includes('/zeitreihen?'))windows.push(new URL(r.url()).searchParams);});
  page.on('response',response=>{if(response.url().includes('/zeitreihen?')&&response.ok())replies.push(response.json());});
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(config.origin);
  await page.locator('.site-nav [data-view="umwelt"]').click();
  await page.locator('#umLogin input[name="username"]').fill(config.username);
  await page.locator('#umLogin input[name="password"]').fill(config.password);
  await page.locator('#umLogin button[type="submit"]').click();
  await page.locator('.um-chart[aria-label*="Bodentemperatur"]').waitFor();
  if(config.stability)assert.equal(await page.locator('#umFields input:checked').count(),4,'dynamic temperature overview must be the default');
  async function complete(action){await action();try{await page.waitForFunction(()=>document.querySelector('#umStatus')?.textContent.startsWith('Vollständig geladen'));}catch(error){console.error('Chart status:',await page.locator('#umStatus').textContent());console.error('Page errors:',errors);throw error;}}
  async function newest(range){
   const values=await page.locator('.um-chart[aria-label*="Bodentemperatur"]').evaluate(node=>window.echarts.getInstanceByDom(node).getOption().series.flatMap(s=>s.data.map(p=>p.value[1])));
   assert.ok(values.includes(config.last_value),range+': newest temperature missing from actual ECharts ('+values.length+' displayed soil points)');
   return values;
  }
  for(const range of ['24 h','7 Tage','30 Tage','Saison']){
   await complete(()=>page.getByRole('button',{name:range,exact:true}).click());
   await newest(range);
   if(config.stability&&range==='Saison'){
    const year=Number(new Intl.DateTimeFormat('en',{timeZone:'Europe/Berlin',year:'numeric'}).format(new Date()));
    assert.equal(windows.at(-1).get('von'),new Date(Date.UTC(year,0,1)-3600000).toISOString(),'season must start at Berlin midnight');
   }
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
  if(config.stability){
   const devtools=await context.newCDPSession(page);
   await complete(()=>page.getByRole('button',{name:'30 Tage',exact:true}).click());
   await page.locator('.um-chart[aria-label*="Bodentemperatur"]').evaluate(node=>{
    const chart=window.echarts.getInstanceByDom(node);window.stabilityChart=chart;window.stabilityNode=node;
    chart.dispatchAction({type:'dataZoom',start:20,end:80});
    chart.dispatchAction({type:'legendUnSelect',name:'Bodentemperatur 20 cm'});
   });
   for(let cycle=0;cycle<3;cycle++){
    const response=await page.waitForResponse(r=>r.url().includes('/zeitreihen?')&&r.ok(),{timeout:45000});
    await response.finished();await page.waitForFunction(()=>document.querySelector('#umStatus')?.textContent.startsWith('Vollständig geladen'));
    await page.locator('.um-chart[aria-label*="Bodentemperatur"]').evaluate(node=>{
     const c=window.echarts.getInstanceByDom(node),o=c.getOption();
     if(c!==window.stabilityChart||node!==window.stabilityNode)throw Error('Chart recreated during regular poll');
     if(o.dataZoom[0].start!==20||o.dataZoom[0].end!==80)throw Error('Zoom lost during poll');
     if(o.legend[0].selected['Bodentemperatur 20 cm']!==false)throw Error('Legend state lost');
    });
    assert.equal(await page.locator('.um-chart').count(),2,'no leaked chart instances');
    const heap=await devtools.send('Runtime.getHeapUsage');heapSamples.push(heap.usedSize);
    assert.ok(heap.usedSize<256*1024*1024,'35-day browser fixture exceeds 256 MiB JS heap budget');
   }
   await page.locator('.um-range input[name="from"]').fill('2024-01-01T00:00');
   await page.locator('.um-range input[name="to"]').fill('2027-01-01T00:00');
   await page.getByRole('button',{name:'Zeitraum anwenden',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('#umStatus')?.textContent.includes('Zeitraum verkürzen'));
   assert.equal(await page.locator('.um-chart').count(),0,'limit error must not leave apparently successful curves');
   await complete(()=>page.getByRole('button',{name:'7 Tage',exact:true}).click());
   const registry=await (await context.request.get(config.origin+'/api/v1/umwelt/kanaele?stand_id='+config.stand_id)).json();
   const humidity=registry.find(c=>c.field==='h');assert.ok(humidity);
   await complete(()=>page.locator('#umFields input[value="'+humidity.id+'"]').check());
   assert.equal(await page.locator('.um-chart').count(),3,'additional actual registry channel must be selectable');
   await complete(()=>page.locator('#umFields input[value="'+humidity.id+'"]').uncheck());
   assert.equal(await page.locator('.um-chart').count(),2);
  }
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
  console.log(JSON.stringify({result:'PASS',checks:['long-7d','long-30d','season-latest','raw-pages','free-window','rapid-change','apiary-switch','microsecond-order','live-poll','mobile',...(config.stability?['temperature-defaults','berlin-season-start','three-polls-same-instance','zoom-legend-retained','real-limit-error-recovery','dynamic-channel-add']:[])],poll_heap_bytes:heapSamples,live_update_ms:liveUpdate,browser:browser.version()}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});

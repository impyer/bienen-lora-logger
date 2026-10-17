/* SPDX-License-Identifier: GPL-3.0-or-later */
'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const config=JSON.parse(process.env.R1_BROWSER_INPUT);
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PW_CHROMIUM||undefined,args:['--ignore-certificate-errors-spki-list='+config.ca_pins]});
 try{
  const context=await browser.newContext();
  const page=await context.newPage();
  await page.goto(config.origin);
  await page.locator('.site-nav [data-view="umwelt"]').click();
  await page.locator('#umLogin input[name="username"]').fill(config.username);
  await page.locator('#umLogin input[name="password"]').fill(config.password);
  await page.locator('#umLogin button[type="submit"]').click();
  await page.locator('.um-chart[aria-label*="Bodentemperatur"]').waitFor();
  for(const range of ['7 Tage','30 Tage','Saison']){
   const response=page.waitForResponse(r=>/\/(messreihen|zeitreihen)\?/.test(r.url()));
   await page.getByRole('button',{name:range,exact:true}).click();
   await (await response).finished();
   await page.waitForFunction(()=>{
    const element=document.querySelector('.um-chart[aria-label*="Bodentemperatur"]');
    return element&&window.echarts.getInstanceByDom(element);
   });
   const values=await page.locator('.um-chart[aria-label*="Bodentemperatur"]').evaluate(node=>window.echarts.getInstanceByDom(node).getOption().series.flatMap(s=>s.data.map(p=>p.value[1])));
   assert.ok(values.includes(77.125),range+': newest temperature missing from actual ECharts ('+values.length+' displayed soil points)');
  }
  console.log(JSON.stringify({result:'PASS',checks:['long-7d','long-30d','season-latest'],browser:browser.version()}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});

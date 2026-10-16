from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parent.parent
html=(root/'bienenlogger-claude-prototyp.html').read_text()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(accept_downloads=True)
 page.set_default_timeout(6000)
 page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return this._d[k]||null},setItem(k,v){this._d[k]=v}}})")
 errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
 page.set_content(html)
 def nav(s):
   page.locator('.nav-link[data-view="'+s+'"]').click()
 checks=0
 def ok(desc,pred=True):
  global checks
  assert pred,desc
  checks+=1;print('OK',desc)
 nav('volk')
 cs=page.locator('main svg[aria-label^="Gewichtskurve"] circle')
 print('svg count',cs.count())
 if cs.count():
  ok('single marker positioned on axis, not off-time',float(cs.first.get_attribute('cx'))>300)
  ok('single date label only',page.locator('main svg[aria-label^="Gewichtskurve"] text').count()<12)
 nav('quellen')
 bogus={'devices':[{'volk':'Volk 5','rows':[{'zeit_utc':'2026-10-16T00:51:32Z','gewicht_kg':None,'temperatur_c':None,'fft_baender':[{'von_hz':71,'bis_hz':122,'wert':None},{'von_hz':70,'bis_hz':71,'wert':0},{'von_hz':None,'bis_hz':122,'wert':19}]}]}]}
 with page.expect_file_chooser() as fc:page.locator('[data-action="import"]').first.click()
 fc.value.set_files({'name':'null.json','mimeType':'application/json','buffer':json.dumps(bogus).encode()})
 page.wait_for_timeout(120)
 nav('volk');page.locator('#colonyPicker').select_option('5')
 ok('null weight not shown as 0', '0,000 kg' not in page.locator('main').inner_text())
 ok('invalid FFT bands removed', '1 Bänder' in page.locator('main').inner_text())
 nav('stockkarte');page.locator('[data-action="new-inspection"]').click()
 payload='<img src=x onerror="window.__xss=1">'
 page.locator('textarea[name="summary"]').fill(payload)
 page.locator('#inspectionForm button[type="submit"]').click()
 ok('user input not inserted as live HTML',page.evaluate('window.__xss') is None)
 ok('user input visible as escaped text',payload in page.locator('main').inner_text())
 nav('beute');page.locator('#hiveForm input[name="brood"]').fill('0');page.locator('#hiveForm input[name="honey"]').fill('0');page.locator('#hiveForm button[type="submit"]').click()
 ok('zero boxes rejected', 'mindestens eine Zarge' in page.locator('#toast').inner_text())
 nav('quellen')
 with page.expect_download() as dl:page.locator('[data-action="export"]').first.click()
 ok('JSON export produced',dl.value.suggested_filename.endswith('.json'))
 for width in [320,360,390,768,1024,1440]:
  page.set_viewport_size({'width':width,'height':780})
  for s in ['stand','volk','stockkarte','beute','analyse','umwelt','quellen']:
   nav(s)
   # Keine scrollWidth-Regression durch die horizontale mobile Navigation.
   geom=page.evaluate('({a:document.documentElement.scrollWidth,b:window.innerWidth})')
   if geom['a']>geom['b']+3: print('OVERFLOW',width,s,geom)
  ok('all views render at '+str(width),not errors)
 ok('no page exceptions',not errors)
 b.close();print('PASSED',checks)
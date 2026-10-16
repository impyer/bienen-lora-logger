#!/usr/bin/env python3
"""Exercise the ACTUAL distributable HTML in Chromium, no web navigation needed.
Chromium in this environment blocks navigation via enterprise policy; page.set_content
parses and executes the distributable exactly as a document. It does not test file://
or network serving behavior, which must be checked externally. Browser storage is
mocked for persistence testing because about:blank has no localStorage origin.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
root = Path(__file__).resolve().parent.parent
html = (root / 'bienenlogger-claude-prototyp.html').read_text()
with sync_playwright() as playwright:
    b = playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = b.new_page(viewport={'width': 1365, 'height': 900}, accept_downloads=True)
    page.set_default_timeout(6000)
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.evaluate("""Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return this._d[k]||null},setItem(k,v){this._d[k]=v},removeItem(k){delete this._d[k]}}})""")
    checks=[]
    def check(name, fn):
      try:
        out = fn();checks.append(name);print('PASS',name)
      except Exception as e:
        print('FAIL',name,repr(e)); raise
    def visit(name):
      page.locator(f'[data-view="{name}"]').first.click()
      assert page.locator('h1').count()==1 and len(page.locator('main').inner_text())>100
    check('Einzeldatei startet', lambda:(page.set_content(html),page.locator('h1').wait_for(),len(page.locator('.colony').all())==2))
    check('Genau 2 Völker', lambda: (len(page.locator('.colony').all())==2 or (_ for _ in ()).throw(AssertionError())))
    check('Reale Werte Volk 8', lambda: '31,419 kg' in page.locator('main').inner_text() or (_ for _ in ()).throw(AssertionError(page.locator('main').inner_text()[:800])))
    check('Volk 5 keine erfundenen Werte', lambda:'ohne Messung' in page.locator('main').inner_text() or (_ for _ in ()).throw(AssertionError()))
    for name in ['volk','stockkarte','beute','analyse','umwelt','quellen','stand']:
      check('Navigation '+name, lambda name=name:visit(name))
    check('Volk auswählen', lambda:(page.locator('[data-volk="5"]').first.click(), 'Volk 5 · Volk-Cockpit' in page.locator('h1').inner_text() or (_ for _ in ()).throw(AssertionError())))
    check('Volk 8 umschalten', lambda:(page.locator('[data-choose-volk="8"]').first.click(), 'Volk 8' in page.locator('h1').inner_text() or (_ for _ in ()).throw(AssertionError())))
    check('Zoom 24h', lambda:(page.locator('[data-days="1"]').first.click(),page.locator('[data-days="1"].active').count()==1 or (_ for _ in ()).throw(AssertionError())))
    check('Modal öffnen', lambda:(page.locator('[data-action="new-inspection"]').first.click(),page.locator('#inspectionForm').wait_for()))
    check('Modal abbrechen Escape', lambda:(page.keyboard.press('Escape'),page.locator('#inspectionForm').count()==0 or (_ for _ in ()).throw(AssertionError())))
    page.locator('[data-view="stockkarte"]').first.click()
    def checklist():
      page.locator('#checklistForm input[name="item"]').fill('Königinnenzellen geprüft')
      page.locator('#checklistForm button[type="submit"]').click()
      assert page.locator('main').inner_text().count('Königinnenzellen geprüft') >= 1
    check('Eigener Checklistenpunkt', checklist)
    def inspection():
      page.locator('[data-action="new-inspection"]').click()
      page.locator('#inspectionForm textarea[name="summary"]').fill('Testdurchsicht von heute')
      page.locator('#inspectionForm input[type="checkbox"]').first.check()
      page.locator('#inspectionForm button[type="submit"]').click()
      assert 'Testdurchsicht von heute' in page.locator('main').inner_text()
      assert page.evaluate('JSON.parse(localStorage.getItem("bienenlogger-claude-prototype-v1")).inspections.length') == 1
    check('Durchsicht speichern', inspection)
    def hive():
      visit('beute')
      page.locator('#hiveForm input[name="honey"]').fill('1')
      page.locator('#hiveForm textarea[name="note"]').fill('Honigraum aufgesetzt')
      page.locator('#hiveForm button[type="submit"]').click()
      assert 'lokaler Änderungsentwurf' in page.locator('main').inner_text()
      visit('stockkarte')
      assert 'Honigraum aufgesetzt' in page.locator('main').inner_text()
    check('Beutenänderung verknüpft Stockkarte', hive)
    def channel():
      visit('quellen')
      page.locator('#channelForm input[name="key"]').fill('co2_ppm')
      page.locator('#channelForm input[name="name"]').fill('CO₂')
      page.locator('#channelForm input[name="unit"]').fill('ppm')
      page.locator('#channelForm button[type="submit"]').click()
      assert page.locator('td code').filter(has_text='co2_ppm').count()==1
    check('Neuer Messkanal', channel)
    def demo():
      page.locator('#dataToggle').click()
      assert 'SIMULATION' in page.locator('#modeMark').inner_text()
      visit('analyse')
      assert '161' in page.locator('main').inner_text()
      page.locator('#dataToggle').click()
      assert 'SIMULATION' not in page.locator('#modeMark').inner_text()
    check('Mustersimulation umschalten', demo)
    def import_data():
      visit('quellen')
      with page.expect_file_chooser() as fc:page.locator('[data-action="import"]').first.click()
      fc.value.set_files({'name':'sample.json','mimeType':'application/json','buffer':b'{"devices":[{"volk":"Volk 5","rows":[{"zeit_utc":"2026-10-16T00:51:32Z","gewicht_kg":25.5,"temperatur_c":18.0}]}]}'})
      page.wait_for_timeout(100)
      visit('stand')
      assert '25,500 kg' in page.locator('main').inner_text()
    check('JSON Import für Volk 5', import_data)
    def reset_import():
      visit('quellen')
      page.once('dialog',lambda dialog:dialog.accept())
      page.locator('[data-action="clear-import"]').click()
      visit('stand')
      assert '25,500 kg' not in page.locator('main').inner_text()
    check('Import zurücksetzen',reset_import)
    def persistence():
      page.set_content(html)
      visit('stockkarte')
      assert 'Honigraum aufgesetzt' in page.locator('main').inner_text()
    check('Browserdaten nach Neuladen',persistence)
    def mobile():
      page.set_viewport_size({'width': 390, 'height': 844})
      page.locator('#menuBtn').click()
      assert page.locator('.side').evaluate("el=>el.classList.contains('open')")
      page.locator('[data-view="analyse"]').click()
      assert page.locator('h1').count()==1
      assert page.locator('.side').evaluate("el=>!el.classList.contains('open')")
    check('Mobile Navigation',mobile)
    print('ERRS',errors)
    assert not errors, errors
    b.close()
    print('PASSED',len(checks))
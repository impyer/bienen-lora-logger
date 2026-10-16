#!/usr/bin/env python3
"""Functional + design regression on the ACTUAL standalone file using set_content.
Chromium in this environment has URLBlocklist=*, therefore no local navigation is used.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from datetime import datetime
base=Path(__file__).resolve().parents[1]
html=(base/'bienenlogger-claude-prototyp.html').read_text()
checks=[]
def ok(label, value):
    assert value,label
    checks.append(label)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':900},accept_downloads=True)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return this._d[k]||null},setItem(k,v){this._d[k]=v},removeItem(k){delete this._d[k]}}})")
    page.set_content(html)
    ok('Original-Layout: horizontale Navigation',page.locator('.site-header nav .nav-link').count()==7)
    ok('Keine Seitenleiste',page.locator('.side').count()==0)
    ok('Original-Layout: acht Umweltkennzahlen',page.locator('.stand-metric').count()==8)
    ok('Original-Layout: vier Hinweisfelder',page.locator('.alert-card').count()==4)
    ok('Völkerzahl der Claude-Referenz',page.locator('.colony').count()==11)
    ok('Keine erfundenen Gewichte für andere Völker','Keine Messreihe vorhanden' in page.locator('.colony').first.inner_text())
    ok('Volk 8 hat das reale Gewicht','31,419' in page.locator('main').inner_text())
    ok('Claude-Kacheln mit Hive-Symbol',page.locator('.colony .hive-mini').count()==11)
    page.locator('[data-action="view-table"]').click()
    ok('Liste mit elf Völkern',page.locator('main table tbody tr').count()==11)
    page.locator('[data-action="view-cards"]').click()
    ok('Zurück zur Kachelansicht',page.locator('.colony').count()==11)
    page.locator('[data-action="sort-gewicht"]').click()
    ok('Gewichtssortierung',page.locator('.colony').first.get_attribute('data-volk')=='8')
    page.locator('[data-action="sort-nr"]').click()
    page.locator('[data-action="toggle-audio"]').click()
    ok('Akustik ein/aus',page.locator('.colony-audio').count()==0)
    page.locator('[data-action="toggle-audio"]').click()
    ok('Akustik wieder eingeblendet',page.locator('.colony-audio').count()==11)
    page.locator('[data-volk="5"]').click()
    ok('Volk 5 navigierbar','Volk 5' in page.locator('h1').first.inner_text())
    page.locator('#colonyPicker').select_option('8')
    ok('Volk im Cockpit umschaltbar','Volk 8' in page.locator('h1').first.inner_text())
    for v in ['stockkarte','beute','analyse','umwelt','quellen','stand','volk']:
        page.locator(f'[data-view="{v}"]').first.click()
        ok('Navigation '+v,page.locator('main h1').count()==1 and len(page.locator('main').inner_text())>100)
    page.locator('[data-action="new-inspection"]').first.click()
    ok('BEEP-inspirierte Durchsicht',page.locator('#inspectionForm').count()==1)
    page.locator('#inspectionForm textarea[name="summary"]').fill('V03 Testdurchsicht')
    page.locator('#inspectionForm button[type="submit"]').click()
    page.locator('[data-view="stockkarte"]').first.click()
    ok('Durchsicht lokal gespeichert','V03 Testdurchsicht' in page.locator('main').inner_text())
    page.locator('[data-view="beute"]').first.click()
    page.locator('#hiveForm input[name="honey"]').fill('1')
    page.locator('#hiveForm button[type="submit"]').click()
    ok('Beutenänderung als Entwurf','lokaler Änderungsentwurf' in page.locator('main').inner_text())
    page.locator('[data-view="stockkarte"]').first.click()
    ok('Beutenhistorie in Stockkarte','Beutenkonfiguration' in page.locator('main').inner_text())
    page.locator('[data-view="quellen"]').first.click()
    page.locator('#channelForm input[name="key"]').fill('co2_ppm')
    page.locator('#channelForm input[name="name"]').fill('CO2')
    page.locator('#channelForm input[name="unit"]').fill('ppm')
    page.locator('#channelForm button[type="submit"]').click()
    ok('Dynamisches Kanalregister',page.locator('td code').filter(has_text='co2_ppm').count()==1)
    page.locator('#dataToggle').click()
    ok('Musteranalyse explizit gekennzeichnet','SIMULATION' in page.locator('#modeMark').inner_text())
    page.locator('#dataToggle').click()
    ok('Zurück zu belegten Daten','SIMULATION' not in page.locator('#modeMark').inner_text())
    # layout and interactions at actual viewport widths
    for width in [320,360,390,768,1024,1440]:
        page.set_viewport_size({'width':width,'height':900})
        page.locator('[data-view="stand"]').first.click()
        widthScroll=page.evaluate('document.documentElement.scrollWidth')
        ok('Kein horizontaler Überlauf bei '+str(width),widthScroll<=width+2)
        ok('Navigation erreichbar bei '+str(width),page.locator('.site-nav').is_visible())
    ok('Keine JavaScript-Fehler',not errors)
    browser.close()
print('PASS',len(checks),'Prüfungen')
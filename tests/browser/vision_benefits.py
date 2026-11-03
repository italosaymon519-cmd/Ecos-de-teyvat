import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def serve(route):
  path=urlparse(route.request.url).path;f=ROOT/('index.html' if path=='/' else path.lstrip('/'));route.fulfill(content_type='text/javascript' if f.suffix=='.js' else mimetypes.guess_type(str(f))[0] or 'application/octet-stream',body=f.read_bytes())
 page.route('https://vision.test/**',serve);page.goto('https://vision.test/')
 for element in ['Geo','Dendro','Electro','Hydro','Anemo','Pyro','Cryo']:
  page.locator('#new-character').click();page.locator('#character-form [name=name]').fill(element);page.locator('[name=element]').select_option(element);page.get_by_role('button',name='Salvar personagem').click()
 def card(name):return page.locator('.character-card').filter(has=page.locator('h3',has_text=name))
 page.evaluate('Math.random=()=>0.999');card('Geo').locator('[data-vision-action=activate]').click();assert 'Escudo: 6' in card('Geo').inner_text();assert card('Geo').locator('[data-vision-action=activate]').is_disabled()
 card('Geo').locator('[data-action=damage]').click();page.locator('#damage-form [name=amount]').fill('8');page.locator('#damage-form button[type=submit]').click();assert 'Perda de 2 PV' in card('Geo').inner_text()
 page.reload();assert card('Geo').locator('[data-vision-action=activate]').is_disabled()
 card('Dendro').locator('[data-vision-action=activate]').click();card('Dendro').locator('[data-vision-action=resistance]').click();page.evaluate('Math.random=()=>0.45');page.locator('#resistance-form button[type=submit]').click();assert '+ 2 Visão = 14' in page.locator('#resistance-result').inner_text();page.locator('#resistance-close').click();assert '+2 no próximo teste' not in card('Dendro').inner_text()
 page.once('dialog',lambda d:d.accept());card('Electro').locator('[data-vision-action=activate]').click();assert 'DEF 14' in card('Electro').inner_text();card('Electro').locator('[data-action=damage]').click();page.locator('#damage-form button[type=submit]').click();assert 'DEF 12' in card('Electro').inner_text()
 page.once('dialog',lambda d:d.dismiss());card('Hydro').locator('[data-vision-action=activate]').click();assert card('Hydro').locator('[data-vision-action=activate]').is_enabled()
 for name in ['Hydro','Anemo']:
  page.once('dialog',lambda d:d.accept());card(name).locator('[data-vision-action=activate]').click();assert card(name).locator('[data-vision-action=activate]').is_disabled()
 for name in ['Pyro','Cryo']:card(name).locator('[data-vision-action=activate]').click()
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.once('dialog',lambda d:d.accept());page.locator('#new-combat').click();page.locator('nav [data-tab=mesa]').click();assert card('Geo').locator('[data-vision-action=activate]').is_enabled()
 assert not errors,errors;b.close();print('PASS: seven benefits, d6 shield and damage absorption, one-use persistence, Dendro save bonus consumed, Electro Defense expires on miss, new combat reset and mobile layout.')

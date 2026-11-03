"""Regression smoke test for the deployed frontend without a configured backend."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':390,'height':844});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def serve(route):
  path=urlparse(route.request.url).path;f=ROOT/('index.html' if path=='/' else path.lstrip('/'))
  route.fulfill(content_type='text/javascript' if f.suffix=='.js' else 'text/css' if f.suffix=='.css' else 'text/html',body=f.read_text())
 page.route('https://local.test/**',serve);page.goto('https://local.test/')
 page.goto('https://local.test/?room=ABCDEF0123456789ABCDEF0123456789');assert page.locator('#room-code').input_value()=='ABCDEF0123456789ABCDEF0123456789';page.goto('https://local.test/');assert page.locator('#room-code').input_value()=='ABCDEF0123456789ABCDEF0123456789'
 page.locator('[data-tab=sala]').click();assert page.locator('#cloud-unconfigured').is_visible();assert page.locator('#cloud-auth').is_hidden()
 page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Viajante local');page.get_by_role('button',name='Salvar personagem').click()
 page.locator('[data-tab=mesa]').click();assert page.locator('.character-card').count()==1
 page.locator('[data-tab=mestre]').click();assert page.locator('.location-card').count()==10
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.locator('[data-tab=biblioteca]').click();assert page.locator('.guide-page').count()==28
 assert not errors,errors
 b.close();print('PASS: unconfigured backend is explicit; local character, GM scenarios, guides and mobile layout remain functional.')

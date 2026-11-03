import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1100});errors=[];failures=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def serve(route):
  path=urlparse(route.request.url).path;f=ROOT/('index.html' if path=='/' else path.lstrip('/'))
  if not f.is_file():failures.append(path);return route.fulfill(status=404,body='missing')
  route.fulfill(content_type='text/javascript' if f.suffix=='.js' else mimetypes.guess_type(str(f))[0] or 'application/octet-stream',body=f.read_bytes())
 page.route('https://design.test/**',serve);page.goto('https://design.test/',wait_until='networkidle');page.evaluate('document.fonts.ready')
 assert page.locator('.element-guide').count()==7
 assert page.evaluate("Array.from(document.querySelectorAll('#mesa img')).every(i=>i.complete&&i.naturalWidth>0)")
 page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Aventureira');page.locator('[name=portrait]').select_option('jean');page.get_by_role('button',name='Salvar personagem').click();page.wait_for_function("document.querySelector('.avatar img').naturalWidth>0")
 page.screenshot(path='/workspace/teyvat-new-desktop.png',full_page=True)
 page.locator('[data-element-guide=Pyro]').click();assert page.locator('#biblioteca').is_visible();assert page.locator('#guide-search').input_value()=='Pyro'
 page.locator('nav [data-tab=mesa]').click();page.locator('[data-open-section=sala]').click();assert page.locator('#sala').is_visible()
 page.locator('nav [data-tab=mesa]').click();page.set_viewport_size({'width':390,'height':844});page.evaluate('window.scrollTo(0,0)');assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');page.screenshot(path='/workspace/teyvat-new-mobile.png',full_page=True)
 page.set_viewport_size({'width':768,'height':1024});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 assert not errors,errors;assert not failures,failures
 b.close();print('PASS: local images/fonts, seven elements, portrait selection, shortcuts and reference search, desktop and mobile/tablet layout; no JS errors or missing assets.')

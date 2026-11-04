import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def serve(route):
  path=urlparse(route.request.url).path;f=ROOT/('index.html' if path=='/' else path.lstrip('/'));route.fulfill(content_type='text/javascript' if f.suffix=='.js' else mimetypes.guess_type(str(f))[0] or 'application/octet-stream',body=f.read_bytes())
 page.route('https://local-effects.test/**',serve);page.goto('https://local-effects.test/');page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Local');page.get_by_role('button',name='Salvar personagem').click();card=page.locator('.character-card');card.locator('[data-action=effects]').click();f=page.locator('#effects-form');f.locator('[name=name]').fill('Congelado');f.locator('[name=rounds]').fill('1');f.locator('[type=submit]').click();page.locator('#effects-close').click();page.locator('#next-round').click();assert 'Congelado' not in card.locator('.character-effects').inner_text()
 card.locator('[data-action=effects]').click();f.locator('[name=kind]').select_option('defense');f.locator('[name=name]').fill('Permanente');f.locator('[name=amount]').fill('2');f.locator('[name=permanent]').check();f.locator('[type=submit]').click();page.locator('#effects-close').click();page.once('dialog',lambda d:d.accept());page.locator('#new-combat').click();page.locator('[data-tab=mesa]').click();assert 'Permanente' in card.inner_text();assert 'DEF 14' in card.inner_text();page.reload();assert 'Permanente' in card.inner_text();assert not errors,errors;b.close();print('PASS: local round expiry, persistent Defense through new combat and reload, mobile.')

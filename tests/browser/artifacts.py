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
 page.route('https://artifacts.test/**',serve);page.goto('https://artifacts.test/')
 page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Artefatos');page.get_by_role('button',name='Salvar personagem').click()
 card=page.locator('.character-card');card.locator('.artifact-panel summary').click();assert card.locator('.artifact-piece').count()==5
 card.locator('[data-artifact-action=plume]').click()
 def roll():page.evaluate("Math.random=()=>0.45;document.querySelector('#outgoing-form button[type=submit]').click()")
 roll();assert '= 8' in page.locator('#outgoing-result').inner_text();roll();assert '+ 0 artefato = 7' in page.locator('#outgoing-result').inner_text()
 page.locator('#outgoing-close').click();page.evaluate("dispatchEvent(new CustomEvent('ecos-local-turn',{detail:{round:1,activeId:'another'}}))")
 card.locator('[data-artifact-action=plume]').click();page.locator('#outgoing-form [name=critical]').check();roll();assert '= 12' in page.locator('#outgoing-result').inner_text();page.locator('#outgoing-close').click()
 card.locator('[data-artifact-action=sand]').click();assert page.locator('#resistance-form [name=useSand]').is_checked();page.evaluate("Math.random=()=>0.45;document.querySelector('#resistance-form button[type=submit]').click()");assert '+ 1 Areias' in page.locator('#resistance-result').inner_text();page.locator('#resistance-close').click();assert card.locator('[data-artifact-action=sand]').is_disabled()
 card.locator('[data-artifact-action=crown]').click();panel=page.locator('[data-skill-sheet]');assert panel.locator('[data-crown-check]').is_checked()
 panel.locator('[data-skill-roll=Atletismo]').click();assert panel.locator('[data-crown-check]').is_enabled()
 page.evaluate("Math.random=()=>0.45;document.querySelector('[data-skill-roll=Conhecimento]').click()")
 assert '+ 1 Tiara' in panel.locator('.skill-roll-result').inner_text();assert panel.locator('[data-crown-check]').is_disabled()
 page.reload();assert page.locator('[data-crown-check]').is_disabled();page.locator('[data-tab=mesa]').click();card.locator('.artifact-panel summary').click();assert card.locator('[data-artifact-action=sand]').is_disabled()
 assert '33' in card.locator('.health-caption').inner_text();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 assert not errors,errors;b.close();print('PASS: five artifacts, turn-limited damage and critical, resistance and skill bonuses, persistence, initial HP and mobile layout.')

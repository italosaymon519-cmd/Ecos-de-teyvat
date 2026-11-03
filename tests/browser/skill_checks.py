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
 page.route('https://skills.test/**',serve);page.goto('https://skills.test/')
 page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Amber');page.locator('[name=level]').fill('5');page.locator('[name=skillChoice][value=Atletismo]').check();page.get_by_role('button',name='Salvar personagem').click()
 page.locator('[data-action=skills]').click();assert page.locator('#personagens').is_visible();assert page.locator('[data-skill-roll]').count()==18
 page.evaluate('Math.random=()=>0.45') # natural ten
 page.locator('[data-skill-roll=Atletismo]').click();assert '+ 3 Força + 3 proficiência = 16' in page.locator('.skill-roll-result').inner_text();assert 'Amber • Amber' in page.locator('.skill-roll-result').inner_text();assert page.locator('.sheet-skill-panel').get_attribute('open') is not None
 page.locator('[data-skill-roll=Furtividade]').click();assert '+ 2 Agilidade + 0 proficiência (não treinado) = 12' in page.locator('.skill-roll-result').inner_text()
 page.locator('.sheet-skill-panel select').select_option('advantage');page.evaluate("window.diceValues=[0,0.9999];Math.random=()=>window.diceValues.shift()??0.5;document.querySelector('[data-skill-roll=Atletismo]').click()");assert '2d20 [1, 20]' in page.locator('.skill-roll-result').inner_text(),page.locator('.skill-roll-result').inner_text();assert '= 26' in page.locator('.skill-roll-result').inner_text();assert 'crítico' not in page.locator('.skill-roll-result').inner_text();assert page.locator('.sheet-skill-panel select').input_value()=='advantage'
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.reload();page.locator('nav [data-tab=personagens]').click();assert 'Nível 5' in page.locator('#character-list').inner_text();assert 'Atletismo' in page.evaluate("JSON.parse(localStorage.getItem('ecos-teyvat-v1')).events[0].text")
 assert not errors,errors;b.close();print('PASS: skill buttons in sheet; trained/untrained math, level-five proficiency, advantage breakdown, character attribution, open-panel preservation, persistence and mobile layout.')

from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def serve(route):
  path=urlparse(route.request.url).path;f=ROOT/('index.html' if path=='/' else path.lstrip('/'))
  route.fulfill(content_type='text/javascript' if f.suffix=='.js' else 'text/css' if f.suffix=='.css' else 'text/html',body=f.read_text())
 page.route('https://ecos.test/**',serve);page.goto('https://ecos.test/')
 page.locator('#roll-nick').fill('Teste de dados');page.locator('[data-die="12"]').click();page.locator('#roll').click()
 assert '1d12:' in page.locator('#roll-detail').inner_text();assert 1<=int(page.locator('#die-result').inner_text())<=12
 page.locator('#roll-mode').select_option('advantage');assert page.locator('[data-die="20"]').get_attribute('class')=='selected';page.locator('#roll').click();assert 'Vantagem · 2d20 [' in page.locator('#roll-detail').inner_text()
 page.locator('#roll-mode').select_option('disadvantage');page.locator('#roll').click();assert 'Desvantagem · 2d20 [' in page.locator('#roll-detail').inner_text()
 page.locator('[data-die="8"]').click();assert page.locator('#roll-mode').input_value()=='normal';page.locator('#roll-mode').select_option('critical');page.locator('#roll').click();assert 'Teste de dados • Crítico (dano) · 2d8 [' in page.locator('#roll-detail').inner_text()
 page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Teste')
 assert page.locator('[name=skillChoice]').count()==18;assert page.locator('[name=talentChoice]').count()==8
 for value in ['Atletismo','Furtividade']:page.locator('[name=skillChoice][value="'+value+'"]').check()
 for value in ['Golpe Preciso','Passo Ágil']:page.locator('[name=talentChoice][value="'+value+'"]').check()
 page.get_by_role('button',name='Salvar personagem').click();page.locator('[data-action=edit]').first.click()
 assert page.locator('[name=skillChoice]:checked').count()==2;assert page.locator('[name=talentChoice]:checked').count()==2
 page.locator('#close-editor').click()
 page.evaluate("""()=>{const s=JSON.parse(localStorage.getItem('ecos-teyvat-v1'));s.characters[0].skills='Atletismo, Perícia antiga';s.characters[0].talents='Golpe Preciso; Talento antigo';localStorage.setItem('ecos-teyvat-v1',JSON.stringify(s));}""")
 page.reload();page.locator('[data-action=edit]').first.click()
 assert page.locator('[name=skillChoice][value="Perícia antiga"]').is_checked();assert page.locator('[name=talentChoice][value="Talento antigo"]').is_checked()
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.get_by_role('button',name='Salvar personagem').click()
 saved=page.evaluate("JSON.parse(localStorage.getItem('ecos-teyvat-v1')).characters[0]")
 assert 'Perícia antiga' in saved['skills'];assert 'Talento antigo' in saved['talents'];assert not errors,errors
 b.close();print('PASS: d12 within range, 18 skills and 8 talents selectable, selections saved and reloaded, legacy custom values preserved, mobile layout.')

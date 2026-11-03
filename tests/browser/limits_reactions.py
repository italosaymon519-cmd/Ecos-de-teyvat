import mimetypes,json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def serve(route):
  path=urlparse(route.request.url).path;f=ROOT/('index.html' if path=='/' else path.lstrip('/'));route.fulfill(content_type='text/javascript' if f.suffix=='.js' else mimetypes.guess_type(str(f))[0] or 'application/octet-stream',body=f.read_bytes())
 page.route('https://rules.test/**',serve);page.goto('https://rules.test/')
 page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Amber');page.locator('[name=element]').select_option('Pyro')
 for value in ['Atletismo','Furtividade']:page.locator('[name=skillChoice][value="'+value+'"]').check()
 assert page.locator('[name=skillChoice][value=Medicina]').is_disabled()
 page.locator('[name=skillChoice][value=Atletismo]').uncheck();assert page.locator('[name=skillChoice][value=Medicina]').is_enabled();page.locator('[name=skillChoice][value=Atletismo]').check()
 for value in ['Golpe Preciso','Passo Ágil']:page.locator('[name=talentChoice][value="'+value+'"]').check()
 assert page.locator('[name=talentChoice][value="Postura Defensiva"]').is_disabled()
 page.get_by_role('button',name='Salvar personagem').click()
 page.locator('#new-character').click();page.locator('#character-form [name=name]').fill('Barbara');page.locator('[name=element]').select_option('Hydro');page.get_by_role('button',name='Salvar personagem').click()
 page.locator('#source').select_option(index=1);assert page.locator('#reaction-mark').is_disabled();assert page.locator('#reaction-mark option').count()==1;assert page.locator('#reaction-mark').input_value()=='Pyro';assert page.locator('[data-action=mark]').first.locator('option').count()==2;page.locator('#trigger').select_option(index=2);assert page.locator('#reaction').is_disabled();assert 'Preparar marca' in page.locator('#reaction-feedback').inner_text()
 page.locator('#prepare-mark').click();assert page.locator('#reaction').is_enabled();page.locator('#reaction').click();assert 'Vaporizar' in page.locator('#reaction-result').inner_text();assert 'Amber: 0 → 1 EE' in page.locator('#reaction-result').inner_text();assert page.locator('.energy .filled').count()==2;assert page.locator('#reaction').is_disabled()
 # Import cannot bypass the cap or overwrite valid current data.
 backup=page.evaluate("JSON.parse(localStorage.getItem('ecos-teyvat-v1'))");backup['characters'][0]['skills']='Atletismo,Furtividade,Medicina'
 page.locator('#import').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})
 page.wait_for_function("document.querySelector('#notice').textContent.includes('2 perícias')")
 assert page.evaluate("JSON.parse(localStorage.getItem('ecos-teyvat-v1')).characters[0].skills")=='Atletismo, Furtividade'
 # Legacy over-limit selections must be corrected without silent deletion.
 page.evaluate("""()=>{const s=JSON.parse(localStorage.getItem('ecos-teyvat-v1'));s.characters[0].skills='Atletismo,Furtividade,Medicina';s.characters[0].mark='Cryo';localStorage.setItem('ecos-teyvat-v1',JSON.stringify(s));}""")
 page.reload();assert page.locator('[data-action=mark]').first.input_value()=='';page.locator('[data-action=edit]').first.click();assert page.locator('[name=skillChoice]:checked').count()==3;page.get_by_role('button',name='Salvar personagem').click();assert page.locator('#editor').is_visible();assert '2 perícias' in page.locator('#choice-error').inner_text();page.locator('[name=skillChoice][value=Medicina]').uncheck();page.get_by_role('button',name='Salvar personagem').click();assert page.locator('#editor').is_hidden()
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');page.set_viewport_size({'width':768,'height':1024});assert page.evaluate('document.documentElement.scrollWidth <= innerWidth');assert not errors,errors
 b.close();print('PASS: third selections blocked, legacy excess preserved but cannot save, reaction prerequisites visible, reaction result and 1 EE per participant, mark consumed, mobile layout.')

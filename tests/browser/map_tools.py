"""Two-account map tools integration using the existing simulated Supabase harness."""
from pathlib import Path
exec(Path(__file__).with_name('shared_room.py').read_text().split('with sync_playwright() as p:')[0])
import math,struct,zlib,re
rooms.append({'id':RID,'name':'Mondstadt','gm_id':'gm'});members.extend({'room_id':RID,'user_id':u,'display_name':n} for u,n in [('gm','Mestre'),('player','Aventureira')])
MID='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';items.append({'id':MID,'room_id':RID,'kind':'map','title':'Campo de batalha','public_text':'Teste','visible':True,'is_current':True,'image_path':RID+'/map.png'})
settings={};markers=[];base_api=api;fail_once={'value':False}

def map_api(route):
 req=route.request;u=urlparse(req.url);path=u.path;user=req.headers.get('authorization','').replace('Bearer token-','');q=parse_qs(u.query)
 try:body=req.post_data_json or {}
 except:body={}
 if path=='/rest/v1/campaign_map_settings':return reply(route,[settings[q['item_id'][0][3:]]] if q['item_id'][0][3:] in settings else [])
 if path=='/rest/v1/campaign_map_markers':return reply(route,[m for m in markers if m['item_id']==q['item_id'][0][3:]])
 if path=='/rest/v1/rpc/save_campaign_map_settings':
  if user!='gm':return reply(route,{},403)
  old=settings.get(body['map_id'],{'revision':0})
  if old['revision']!=body['expected_revision']:return reply(route,{'code':'40001','message':'Escala alterada; recarregue'},409)
  settings[body['map_id']]={'item_id':body['map_id'],'room_id':RID,**body['payload'],'revision':old['revision']+1};return reply(route,settings[body['map_id']])
 if path=='/rest/v1/rpc/create_campaign_map_marker':
  old=next((m for m in markers if m['id']==body['marker_id']),None)
  if old:return reply(route,old)
  member=next(m for m in members if m['user_id']==user)
  marker={'id':body['marker_id'],'item_id':body['map_id'],'room_id':RID,'created_by':user,'creator_name':member['display_name'],**body['payload']};markers.append(marker)
  if fail_once['value']:fail_once['value']=False;return reply(route,{'message':'Resposta perdida após gravar'},503)
  return reply(route,marker)
 if path=='/rest/v1/rpc/delete_campaign_map_marker':
  marker=next((m for m in markers if m['id']==body['marker_id']),None)
  if marker and user not in [marker['created_by'],'gm']:return reply(route,{},403)
  if marker:markers.remove(marker)
  return reply(route,None)
 return base_api(route)

def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',600,300,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+b'\x35\x45\x35'*600)*300))+chunk(b'IEND',b'')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def context(email):
  ctx=b.new_context(viewport={'width':1440,'height':1100});ctx.route('https://ecos.test/**',static);ctx.route('https://db.test/**',map_api);ctx.route('https://db.test/storage/v1/object/sign/campaign-images/image.png?token=test',lambda r:r.fulfill(content_type='image/png',body=png));page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));login(page,email);page.wait_for_function("document.querySelector('#room-stage-image').naturalWidth===600");page.wait_for_function("document.querySelector('#map-tools-status').textContent.includes('conectadas')");return ctx,page
 gc,gm=context('gm@example.test');pc,player=context('player@example.test')
 assert player.locator('#map-settings-details').is_hidden()
 player.locator('[data-map-mode=measure]').click();assert 'salvar a escala' in player.locator('#map-tools-status').inner_text()
 gm.locator('#map-settings-details summary').click();gm.locator('#map-settings-form [name=grid_enabled]').check();gm.locator('#map-settings-form [name=grid_columns]').fill('10');gm.locator('#map-settings-form [name=units_per_cell]').fill('2');gm.locator('#map-settings-save').click()
 gm.wait_for_function("document.querySelector('#map-grid-layer').hasAttribute('hidden')===false")
 player.wait_for_function("document.querySelector('#map-grid-layer').hasAttribute('hidden')===false",timeout=12000)
 assert gm.locator('#map-grid-layer').get_attribute('viewBox')=='0 0 600 300';assert gm.locator('#map-grid-layer pattern').get_attribute('width')=='60'
 def measure(page):
  page.locator('[data-map-mode=measure]').click();page.locator('#room-image-wrap').scroll_into_view_if_needed();rect=page.locator('#room-board').bounding_box();a=(rect['x']+rect['width']*.1,rect['y']+rect['height']*.2);z=(rect['x']+rect['width']*.3,rect['y']+rect['height']*.6);page.mouse.move(*a);page.mouse.down();page.mouse.move(*z,steps=8);page.mouse.up();page.wait_for_function("document.querySelector('#map-measure-result').textContent.includes('sua medida')");return float(re.search(r'[\d,]+',page.locator('#map-measure-result').inner_text()).group().replace(',','.'))
 first=measure(gm);assert math.isclose(first,math.sqrt(8)*2,abs_tol=.05),first
 assert player.locator('#map-measure-layer').get_attribute('hidden') is not None;assert player.locator('#room-marker-layer .map-marker').count()==0
 gm.locator('[data-map-mode=move]').click();gm.locator('#room-zoom-in').click();gm.locator('#room-zoom-in').click();gm.locator('#room-image-wrap').evaluate('(n)=>{n.scrollLeft=0;n.scrollTop=0}')
 second=measure(gm);assert math.isclose(first,second,abs_tol=.05),(first,second)
 gm.locator('#map-marker-label').fill('Alcance');gm.locator('#map-share-measure').click();gm.wait_for_function("document.querySelectorAll('#room-marker-layer .map-marker').length===1")
 player.wait_for_function("document.querySelectorAll('#room-marker-layer .map-marker').length===1",timeout=12000);ruler=markers[0];assert ruler['kind']=='ruler';assert player.locator('#room-marker-layer').inner_text().startswith('↔')
 fail_once['value']=True;player.locator('#map-marker-label').fill('Entrada');player.locator('[data-map-mode=pin]').click();player.locator('#room-image-wrap').scroll_into_view_if_needed();rect=player.locator('#room-board').bounding_box();player.mouse.click(rect['x']+rect['width']*.6,rect['y']+rect['height']*.4)
 player.locator('#map-marker-retry').wait_for(state='visible');assert len(markers)==2;player.locator('#map-marker-retry').click();player.locator('#map-marker-retry').wait_for(state='hidden');player.wait_for_function("document.querySelectorAll('#room-marker-layer .map-marker').length===2");assert len(markers)==2;pin=next(m for m in markers if m['kind']=='pin');assert pin['created_by']=='player';assert abs(pin['x']-60)<.2
 gm.wait_for_function("document.querySelectorAll('#room-marker-layer .map-marker').length===2",timeout=12000)
 player.locator('#map-markers-details summary').click();assert player.locator('[data-remove-marker="'+ruler['id']+'"]').count()==0
 player.once('dialog',lambda d:d.accept());player.locator('[data-remove-marker="'+pin['id']+'"]').click();player.wait_for_function("document.querySelectorAll('#room-marker-layer .map-marker').length===1")
 player.reload();player.locator('[data-tab=sala]').click();player.wait_for_function("document.querySelectorAll('#room-marker-layer .map-marker').length===1");assert '10 colunas' in player.locator('#map-scale-label').inner_text()
 # Personal rulers also support touch-style two-click input.
 player.locator('[data-map-mode=measure]').click();player.locator('#room-image-wrap').scroll_into_view_if_needed();rect=player.locator('#room-board').bounding_box();player.mouse.click(rect['x']+rect['width']*.2,rect['y']+rect['height']*.2);player.mouse.click(rect['x']+rect['width']*.4,rect['y']+rect['height']*.4);assert 'sua medida' in player.locator('#map-measure-result').inner_text()
 player.set_viewport_size({'width':390,'height':844});assert player.evaluate('document.documentElement.scrollWidth<=innerWidth')
 # An unchanged polling response must preserve markers and the grid.
 gm.evaluate("window.keptMarker=document.querySelector('.map-marker');window.keptGrid=document.querySelector('#map-grid-layer pattern')");gm.locator('#map-tools-refresh').click();gm.wait_for_function("!document.querySelector('#map-tools-status').textContent.includes('Não foi possível')");assert gm.evaluate('keptMarker.isConnected&&keptGrid.isConnected')
 # A remote scale edit cannot silently overwrite a master's unsaved form.
 gm.locator('#map-settings-form [name=grid_columns]').fill('12');settings[MID]={**settings[MID],'grid_columns':15,'revision':settings[MID]['revision']+1};gm.locator('#map-tools-refresh').click();gm.wait_for_function("document.querySelector('#map-scale-label').textContent.includes('15 colunas')");assert gm.locator('#map-settings-form [name=grid_columns]').input_value()=='12'
 gm.locator('#map-settings-save').click();gm.wait_for_function("document.querySelector('#map-tools-status').textContent.includes('recarregue')");gm.locator('#map-settings-reload').click();gm.wait_for_function("document.querySelector('#map-settings-form [name=grid_columns]').value==='15'");gm.locator('#map-settings-form [name=grid_columns]').fill('10');gm.locator('#map-settings-save').click();gm.wait_for_function("document.querySelector('#map-scale-label').textContent.includes('10 colunas')")
 # Settings, rulers and markers belong to their map, not the entire room.
 items[0]['is_current']=False;items.append({'id':'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','room_id':RID,'kind':'map','title':'Outro mapa','public_text':'','visible':True,'is_current':True,'image_path':RID+'/other.png'})
 gm.locator('#room-refresh').click();gm.wait_for_function("document.querySelector('#room-stage-title').textContent==='Outro mapa'");assert gm.locator('#room-marker-layer .map-marker').count()==0;assert gm.locator('#map-grid-layer').get_attribute('hidden') is not None;assert 'ainda não configurada' in gm.locator('#map-scale-label').inner_text()
 items[-1]['is_current']=False;items[0]['is_current']=True;gm.locator('#room-refresh').click();gm.wait_for_function("document.querySelectorAll('#room-marker-layer .map-marker').length===1");assert '10 colunas' in gm.locator('#map-scale-label').inner_text()
 assert not errors,errors
 b.close();print('PASS: shared square grid, calibrated diagonal distance at 100/200% zoom, private/shared rulers, player pins, ownership deletion, persistence, two-click input, mobile, stable polling DOM, retry idempotence, scale conflict protection and per-map isolation.')

"""UI integration with simulated Supabase API. Run after npm run build; requires Python Playwright + Chromium.
Database authorization is separately exercised by room-policies.test.js against PostgreSQL/PGlite.
"""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import json,base64,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
RID='11111111-1111-1111-1111-111111111111';CODE='ABCDEF0123456789ABCDEF0123456789'
rooms=[];members=[];items=[];tokens=[];files={};errors=[];combats={};characters=[];presence={};rolls=[]
def reply(route,data,status=200):route.fulfill(status=status,content_type='application/json',body=json.dumps(data))
def api(route):
 req=route.request;u=urlparse(req.url);path=u.path;method=req.method;token=req.headers.get('authorization','').replace('Bearer ','');user=token.replace('token-','');q=parse_qs(u.query)
 try: body=req.post_data_json or {}
 except:body={}
 if path=='/auth/v1/token':
  user='gm' if body.get('email','').startswith('gm') else 'player'
  return reply(route,{'access_token':'token-'+user,'refresh_token':'refresh-'+user,'expires_in':3600,'user':{'id':user,'email':user+'@example.test'}})
 if path=='/auth/v1/logout':return reply(route,{})
 if path=='/rest/v1/rpc/create_campaign_room':
  rooms.append({'id':RID,'name':body['room_name'],'gm_id':user});members.append({'room_id':RID,'user_id':user,'display_name':body['member_name']});return reply(route,RID)
 if path=='/rest/v1/rpc/campaign_invite':return reply(route,CODE if user=='gm' else 'denied',200 if user=='gm' else 403)
 if path=='/rest/v1/rpc/join_campaign_room':
  if body.get('code')!=CODE:return reply(route,{'message':'Convite inválido.'},400)
  if not any(m['user_id']==user for m in members):members.append({'room_id':RID,'user_id':user,'display_name':body['member_name']})
  return reply(route,RID)
 if path=='/rest/v1/campaign_rooms':return reply(route,rooms if any(m['user_id']==user for m in members) else [])
 if path=='/rest/v1/campaign_members':return reply(route,[m for m in members if m['room_id']==q['room_id'][0][3:]])
 if path=='/rest/v1/campaign_rolls':
  rows=[r for r in rolls if r['room_id']==q['room_id'][0][3:]]
  if 'seq' in q:rows=[r for r in rows if r['seq']>int(q['seq'][0][3:])]
  rows=sorted(rows,key=lambda r:r['seq'],reverse=q.get('order',[''])[0].endswith('desc'));return reply(route,rows[:int(q.get('limit',['100'])[0])])
 if path=='/rest/v1/rpc/record_campaign_roll':
  old=next((r for r in rolls if r['room_id']==body['target_room'] and r['id']==body['roll_id']),None)
  if old:return reply(route,old)
  sheet=next((r for r in characters if r['id']==body['payload'].get('character_id') and r['room_id']==body['target_room']),None)
  if sheet and sheet['owner_id']!=user and user!='gm':return reply(route,{},403)
  member=next(m for m in members if m['room_id']==body['target_room'] and m['user_id']==user)
  row={'id':body['roll_id'],'seq':len(rolls)+1,'room_id':body['target_room'],'actor_id':user,'actor_name':member['display_name'],'character_name':sheet['data']['name'] if sheet else None,'created_at':'2026-11-04T12:00:00Z',**body['payload']};rolls.append(row);return reply(route,row)
 if path=='/rest/v1/rpc/link_campaign_token':
  if user!='gm':return reply(route,{},403)
  token=next(t for t in tokens if t['id']==body['token_id']);token['character_id']=body['sheet_id']
  sheet=next((r for r in characters if r['id']==body['sheet_id']),None)
  token['owner_id']=sheet['owner_id'] if sheet and token['kind']=='character' else None
  if sheet:token['name']=sheet['data']['name']
  return reply(route,token)
 if path=='/rest/v1/campaign_characters':return reply(route,[r for r in characters if r['room_id']==q['room_id'][0][3:]])
 if path=='/rest/v1/rpc/save_campaign_character':
  r=next((r for r in characters if r['id']==body['character_id'] and r['room_id']==body['target_room']),None)
  if r and r['owner_id']!=user and user!='gm':return reply(route,{},403)
  if (r['revision'] if r else 0)!=body['expected_revision']:return reply(route,{'code':'40001','message':'Versão diferente'},409)
  if not r:r={'id':body['character_id'],'room_id':body['target_room'],'owner_id':user,'revision':0};characters.append(r)
  r.update({'data':body['payload'] if body['payload'] is not None else r['data'],'deleted':body['payload'] is None,'revision':r['revision']+1});return reply(route,r)
 if path=='/rest/v1/rpc/react_campaign_characters':
  a=next(r for r in characters if r['id']==body['source_id']);b=next(r for r in characters if r['id']==body['trigger_id'])
  if b['owner_id']!=user and user!='gm':return reply(route,{},403)
  if not a['data']['mark']:return reply(route,{'message':'Sem marca'},400)
  for r in [a,b]:r['data']['ee']=min(3,r['data']['ee']+1);r['revision']+=1
  a['data']['mark']=None;return reply(route,[a,b])
 if path=='/rest/v1/rpc/campaign_heartbeat':presence[(body['target_room'],user,body['session_id'])]=time.monotonic();return reply(route,None)
 if path=='/rest/v1/rpc/leave_campaign_session':presence.pop((body['target_room'],user,body['session_id']),None);return reply(route,None)
 if path=='/rest/v1/campaign_presence':return reply(route,[{'user_id':u} for (r,u,session),last in presence.items() if r==q['room_id'][0][3:] and time.monotonic()-last<90])

 if path=='/rest/v1/campaign_combats':
  selected=q['room_id'][0][3:];return reply(route,[combats[selected]] if selected in combats else [])
 if path=='/rest/v1/rpc/save_campaign_combat':
  if user!='gm':return reply(route,{},403)
  old=combats.get(RID,{'revision':0})
  if old['revision']!=body['expected_revision']:return reply(route,{'message':'Conflito de versão'},400)
  combats[RID]={'room_id':RID,**body['payload'],'revision':old['revision']+1};return reply(route,combats[RID])
 if path=='/rest/v1/campaign_tokens':
  if method=='GET':
   ids=[i['id'] for i in items if i['visible'] or user=='gm']
   return reply(route,[t for t in tokens if t['item_id'] in ids and t['item_id']==q['item_id'][0][3:]])
  if method=='POST':
   if user!='gm':return reply(route,{},403)
   t={'id':'t'+str(len(tokens)+1),**body};tokens.append(t);return reply(route,[t])
  t=next(t for t in tokens if t['id']==q['id'][0][3:])
  if method=='PATCH':
   if user!='gm' and t.get('owner_id')!=user:return reply(route,[])
   t.update(body);return reply(route,[t])
  if method=='DELETE' and user=='gm':tokens.remove(t);return reply(route,{})
 if path=='/rest/v1/campaign_items':
  if method=='GET':return reply(route,[i for i in items if user=='gm' or i['visible']])
  if user!='gm':return reply(route,{'message':'denied'},403)
  if method=='POST':
   i={'id':str(len(items)+1),'updated_at':'now',**body};items.append(i);return reply(route,[i])
  i=next(i for i in items if i['id']==q['id'][0][3:])
  if method=='PATCH':i.update(body);return reply(route,[i])
  if method=='DELETE':items.remove(i);return reply(route,{})
 if path=='/rest/v1/rpc/present_campaign_item':
  if user!='gm':return reply(route,{},403)
  for i in items:i['is_current']=i['id']==body['item_id'];i['visible']=i['visible'] or i['is_current']
  return reply(route,{})
 if path.startswith('/storage/v1/object/campaign-images/') and method=='POST':files[path]=True;return reply(route,{'Key':path})
 if path.startswith('/storage/v1/object/sign/campaign-images/'):
  return reply(route,{'signedURL':'/object/sign/campaign-images/image.png?token=test'})
 return reply(route,{'message':'Unexpected '+path},404)
def static(route):
 path=urlparse(route.request.url).path
 if path=='/src/cloud-config.js':return route.fulfill(content_type='text/javascript',body="export const cloudConfig={url:'https://db.test',key:'sb_publishable_test'};")
 f=ROOT/('index.html' if path=='/' else path.lstrip('/'))
 route.fulfill(status=200,content_type='text/javascript' if f.suffix=='.js' else (mimetypes.guess_type(str(f))[0] or 'application/octet-stream'),body=f.read_bytes())
def login(page,email):
 page.goto('https://ecos.test/');page.locator('[data-tab=sala]').click();page.locator('#cloud-email').fill(email);page.locator('#cloud-password').fill('long-password-123');page.locator('#cloud-auth-form button[type=submit]').click();page.locator('#cloud-account').wait_for(state='visible')
def item(page,kind,name,text):
 page.locator('#room-item-kind').select_option(kind);page.locator('#room-item-title').fill(name);page.locator('#room-item-text').fill(text);page.locator('#room-item-form button[value=save]').click();page.wait_for_function("document.querySelectorAll('.room-content-card').length > 0")
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def context():
  c=b.new_context(viewport={'width':1440,'height':1000});c.route('https://ecos.test/**',static);c.route('https://db.test/**',api);page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));return c,page
 gmctx,gm=context();pc,player=context();login(gm,'gm@example.test')
 gm.locator('#room-create-form [name=roomName]').fill('Mondstadt compartilhada');gm.locator('#room-create-form [name=displayName]').fill('Mestre');gm.locator('#room-create-form button').click();gm.locator('#room-composer').wait_for(state='visible')
 assert gm.locator('#room-open-tokens').is_visible();assert gm.locator('#room-token-help').inner_text().startswith('Primeiro prepare');assert gm.locator('#room-token-form').is_hidden()
 gm.locator('#room-show-code').click();gm.wait_for_function("document.querySelector('#room-invite-value').value.length === 32");assert gm.locator('#room-invite-value').input_value()==CODE
 item(gm,'scene','Cena secreta','Texto público sem segredo')
 player.goto('https://ecos.test/');player.locator('#new-character').click();player.locator('#character-form [name=name]').fill('Ficha local');player.locator('[name=element]').select_option('Geo');player.get_by_role('button',name='Salvar personagem').click()
 login(player,'player@example.test');player.locator('#room-join-form [name=code]').fill('https://old--comfy-jalebi-598a6d.netlify.app/?room='+CODE);player.locator('#room-join-form [name=displayName]').fill('Aventureira');player.locator('#room-join-form button').click();player.locator('#room-panel').wait_for(state='visible')
 assert player.locator('.room-content-card').count()==0
 assert player.locator('#room-composer').is_hidden()
 # Existing local sheets are explicitly copied and keep their original local copy.
 player.locator('.campaign-sheets details summary').click();player.locator('#room-sheet-local').select_option(label='Ficha local');player.locator('#room-sheet-copy').click()
 player.wait_for_function("document.querySelector('#room-sheets-status').textContent.includes('Todas as fichas salvas')")
 assert len(characters)==1;assert characters[0]['owner_id']=='player'
 assert player.evaluate("JSON.parse(localStorage.getItem('ecos-teyvat-v1')).characters[0].name")=='Ficha local'
 gm.locator('[data-tab=mesa]').click();gm.locator('#new-character').click();gm.locator('#character-form [name=name]').fill('Mestre Pyro');gm.get_by_role('button',name='Salvar personagem').click()
 gm.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')")
 player.locator('[data-tab=mesa]').click();player.wait_for_function("document.querySelectorAll('.character-card').length===2",timeout=12000)
 assert player.locator('.character-card').filter(has_text='Mestre Pyro').locator('[data-action=edit]').is_disabled()
 geo=player.locator('.character-card').filter(has_text='Ficha local');page_id=characters[0]['id']
 player.evaluate('Math.random=()=>0.999');geo.locator('[data-vision-action=activate]').click();geo.locator('[data-action=damage]').click();player.locator('#damage-form [name=amount]').fill('8');player.locator('#damage-form button[type=submit]').click()
 player.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')")
 assert next(r for r in characters if r['id']==page_id)['data']['hp']==31
 gm.wait_for_function("document.querySelectorAll('.character-card').length===2",timeout=12000)
 gm.locator('.character-card').filter(has_text='Mestre Pyro').locator('[data-action=mark]').select_option('Pyro');gm.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')")
 player.wait_for_function("[...document.querySelectorAll('#source option')].some(o=>o.textContent.includes('Mestre Pyro')&&o.textContent.includes('Pyro'))")
 player.locator('#source').select_option(label='Mestre Pyro · Pyro');player.locator('#trigger').select_option(page_id);player.locator('#reaction').click();player.wait_for_function("document.querySelector('#reaction-result').textContent.includes('Cristalização')")
 assert [r['data']['ee'] for r in characters]==[1,1]
 # Fresh browser/account login recovers cloud HP and used benefit without local storage.
 freshctx,fresh=context();login(fresh,'player@example.test');fresh.locator('[data-tab=mesa]').click();fresh.wait_for_function("document.querySelectorAll('.character-card').length===2")
 recovered=fresh.locator('.character-card').filter(has_text='Ficha local');assert '31' in recovered.locator('.health-caption').inner_text();assert recovered.locator('[data-vision-action=activate]').is_disabled()
 fresh.locator('[data-tab=sala]').click();fresh.locator('#cloud-logout').click();fresh.locator('#cloud-auth').wait_for(state='visible');freshctx.close()
 gm.locator('[data-tab=sala]').click();player.locator('[data-tab=sala]').click();gm.locator('#room-refresh').click();player.locator('#room-refresh').click()
 gm.wait_for_function("document.querySelectorAll('.presence-person.is-online').length===2")
 assert 'Aventureira' in gm.locator('#room-presence').inner_text();assert 'Mestre' in player.locator('#room-presence').inner_text()
 gm.locator('[data-room-action=present]').first.click();player.wait_for_function("document.querySelector('#room-stage-title').textContent === 'Cena secreta'",timeout=12000)
 assert player.locator('[data-room-action=edit]').count()==0
 assert player.locator('.room-content-card').count()==1
 gm.locator('[data-room-action=visibility]').first.click();player.locator('#room-refresh').click();player.wait_for_function("document.querySelectorAll('.room-content-card').length === 0")
 # Add a map and exercise its private upload and signing flow.
 gm.locator('#room-item-kind').select_option('map');gm.locator('#room-item-title').fill('Mapa da campanha');gm.locator('#room-item-text').fill('Teyvat')
 png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aS1sAAAAASUVORK5CYII=')
 gm.locator('#room-item-image').set_input_files({'name':'map.png','mimeType':'image/png','buffer':png})
 gm.locator('#room-item-form button[value=save]').click();gm.wait_for_function("document.querySelectorAll('.room-content-card').length === 2")
 # Image bytes served independently of metadata response.
 for ctx in [gmctx,pc]:ctx.route('https://db.test/storage/v1/object/sign/campaign-images/image.png?token=test',lambda r:r.fulfill(content_type='image/png',body=png))
 gm.locator('.room-content-card').filter(has_text='Mapa da campanha').locator('[data-room-action=present]').click();player.locator('#room-refresh').click()
 player.wait_for_function("document.querySelector('#room-stage-title').textContent === 'Mapa da campanha'")
 player.locator('#room-stage-image').wait_for(state='visible');player.wait_for_function("document.querySelector('#room-stage-image').naturalWidth > 0");player.locator('#room-zoom-in').click();assert player.locator('#room-zoom-label').inner_text()=='150%'
 # Tokens persist on the map; only assigned players can move them.
 gm.locator('#room-token-tools').wait_for(state='visible')
 for expected,(name,kind,owner) in enumerate([('Amber','character','player'),('Hilichurl','enemy','')],start=1):
  gm.locator('#room-token-name').fill(name);gm.locator('#room-token-kind').select_option(kind)
  if owner:gm.locator('#room-token-owner').select_option(owner)
  gm.locator('#room-token-form button').click()
  gm.wait_for_function('document.querySelectorAll(".board-token").length === '+str(expected))
 player.wait_for_function('document.querySelectorAll(".board-token").length === 2',timeout=12000)
 assert player.locator('.board-token.movable').count()==1
 before=tokens[0]['x']
 player.locator('.board-token.movable').focus();player.locator('.board-token.movable').press('ArrowRight')
 player.wait_for_function('document.querySelector(".board-token.movable").style.left !== "'+str(before)+'%"')
 assert tokens[0]['x']==before+1
 gm.wait_for_function('document.querySelector("[data-token-id=t1]").style.left === "'+str(tokens[0]['x'])+'%"',timeout=12000)
 # Drag works independently of map zoom and persists to the second browser.
 player.locator('.board-token.movable').scroll_into_view_if_needed()
 box=player.locator('.board-token.movable').bounding_box();before_drag=tokens[0]['x']
 px,py=box['x']+box['width']/2,box['y']+box['height']/2
 player.mouse.move(px,py);player.mouse.down();player.mouse.move(px+20,py+15,steps=5);player.mouse.up()
 player.wait_for_function("parseFloat(document.querySelector('.board-token.movable').style.left) !== "+str(before_drag))
 player.wait_for_function("document.querySelector('#room-token-status').textContent.includes('posição atualizada')");assert tokens[0]['x']!=before_drag
 # A private preview does not replace what is presented to others.
 gm.locator('#room-search').fill('secreta');assert gm.locator('.room-content-card').count()==1
 gm.locator('[data-room-action=preview]').click();assert gm.locator('#room-follow').is_visible()
 gm.locator('#room-follow').click();assert gm.locator('#room-stage-title').inner_text()=='Mapa da campanha'
 gm.locator('#room-search').fill('')
 # Shared initiative starts at highest result and drives the local round clock.
 gm.locator('#combat-prepare').wait_for(state='visible');gm.locator('#combat-prepare').click();gm.locator('#combat-import-tokens').click()
 gm.wait_for_function('document.querySelectorAll(".combat-draft-row").length === 2')
 gm.locator('.combat-draft-row').filter(has_text='Amber').locator('[data-combat-field=initiative]').fill('12')
 gm.locator('.combat-draft-row').filter(has_text='Hilichurl').locator('[data-combat-field=initiative]').fill('18')
 gm.locator('#combat-start').click();gm.wait_for_function("document.querySelector('#combat-active').textContent === 'Turno de Hilichurl'")
 player.wait_for_function("document.querySelector('#combat-active').textContent === 'Turno de Hilichurl'",timeout=12000)
 assert player.locator('#combat-next').is_hidden()
 gm.locator('#combat-next').click();gm.wait_for_function("document.querySelector('#combat-active').textContent === 'Turno de Amber'")
 gm.locator('#combat-next').click();gm.wait_for_function("document.querySelector('#combat-round').textContent === 'rodada 2'")
 player.wait_for_function("document.querySelector('#combat-round').textContent === 'rodada 2'",timeout=12000)
 assert player.locator('#round').inner_text()=='2'
 # Rejoining an ongoing combat must not refresh already-spent resources.
 player.locator('[data-tab=mesa]').click();geo=player.locator('.character-card').filter(has_text='Ficha local')
 player.evaluate('Math.random=()=>0.999');geo.locator('[data-vision-action=activate]').click();geo.locator('[data-action=damage]').click();player.locator('#damage-form [name=amount]').fill('8');player.locator('#damage-form button[type=submit]').click();geo.locator('[data-action=energy][data-value="2"]').click()
 geo.locator('.artifact-panel summary').click();geo.locator('[data-artifact-action=sand]').click();player.locator('#resistance-form button[type=submit]').click();player.locator('#resistance-close').click()
 player.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')",timeout=12000)
 resumedctx,resumed=context();login(resumed,'player@example.test');resumed.locator('[data-tab=mesa]').click();resumed.wait_for_function("document.querySelectorAll('.character-card').length===2")
 resumed.wait_for_function("document.querySelector('#round').textContent==='2'",timeout=12000)
 rgeo=resumed.locator('.character-card').filter(has_text='Ficha local');assert '29' in rgeo.locator('.health-caption').inner_text();assert rgeo.locator('[data-vision-action=activate]').is_disabled();assert rgeo.locator('.energy .filled').count()==2
 rgeo.locator('.artifact-panel summary').click();assert rgeo.locator('[data-artifact-action=sand]').is_disabled();resumed.locator('[data-tab=sala]').click();resumed.locator('#cloud-logout').click();resumed.locator('#cloud-auth').wait_for(state='visible');resumedctx.close()
 player.locator('[data-tab=sala]').click()
 # Link an existing token and propagate sheet name, HP and conditions to both browsers.
 gm.locator('[data-link-token=t1]').click();gm.locator('#token-link-sheet').select_option(page_id);gm.locator('#token-link-form [type=submit]').click();gm.locator('#token-link-dialog').wait_for(state='hidden')
 player.wait_for_function("document.querySelector('[data-token-id=t1] .token-sheet-health')?.textContent==='29/33 PV'",timeout=12000)
 player.evaluate("window.linkedNode=document.querySelector('[data-token-id=t1]')")
 player.locator('[data-tab=mesa]').click();geo=player.locator('.character-card').filter(has_text='Ficha local');geo.locator('[data-action=edit]').click();player.locator('#character-form [name=conditions]').fill('Congelado');player.locator('#character-form [name=name]').fill('Geo da campanha');player.get_by_role('button',name='Salvar personagem').click()
 geo=player.locator('.character-card').filter(has_text='Geo da campanha');geo.locator('[data-action=damage]').click();player.locator('#damage-form [name=amount]').fill('3');player.locator('#damage-form button[type=submit]').click()
 gm.wait_for_function("document.querySelector('[data-token-id=t1] .token-sheet-health')?.textContent==='26/33 PV'",timeout=12000)
 assert 'Congelado' in gm.locator('[data-token-id=t1]').inner_text();assert 'Geo da campanha' in gm.locator('[data-token-id=t1]').inner_text()
 # Every supported rolling flow publishes the result under the authenticated member's nick.
 player.locator('[data-die="12"]').click();player.locator('#modifier').fill('3');player.evaluate("Math.random=()=>0.45;document.querySelector('#roll').click()")
 geo.locator('[data-action=skills]').click();player.evaluate("Math.random=()=>0.45;document.querySelector('[data-skill-roll=Conhecimento][data-id=\""+page_id+"\"]').click()")
 player.locator('[data-tab=mesa]').click();geo.locator('[data-vision-action=resistance]').click();player.evaluate("Math.random=()=>0.45;document.querySelector('#resistance-form button[type=submit]').click()");player.locator('#resistance-close').click()
 geo.locator('.artifact-panel').evaluate('(node)=>node.open=true');geo.locator('[data-artifact-action=plume]').click();player.evaluate("Math.random=()=>0.45;document.querySelector('#outgoing-form button[type=submit]').click()");player.locator('#outgoing-close').click()
 gm.wait_for_function("document.querySelectorAll('#room-rolls-list .shared-roll-entry').length>=5",timeout=12000)
 assert {'dice','skill','resistance','damage','vision'}<=set(r['kind'] for r in rolls)
 assert all(r['actor_name']=='Aventureira' for r in rolls if r['actor_id']=='player')
 assert 'Aventureira' in gm.locator('#room-rolls-list').inner_text()
 player.locator('[data-tab=sala]').click();player.locator('#room-refresh').click();assert player.evaluate('linkedNode.isConnected');player.wait_for_function("!document.querySelector('#room-refresh').disabled")
 player.locator('[data-token-id=t1]').focus();player.locator('[data-token-id=t1]').press('Enter');assert player.locator('#personagens').is_visible();player.locator('[data-tab=sala]').click()
 # NPC creation is another distinct published content kind.
 gm.locator('#room-item-kind').select_option('npc');gm.locator('#room-item-title').fill('Mira');gm.locator('#room-item-text').fill('Contratante da Guilda');gm.locator('#room-item-form button[value=present]').click()
 gm.wait_for_function("document.querySelectorAll('.room-content-card').length === 3")
 player.wait_for_function("document.querySelector('#room-stage-title').textContent === 'Mira'",timeout=12000);assert player.locator('.room-content-card').count()==2
 player.reload();player.locator('[data-tab=sala]').click();player.locator('#room-select').select_option(RID);player.locator('#room-panel').wait_for(state='visible')
 player.set_viewport_size({'width':390,'height':844});assert player.evaluate('document.documentElement.scrollWidth <= innerWidth')
 gm.locator('#room-player-view').check();assert gm.locator('#room-composer').is_hidden();assert gm.locator('.room-content-card').count()==2
 gm.locator('#room-player-view').uncheck();gm.set_viewport_size({'width':390,'height':844});gm.locator('#combat-prepare').click();assert gm.evaluate('document.documentElement.scrollWidth <= innerWidth');gm.locator('#combat-cancel').click()
 # Selecting another campaign shows its own sheets, then returning restores the first.
 second='22222222-2222-2222-2222-222222222222';rooms.append({'id':second,'name':'Outra campanha','gm_id':'gm'});members.append({'room_id':second,'user_id':'player','display_name':'Aventureira'})
 player.reload();player.locator('[data-tab=sala]').click();player.locator('#room-select').select_option(second);player.wait_for_function("document.querySelector('#campaign-mode').textContent.includes('Outra campanha')");player.wait_for_function("document.querySelectorAll('.character-card').length===0");assert player.locator('#room-rolls-list .shared-roll-entry').count()==0
 player.locator('[data-tab=mesa]').click();player.locator('#new-character').click();player.locator('#character-form [name=name]').fill('Temporária');player.get_by_role('button',name='Salvar personagem').click();player.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')")
 player.locator('.character-card [data-action=edit]').click();player.once('dialog',lambda d:d.accept());player.locator('#delete-character').click();player.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')");assert player.locator('.character-card').count()==0
 player.locator('[data-tab=sala]').click()
 player.locator('#room-select').select_option(RID);player.wait_for_function("document.querySelectorAll('.character-card').length===2")
 player.locator('[data-tab=mesa]').click();assert player.locator('#roll-nick').input_value()=='Aventureira';assert player.locator('#roll-nick').get_attribute('readonly') is not None;player.locator('#roll-mode').select_option('advantage');player.locator('#roll').click();assert 'Aventureira • Vantagem · 2d20' in player.locator('#roll-detail').inner_text();player.locator('[data-tab=sala]').click();player.locator('#cloud-logout').click();player.locator('#cloud-auth').wait_for(state='visible');assert player.locator('#room-panel').is_hidden();assert player.locator('.room-content-card').count()==0
 # Existing deployments without migration 004 keep their local sheets and show activation instructions.
 pendingctx,pending=context();pendingctx.route('https://db.test/rest/v1/campaign_characters*',lambda r:reply(r,{'code':'PGRST205','message':'Tabela ausente'},404))
 login(pending,'player@example.test');pending.locator('#room-select').select_option(RID);pending.locator('#room-sheets-setup').wait_for(state='visible');assert '004' in pending.locator('#room-sheets-status').inner_text();pending.locator('[data-tab=mesa]').click();assert pending.locator('#new-character').is_disabled();pendingctx.close()
 assert not errors,errors
 b.close();print('PASS: two independent accounts; create/join room; hidden/revealed scene; map upload and zoom; NPC reveal; projection; session reload; logout clears shared content; mobile layout. tokens, assigned-player movement by keyboard and drag, search and save-and-present. API simulated; shared initiative and round synchronization; SQL permissions tested separately. Campaign sheets recover in a fresh browser, owner permissions, atomic reaction, HP and Vision persistence, local migration, online roster, shared dice/skill/resistance/damage/Geo rolls and linked token HP/name/conditions.')

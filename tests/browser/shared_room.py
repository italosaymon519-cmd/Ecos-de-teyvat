"""UI integration with simulated Supabase API. Run after npm run build; requires Python Playwright + Chromium.
Database authorization is separately exercised by room-policies.test.js against PostgreSQL/PGlite.
"""
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import json,base64
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]/'dist'
RID='11111111-1111-1111-1111-111111111111';CODE='ABCDEF0123456789ABCDEF0123456789'
rooms=[];members=[];items=[];files={};errors=[]
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
 if path=='/rest/v1/campaign_members':return reply(route,members)
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
 route.fulfill(status=200,content_type='text/javascript' if f.suffix=='.js' else 'text/css' if f.suffix=='.css' else 'text/html',body=f.read_text())
def login(page,email):
 page.goto('https://ecos.test/');page.locator('[data-tab=sala]').click();page.locator('#cloud-email').fill(email);page.locator('#cloud-password').fill('long-password-123');page.locator('#cloud-auth-form button[type=submit]').click();page.locator('#cloud-account').wait_for(state='visible')
def item(page,kind,name,text):
 page.locator('#room-item-kind').select_option(kind);page.locator('#room-item-title').fill(name);page.locator('#room-item-text').fill(text);page.locator('#room-item-form button[type=submit]').click();page.wait_for_function("document.querySelectorAll('.room-content-card').length > 0")
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def context():
  c=b.new_context(viewport={'width':1440,'height':1000});c.route('https://ecos.test/**',static);c.route('https://db.test/**',api);page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));return c,page
 gmctx,gm=context();pc,player=context();login(gm,'gm@example.test')
 gm.locator('#room-create-form [name=roomName]').fill('Mondstadt compartilhada');gm.locator('#room-create-form [name=displayName]').fill('Mestre');gm.locator('#room-create-form button').click();gm.locator('#room-composer').wait_for(state='visible')
 item(gm,'scene','Cena secreta','Texto público sem segredo')
 login(player,'player@example.test');player.locator('#room-join-form [name=code]').fill(CODE);player.locator('#room-join-form [name=displayName]').fill('Aventureira');player.locator('#room-join-form button').click();player.locator('#room-panel').wait_for(state='visible')
 assert player.locator('.room-content-card').count()==0
 assert player.locator('#room-composer').is_hidden()
 gm.locator('[data-room-action=present]').first.click();player.wait_for_function("document.querySelector('#room-stage-title').textContent === 'Cena secreta'",timeout=12000)
 assert player.locator('[data-room-action=edit]').count()==0
 assert player.locator('.room-content-card').count()==1
 gm.locator('[data-room-action=visibility]').first.click();player.locator('#room-refresh').click();player.wait_for_function("document.querySelectorAll('.room-content-card').length === 0")
 # Add a map and exercise its private upload and signing flow.
 gm.locator('#room-item-kind').select_option('map');gm.locator('#room-item-title').fill('Mapa da campanha');gm.locator('#room-item-text').fill('Teyvat')
 png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aS1sAAAAASUVORK5CYII=')
 gm.locator('#room-item-image').set_input_files({'name':'map.png','mimeType':'image/png','buffer':png})
 gm.locator('#room-item-form button[type=submit]').click();gm.wait_for_function("document.querySelectorAll('.room-content-card').length === 2")
 # Image bytes served independently of metadata response.
 for ctx in [gmctx,pc]:ctx.route('https://db.test/storage/v1/object/sign/campaign-images/image.png?token=test',lambda r:r.fulfill(content_type='image/png',body=png))
 gm.locator('.room-content-card').filter(has_text='Mapa da campanha').locator('[data-room-action=present]').click();player.locator('#room-refresh').click()
 player.wait_for_function("document.querySelector('#room-stage-title').textContent === 'Mapa da campanha'")
 player.locator('#room-stage-image').wait_for(state='visible');player.wait_for_function("document.querySelector('#room-stage-image').naturalWidth > 0");player.locator('#room-zoom-in').click();assert player.locator('#room-zoom-label').inner_text()=='150%'
 # NPC creation is another distinct published content kind.
 item(gm,'npc','Mira','Contratante da Guilda')
 gm.wait_for_function("document.querySelectorAll('.room-content-card').length === 3")
 gm.locator('.room-content-card').filter(has_text='Mira').locator('[data-room-action=visibility]').click();player.locator('#room-refresh').click();player.wait_for_function("document.querySelectorAll('.room-content-card').length === 2")
 player.reload();player.locator('[data-tab=sala]').click();player.locator('#room-select').select_option(RID);player.locator('#room-panel').wait_for(state='visible')
 player.set_viewport_size({'width':390,'height':844});assert player.evaluate('document.documentElement.scrollWidth <= innerWidth')
 gm.locator('#room-player-view').check();assert gm.locator('#room-composer').is_hidden();assert gm.locator('.room-content-card').count()==2
 player.locator('#cloud-logout').click();player.locator('#cloud-auth').wait_for(state='visible');assert player.locator('#room-panel').is_hidden();assert player.locator('.room-content-card').count()==0
 assert not errors,errors
 b.close();print('PASS: two independent accounts; create/join room; hidden/revealed scene; map upload and zoom; NPC reveal; projection; session reload; logout clears shared content; mobile layout. API simulated; SQL permissions tested separately.')

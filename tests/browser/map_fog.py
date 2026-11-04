"""Two-account fog controls, overlapping areas, projection, persisted state and map isolation."""
from pathlib import Path
exec(Path(__file__).with_name('shared_room.py').read_text().split('with sync_playwright() as p:')[0])
from PIL import Image
from io import BytesIO
rooms.append({'id':RID,'name':'Exploração','gm_id':'gm'})
members.extend({'room_id':RID,'user_id':u,'display_name':u} for u in ['gm','player'])
MID='40000000-0000-0000-0000-000000000001';OTHER='40000000-0000-0000-0000-000000000002'
for mid in [MID,OTHER]:items.append({'id':mid,'room_id':RID,'kind':'map','title':'Mapa '+mid[-1],'public_text':'Exploração','visible':True,'is_current':mid==MID,'image_path':RID+'/'+mid+'.png'})
for tid,x,kind,owner in [('hero',25,'character','player'),('enemy',75,'enemy',None)]:tokens.append({'id':tid,'room_id':RID,'item_id':MID,'name':tid,'kind':kind,'owner_id':owner,'color':'#d9ba7e','size':4,'x':x,'y':25})
img=BytesIO();Image.new('RGB',(1000,400),'#406b50').save(img,format='PNG');png=img.getvalue()
base_api=api;fog={}
def visible(state,x,y):
 if not state or not state['enabled']:return True
 result=False
 for r in state['regions']:
  if r['x']<=x<=r['x']+r['width'] and r['y']<=y<=r['y']+r['height']:result=r['reveal']
 return result
def fog_api(route):
 req=route.request;u=urlparse(req.url);path=u.path;q=parse_qs(u.query);user=req.headers.get('authorization','').replace('Bearer token-','')
 body=req.post_data_json or {} if req.method=='POST' else {}
 if path=='/rest/v1/campaign_map_fog':
  mid=q['item_id'][0][3:];return reply(route,[fog[mid]] if mid in fog else [])
 if path=='/rest/v1/rpc/save_campaign_map_fog':
  mid=body['map_id'];old=fog.get(mid,{'revision':0})
  if old['revision']!=body['expected_revision']:return reply(route,{'code':'40001','message':'Conflito'},409)
  fog[mid]={'item_id':mid,'room_id':RID,**body['payload'],'revision':old['revision']+1};return reply(route,fog[mid])
 if path=='/rest/v1/campaign_tokens' and req.method=='GET':
  mid=q['item_id'][0][3:];return reply(route,[t for t in tokens if t['item_id']==mid and (user=='gm' or visible(fog.get(mid),t['x'],t['y']))])
 if path=='/rest/v1/campaign_map_settings' or path=='/rest/v1/campaign_map_markers':return reply(route,[])
 return base_api(route)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def context():
  c=b.new_context(viewport={'width':1440,'height':1000});c.route('https://ecos.test/**',static);c.route('https://db.test/**',fog_api)
  c.route('https://db.test/storage/v1/object/sign/campaign-images/image.png?token=test',lambda r:r.fulfill(content_type='image/png',body=png))
  page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());return c,page
 gc,gm=context();pc,player=context();login(gm,'gm@example.test');login(player,'player@example.test')
 gm.wait_for_function("document.querySelectorAll('.board-token').length===2");assert player.locator('#fog-master-controls').is_hidden();assert player.locator('[data-room-image]').count()==0
 gm.locator('#fog-cover-all').click();gm.wait_for_function("document.querySelector('#fog-status').textContent.includes('salva')");player.locator('#fog-refresh').click();player.wait_for_function("document.querySelectorAll('.board-token').length===0");assert player.locator('#fog-overlay').is_visible();assert gm.locator('.board-token').count()==2;shot=Image.open(BytesIO(player.locator('#room-board').screenshot()));assert shot.getpixel((int(shot.width*.05),int(shot.height*.05)))[:3]==(8,16,21)
 def area(mode,x1,y1,x2,y2):
  gm.locator('[data-fog-mode='+mode+']').click();gm.locator('#room-image-wrap').scroll_into_view_if_needed();box=gm.locator('#room-board').bounding_box();gm.mouse.move(box['x']+box['width']*x1,box['y']+box['height']*y1);gm.mouse.down();gm.mouse.move(box['x']+box['width']*x2,box['y']+box['height']*y2,steps=5);gm.mouse.up();gm.wait_for_function("document.querySelector('#fog-status').textContent.includes('salva')")
 area('reveal',.1,.1,.4,.4);player.locator('#fog-refresh').click();player.wait_for_function("document.querySelectorAll('.board-token').length===1");assert player.locator('[data-token-id=hero]').count()==1;assert player.locator('[data-token-id=enemy]').count()==0;shot=Image.open(BytesIO(player.locator('#room-board').screenshot()));assert shot.getpixel((int(shot.width*.15),int(shot.height*.15)))[:3]==(64,107,80)
 gm.locator('#room-player-view').check();gm.wait_for_function("document.querySelectorAll('.board-token').length===1");assert gm.locator('#fog-master-controls').is_hidden();assert gm.locator('#fog-overlay').evaluate("e=>getComputedStyle(e).opacity")=='1';gm.locator('#room-player-view').uncheck()
 area('hide',.2,.2,.3,.3);player.locator('#fog-refresh').click();player.wait_for_function("document.querySelectorAll('.board-token').length===0")
 gm.locator('#fog-reveal-all').click();player.locator('#fog-refresh').click();player.wait_for_function("document.querySelectorAll('.board-token').length===2");assert player.locator('#fog-overlay').is_hidden()
 gm.locator('#fog-cover-all').click();gm.locator('#fog-status').filter(has_text='salva').wait_for();gm.reload();gm.locator('[data-tab=sala]').click();gm.locator('#fog-panel').wait_for(state='visible');gm.wait_for_function("document.querySelector('#fog-summary').textContent.includes('Névoa ativa')")
 gm.locator('[data-room-action=preview][data-id="'+OTHER+'"]').first.click();gm.wait_for_function("document.querySelector('#room-stage-title').textContent.includes('Mapa 2')");gm.wait_for_function("document.querySelector('#fog-summary').textContent.includes('inteiro revelado')");assert gm.locator('#fog-overlay').is_hidden()
 gm.set_viewport_size({'width':390,'height':844});assert gm.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 assert not errors,errors
 print('PASS: cover/reveal/hide rectangles, server-filtered tokens, GM projection, no player map thumbnails, persisted state, per-map isolation and mobile layout.')
 b.close()

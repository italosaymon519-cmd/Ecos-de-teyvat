"""Two-account administration UI; real authorization is verified by room-policies.test.js."""
from pathlib import Path
exec(Path(__file__).with_name('shared_room.py').read_text().split('with sync_playwright() as p:')[0])
rooms.append({'id':RID,'name':'Mondstadt','gm_id':'gm'})
members.extend({'room_id':RID,'user_id':u,'display_name':u} for u in ['gm','player'])
CID='60000000-0000-0000-0000-000000000001'
characters.append({'id':CID,'room_id':RID,'owner_id':'player','revision':1,'deleted':False,'data':{'id':CID,'name':'Amber','element':'Pyro','attrs':[3,2,2,1,1],'hp':33,'maxHp':33,'ee':0,'eReady':0,'qLong':0,'qShort':False,'mark':None,'skills':'Atletismo','talents':'','weapon':'Espada','level':1}})
base_api=api
code=CODE
admin_calls=[]
def admin_api(route):
 global code
 path=urlparse(route.request.url).path;user=route.request.headers.get('authorization','').replace('Bearer token-','')
 body=route.request.post_data_json or {} if route.request.method=='POST' else {}
 if path=='/rest/v1/rpc/campaign_invite':return reply(route,code)
 if path.endswith('/rotate_campaign_invite'):
  code='1'*32;admin_calls.append('rotate');return reply(route,code)
 if path.endswith('/transfer_campaign_character'):
  row=characters[0];assert body['expected_revision']==row['revision'];row['owner_id']=body['new_owner'];row['revision']+=1;admin_calls.append('transfer');return reply(route,row)
 if path.endswith('/remove_campaign_member'):
  members[:]=[m for m in members if m['user_id']!=body['member_id']]
  for r in characters:
   if r['owner_id']==body['member_id']:r['owner_id']='gm';r['revision']+=1
  code='2'*32;admin_calls.append('remove');return reply(route,code)
 if path=='/rest/v1/campaign_members' and not any(m['user_id']==user for m in members):return reply(route,[])
 if path in ['/rest/v1/campaign_characters','/rest/v1/campaign_items'] and not any(m['user_id']==user for m in members):return reply(route,[])
 return base_api(route)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def context():
  c=b.new_context(viewport={'width':1440,'height':1000});c.route('https://ecos.test/**',static);c.route('https://db.test/**',admin_api);page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept());return c,page
 gc,gm=context();pc,player=context();login(gm,'gm@example.test');login(player,'player@example.test')
 gm.locator('#room-admin').wait_for(state='visible');assert player.locator('#room-admin').is_hidden()
 gm.locator('#room-admin summary').click();gm.wait_for_function("document.querySelector('#room-admin-sheet').options.length===1")
 gm.locator('#room-admin-owner').select_option('gm');gm.locator('#room-admin-transfer').click();gm.wait_for_function("document.querySelector('#room-admin [role=status]').textContent.includes('Ficha transferida')")
 player.locator('#room-refresh').click();player.locator('[data-tab=mesa]').click();player.wait_for_function("document.querySelector('.character-card [data-action=edit]').disabled")
 gm.locator('#room-admin-owner').select_option('player');gm.locator('#room-admin-transfer').click();gm.wait_for_function("document.querySelector('#room-admin [role=status]').textContent.includes('Ficha transferida')")
 gm.locator('#room-admin-rotate').click();gm.wait_for_function("document.querySelector('#room-invite-value').value==='11111111111111111111111111111111'")
 gm.locator('#room-player-view').check();assert gm.locator('#room-admin').is_hidden();gm.locator('#room-player-view').uncheck();assert gm.locator('#room-admin').is_visible()
 gm.locator('#room-admin-remove').click();gm.wait_for_function("document.querySelector('#room-admin [role=status]').textContent.includes('Participante removido')")
 player.locator('[data-tab=sala]').click();player.locator('#room-refresh').click();player.locator('#room-panel').wait_for(state='hidden');assert player.locator('#cloud-account').is_visible();assert characters[0]['owner_id']=='gm';assert admin_calls==['transfer','transfer','rotate','remove']
 gm.set_viewport_size({'width':390,'height':844});assert gm.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
 assert not errors,errors
 print('PASS: GM-only administration, ownership transfer, player read-only refresh, invite rotation, removal clears room without logout, mobile layout.')
 b.close()

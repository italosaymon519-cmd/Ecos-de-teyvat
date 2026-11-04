"""Repeatable idle-room benchmark with simulated API and a populated campaign."""
from pathlib import Path
support=Path(__file__).with_name('shared_room.py').read_text().split('with sync_playwright() as p:')[0]
exec(support)
rooms.append({'id':RID,'name':'Mesa de desempenho','gm_id':'gm'})
members.extend({'room_id':RID,'user_id':u,'display_name':u} for u in ['gm','player'])
items.append({'id':'map1','room_id':RID,'kind':'map','title':'Mapa','public_text':'','visible':True,'is_current':True,'image_path':RID+'/map.png'})
for i in range(40):
 cid='60000000-0000-0000-0000-'+str(i+1).zfill(12)
 characters.append({'id':cid,'room_id':RID,'owner_id':'gm','revision':1,'deleted':False,'data':{'id':cid,'name':'Herói '+str(i),'element':'Geo','attrs':[3,2,2,1,1],'hp':33,'maxHp':33,'ee':0,'eReady':0,'qLong':0,'qShort':False,'mark':None,'skills':'Atletismo','talents':'','weapon':'Espada','level':1,'campaignClock':{'id':'battle','round':1}}})
for i in range(100):tokens.append({'id':'token'+str(i),'room_id':RID,'item_id':'map1','name':'Token '+str(i),'kind':'enemy','owner_id':None,'color':'#d9ba7e','size':4,'x':5+i%10*9,'y':5+i//10*9})
combatants=[{'id':t['id'],'name':t['name'],'initiative':i,'bonus':0,'enabled':True} for i,t in enumerate(tokens)]
combats[RID]={'room_id':RID,'combat_id':'battle','round':1,'running':True,'active_id':combatants[-1]['id'],'combatants':combatants,'revision':1}
imageRequests={'signed':0,'loaded':0}
base_api=api
def counted_api(route):
 if urlparse(route.request.url).path.startswith('/storage/v1/object/sign/'):
  imageRequests['signed']+=1;return reply(route,{'signedURL':'/object/sign/campaign-images/image.png?token='+str(imageRequests['signed'])})
 return base_api(route)
def image_bytes(route):
 imageRequests['loaded']+=1;route.fulfill(content_type='image/png',body=png)
png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aS1sAAAAASUVORK5CYII=')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1280,'height':900});ctx.route('https://ecos.test/**',static);ctx.route('https://db.test/**',counted_api);ctx.route('https://db.test/storage/v1/object/sign/campaign-images/image.png?*',image_bytes);page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 login(page,'gm@example.test');page.wait_for_function("document.querySelectorAll('.board-token').length===100&&document.querySelectorAll('.character-card').length===40")
 page.wait_for_function("document.querySelector('#room-stage-image').naturalWidth>0")
 page.evaluate('''() => {window.idle={added:0,removed:0,writes:0,longTasks:0};const areas=['#characters','#character-list','#room-token-layer','#room-token-list','#combat-order','#room-presence'];window.watch=new MutationObserver(ms=>{for(const m of ms){idle.added+=m.addedNodes.length;idle.removed+=m.removedNodes.length;}});areas.forEach(s=>watch.observe(document.querySelector(s),{childList:true,subtree:true}));const original=Storage.prototype.setItem;Storage.prototype.setItem=function(...args){idle.writes++;return original.apply(this,args)};new PerformanceObserver(list=>{idle.longTasks+=list.getEntries().length}).observe({type:'longtask'});window.keptToken=document.querySelector('.board-token');}''')
 page.wait_for_timeout(8500)
 result=page.evaluate('({...idle,tokenPreserved:keptToken.isConnected})');print('IDLE_ROOM',result)
 if '--assert' in __import__('sys').argv:
  assert result['added']==0 and result['removed']==0,result
  assert result['writes']==0,result
  assert result['tokenPreserved'],result
 # A one-sheet server change replaces only that character's two views.
 page.evaluate("window.cards=[...document.querySelectorAll('.character-card')];window.sheets=[...document.querySelectorAll('.sheet-row')]")
 characters[0]['data']['hp']=30;characters[0]['revision']+=1
 page.locator('#room-refresh').click();page.wait_for_function("document.querySelector('.character-card .health-caption').textContent.includes('30')")
 preserved=page.evaluate('cards.slice(1).every(n=>n.isConnected)&&sheets.slice(1).every(n=>n.isConnected)');assert preserved,'Unchanged character views were rebuilt'
 # A token move preserves the original DOM node, and an expired URL does not reload a decoded map.
 tokens[0]['x']=17;page.evaluate('const now=Date.now;Date.now=()=>now()+60000');page.locator('#room-refresh').click();page.wait_for_function("document.querySelector('[data-token-id=token0]').style.left==='17%'")
 assert page.evaluate('keptToken.isConnected');assert imageRequests=={'signed':1,'loaded':1},imageRequests
 print('PASS: unchanged sheets and tokens retain their nodes; a displayed map is not signed or downloaded again on URL expiry.')
 assert not errors,errors
 b.close()

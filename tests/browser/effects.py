"""Two-account effect UI; PostgreSQL clock/permissions are tested separately."""
from pathlib import Path
exec(Path(__file__).with_name('shared_room.py').read_text().split('with sync_playwright() as p:')[0])
import copy
BATTLE='50000000-0000-0000-0000-000000000001';HERO='60000000-0000-0000-0000-000000000001';GMH='60000000-0000-0000-0000-000000000002';MID='11111111-1111-1111-1111-111111111112'
rooms.append({'id':RID,'name':'Combate com efeitos','gm_id':'gm'});members.extend({'room_id':RID,'user_id':u,'display_name':n} for u,n in [('gm','Mestre'),('player','Aventureira')]);items.append({'id':MID,'room_id':RID,'kind':'map','title':'Campo','public_text':'','visible':True,'is_current':True,'image_path':RID+'/map.png'})
for cid,name,element,owner in [(HERO,'Heroína','Geo','player'),(GMH,'Mestre Pyro','Pyro','gm')]:characters.append({'id':cid,'room_id':RID,'owner_id':owner,'revision':1,'deleted':False,'data':{'id':cid,'name':name,'element':element,'attrs':[3,2,2,1,1],'hp':33,'maxHp':33,'ee':0,'eReady':0,'qLong':0,'qShort':False,'mark':None,'skills':'Atletismo','talents':'','weapon':'Espada','level':1,'conditions':'Anotação livre','campaignClock':{'id':BATTLE,'round':1}}})
combatants=[{'id':'40000000-0000-0000-0000-000000000001','name':'Mestre Pyro','bonus':2,'initiative':18,'enabled':True,'character_id':GMH},{'id':'40000000-0000-0000-0000-000000000002','name':'Heroína','bonus':2,'initiative':12,'enabled':True,'character_id':HERO}]
combats[RID]={'room_id':RID,'combat_id':BATTLE,'combatants':combatants,'active_id':combatants[0]['id'],'round':1,'running':True,'revision':1}
tokens.append({'id':'hero-token','room_id':RID,'item_id':MID,'character_id':HERO,'name':'Heroína','kind':'character','owner_id':'player','color':'#d9ba7e','size':4,'x':40,'y':40})
base_api=api

def effects_api(route):
 req=route.request;path=urlparse(req.url).path;user=req.headers.get('authorization','').replace('Bearer token-','')
 try:body=req.post_data_json or {}
 except:body={}
 if path=='/rest/v1/rpc/campaign_effects_ready':return reply(route,True)
 if path=='/rest/v1/rpc/save_campaign_character':
  old=next((r for r in characters if r['id']==body['character_id']),None)
  if old and old['owner_id']!=user and user!='gm':return reply(route,{},403)
  if old and old['revision']!=body['expected_revision']:return reply(route,{'code':'40001','message':'Ficha alterada'},409)
  if body['payload'] is not None:
   data=copy.deepcopy(body['payload']);battle=combats[RID];previous={e['id']:e for e in (old['data'].get('effects',[]) if old else [])}
   for effect in data.get('effects',[]):
    prior=previous.get(effect['id']);effect['remaining']=prior['remaining'] if prior else effect['rounds'];effect['combatId']=prior['combatId'] if prior else battle['combat_id'] if battle['running'] and effect['rounds'] is not None else None
   if data.get('effects'):data['effectClock']={'id':battle['combat_id'] if battle['running'] else None,'round':battle['round'],'running':battle['running']}
   else:data.pop('effectClock',None)
   body['payload']=data
  if old:old.update(data=body['payload'] if body['payload'] is not None else old['data'],deleted=body['payload'] is None,revision=old['revision']+1);return reply(route,old)
 if path=='/rest/v1/rpc/save_campaign_combat':
  old=combats[RID];next_battle={**body['payload'],'room_id':RID,'revision':old['revision']+1}
  if user!='gm':return reply(route,{},403)
  if old['revision']!=body['expected_revision']:return reply(route,{'message':'Conflito'},409)
  boundary=old['combat_id']!=next_battle['combat_id'] or old['round']!=next_battle['round'] or old['running']!=next_battle['running']
  if boundary:
   for row in characters:
    data=row['data'];old_clock=data.get('effectClock',{});updated=[]
    for effect in data.get('effects',[]):
     e=copy.deepcopy(effect)
     if e['rounds'] is None:updated.append(e);continue
     if old['running'] and not next_battle['running']:continue
     if next_battle['running']:
      if e['combatId'] and e['combatId']!=next_battle['combat_id']:continue
      if e['combatId']==next_battle['combat_id'] and old_clock.get('id')==next_battle['combat_id']:e['remaining']-=max(0,next_battle['round']-old_clock['round'])
      e['combatId']=next_battle['combat_id']
     if e['remaining']>0:updated.append(e)
    if data.get('effects'):
     data['effects']=updated
     if updated:data['effectClock']={'id':next_battle['combat_id'],'round':next_battle['round'],'running':next_battle['running']}
     else:data.pop('effectClock',None)
     row['revision']+=1
  combats[RID]=next_battle;return reply(route,next_battle)
 return base_api(route)

png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aS1sAAAAASUVORK5CYII=')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 def context(email):
  ctx=b.new_context(viewport={'width':1440,'height':1000});ctx.route('https://ecos.test/**',static);ctx.route('https://db.test/**',effects_api);ctx.route('https://db.test/storage/v1/object/sign/campaign-images/image.png?token=test',lambda r:r.fulfill(content_type='image/png',body=png));page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));login(page,email);page.wait_for_function("[...document.querySelectorAll('.character-card')].some(n=>n.textContent.includes('Heroína'))");return ctx,page
 gc,gm=context('gm@example.test');pc,player=context('player@example.test')
 player.locator('[data-tab=mesa]').click();hero=player.locator('.character-card').filter(has_text='Heroína');hero.locator('[data-action=effects]').click();player.locator('#effect-fields').wait_for(state='visible');player.wait_for_function("!document.querySelector('#effect-fields').disabled")
 def add(kind,name,amount=None,rounds='2',permanent=False):
  player.locator('#effects-form [name=kind]').select_option(kind);player.locator('#effects-form [name=name]').fill(name)
  if amount is not None:player.locator('#effects-form [name=amount]').fill(str(amount))
  player.locator('#effects-form [name=permanent]').set_checked(permanent)
  if not permanent:player.locator('#effects-form [name=rounds]').fill(rounds)
  player.locator('#effects-form [type=submit]').click();player.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')")
 add('condition','Congelado');add('shield','Proteção',5);add('defense','Guarda',2,'1');add('check','Inspiração',3);add('damage','Força extra',2);add('condition','Marca narrativa',permanent=True)
 player.locator('#effects-close').click();assert 'DEF 14' in hero.inner_text()
 player.evaluate('Math.random=()=>0.999');hero.locator('[data-vision-action=activate]').click();hero.locator('[data-action=damage]').click();player.locator('#damage-form [name=amount]').fill('8');player.locator('#damage-form [type=submit]').click();assert '33' in hero.locator('.health-caption').inner_text();assert 'Escudo: 3' in hero.inner_text();assert 'Proteção' not in hero.locator('.character-effects').inner_text()
 hero.locator('[data-action=skills]').click();player.evaluate("Math.random=()=>0.45;document.querySelector('[data-skill-roll=Atletismo][data-id=\\\""+HERO+"\\\"]').click()")
 assert '= 18' in player.locator('.sheet-row').filter(has_text='Heroína').locator('.skill-roll-result').inner_text()
 player.locator('[data-tab=mesa]').click();hero.locator('.artifact-panel').evaluate('(n)=>n.open=true');hero.locator('[data-artifact-action=plume]').click();player.locator('#outgoing-form [name=critical]').check();player.evaluate("Math.random=()=>0.45;document.querySelector('#outgoing-form [type=submit]').click()");assert '+ 2 efeitos = 14' in player.locator('#outgoing-result').inner_text();player.locator('#outgoing-close').click()
 gm.wait_for_function("document.querySelector('[data-token-id=hero-token]').textContent.includes('Congelado')",timeout=12000);gm.wait_for_function("document.querySelector('#combat-order').textContent.includes('Congelado')",timeout=12000)
 player.locator('.character-card').filter(has_text='Mestre Pyro').locator('[data-action=effects]').click();assert 'Mestre Pyro' in player.locator('#effects-title').inner_text();assert player.locator('#effects-form [type=submit]').is_disabled();player.locator('#effects-close').click()
 def next_turn(round_number):
  gm.locator('#combat-next').click();gm.wait_for_function("document.querySelector('#combat-round').textContent==='rodada "+str(round_number)+"'");gm.wait_for_function("!document.querySelector('#combat-next').disabled")
 next_turn(1);assert '2 rodada(s)' in hero.locator('.character-effects').inner_text();next_turn(2)
 player.wait_for_function("document.querySelector('#round').textContent==='2'&&!document.querySelector('[data-action=damage][data-id=\\\""+HERO+"\\\"]').disabled",timeout=15000)
 assert 'DEF 12' in hero.inner_text();assert 'Congelado · 1 rodada(s)' in hero.locator('.character-effects').inner_text();assert 'Guarda' not in hero.locator('.character-effects').inner_text()
 next_turn(2);next_turn(3);player.wait_for_function("document.querySelector('#round').textContent==='3'&&!document.querySelector('[data-action=damage][data-id=\\\""+HERO+"\\\"]').disabled",timeout=15000)
 player.wait_for_function("document.querySelector('#campaign-save-status').textContent.includes('Todas as fichas salvas')&&![...document.querySelectorAll('.character-card')].find(n=>n.textContent.includes('Heroína')).querySelector('.character-effects').textContent.includes('Congelado')",timeout=15000)
 assert 'Congelado' not in hero.locator('.character-effects').inner_text();assert 'Marca narrativa' in hero.locator('.character-effects').inner_text()
 hero.locator('[data-action=skills]').click();player.evaluate("Math.random=()=>0.45;document.querySelector('[data-skill-roll=Atletismo][data-id=\\\""+HERO+"\\\"]').click()");assert '= 15' in player.locator('.sheet-row').filter(has_text='Heroína').locator('.skill-roll-result').inner_text()
 third,returned=context('player@example.test');returned.locator('[data-tab=mesa]').click();returned.wait_for_function("document.querySelector('#round').textContent==='3'");assert 'Marca narrativa' in returned.locator('.character-card').filter(has_text='Heroína').inner_text();third.close()
 player.locator('[data-tab=sala]').click();player.wait_for_function("!document.querySelector('[data-token-id=hero-token]').textContent.includes('Congelado')",timeout=12000)
 player.set_viewport_size({'width':390,'height':844});assert player.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 b.close();print('PASS: owner/GM effect editor, timed conditions, round wrap and reload, persistent effects, shield+Geo absorption, defense/test/critical damage bonuses, linked tokens and initiative, mobile.')

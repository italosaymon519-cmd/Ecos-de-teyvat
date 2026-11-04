import {updateHTML,updateText} from './dom-updates.js';
const $=s=>document.querySelector(s),esc=t=>String(t??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function createRoomPresence({cloud}){
 const sessionId=crypto.randomUUID();let room=null,members=[],online=new Set(),generation=0,loading=false,lastBeat=0,known=false;
 function draw(){const summary=$('#campaign-presence-summary');summary.hidden=!room;const count=members.filter(m=>online.has(m.user_id)).length;updateText(summary,known?count+' online · Ver participantes':'Ver presença na mesa');updateHTML($('#room-presence'),members.map(m=>`<span class="presence-person ${known&&online.has(m.user_id)?'is-online':''}"><span aria-hidden="true">●</span> ${esc(m.display_name)}${m.user_id===room?.gm_id?' · Mestre':''}<small>${known?(online.has(m.user_id)?'Online':'Offline'):'Presença indisponível'}</small></span>`).join(''));if(known)updateText($('#room-presence-status'),count+' online · a presença é atualizada automaticamente. Ao fechar a mesa, a indicação pode levar até 90 segundos para mudar.');}
 async function refresh(force=false){if(!room||loading||!cloud.user)return;loading=true;const version=generation,id=room.id;try{if(force||Date.now()-lastBeat>=20000){await cloud.rpc('campaign_heartbeat',{target_room:id,session_id:sessionId});if(version!==generation)return;lastBeat=Date.now();}if(document.hidden)return;const rows=await cloud.presence(id);if(version!==generation)return;online=new Set(rows.map(r=>r.user_id));known=true;draw();}catch(e){if(version!==generation)return;known=false;draw();$('#room-presence-status').textContent=e.status===404||['PGRST202','PGRST205','42P01'].includes(e.code)?'A presença aguarda a atualização 004 no Supabase.':'Não foi possível atualizar quem está online. Tentaremos novamente.';}finally{if(version===generation)loading=false;}}
 function leave(){if(room&&cloud.user)cloud.leavePresence(room.id,sessionId).catch(()=>{});}
 function setRoom(next){leave();generation++;room=next;members=[];online=new Set();known=false;lastBeat=0;loading=false;$('#campaign-presence-summary').hidden=!room;$('#room-presence').replaceChildren();$('#room-presence-status').textContent='';if(room)refresh(true);}
 function setMembers(next){members=next;draw();}
 $('#campaign-presence-summary').onclick=()=>{document.querySelector('[data-tab=sala]').click();$('#room-presence').scrollIntoView({block:'center'});};
 setInterval(()=>{if(room)refresh();},10000);
 window.addEventListener('pagehide',leave);window.addEventListener('pageshow',()=>{if(room)refresh(true);});window.addEventListener('online',()=>refresh(true));document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh(true);});
 return {setRoom,setMembers,refresh};
}

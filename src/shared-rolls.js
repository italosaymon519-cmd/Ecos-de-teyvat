import {RollFeed} from './roll-feed.js';
import {updateText,updateKeyedHTML} from './dom-updates.js';
const $=s=>document.querySelector(s),esc=t=>String(t??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={dice:'Dados',skill:'Perícia',resistance:'Resistência',damage:'Dano',vision:'Visão'};
export function createSharedRolls({cloud}){
 let context=null;
 function status(text){updateText($('#room-rolls-status'),text);updateText($('#mesa-rolls-status'),text);$('#room-rolls-setup').hidden=!text.includes('005');}
 function entries(rows){return rows.map(r=>({key:r.id,version:JSON.stringify(r),html:()=>`<li class="shared-roll-entry"><header><strong>${esc(r.actor_name)}</strong><span>${esc(labels[r.kind]||r.kind)}${r.character_name?' · '+esc(r.character_name):''}</span><time>${esc(new Date(r.created_at).toLocaleTimeString('pt-BR'))}</time></header><p>${esc(r.detail)}</p><b class="shared-roll-total">${Number(r.total)}</b></li>`}));}
 const feed=new RollFeed({cloud,status,update:(rows,pending)=>{const list=$('#room-rolls-list'),scrolled=list.scrollTop>5,oldHeight=list.scrollHeight,oldTop=list.scrollTop;updateKeyedHTML(list,entries(rows),'<li class="muted">As rolagens da campanha aparecerão aqui para todos.</li>');if(scrolled)list.scrollTop=oldTop+list.scrollHeight-oldHeight;updateKeyedHTML($('#mesa-rolls-list'),entries(rows.slice(0,3)),'<li class="muted">Nenhuma rolagem compartilhada ainda.</li>');$('#room-rolls-discard').hidden=!pending;updateText($('#room-rolls-pending'),pending?pending+' rolagem(ns) aguardando envio. Não limpe os dados deste navegador.':'');}});
 function setRoom(room){context=room?{roomId:room.id,userId:cloud.user.id}:null;$('#mesa-room-rolls').hidden=!context;feed.setContext(context);if(context){status('Carregando histórico da sala…');feed.refresh();}else status('');}
 window.addEventListener('ecos-share-roll',e=>{const roll=e.detail;if(!context||roll?.roomId!==context.roomId||roll.userId!==context.userId)return;feed.enqueue(roll.id,roll.payload);});
 $('#room-rolls-discard').onclick=()=>{if(confirm('Descartar os resultados que ainda aguardam envio? Os já publicados continuam no histórico.'))feed.clearPending();};$('#room-rolls-refresh').onclick=()=>feed.refresh();$('#mesa-rolls-open').onclick=()=>{document.querySelector('[data-tab=sala]').click();$('#room-rolls').scrollIntoView({block:'center'});};
 setInterval(()=>{if(context&&!document.hidden)feed.refresh();},3000);
 window.addEventListener('online',()=>{if(context)feed.refresh();});window.addEventListener('beforeunload',e=>{if(feed.pending.length){e.preventDefault();e.returnValue='';}});
 return {setRoom,refresh:()=>feed.refresh()};
}

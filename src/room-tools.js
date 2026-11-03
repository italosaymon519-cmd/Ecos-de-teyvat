export function filterRoomItems(items,{query='',kind='',visibility='',player=false}={}) {
 const normalize=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
 const terms=normalize(query).trim().split(/\s+/).filter(Boolean);
 return items.filter(i=>(!player||i.visible)&&(!kind||i.kind===kind)&&(player||!visibility||visibility==='visible'&&i.visible||visibility==='hidden'&&!i.visible||visibility==='current'&&i.is_current)&&terms.every(t=>normalize(i.title+' '+i.public_text).includes(t)));
}
export function imageFileError(file){if(!file)return '';if(!['image/png','image/jpeg','image/webp'].includes(file.type))return 'Escolha uma imagem PNG, JPG ou WebP.';if(file.size>15728640)return 'A imagem deve ter até 15 MB.';return '';}
export function clampZoom(value){return Math.max(1,Math.min(5,value));}

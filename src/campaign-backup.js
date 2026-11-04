export const BACKUP_FORMAT='ecos-campaign-backup',BACKUP_VERSION=1,MAX_BACKUP_BYTES=100*1024*1024,MAX_IMAGE_BYTES=64*1024*1024;
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const limits={items:500,characters:500,tokens:2000,settings:500,markers:5000,rolls:10000};
const fail=message=>{throw Error(message);};
export async function digest(bytes){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
export function imageType(bytes){if(bytes[0]===137&&bytes[1]===80&&bytes[2]===78&&bytes[3]===71&&bytes[4]===13&&bytes[5]===10&&bytes[6]===26&&bytes[7]===10)return 'image/png';if(bytes[0]===255&&bytes[1]===216&&bytes[2]===255)return 'image/jpeg';if(String.fromCharCode(...bytes.slice(0,4))==='RIFF'&&String.fromCharCode(...bytes.slice(8,12))==='WEBP')return 'image/webp';fail('Imagem do backup não é PNG, JPG ou WebP.');}
export function encodeBytes(bytes){let str='';for(let i=0;i<bytes.length;i+=32768)str+=String.fromCharCode(...bytes.subarray(i,i+32768));return btoa(str);}
export function decodeBytes(base64){if(typeof base64!=='string'||base64.length>21*1024*1024||(base64.length%4!==0||!/^[A-Za-z0-9+/]*={0,2}$/.test(base64)))fail('Imagem codificada inválida.');return Uint8Array.from(atob(base64),c=>c.charCodeAt(0));}
export function validateMetadata(data,validateCharacter=()=>{}){
 if(!data||typeof data.name!=='string'||!data.name.trim()||data.name.length>100)fail('Nome da campanha inválido.');
 for(const [key,max] of Object.entries(limits))if(!Array.isArray(data[key])||data[key].length>max)fail('Coleção inválida ou acima do limite: '+key);
 if(new TextEncoder().encode(JSON.stringify(data)).length>16*1024*1024)fail('Os dados da campanha excedem 16 MB.');
 const ids={};for(const key of ['items','characters','tokens','markers','rolls']){ids[key]=new Map();for(const row of data[key]){if(!row||!uuid.test(row.id)||ids[key].has(row.id))fail('Identificador inválido ou duplicado: '+key);ids[key].set(row.id,row);}}
 const map=id=>{if(ids.items.get(id)?.kind!=='map')fail('Referência a mapa inválida.');};
 if(data.items.filter(i=>i.is_current).length>1)fail('Mais de uma cena está em apresentação.');
 for(const item of data.items){if(!['map','scene','npc'].includes(item.kind)||typeof item.title!=='string'||typeof item.public_text!=='string'||typeof item.visible!=='boolean'||typeof item.is_current!=='boolean'||item.is_current&&!item.visible||item.image_path!==null&&typeof item.image_path!=='string')fail('Conteúdo de campanha inválido.');}
 if(data.characters.filter(c=>!c.deleted).length>50)fail('O limite é de 50 fichas ativas por campanha.');
 for(const c of data.characters){if(typeof c.deleted!=='boolean'||c.data?.id!==c.id)fail('Ficha do backup inválida.');validateCharacter(c.data);}
 for(const t of data.tokens){map(t.item_id);if(t.character_id&&!ids.characters.has(t.character_id))fail('Token ligado a uma ficha ausente.');}
 const settings=new Set();for(const s of data.settings){map(s.item_id);if(settings.has(s.item_id))fail('Configuração de mapa duplicada.');settings.add(s.item_id);}
 for(const m of data.markers)map(m.item_id);
 if(data.combat){if(!uuid.test(data.combat.combat_id)||!Array.isArray(data.combat.combatants)||data.combat.combatants.length>200)fail('Combate inválido.');const seen=new Set();for(const c of data.combat.combatants){if(!uuid.test(c.id)||seen.has(c.id)||c.character_id&&!ids.characters.has(c.character_id))fail('Participante de combate inválido.');seen.add(c.id);}if(data.combat.active_id&&!seen.has(data.combat.active_id))fail('Turno ativo inválido.');}
 return data;
}
export async function validateBackup(backup,{validateCharacter,progress=()=>{}}={}){
 if(backup?.format!==BACKUP_FORMAT||backup.version!==BACKUP_VERSION)fail('Selecione um backup de campanha Ecos de Teyvat, versão 1.');
 validateMetadata(backup.data,validateCharacter);if(!Array.isArray(backup.assets)||backup.assets.length>500)fail('Lista de imagens inválida.');
 const paths=new Set(),assetIds=new Set();let size=0;
 for(let i=0;i<backup.assets.length;i++){const a=backup.assets[i];if(!a||!uuid.test(a.id)||assetIds.has(a.id)||typeof a.path!=='string'||paths.has(a.path))fail('Imagem duplicada ou inválida.');paths.add(a.path);assetIds.add(a.id);const bytes=decodeBytes(a.base64);size+=bytes.length;if(bytes.length>15728640||size>MAX_IMAGE_BYTES)fail('Imagens excedem 15 MB por arquivo ou 64 MB no total.');if(imageType(bytes)!==a.mime||await digest(bytes)!==a.sha256)fail('Uma imagem foi alterada ou está incompleta.');progress(`Verificando imagem ${i+1}/${backup.assets.length}…`);await new Promise(r=>setTimeout(r,0));}
 const used=new Set(backup.data.items.map(i=>i.image_path).filter(Boolean));for(const path of used)if(!paths.has(path))fail('O backup não contém todas as imagens da campanha.');for(const path of paths)if(!used.has(path))fail('O backup contém uma imagem sem conteúdo associado.');return {images:paths.size,imageBytes:size,characters:backup.data.characters.filter(c=>!c.deleted).length,archived:backup.data.characters.filter(c=>c.deleted).length,items:backup.data.items.length,tokens:backup.data.tokens.length,markers:backup.data.markers.length,rolls:backup.data.rolls.length};
}
export function restorePayload(backup,roomId,newId=()=>crypto.randomUUID()){
 if(!uuid.test(roomId))fail('Sala de destino inválida.');const data=structuredClone(backup.data),chars=new Map(data.characters.map(c=>[c.id,newId()])),items=new Map(data.items.map(i=>[i.id,newId()])),tokens=new Map(data.tokens.map(t=>[t.id,newId()]));
 const images=new Map(backup.assets.map(a=>[a.path,roomId+'/'+a.id+'.'+({'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}[a.mime])]));
 const deleted=new Set(data.characters.filter(c=>c.deleted).map(c=>c.id));
 for(const c of data.characters){c.id=chars.get(c.id);c.data.id=c.id;delete c.owner_id;delete c.room_id;}
 for(const i of data.items){i.id=items.get(i.id);i.image_path=i.image_path?images.get(i.image_path):null;delete i.room_id;}
 for(const t of data.tokens){t.id=tokens.get(t.id);t.item_id=items.get(t.item_id);t.character_id=t.character_id&&!deleted.has(t.character_id)?chars.get(t.character_id):null;delete t.owner_id;delete t.room_id;}
 for(const s of data.settings){s.item_id=items.get(s.item_id);delete s.room_id;}
 for(const m of data.markers){m.id=newId();m.item_id=items.get(m.item_id);delete m.room_id;delete m.created_by;}
 for(const r of data.rolls){r.id=newId();r.character_id=chars.get(r.character_id)||null;delete r.room_id;delete r.actor_id;}
 if(data.combat){const entries=new Map(data.combat.combatants.map(c=>[c.id,tokens.get(c.id)||newId()]));for(const c of data.combat.combatants){c.id=entries.get(c.id);c.character_id=c.character_id&&!deleted.has(c.character_id)?chars.get(c.character_id):null;}data.combat.active_id=entries.get(data.combat.active_id)||null;delete data.combat.room_id;}
 return {data,images};
}

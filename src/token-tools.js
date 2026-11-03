export function boardPosition(rect,x,y){if(rect.width<=0||rect.height<=0)throw Error('Aguarde o mapa carregar.');return {x:Math.max(0,Math.min(100,(x-rect.left)/rect.width*100)),y:Math.max(0,Math.min(100,(y-rect.top)/rect.height*100))};}
export function canMoveToken(token,userId,gmId){return Boolean(userId&&(userId===gmId||token.owner_id===userId));}
export function tokenInitials(name){return String(name).trim().split(/\s+/).slice(0,2).map(s=>s[0]||'').join('').toUpperCase();}

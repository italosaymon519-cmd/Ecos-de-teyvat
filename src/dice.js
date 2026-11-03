export const rollModes={normal:'Normal',advantage:'Vantagem',disadvantage:'Desvantagem',critical:'Crítico (dano)'};
export function rollDice(sides,modifier=0,mode='normal',random=Math.random){
 if(![4,6,8,10,12,20].includes(sides)||!Object.hasOwn(rollModes,mode)||!Number.isInteger(modifier)||Math.abs(modifier)>100)throw Error('Configuração de rolagem inválida.');
 if(['advantage','disadvantage'].includes(mode)&&sides!==20)throw Error('Vantagem e desvantagem usam 2d20.');
 const count=mode==='normal'?1:2,rolls=Array.from({length:count},()=>Math.floor(random()*sides)+1);
 const chosen=mode==='advantage'?Math.max(...rolls):mode==='disadvantage'?Math.min(...rolls):mode==='critical'?rolls.reduce((a,b)=>a+b,0):rolls[0];
 return {sides,modifier,mode,rolls,chosen,total:chosen+modifier,natural:sides===20&&mode!=='critical'?(chosen===20?'critical':chosen===1?'failure':null):null};
}
export function describeRoll(result,nick){const {sides,modifier,mode,rolls,chosen,total,natural}=result,sign=modifier>=0?'+':'−';
 const dice=rolls.length+'d'+sides,detail=rolls.length>1?' ['+rolls.join(', ')+']':'';
 const pick=['advantage','disadvantage'].includes(mode)?' → '+chosen:'';
 const outcome=natural==='critical'?' · 20 natural: crítico em ataques':natural==='failure'?' · 1 natural: falha em ataques':'';
 return `${nick} • ${rollModes[mode]} · ${dice}${detail}${rolls.length===1?': '+chosen:''}${pick} ${sign} ${Math.abs(modifier)} = ${total}${outcome}`;
}

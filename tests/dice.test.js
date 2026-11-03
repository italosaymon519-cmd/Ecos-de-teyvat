import test from 'node:test';import assert from 'node:assert/strict';import {rollDice,describeRoll} from '../src/dice.js';
const sequence=(...v)=>()=>v.shift();
test('advantage picks the largest natural die and adds modifier once',()=>{const r=rollDice(20,3,'advantage',sequence(0,.9999));assert.deepEqual(r.rolls,[1,20]);assert.equal(r.chosen,20);assert.equal(r.total,23);assert.equal(r.natural,'critical');});
test('disadvantage ignores a discarded natural twenty',()=>{const r=rollDice(20,4,'disadvantage',sequence(.9999,0));assert.equal(r.total,5);assert.equal(r.natural,'failure');});
test('critical damage doubles dice, not the fixed modifier',()=>{const r=rollDice(8,3,'critical',sequence(.5,.999));assert.deepEqual(r.rolls,[5,8]);assert.equal(r.total,16);assert.equal(r.natural,null);assert.match(describeRoll(r,'Mestre'),/^Mestre • Crítico \(dano\) · 2d8 \[5, 8\] \+ 3 = 16$/);});
test('normal d12 and validation',()=>{assert.equal(rollDice(12,-2,'normal',()=>.999).total,10);assert.throws(()=>rollDice(8,0,'advantage'));assert.throws(()=>rollDice(20,101));});

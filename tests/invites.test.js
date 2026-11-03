import test from 'node:test';import assert from 'node:assert/strict';import {inviteCode,invitationUrl} from '../src/invites.js';
const code='ABCDEF0123456789ABCDEF0123456789';
test('accepts full invite links and codes, preserving all 32 characters',()=>{assert.equal(inviteCode('https://comfy-jalebi-598a6d.netlify.app/?room='+code),code);assert.equal(inviteCode(' '+code.toLowerCase()+' '),code);assert.equal(inviteCode('https://old--comfy-jalebi-598a6d.netlify.app/?room='+code+'#sala'),code);});
test('rejects truncated links or unrelated identifiers before making a server call',()=>{for(const bad of ['','https://comfy-jalebi-598a6d.net','https://example.com/','ABC123','not-a-code'])assert.throws(()=>inviteCode(bad));});
test('generated links remove old queries and fragments',()=>{const u=new URL(invitationUrl(code,'https://example.com/?old=1#sala'));assert.equal(u.searchParams.get('room'),code);assert.equal(u.searchParams.has('old'),false);assert.equal(u.hash,'');});

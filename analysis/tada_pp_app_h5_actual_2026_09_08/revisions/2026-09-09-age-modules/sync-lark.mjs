import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const dir='analysis/tada_pp_app_h5_actual_2026_09_08/revisions/2026-09-09-age-modules/',x=JSON.parse(fs.readFileSync(dir+'data.json'));
const call=args=>{const r=JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs',...args,'--doc','MUmUdKO7ko3hKIxY822lBXJQggg','--as','user','--format','json'],{encoding:'utf8',timeout:45000,maxBuffer:8e6}));assert(r.ok,JSON.stringify(r));return r.data;};
const fetch=k=>call(['+fetch','--detail','full',...(k?['--scope','keyword','--keyword',k]:[])]).document;
const target=(d,k)=>{const matches=[...d.content.matchAll(/<(p|h1)\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/\1>/g)].filter(m=>m[3].replace(/<[^>]+>/g,'').includes(k));assert.equal(matches.length,1);return matches[0][2];};
const inline=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\*\*(.*?)\*\*/g,'<b>$1</b>');
const p=s=>'<p>'+inline(s)+'</p>';
const before=fetch();fs.writeFileSync(dir+'lark.before.json',JSON.stringify(before,null,2));
async function replace(k,xml,verify){const d=fetch(k),r=call(['+update','--command','block_replace','--block-id',target(d,k),'--revision-id',String(d.revision_id),'--content',xml]);assert.equal(r.result,'success');assert.equal((r.warnings||[]).length,0);assert(fetch(verify).content.includes(verify));}
await replace('先明确：比较的是渠道人群','<h1 seq="auto">'+x.headingNew+'</h1>',x.headingNew);
let xml=p(x.endNew.split('\n\n')[0]);
for(const m of x.modules){const rows=m.table.split('\n').filter(l=>l.startsWith('|')&&!l.includes('---')).map(l=>l.split('|').slice(1,-1).map(s=>s.trim()));xml+='<h2>'+m.title+'</h2>'+p(m.intro)+p(m.denom)+'<table><thead><tr>'+rows[0].map(c=>'<th background-color="light-gray">'+p(c)+'</th>').join('')+'</tr></thead><tbody>'+rows.slice(1).map(r=>'<tr>'+r.map(c=>'<td>'+p(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table>'+p(m.note);}
await replace('两类份额分别为',xml,'01.1｜新用户：注册0—29天');
await replace('四组合下注总览','<p><b>全体用户下注总览（参考）</b></p>','全体用户下注总览（参考）');
const after=fetch();fs.writeFileSync(dir+'lark.after.json',JSON.stringify(after,null,2));
for(const m of x.modules){assert(after.content.includes(m.title));for(const row of m.rows)for(const cell of row)assert(after.content.includes(cell));}
const count=(s,t)=>(s.match(new RegExp('<'+t+'\\b','g'))||[]).length;
assert.equal(count(after.content,'table'),count(before.content,'table')+2);for(const t of ['img','source','whiteboard'])assert.equal(count(after.content,t),count(before.content,t));
assert(after.content.includes('PP资源较小是事实，但不是投注差异的原因证据。'));
fs.writeFileSync(dir+'lark-receipt.json',JSON.stringify({status:'full_readback_verified',before_revision:before.revision_id,revision:after.revision_id,added_tables:2,unrelated_user_edits_preserved:true},null,2));console.log(JSON.stringify({status:'full_readback_verified',revision:after.revision_id}));

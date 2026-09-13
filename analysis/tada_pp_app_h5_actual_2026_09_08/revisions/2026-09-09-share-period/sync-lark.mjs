import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const dir='analysis/tada_pp_app_h5_actual_2026_09_08/revisions/2026-09-09-share-period/',x=JSON.parse(fs.readFileSync(dir+'text.json'));
const call=args=>{const r=JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs',...args,'--doc','MUmUdKO7ko3hKIxY822lBXJQggg','--as','user','--format','json'],{encoding:'utf8',timeout:45000,maxBuffer:8e6}));assert(r.ok,JSON.stringify(r));return r.data;};
const fetch=k=>call(['+fetch','--detail','full',...(k?['--scope','keyword','--keyword',k]:[])]).document;
const xml=s=>s.split('\n\n').map(p=>'<p>'+p.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\*\*(.*?)\*\*/g,'<b>$1</b>')+'</p>').join('');
const before=fetch();fs.writeFileSync(dir+'lark.before.json',JSON.stringify(before,null,2));
for(const [keyword,body,verify] of [['APP渠道Tada下注额为',x.next,'全体平均不能代替分组判断'],['下图以各端',x.newChart,'下图展示上述统计期的']]){
 const d=fetch(keyword),targets=[...d.content.matchAll(/<p\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/p>/g)].filter(m=>m[2].replace(/<[^>]+>/g,'').includes(keyword));assert.equal(targets.length,1);
 const r=call(['+update','--command','block_replace','--block-id',targets[0][1],'--revision-id',String(d.revision_id),'--content',xml(body)]);assert.equal(r.result,'success');assert.equal((r.warnings||[]).length,0);assert(fetch(verify).content.includes(verify));
}
const after=fetch();fs.writeFileSync(dir+'lark.after.json',JSON.stringify(after,null,2));
for(const s of ['统计期：2026年8月1日—9月7日','59.96亿','16.52亿','325.37亿','73.97亿','6.75%／4.51%','22.27%／22.50%','全体平均不能代替分组判断'])assert(after.content.includes(s));
const count=(s,t)=>(s.match(new RegExp('<'+t+'\\b','g'))||[]).length;for(const t of ['table','img','source','whiteboard'])assert.equal(count(before.content,t),count(after.content,t));
fs.writeFileSync(dir+'lark-receipt.json',JSON.stringify({status:'full_readback_verified',before_revision:before.revision_id,revision:after.revision_id,resource_counts_unchanged:true},null,2));console.log(JSON.stringify({status:'full_readback_verified',revision:after.revision_id}));

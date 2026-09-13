import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const dir='analysis/tada_pp_app_h5_actual_2026_09_08/revisions/2026-09-09-per-capita-rtp/',x=JSON.parse(fs.readFileSync(dir+'data.json'));
const call=args=>{const r=JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs',...args,'--doc','MUmUdKO7ko3hKIxY822lBXJQggg','--as','user','--format','json'],{encoding:'utf8',timeout:60000,maxBuffer:10e6}));assert(r.ok,JSON.stringify(r));return r.data;};
const fetch=k=>call(['+fetch','--detail','full',...(k?['--scope','keyword','--keyword',k]:[])]).document;
const inline=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\*\*(.*?)\*\*/g,'<b>$1</b>');
const md=s=>s.split('\n\n').map(p=>p.startsWith('### ')?'<h2>'+inline(p.slice(4))+'</h2>':'<p>'+inline(p)+'</p>').join('');
const table=(t,rows)=>'<p><b>'+t.title+'</b></p><table><thead><tr>'+t.columns.map(c=>'<th background-color="light-gray"><p>'+c.label+'</p></th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+t.columns.map(c=>'<td><p>'+inline(String(r[c.field]))+'</p></td>').join('')+'</tr>').join('')+'</tbody></table>';
const target=(d,k)=>{const m=[...d.content.matchAll(/<(p|h1)\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/\1>/g)].filter(m=>m[3].replace(/<[^>]+>/g,'').includes(k));assert.equal(m.length,1);return m[0][2];};
const before=fetch();fs.writeFileSync(dir+'lark.before.json',JSON.stringify(before,null,2));
const newHeader='人数、下注深度与RTP：规模和回报分开看';
const mean=md(x.meanNote)+'<p><b>'+x.chart.title+'</b></p><p>'+x.chart.subtitle+'</p><img path="@./analysis/tada_pp_app_h5_actual_2026_09_08/lark-assets/per-bettor-chart-block.png" width="1136" height="356" caption="全期人均下注额：Tada与PP"/>'+table(x.tables[0],x.meanRows)+'<h1 seq="auto">'+newHeader+'</h1>';
for(const [keyword,content,verify] of [['人数、局次和局均金额共同扩大Tada优势',mean,'人均下注额：按实际下注人数比较'],['下注深度与结算回报',md(x.rtpNote)+table(x.tables[1],x.rtpRows)+'<p><b>下注深度与结算回报</b></p>','RTP对照：结算回报与下注规模分开看']]){
 const d=fetch(keyword),r=call(['+update','--command','block_replace','--block-id',target(d,keyword),'--revision-id',String(d.revision_id),'--content',content]);assert.equal(r.result,'success');assert.equal((r.warnings||[]).length,0);assert(fetch(verify).content.includes(verify));
}
const after=fetch();fs.writeFileSync(dir+'lark.after.json',JSON.stringify(after,null,2));
for(let i=0;i<x.tables.length;i++)for(const row of [x.meanRows,x.rtpRows][i])for(const c of x.tables[i].columns)assert(after.content.includes(String(row[c.field])));
const count=(s,t)=>(s.match(new RegExp('<'+t+'\\b','g'))||[]).length;
assert.equal(count(after.content,'table'),count(before.content,'table')+2);assert.equal(count(after.content,'img'),count(before.content,'img')+1);for(const t of ['source','whiteboard'])assert.equal(count(after.content,t),count(before.content,t));
fs.writeFileSync(dir+'lark-receipt.json',JSON.stringify({status:'full_readback_verified',before_revision:before.revision_id,revision:after.revision_id,added_tables:2,added_images:1,existing_resources_preserved:true},null,2));console.log(JSON.stringify({status:'full_readback_verified',revision:after.revision_id}));

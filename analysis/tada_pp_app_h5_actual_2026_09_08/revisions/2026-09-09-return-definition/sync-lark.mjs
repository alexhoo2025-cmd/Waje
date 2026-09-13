import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(dir,'../..');
const x=JSON.parse(fs.readFileSync(path.join(dir,'replacements.json'),'utf8'));
const cli='/Users/robin/.local/node/bin/lark-cli',doc='MUmUdKO7ko3hKIxY822lBXJQggg';
function call(args){const r=JSON.parse(execFileSync(cli,['docs',...args,'--doc',doc,'--as','user','--format','json'],{encoding:'utf8',timeout:45000,maxBuffer:2e6}));assert(r.ok,JSON.stringify(r));return r.data;}
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const inline=s=>esc(s).replace(/\*\*(.*?)\*\*/g,'<b>$1</b>');
const paras=s=>s.split('\n\n').map(p=>'<p>'+inline(p)+'</p>').join('');
const read=keyword=>call(['+fetch','--scope','keyword','--keyword',keyword,'--detail','full']).document;
const artifact=JSON.parse(fs.readFileSync(path.join(base,'artifact.json'),'utf8'));
const resource=artifact.manifest.blocks.find(b=>b.id==='summary').body.split('\n\n').find(p=>p.includes('PP资源较小是事实'));
const specs=[
 ['回访应优先下钻H5新用户',x.summaryNew,'优先关注H5注册未满30天'],
 ['PP资源较小是目录事实',resource,'PP资源较小是事实'],
 ['新用户：行为当天',x.scopeNew,'新老用户按注册时长划分'],
 ['回访定义：在窗口内首次下注',x.returnNew,'回访率＝第N日再次有效下注']
];
const receipts=[];
for(const [oldKeyword,body,newKeyword] of specs){
 const before=read(oldKeyword),blocks=[...before.content.matchAll(/<p\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/p>/g)];
 const selected=blocks.filter(m=>m[2].replace(/<[^>]+>/g,'').includes(oldKeyword));assert.equal(selected.length,1,'target '+oldKeyword);
 const result=call(['+update','--command','block_replace','--block-id',selected[0][1],'--revision-id',String(before.revision_id),'--content',paras(body)]);
 assert.equal(result.result,'success');assert.equal((result.warnings||[]).length,0);
 const after=read(newKeyword);assert(after.content.includes(newKeyword));
 receipts.push({action:'block_replace',keyword:oldKeyword,before_revision:before.revision_id,after_revision:after.revision_id,readback:after.content});
 console.log(JSON.stringify({updated:newKeyword,revision:after.revision_id}));
}
const anchor='这意味着，约58%的账面差距与新老构成有关';
const before=read(anchor),m=[...before.content.matchAll(/<p\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/p>/g)].find(m=>m[2].includes(anchor));assert(m);
const lines=x.table.split('\n'),rows=lines.filter(l=>l.startsWith('|')).filter(l=>!l.includes('---')).map(l=>l.split('|').slice(1,-1).map(s=>s.trim()));
const xml='<h3>新老下注用户第7／14／30日回访率</h3>'+paras(lines[2])+'<table><thead><tr>'+rows[0].map(s=>'<th background-color="light-gray"><p>'+esc(s)+'</p></th>').join('')+'</tr></thead><tbody>'+rows.slice(1).map(r=>'<tr>'+r.map(s=>'<td><p>'+esc(s)+'</p></td>').join('')+'</tr>').join('')+'</tbody></table>'+paras(lines.at(-1));
const result=call(['+update','--command','block_insert_after','--block-id',m[1],'--revision-id',String(before.revision_id),'--content',xml]);
assert.equal(result.result,'success');assert.equal((result.warnings||[]).length,0);
const after=read('新老下注用户第7／14／30日回访率');
const head=after.content.match(/<h3[^>]*id="([^"]+)"/);assert(head);
const section=call(['+fetch','--scope','section','--start-block-id',head[1],'--detail','full']).document;
for(const row of rows)for(const cell of row)assert(section.content.includes(esc(cell))||section.content.includes(cell),'missing cell '+cell);
receipts.push({action:'insert_return_table',before_revision:before.revision_id,after_revision:section.revision_id,rows:rows.length-1,readback:section.content});
fs.writeFileSync(path.join(dir,'lark-receipt.json'),JSON.stringify({status:'readback_verified',document:doc,revision:section.revision_id,receipts},null,2)+'\n');
console.log(JSON.stringify({status:'readback_verified',revision:section.revision_id,table_rows:rows.length-1}));

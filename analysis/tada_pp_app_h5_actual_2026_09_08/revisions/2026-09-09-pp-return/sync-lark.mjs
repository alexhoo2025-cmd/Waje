import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const dir='analysis/tada_pp_app_h5_actual_2026_09_08/revisions/2026-09-09-pp-return/';
const doc='MUmUdKO7ko3hKIxY822lBXJQggg';
const call=args=>{const r=JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs',...args,'--doc',doc,'--as','user','--format','json'],{encoding:'utf8',timeout:45000,maxBuffer:8e6}));assert(r.ok,JSON.stringify(r));return r.data;};
const full=()=>call(['+fetch','--detail','full']).document;
const before=full();fs.writeFileSync(dir+'lark.before.json',JSON.stringify(before,null,2));
const inline=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\*\*(.*?)\*\*/g,'<b>$1</b>');
const xml=s=>s.split('\n\n').map(p=>p.startsWith('- ')?'<ul>'+p.split('\n').map(l=>'<li>'+inline(l.slice(2))+'</li>').join('')+'</ul>':'<p>'+inline(p)+'</p>').join('');
const actions=[["优先关注H5注册未满30天","**Tada与PP的新下注用户，H5回访均低于APP。** 新下注用户指回访起点时注册未满30天、已下注对应厂商的用户；未按充值筛选，不是新增付费或全部新增注册用户口径。同为8月1—9日起点批次，第7／14／30日回访率：\n\n- **Tada：** APP **13.93%／10.47%／7.33%**；H5 **8.21%／5.94%／4.45%**。\n- **PP：** APP **8.17%／5.67%／4.66%**；H5 **6.68%／3.84%／3.24%**。\n\n同渠道、同观察日下，Tada均高于PP；两家都应关注H5新下注用户的首周回访。","Tada与PP的新下注用户"],["Tada注册未满30天的下注用户，H5第7日","**PP也存在H5新下注用户回访偏低的情况。** APP的3,758名起点用户中，第7／14／30日分别有307／213／175人再次下注PP，回访率为8.17%／5.67%／4.66%；H5的1,483人中分别有99／57／48人，回访率为6.68%／3.84%／3.24%。\n\n**同渠道、同观察日下，Tada新下注用户回访率均高于PP。** 两家在H5的第7日回访都低于APP，差距延续至第14、30日；优先核验两家H5首周的入口、游戏体验与持续下注路径，现有对照尚不能确定原因。注册日期未知的用户保留在全体口径及明细中，未并入新老两组。","PP也存在H5新下注用户回访偏低"]];
for(const [keyword,text,updated] of actions){
 const read=call(['+fetch','--scope','keyword','--keyword',keyword,'--detail','full']).document;
 const target=[...read.content.matchAll(/<p\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/p>/g)].filter(m=>m[2].replace(/<[^>]+>/g,'').includes(keyword));assert.equal(target.length,1);
 const result=call(['+update','--command','block_replace','--block-id',target[0][1],'--revision-id',String(read.revision_id),'--content',xml(text)]);assert.equal(result.result,'success');assert.equal((result.warnings||[]).length,0);
 const verify=call(['+fetch','--scope','keyword','--keyword',updated,'--detail','full']).document;assert(verify.content.includes(updated));
}
const after=full();fs.writeFileSync(dir+'lark.after.json',JSON.stringify(after,null,2));
for(const text of ['8.17%／5.67%／4.66%','6.68%／3.84%／3.24%','307／213／175','99／57／48'])assert(after.content.includes(text));
const counts=s=>Object.fromEntries(['table','img','source','whiteboard'].map(tag=>[tag,(s.match(new RegExp('<'+tag+'\\b','g'))||[]).length]));
assert.deepEqual(counts(before.content),counts(after.content));
assert(after.content.includes('Tada的下注规模优势不仅仅是头部游戏，是全面领先。'));
fs.writeFileSync(dir+'lark-receipt.json',JSON.stringify({status:'full_readback_verified',before_revision:before.revision_id,revision:after.revision_id,resource_counts:counts(after.content),unrelated_user_edit_preserved:true},null,2));
console.log(JSON.stringify({status:'full_readback_verified',revision:after.revision_id,counts:counts(after.content)}));


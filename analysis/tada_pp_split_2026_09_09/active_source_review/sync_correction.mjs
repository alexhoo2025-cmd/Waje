import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const dir='analysis/tada_pp_split_2026_09_09/active_source_review/',p=JSON.parse(fs.readFileSync(dir+'macro-patch.json'));
const call=args=>{const r=JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs',...args,'--doc','HWzVdQfWVoHhZRxiwcBlIJ55grh','--as','user','--format','json'],{encoding:'utf8',timeout:60000,maxBuffer:10e6}));assert(r.ok,JSON.stringify(r));return r.data;};
const fetch=()=>call(['+fetch','--detail','full']).document;
const strip=s=>s.replace(/<[^>]*>/g,'');
const xml=s=>'<p>'+s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\*\*(.*?)\*\*/g,'<b>$1</b>')+'</p>';
let current=fetch();if(!fs.existsSync(dir+'lark.pre-correction.json'))fs.writeFileSync(dir+'lark.pre-correction.json',JSON.stringify(current,null,2));const receipt=[];
function replace(match,body,tag='p'){
 const re=tag==='img'?/<img\b[^>]*id="([^"]+)"[^>]*\/>/g:new RegExp('<'+tag+'\\b[^>]*id="([^"]+)"[^>]*>([\\s\\S]*?)<\\/'+tag+'>','g');
 const targets=[...current.content.matchAll(re)].filter(m=>match(strip(m[2]||m[0]),m[0]));assert.equal(targets.length,1,'target count '+targets.length+' '+body.slice(0,70));
 const r=call(['+update','--command','block_replace','--block-id',targets[0][1],'--revision-id',String(current.revision_id),'--content',body]);assert.equal(r.result,'success');assert.equal((r.warnings||[]).length,0);current=fetch();receipt.push({revision:current.revision_id,updated:targets[0][1]});console.log(JSON.stringify(receipt.at(-1)));
}
if(!process.argv.includes('--resume-tables')){
replace(t=>t.includes('PP老用户在H5参与更广'),xml(p.patches.summary.split('\n\n')[2]));
replace(t=>t.startsWith('新用户：'),'<h1 seq="auto">新用户：先比较下注人数与金额</h1>','h1');
replace(t=>t.includes('PP在H5')&&t.includes('7.57%')&&t.includes('1.23%'),xml(p.newIntro));
replace(t=>t.includes('同组平台用户日表去重账号数'),xml(p.verified));
replace(t=>t.includes('该日表具体由登录还是页面访问'),xml(p.pending));
replace(t=>t.includes('下注渗透率')&&t.includes('计算方式')&&t.includes('5,628'),xml(p.formula));
replace(t=>t.startsWith('老用户：')&&t.includes('参与比例'),'<h1 seq="auto">老用户：先比较下注人数与金额</h1>','h1');
replace(t=>t.includes('PP在H5')&&t.includes('8.86%')&&t.includes('6.00%'),xml(p.oldIntro));
replace(t=>t.includes('同组平台活跃人数')&&t.includes('402,803'),xml(p.oldPending));
replace(t=>t.startsWith('老用户：')&&t.includes('较高参与比例'),'<ol seq="2"><li>老用户：分别比较两家厂商的下注规模与回访；渠道参与比例待活跃分母核验后再判断。</li></ol>','li');
}
for(const [age,label,marker] of [['new_30d','新用户','60,688'],['old_over_30d','老用户','89,714']]){
 const tables=[...current.content.matchAll(/<table\b[^>]*id="([^"]+)"[^>]*>[\s\S]*?<\/table>/g)].filter(m=>m[0].includes(marker)&&m[0].includes('下注渗透率'));assert.equal(tables.length,1);let table=tables[0][0].replace(/\s+id="[^"]+"/g,'');
 table=table.replace(/<thead>[\s\S]*?<\/thead>/,x=>x.replace('下注渗透率','下注渗透率（待核）')).replace(/<tbody>[\s\S]*?<\/tbody>/,x=>x.replace(/<tr>[\s\S]*?<\/tr>/g,row=>{const cells=[...row.matchAll(/<td\b[^>]*>[\s\S]*?<\/td>/g)];assert.equal(cells.length,7);const last=cells.at(-1)[0],replacement=last.replace(/<p[^>]*>[\s\S]*?<\/p>/,'<p>待核</p>');return row.replace(last,replacement);}));
 const r=call(['+update','--command','block_replace','--block-id',tables[0][1],'--revision-id',String(current.revision_id),'--content',table]);assert.equal(r.result,'success');assert.equal((r.warnings||[]).length,0);current=fetch();
 replace(t=>t===label+'下注渗透率',xml('**'+label+'下注人数**'));
 // Change only the caption immediately associated with the current chart block.
 const name='macro-pen-'+age+'-block.png';const image=[...current.content.matchAll(/<img\b[^>]*id="([^"]+)"[^>]*\/>/g)].find(m=>m[0].includes(name));assert(image);
 const pos=current.content.indexOf(image[0]);const pre=current.content.slice(0,pos);const para=[...pre.matchAll(/<p\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/p>/g)].at(-1);assert(para&&strip(para[2]).includes('活跃人数'));
 const cap=call(['+update','--command','block_replace','--block-id',para[1],'--revision-id',String(current.revision_id),'--content',xml('统计期内该厂商去重下注人数；活跃分母待核，当前展示人数而非渗透率。')]);assert.equal(cap.result,'success');current=fetch();
 replace((_,raw)=>raw.includes(name),'<img path="@./analysis/tada_pp_split_2026_09_09/qa/'+name+'" width="1136" height="360" caption="'+label+'下注人数（已核验分子）"/>','img');
}
fs.writeFileSync(dir+'lark.after-correction.json',JSON.stringify(current,null,2));const text=strip(current.content);assert(!text.includes('PP老用户在H5参与更广'));assert(!text.includes('渗透率为8.86%'));assert(text.includes('AL')||text.includes('APP启动'));assert((text.match(/待核/g)||[]).length>=8);assert(text.includes('12,213')&&text.includes('24,179'));
fs.writeFileSync(dir+'lark-correction-receipt.json',JSON.stringify({status:'provisional_correction_readback_verified',revision:current.revision_id,updates:receipt,active_denominator:'pending',raw_numbers_preserved_in_archive:true,production_configuration_writes:0},null,2));console.log(JSON.stringify({status:'provisional_correction_readback_verified',revision:current.revision_id}));

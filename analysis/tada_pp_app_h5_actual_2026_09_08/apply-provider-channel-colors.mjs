import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const base='analysis/tada_pp_app_h5_actual_2026_09_08/',dir=base+'revisions/2026-09-09-provider-channel-colors/';fs.mkdirSync(dir,{recursive:true});
const call=args=>{const r=JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs',...args,'--doc','MUmUdKO7ko3hKIxY822lBXJQggg','--as','user','--format','json'],{encoding:'utf8',timeout:45000,maxBuffer:8e6}));assert(r.ok);return r.data;};
const fetch=()=>call(['+fetch','--detail','full']).document;
const before=fetch();fs.writeFileSync(dir+'lark.before.json',JSON.stringify(before,null,2));
const specs=[{id:'depth',match:s=>s.includes('有效下注局次')&&s.includes('局均金额')&&s.includes('结算RTP'),color:s=>s.includes('Tada')?'light-blue':'light-orange',legend:'Tada：浅蓝；PP：浅橙。颜色只区分厂商，表格按固定顺序展示。'},
{id:'app-detail',match:s=>s.includes('APP渠道')&&s.includes('Android渠道')&&s.includes('iOS渠道'),color:s=>s.includes('Android渠道')?'light-blue':'light-purple',legend:'Android渠道：浅蓝；iOS渠道：浅紫。颜色只区分渠道，表格按固定顺序展示。'}];
const a=JSON.parse(fs.readFileSync(base+'artifact.json')),bodies={},receipts=[];
for(const spec of specs){
 const current=fetch(),matches=[...current.content.matchAll(/<table\b[^>]*id="([^"]+)"[^>]*>[\s\S]*?<\/table>/g)].filter(m=>spec.match(m[0]));assert.equal(matches.length,1);
 const original=matches[0][0];let xml=original.replace(/\s+id="[^"]+"/g,'');
 xml=xml.replace(/<tbody>[\s\S]*?<\/tbody>/,body=>body.replace(/<tr>[\s\S]*?<\/tr>/g,row=>row.replace(/<td\b([^>]*)>/g,(_,attrs)=>'<td'+attrs.replace(/\s+background-color="[^"]*"/g,'')+' background-color="'+spec.color(row)+'">')));
 const result=call(['+update','--command','block_replace','--block-id',matches[0][1],'--revision-id',String(current.revision_id),'--content',xml]);assert.equal(result.result,'success');assert.equal((result.warnings||[]).length,0);
 const after=fetch(),found=[...after.content.matchAll(/<table\b[^>]*>[\s\S]*?<\/table>/g)].filter(m=>spec.match(m[0]));assert.equal(found.length,1);assert.equal(found[0][0].replace(/<[^>]*>/g,''),original.replace(/<[^>]*>/g,''));
 const colors=[...found[0][0].matchAll(/<tbody>([\s\S]*?)<\/tbody>/g)][0][1];const grouped=[...colors.matchAll(/<tr>[\s\S]*?<\/tr>/g)].map(m=>[...m[0].matchAll(/background-color="([^"]+)"/g)].map(v=>v[1]));assert.equal(grouped.length,4);assert(grouped.every(g=>g.length===6));assert.notEqual(grouped[0][0],grouped[spec.id==='depth'?1:2][0]);
 receipts.push({id:spec.id,revision:after.revision_id,colors:grouped,text_unchanged:true});
 const t=a.manifest.tables.find(t=>t.id===spec.id),rows=a.snapshot.datasets[t.dataset];bodies[spec.id]='### '+t.title+'\n\n'+spec.legend+'\n\n'+(t.subtitle?t.subtitle+'\n\n':'')+'| '+t.columns.map(c=>c.label).join(' | ')+' |\n| '+t.columns.map(()=> '---').join(' | ')+' |\n'+rows.map(r=>'| '+t.columns.map(c=>r[c.field]).join(' | ')+' |').join('\n');
}
const after=fetch();fs.writeFileSync(dir+'lark.after.json',JSON.stringify(after,null,2));
fs.writeFileSync(dir+'lark-receipt.json',JSON.stringify({status:'full_readback_verified',revision:after.revision_id,receipts},null,2));fs.writeFileSync(dir+'bodies.json',JSON.stringify(bodies,null,2));console.log(JSON.stringify({status:'full_readback_verified',revision:after.revision_id}));

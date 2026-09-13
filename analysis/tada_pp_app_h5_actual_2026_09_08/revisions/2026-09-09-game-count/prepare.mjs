import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(dir,'../..');
const read=n=>JSON.parse(fs.readFileSync(path.join(base,n),'utf8'));
const artifact=read('artifact.json'),A=read('analysis-results.json'),raw=read('queries/14_full_core.result.json');
const rows=[];
for(const platform of ['APP','H5'])for(const scope of ['全量游戏','剔除各自前5款'])for(const provider of ['Tada','PP']){
 const core=A.overview.find(r=>r.platform===platform&&r.provider===provider&&r.age==='all_ages');
 const r=raw.find(r=>r.product_mode==='Waje'&&r.time_grain==='period'&&r.segment_grain==='platform'&&r.platform_group===platform&&r.provider_group===provider&&r.age_segment==='all_ages');
 assert.equal(core.played_game_count,r.played_game_count);
 const games=A.games.filter(r=>r.platform_group===platform&&r.provider===provider).sort((a,b)=>b.stake-a.stake);
 assert.equal(new Set(games.map(r=>r.play_id)).size,games.length);
 const top5=games.slice(0,5);assert(top5.every(r=>r.stake>0));
 const h=A.heads.find(r=>r.platform===platform&&r.provider===provider);
 const head=top5.reduce((s,r)=>s+r.stake,0);assert(Math.abs(head-h.top5_stake)<0.001);
 const n=core.played_game_count-(scope==='全量游戏'?0:5),amount=core.stake-(scope==='全量游戏'?0:head);
 rows.push({platform,provider,scope,games:n,stake:amount,per_game:amount/n});
}
const fmt=x=>x.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const table='### 游戏数量与平均每款下注额\n\n游戏数指8月1日—9月7日有有效下注的去重游戏数，不是目录收录数或当前上架数。平均每款下注额＝同范围有效下注总额÷游戏数；金额沿用报表单位。\n\n| 渠道 | 厂商 | 范围 | 游戏数（款） | 下注总额（亿） | 平均每款下注额（万） |\n| --- | --- | --- | ---: | ---: | ---: |\n'+rows.map(r=>'| '+[r.platform,r.provider,r.scope,r.games,fmt(r.stake/1e8),fmt(r.per_game/1e4)].join(' | ')+' |').join('\n');
const comparisons=[];for(const platform of ['APP','H5'])for(const scope of ['全量游戏','剔除各自前5款']){const t=rows.find(r=>r.platform===platform&&r.scope===scope&&r.provider==='Tada'),p=rows.find(r=>r.platform===platform&&r.scope===scope&&r.provider==='PP');comparisons.push({platform,scope,total_ratio:t.stake/p.stake,per_game_ratio:t.per_game/p.per_game});}
const summary='**Tada游戏数量更少，但总下注额和平均每款下注额更高。** APP本期有有效下注的游戏：Tada **161款**、PP **415款**；平均每款下注约**2.40亿**、**324万**，Tada约为PP的**74.0倍**。剔除各自前5款后，剩余**156款／410款**，下注总额之比为**32.1倍**，平均每款之比约**84.4倍**。这是不同游戏组合的均值，不代表每款游戏都领先。';
const explanation='**差距不只是游戏数量造成的。** APP中Tada的游戏数少于PP，平均每款下注额却约为PP的74.0倍；剔除各自前5款后约为84.4倍。H5对应约为50.3倍和53.5倍。\n\n平均每款是各游戏下注额的算术平均，不是典型游戏的中位数，也不是同款游戏的对照；上线天数、曝光、品类及玩家构成尚未控制。完整汇总中的游戏数包含明细中未展示的小样本游戏，均值使用对应完整总额，避免少算分母。';
const oldSummary=artifact.manifest.blocks.find(b=>b.id==='summary').body.split('\n\n').find(p=>p.includes('Tada的下注规模优势'));
const oldDetail=artifact.manifest.blocks.find(b=>b.id==='games').body.split('\n\n').find(p=>p.startsWith('**32.1倍比较的是'));
assert(oldSummary&&oldDetail);const detail=oldDetail+'\n\n'+table+'\n\n'+explanation;
const pairs=[[oldSummary,summary],[oldDetail,detail]];
for(const name of ['artifact.json','报告.md','build_report.py']){const target=path.join(dir,name+'.before');assert(!fs.existsSync(target));fs.copyFileSync(path.join(base,name),target);}
fs.copyFileSync(path.resolve(base,'../../output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html'),path.join(dir,'report.before.html'));
let patch='*** Begin Patch\n';for(const name of ['artifact.json','报告.md','build_report.py']){
 const old=fs.readFileSync(path.join(base,name),'utf8');patch+='*** Update File: '+path.join(base,name)+'\n';
 if(name==='artifact.json'){let next=old;for(const [a,b]of pairs)next=next.replace(JSON.stringify(a).slice(1,-1),JSON.stringify(b).slice(1,-1));const ol=old.split('\n'),nl=next.split('\n');for(let i=0;i<ol.length;i++)if(ol[i]!==nl[i])patch+='@@\n-'+ol[i]+'\n+'+nl[i]+'\n';}
 else for(const [a,b]of pairs){const line=old.split('\n').find(l=>l.includes(a));assert(line);patch+='@@\n-'+line+'\n+'+line.replace(a,b).split('\n').join('\n+')+'\n';}
}
fs.writeFileSync(path.join(dir,'calculation.json'),JSON.stringify({status:'verified_against_saved_aggregates',rows,comparisons,summary,table,explanation,oldDetail,online_queries_run:false},null,2));
console.log(patch+'*** End Patch');

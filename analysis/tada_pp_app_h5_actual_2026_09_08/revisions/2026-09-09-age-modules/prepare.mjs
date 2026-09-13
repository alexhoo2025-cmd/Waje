import fs from 'node:fs';
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(dir,'../..');
const read=n=>JSON.parse(fs.readFileSync(path.join(base,n),'utf8'));
const artifact=read('artifact.json'),A=read('analysis-results.json'),core=read('core-corrected.json'),active=read('queries/16_full_active_base.result.json');
const f=x=>x.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}),pct=x=>f(100*x)+'%';
const checked=[];const modules=[];
for(const age of ['new_30d','old_over_30d']){
 const rows=[];
 for(const platform of ['APP','H5'])for(const provider of ['Tada','PP']){
  const get=v=>core.find(r=>r.product_mode==='Waje'&&r.time_grain==='period'&&r.segment_grain==='platform'&&r.platform_group===platform&&r.provider_group===v&&r.age_segment===age);
  const r=get(provider),all=get('all_games'),pair=get('Tada').stake+get('PP').stake;
  const n=active.find(r=>r.time_grain==='period'&&r.segment_grain==='platform'&&r.platform_group===platform&&r.age_segment===age).active_accounts;
  const saved=A.overview.find(r=>r.platform===platform&&r.provider===provider&&r.age===age);
  const metrics={stake:r.stake,all_share:r.stake/all.stake,pair_share:r.stake/pair,bettors:r.bettors,penetration:r.bettors/n};
  assert.equal(metrics.all_share,saved.all_game_share);assert.equal(metrics.pair_share,saved.pair_share);assert.equal(metrics.penetration,saved.penetration);assert.equal(metrics.stake,saved.stake);
  checked.push({age,platform,provider,...metrics,all_game_denominator:all.stake,pair_denominator:pair,active_denominator:n});
  rows.push([platform+' · '+provider,f(r.stake/1e8),pct(metrics.all_share),pct(metrics.pair_share),r.bettors.toLocaleString('en-US'),pct(metrics.penetration)]);
 }
 const title=age==='new_30d'?'01.1｜新用户：注册0—29天':'01.2｜老用户：注册30天及以上';
 const intro=age==='new_30d'?'**新用户中，PP在H5的金额份额更高，但参与比例没有更高。** PP占同组Tada＋PP下注额的比例为H5 **7.57%**、APP **2.96%**；下注渗透率却为H5 **1.23%**、APP **1.36%**。应区分“参与人数比例”和“参与后的下注金额”，不能把份额高直接解释成转化好。':'**老用户中，PP在H5的下注渗透率高于APP，与新用户的表现不同。** PP分别为H5 **8.86%**、APP **6.00%**；Tada则为 **22.50%／22.27%**，两渠道接近。老用户的参与结构与新用户不同，应分别分析。';
 const denom=age==='new_30d'?'同组平台活跃人数：APP **899,442人**，H5 **458,169人**。':'同组平台活跃人数：APP **402,803人**，H5 **75,479人**。';
 const table='| 组合 | 下注额（亿） | 占同组全部游戏 | 占同组两厂商 | 下注人数 | 同组下注渗透率 |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'+rows.map(r=>'| '+r.join(' | ')+' |').join('\n');
 const note='两项份额的分母分别为同渠道、同年龄组的全部Waje游戏下注额和Tada＋PP下注额；渗透率分母为上列同组平台活跃人数。';
 modules.push({title,intro,denom,table,note,rows});
}
const appendix=modules.map(m=>'### '+m.title+'\n\n'+m.intro+'\n\n'+m.denom+'\n\n'+m.table+'\n\n'+m.note).join('\n\n');
const headingOld='先明确：比较的是渠道人群，主指标是下注金额份额',headingNew='分新老用户比较：下注金额、份额与参与比例';
const endOld='两类份额分别为：厂商下注额÷同渠道端全部Waje游戏下注额；厂商下注额÷同渠道端Tada＋PP下注额。下注渗透率为厂商下注人数÷同渠道端平台活跃账号数，并非曝光转化率。';
const endNew='以下分新老用户比较，份额和渗透率均使用同渠道、同年龄组的分母。第30天归老用户。新老按行为当天注册时长划分，同一用户可在统计期内跨组，因此两组去重人数不直接相加。\n\n'+appendix;
const scope=artifact.manifest.blocks.find(b=>b.id==='scope'),oldBody=scope.body,newBody=oldBody.replace(headingOld,headingNew).replace(endOld,endNew);
assert(newBody!==oldBody);
for(const name of ['artifact.json','报告.md','build_report.py']){assert(!fs.existsSync(path.join(dir,name+'.before')));fs.copyFileSync(path.join(base,name),path.join(dir,name+'.before'));}
fs.copyFileSync(path.resolve(base,'../../output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html'),path.join(dir,'report.before.html'));
let patch='*** Begin Patch\n';
for(const name of ['artifact.json','报告.md','build_report.py']){
 const old=fs.readFileSync(path.join(base,name),'utf8');patch+='*** Update File: '+path.join(base,name)+'\n';
 if(name==='artifact.json'){
  let next=old.replace(JSON.stringify(oldBody),JSON.stringify(newBody)).replace('"title": "四组合下注总览"','"title": "全体用户下注总览（参考）"');
  const ol=old.split('\n'),nl=next.split('\n');for(let i=0;i<ol.length;i++)if(ol[i]!==nl[i])patch+='@@\n-'+ol[i]+'\n+'+nl[i]+'\n';
 }else for(const [a,b] of [[headingOld,headingNew],[endOld,endNew],['四组合下注总览','全体用户下注总览（参考）']]){const line=old.split('\n').find(l=>l.includes(a));assert(line);patch+='@@\n-'+line+'\n+'+line.replace(a,b).split('\n').join('\n+')+'\n';}
}
fs.writeFileSync(path.join(dir,'data.json'),JSON.stringify({status:'verified',headingNew,endOld,endNew,modules,checked,age_rule:'行为日注册0—29天/30天及以上；非付费分组',online_queries_run:false},null,2));
console.log(patch+'*** End Patch');

import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(dir,'../..');
const raw=JSON.parse(fs.readFileSync(path.join(base,'queries/18_full_return.result.json'),'utf8'));
const analyzed=JSON.parse(fs.readFileSync(path.join(base,'analysis-results.json'),'utf8')).returns;
const get=(platform,provider,age,day,rows=raw)=>rows.find(r=>r.platform===platform&&r.provider===provider&&r.age_segment===age&&r.observation_day===day&&r.sample_mode==='common_30d'&&r.cohort_scope==='summary');
const values=[];const tableRows=[];
for(const provider of ['Tada','PP'])for(const age of ['new_30d','old_over_30d'])for(const platform of ['APP','H5']){
 const group=[7,14,30].map(day=>get(platform,provider,age,day));
 assert(group.every(Boolean));assert.equal(new Set(group.map(r=>r.eligible_accounts)).size,1);
 const cells=[provider,age==='new_30d'?'注册未满30天的下注用户':'注册满30天的下注用户',platform,group[0].eligible_accounts.toLocaleString('en-US')];
 for(const r of group){
   assert.equal(r.first_origin_date,'2026-08-01');assert.equal(r.last_origin_date,'2026-08-09');
   assert.equal(r.same_provider_return_accounts+r.other_provider_only_accounts+r.no_observed_bet_accounts,r.eligible_accounts);
   const rate=r.same_provider_return_accounts/r.eligible_accounts;
   assert.equal(rate,get(platform,provider,age,r.observation_day,analyzed).return_rate);
   values.push({platform,provider,age,day:r.observation_day,numerator:r.same_provider_return_accounts,denominator:r.eligible_accounts,rate});
   cells.push((rate*100).toFixed(2)+'%');
 }
 tableRows.push('| '+cells.join(' | ')+' |');
}
const table='### 新老下注用户第7／14／30日回访率\n\n同为8月1—9日起点批次；各观察日使用相同分母。新老按回访起点的注册时长划分，均未筛选充值状态。\n\n| 厂商 | 人群 | 渠道 | 起点人数 | 第7日 | 第14日 | 第30日 |\n| --- | --- | --- | ---: | ---: | ---: | ---: |\n'+tableRows.join('\n')+'\n\nTada注册未满30天的下注用户，H5第7日已低于APP，差距延续至第14、30日；优先核验首周回访路径。注册日期未知的用户保留在全体口径及明细中，未并入新老两组。';
const summaryOld='**回访应优先下钻H5新用户，而不是只看APP/H5总平均。** 相同成熟批次下，Tada第30日回访率APP为14.84%、H5为12.32%；老用户两端均约18.5%，新用户则为7.33%和4.45%。';
const summaryNew='**优先关注H5注册未满30天的下注用户，非新增付费用户口径。** 这里按回访起点的注册时长分组，未筛选充值状态；分母是已下注该厂商的用户，不是全部新增注册用户。同为8月1—9日起点批次，Tada这组用户第7／14／30日回访率：APP为**13.93%／10.47%／7.33%**，H5为**8.21%／5.94%／4.45%**。';
const scopeOld='**新用户：行为当天距注册0—29天；老用户：30天及以上。** 同一账号可能在本期内由新转老，因此整期新老人数可重叠，全体人数另行去重。回访固定起点当天的新老分组。';
const scopeNew='**新老用户按注册时长划分，不按是否充值划分。** 新用户为行为当天距注册0—29天，老用户为30天及以上；不是“新增付费用户”口径。同一账号可能在本期内由新转老，因此整期新老人数可重叠，全体人数另行去重。回访固定起点当天的新老分组，分母仅包含已有效下注对应厂商的用户，并非全部新增注册用户。';
const returnOld='**回访定义：在窗口内首次下注某厂商后，第N日再次有效下注该厂商。** 起点为第1日，不要求再次充值；按固定渠道人群统计，并非实际端内回访。主图使用8月1—9日起点批次，所有人都已具备第30日观察窗口，保证各观察日分母一致。附表另列“首个下注日游戏集合”的再次下注人数，不将其冒充每款游戏独立起点的回访率。';
const returnNew='**回访率＝第N日再次有效下注同一厂商的人数÷该批起点下注人数。** 窗口内首次有效下注该厂商的当天为第1日。新用户指起点当天注册0—29天的下注用户，不限充值状态；不是全部新增注册用户，也不是新增付费用户。\n\n按固定渠道人群统计，并非实际端内回访。第7、14、30日对照均使用8月1—9日起点批次，各观察日分母一致。附表另列“首个下注日游戏集合”的再次下注人数，不将其冒充每款游戏独立起点的回访率。';
const ageEnd='这意味着，约58%的账面差距与新老构成有关，剩余部分才是同年龄组差异。这里仅控制了账号龄，尚未控制渠道入口、具体游戏和曝光，不能宣称APP本身造成更高留存。建议首先核验H5新用户首周的进入游戏与持续下注路径。';
const replacements=[[summaryOld,summaryNew],['PP资源较小是目录事实','PP资源较小是事实'],[scopeOld,scopeNew],[returnOld,returnNew],[ageEnd,ageEnd+'\n\n'+table]];
const before=JSON.parse(fs.readFileSync(path.join(base,'artifact.json'),'utf8'));
const snapshot=(file,name)=>{const to=path.join(dir,name);if(fs.existsSync(to)){assert.equal(fs.readFileSync(file,'utf8'),fs.readFileSync(to,'utf8'),'source changed since backup');return;}fs.copyFileSync(file,to);};
snapshot(path.join(base,'artifact.json'),'artifact.before.json');snapshot(path.join(base,'报告.md'),'报告.before.md');snapshot(path.join(base,'build_report.py'),'build_report.before.py');
snapshot(path.resolve(base,'../../output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html'),'report.before.html');
let patch='*** Begin Patch\n';
for(const name of ['artifact.json','报告.md','build_report.py']){
 let old=fs.readFileSync(path.join(base,name),'utf8'),next=old;
 for(const [a,b] of replacements){const from=name==='artifact.json'?JSON.stringify(a).slice(1,-1):a,to=name==='artifact.json'?JSON.stringify(b).slice(1,-1):b;assert(next.includes(from),name+' missing '+from);next=next.replace(from,to);}
 patch+='*** Update File: '+path.join(base,name)+'\n';
 if(name==='artifact.json'){
  const ol=old.split('\n'),nl=next.split('\n');assert.equal(ol.length,nl.length);
  for(let i=0;i<ol.length;i++)if(ol[i]!==nl[i])patch+='@@\n-'+ol[i]+'\n+'+nl[i]+'\n';
 }else{
  for(const [a,b] of replacements){
   if(a==='PP资源较小是目录事实'){
    const line=old.split('\n').find(l=>l.includes(a));patch+='@@\n-'+line+'\n+'+line.replace(a,b)+'\n';
   }else {const line=old.split('\n').find(l=>l.includes(a));assert(line);patch+='@@\n-'+line+'\n+'+line.replace(a,b).split('\n').join('\n+')+'\n';}
  }
 }
}
fs.writeFileSync(path.join(dir,'calculation-receipt.json'),JSON.stringify({status:'passed',source:'queries/18_full_return.result.json',verification:'既有聚合分子分母复算并与分析结果逐项核对；未执行线上查询',cohort:'2026-08-01/2026-08-09',payment_filter:false,values,table},null,2)+'\n');
fs.writeFileSync(path.join(dir,'replacements.json'),JSON.stringify({summaryNew,scopeNew,returnNew,table},null,2)+'\n');
console.log(patch+'*** End Patch');

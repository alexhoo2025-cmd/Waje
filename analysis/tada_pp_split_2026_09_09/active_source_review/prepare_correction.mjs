import fs from 'node:fs';
import assert from 'node:assert/strict';
import path from 'node:path';
const base='analysis/tada_pp_split_2026_09_09/',dir=base+'active_source_review/',p=base+'macro/';
const a=JSON.parse(fs.readFileSync(p+'artifact.json'));const d=JSON.parse(fs.readFileSync(base+'data.json'));
for(const f of ['artifact.json','报告.md']){assert(!fs.existsSync(dir+f+'.before'));fs.copyFileSync(p+f,dir+f+'.before');}
fs.copyFileSync('output/html/Tada与PP-宏观对比-新老用户下注与回访-2026-09-09.html',dir+'html.before.html');
const patches={};const summary=a.manifest.blocks.find(b=>b.id==='summary').body.split('\n\n');summary[2]='**Tada的下注额主要来自老用户。** 老用户贡献APP 84.3%、H5 81.7%的Tada下注额。PP新用户下注人数为APP 12,213人、H5 5,628人；活跃分母正在复核，当前以已核验的下注人数和金额比较渠道规模。';patches.summary=summary.join('\n\n');
const newIntro='**APP的PP新用户下注人数更多，H5的两厂商金额份额更高。** PP新用户下注人数为APP 12,213人、H5 5,628人，下注额分别为1.83亿、1.35亿；PP占Tada与PP合计下注额的比例为APP 3.0%、H5 7.6%。';
const verified='**起源已定义平台活跃行为：APP启动／退出、账号登录／登出。** 这与游戏下注、页面进入PV分别统计。';
const pending='原报告分母取自另一张用户日表，两者是否覆盖同一批账号尚未核实。表中下注渗透率先标为“待核”，原始比例保留在核验记录中。';
const formula='确认后的下注渗透率＝厂商去重下注人数÷同渠道、同新老分组的活跃去重人数×100%。需要取得原日表生成逻辑并完成账号集合对账后，再补充该指标。';
patches.new_30d='## 02｜新用户：先比较下注人数与金额\n\n'+newIntro+'\n\n'+verified+'\n\n'+pending+'\n\n'+formula;
const oldIntro='**APP的两家厂商老用户下注规模更大。** PP老用户下注人数为APP 24,179人、H5 6,689人，下注额为11.59亿、3.31亿；Tada老用户下注人数为89,714人、16,985人，下注额为325.37亿、73.97亿。';
const oldPending='老用户的活跃分母同样待核；当前展示已核验的下注人数、金额和份额，下注渗透率待分母对账后补充。';
patches.old_over_30d='## 03｜老用户：先比较下注人数与金额\n\n'+oldIntro+'\n\n'+oldPending;
for(const age of ['new_30d','old_over_30d']){
 const id='table-'+age,b=a.manifest.blocks.find(b=>b.id===id);patches[id]=b.body.split('\n').map(line=>{if(!line.startsWith('|'))return line;const c=line.split('|');if(c[1].trim()==='组合'){c[c.length-2]=' 下注渗透率（待核） ';return c.join('|');}if(line.includes('---'))return line;c[c.length-2]=' 待核 ';return c.join('|');}).join('\n');
}
const action=a.manifest.blocks.find(b=>b.id==='actions');patches.actions=action.body.replace('老用户：分别评估PP在H5的较高参与比例，以及Tada两端相近的回访；不只看全体平均。','老用户：分别比较两家厂商的下注规模与回访；渠道参与比例待活跃分母核验后再判断。');
for(const b of a.manifest.blocks)if(patches[b.id])b.body=patches[b.id];
const chartChanges=[];
for(const age of ['new_30d','old_over_30d']){
 const c=a.manifest.charts.find(c=>c.id==='pen-'+age),label=age==='new_30d'?'新用户':'老用户';const ds='verified-bettors-'+age;
 const rows=['APP','H5'].map(platform=>({渠道:platform,...Object.fromEntries(['Tada','PP'].map(provider=>[provider,d.overview.find(r=>r.platform===platform&&r.provider===provider&&r.age===age).bettors]))}));
 a.snapshot.datasets[ds]=rows;c.title=label+'下注人数';c.subtitle='统计期内该厂商去重下注人数；按行为日注册时长分组。活跃分母待核，当前展示人数而非渗透率。';c.dataset=ds;c.encodings.y.label='去重下注人数（人）';delete c.unit;c.valueFormat='number';chartChanges.push(structuredClone(c));
}
a.snapshot.status='partial';a.manifest.reportContract.metrics.find(m=>m.field==='penetration').definition='厂商下注人数÷原平台用户日表去重账号数；除法可复算，但活跃业务含义待核，当前不作活跃渗透率展示';a.manifest.reportContract.metrics.find(m=>m.field==='penetration').denominator='原平台用户日表去重账号数（尚未认证为活跃用户）';
a.manifest.reportContract.openQuestions.push({parameter:'active_denominator',question:'原日表是否由AL/AQ/LOGIN/LOGOUT事件生成且与起源活跃视图同集合？'});
fs.writeFileSync(dir+'macro-patch.json',JSON.stringify({patches,charts:chartChanges,datasets:Object.fromEntries(chartChanges.map(c=>[c.dataset,a.snapshot.datasets[c.dataset]])),metric:a.manifest.reportContract.metrics.find(m=>m.field==='penetration'),openQuestion:a.manifest.reportContract.openQuestions.at(-1),newIntro,verified,pending,formula,oldIntro,oldPending},null,2));
fs.writeFileSync(dir+'artifact.candidate.json',JSON.stringify(a,null,2)+'\n');
const md=a.manifest.blocks.map(b=>b.type==='markdown'?b.body:(()=>{const c=a.manifest.charts.find(c=>c.id===b.chartId);return '### '+c.title+'\n\n'+c.subtitle+'\n\n图表见同名HTML；精确数据保存在artifact.json的'+c.dataset+'中。';})()).join('\n\n')+'\n';fs.writeFileSync(dir+'md.candidate',md);
console.log('Prepared source-bounded correction, pending rates replaced by verified bettor counts.');

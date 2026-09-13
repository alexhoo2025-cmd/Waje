import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(dir,'../..');
const read=n=>JSON.parse(fs.readFileSync(path.join(base,n),'utf8'));
const artifact=read('artifact.json'),A=read('analysis-results.json'),core=read('core-corrected.json');
const f=n=>n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const chartRows=[],meanRows=[],rtpRows=[],verified=[];
for(const [age,label] of [['all_ages','全体'],['new_30d','新用户'],['old_over_30d','老用户']])for(const platform of ['APP','H5']){
 const row={'渠道与人群':platform+'·'+label,'人群':label,'渠道':platform,'统计期':'2026-08-01—2026-09-07'};
 const t={};
 for(const provider of ['Tada','PP']){
  const r=core.find(r=>r.product_mode==='Waje'&&r.time_grain==='period'&&r.segment_grain==='platform'&&r.platform_group===platform&&r.provider_group===provider&&r.age_segment===age);
  const a=A.overview.find(r=>r.platform===platform&&r.provider===provider&&r.age===age);assert(r.bettors>0&&r.stake>0);assert.equal(r.stake,a.stake);assert.equal(r.bettors,a.bettors);assert(Math.abs(r.payout/r.stake-a.settlement_rtp)<1e-12);
  t[provider]={mean:r.stake/r.bettors,accounts:r.bettors};row[provider]=r.stake/r.bettors/10000;row[provider+'下注总额']=r.stake;row[provider+'下注人数']=r.bettors;
  rtpRows.push({'组合':platform+'·'+provider,'人群':label,'下注额（亿）':f(r.stake/1e8),'对应派奖（亿）':f(r.payout/1e8),'结算RTP':f(100*r.payout/r.stake)+'%','下注减派奖（亿）':f((r.stake-r.payout)/1e8)});
  verified.push({platform,provider,age,stake:r.stake,payout:r.payout,bettors:r.bettors,per_bettor:r.stake/r.bettors,rtp:r.payout/r.stake});
 }
 chartRows.push(row);meanRows.push({'渠道与人群':row['渠道与人群'],'Tada下注人数':t.Tada.accounts.toLocaleString('en-US'),'PP下注人数':t.PP.accounts.toLocaleString('en-US'),'Tada人均（万）':f(t.Tada.mean/10000),'PP人均（万）':f(t.PP.mean/10000),'Tada／PP（倍）':f(t.Tada.mean/t.PP.mean)});
}
const meanNote='### 人均下注额：按实际下注人数比较\n\n**全期人均下注额，Tada在APP约为PP的7.02倍，H5约6.39倍。** 下图分别展示全体、新、老用户，避免把总额优势直接理解成人均优势。\n\n统计期为2026年8月1日—9月7日。人均下注额＝同渠道、同人群、同厂商的有效下注总额÷该厂商全期去重下注人数；单位为万报表单位／人。它不是平台活跃人均、局均金额、每日人均的平均值或用户收益。新用户按行为当天注册0—29天、老用户按30天及以上划分，不按充值状态划分；同一人可在期内跨组，各组人数不相加。\n\n**分组结果也不同：** 新用户中，Tada／PP人均下注额比为APP 6.60倍、H5 3.33倍；老用户为7.57倍、8.80倍。均值仍可能受少数高额下注用户影响，不能代表典型用户。';
const rtpNote='### RTP对照：结算回报与下注规模分开看\n\n**全体用户的结算RTP，Tada为APP 96.94%、H5 97.05%；PP为95.99%、95.58%。** 下表进一步拆分新老用户，避免用厂商总平均替代不同人群的表现。\n\n统计期为2026年8月1日—9月7日；结算RTP＝同范围游戏结算记录的对应派奖÷有效下注额，按金额汇总计算，不平均各游戏的RTP。下注额已扣除退款及已确认重复记录；现金与奖励资产尚未完全拆分。\n\n**RTP用于观察结算回报，不作为上图下注额三因素分解的第四项。** 当前结果不是理论RTP配置，也不能据此认定较高RTP造成了更多下注。下注减派奖仅为该结算口径差额，不等同于净利润或平台充值减提现。';
const chart={...structuredClone(artifact.manifest.charts.find(c=>c.id==='share-chart')),id:'per-bettor-chart',title:'全期人均下注额：Tada与PP',subtitle:'2026年8月1日—9月7日；有效下注总额÷全期去重下注人数；万报表单位／人',dataset:'per-bettor-chart',question:'同渠道同人群的平均下注深度有何差异',rationale:'六个人群渠道组合、两厂商，使用零起点分组柱形图；全期人均不与每日人均混用。',encodings:{x:{field:'渠道与人群',type:'nominal',label:'渠道与人群'},y:{fields:['Tada','PP'],type:'quantitative',format:'number',label:'人均下注额（万／人）'}}};
const table=(id,title,rows)=>({id,title,dataset:id,sourceId:'src-analysis',layout:'full',columns:Object.keys(rows[0]).map(field=>({field,label:field,type:'text'}))});
const tables=[table('per-bettor-table','人均下注额与去重下注人数',meanRows),table('rtp-age-table','全体及新老用户结算RTP',rtpRows)];
const meanBlocks=[{id:'per-bettor-note',type:'markdown',body:meanNote,sourceId:'src-analysis'},{id:'per-bettor-chart-block',type:'chart',chartId:chart.id},{id:'per-bettor-table-block',type:'table',tableId:tables[0].id}];
const rtpBlocks=[{id:'rtp-age-note',type:'markdown',body:rtpNote,sourceId:'src-analysis'},{id:'rtp-age-table-block',type:'table',tableId:tables[1].id}];
const objectLines=(o,indent)=>JSON.stringify(o,null,2).split('\n').map(l=>' '.repeat(indent)+l).join('\n');
const additions=[['    "charts": [','    "charts": [\n'+objectLines(chart,6)+','],['    "tables": [','    "tables": [\n'+tables.map(t=>objectLines(t,6)+',').join('\n')],['        "id": "drivers",',null]];
const oldDriver=artifact.manifest.blocks.find(b=>b.id==='drivers').body;
const newDriver=oldDriver.replace('## 03｜人数、局次和局均金额共同扩大Tada优势','## 03｜人数、下注深度与RTP：规模和回报分开看');
const artifactText=fs.readFileSync(path.join(base,'artifact.json'),'utf8');let next=artifactText;
next=next.replace('    "charts": [','    "charts": [\n'+objectLines(chart,6)+',');
next=next.replace('    "tables": [','    "tables": [\n'+tables.map(t=>objectLines(t,6)+',').join('\n'));
next=next.replace('      {\n        "id": "drivers",',meanBlocks.map(b=>objectLines(b,6)+',').join('\n')+'\n      {\n        "id": "drivers",');
next=next.replace('      {\n        "id": "depth-block",',rtpBlocks.map(b=>objectLines(b,6)+',').join('\n')+'\n      {\n        "id": "depth-block",');
const datasets={'per-bettor-chart':chartRows,'per-bettor-table':meanRows,'rtp-age-table':rtpRows};
next=next.replace('    "datasets": {','    "datasets": {\n'+Object.entries(datasets).map(([k,v])=>'      '+JSON.stringify(k)+': '+JSON.stringify(v,null,2).split('\n').join('\n      ')+',').join('\n'));
next=next.replace(JSON.stringify(oldDriver),JSON.stringify(newDriver));const parsed=JSON.parse(next);assert.equal(parsed.manifest.charts.length,artifact.manifest.charts.length+1);assert.equal(parsed.manifest.blocks.length,artifact.manifest.blocks.length+5);
for(const name of ['artifact.json','报告.md','build_report.py']){assert(!fs.existsSync(path.join(dir,name+'.before')));fs.copyFileSync(path.join(base,name),path.join(dir,name+'.before'));}
fs.copyFileSync(path.resolve(base,'../../output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html'),path.join(dir,'report.before.html'));
fs.writeFileSync(path.join(dir,'artifact.candidate.json'),next);
const markdownTable=(t,rows)=>'### '+t.title+'\n\n| '+t.columns.map(c=>c.label).join(' | ')+' |\n| '+t.columns.map(()=> '---').join(' | ')+' |\n'+rows.map(r=>'| '+t.columns.map(c=>r[c.field]).join(' | ')+' |').join('\n');
const meanMD=meanNote+'\n\n![全期人均下注额：Tada与PP](lark-assets/per-bettor-chart-block.png)\n\n'+markdownTable(tables[0],meanRows);
const rtpMD=rtpNote+'\n\n'+markdownTable(tables[1],rtpRows);
fs.writeFileSync(path.join(dir,'md.candidate'),fs.readFileSync(path.join(base,'报告.md'),'utf8').replace(oldDriver,meanMD+'\n\n'+newDriver).replace('### 下注深度与结算回报',rtpMD+'\n\n### 下注深度与结算回报'));
const pyRows=rows=>JSON.stringify(rows).replace(/true/g,'True').replace(/false/g,'False').replace(/null/g,'None');
const pyTable=(t,rows)=>'table('+JSON.stringify(t.id)+','+JSON.stringify(t.title)+','+pyRows(rows)+','+JSON.stringify(t.columns.map(c=>[c.field,c.label]))+')';
const pyMean='md("per-bettor-note",'+JSON.stringify(meanNote)+',"src-analysis")\nchart("per-bettor-chart","全期人均下注额：Tada与PP",'+pyRows(chartRows)+',"bar","渠道与人群",["Tada","PP"],"渠道与人群","人均下注额（万／人）",subtitle="2026年8月1日—9月7日；有效下注总额÷全期去重下注人数；万报表单位／人")\n'+pyTable(tables[0],meanRows)+'\n';
const pyRtp='md("rtp-age-note",'+JSON.stringify(rtpNote)+',"src-analysis")\n'+pyTable(tables[1],rtpRows)+'\n';
let py=fs.readFileSync(path.join(base,'build_report.py'),'utf8');py=py.replace("md('drivers',",pyMean+"md('drivers',").replace('## 03｜人数、局次和局均金额共同扩大Tada优势','## 03｜人数、下注深度与RTP：规模和回报分开看').replace("table('depth',",pyRtp+"table('depth',");fs.writeFileSync(path.join(dir,'py.candidate'),py);
fs.writeFileSync(path.join(dir,'data.json'),JSON.stringify({meanNote,rtpNote,chart,chartRows,tables,meanRows,rtpRows,verified,oldDriver,newDriver,chart_contract:{surface:'canonical HTML and matching Lark PNG',family:'grouped bar',categories:6,series:2,unit:'万报表单位/去重下注用户',zero_baseline:true,palette:'existing two-series blue/gold',qa:'portable verifier and exported PNG',rtp_table_reason:'精确对照接近100%的RTP，避免用截断轴放大差异'},online_queries_run:false},null,2));
console.log('Candidates and verified data prepared; apply narrow diffs before rendering.');

export function fixture(type='business'){
 const title={business:'经营对比验收样例（模拟数据）',retention:'留存验收样例（模拟数据）',research:'调研验收样例（模拟数据）',mechanism:'机制验收样例（模拟数据）'}[type];
 const rows=Array.from({length:8},(_,i)=>({group:`样例${i+1}`,n:(i+1)*10,d:100,rate:(i+1)/10,rate_pct:(i+1)*10,percent_base:100}));
 const field=type==='retention'?'rate':'n',displayField=type==='retention'?'rate_pct':'n',unit=field==='rate'?'%':type==='research'?'项':'人';
 const numerator=type==='research'?'已确认功能项':type==='retention'?'回访人数':'参与人数';
 const denominator=type==='research'?'已检查功能项':type==='retention'?'成熟起点人数':'同组活跃人数';
 return {surface:'report',manifest:{version:1,surface:'report',title,generatedAt:'2026-01-15T00:00:00Z',sources:[{id:'s',path:'analysis/report_standard_upgrade_2026_09_09/fixtures/synthetic.sql',query:{engine:'SQLite synthetic fixture',sql:rows.map((r,i)=>`${i?'UNION ALL ':''}SELECT '${r.group}' AS "group", ${r.n} AS n, 100 AS d, ${r.rate} AS rate, ${r.rate_pct} AS rate_pct, 100 AS percent_base`).join('\n'),description:'合成验收数据，不用于业务结论',metric_definitions:[`n为合成${numerator}，d为合成${denominator}；rate=n/d，rate_pct=rate×100只用于百分数坐标显示，不代表真实业务。`],tables_used:['synthetic SQLite SELECT rows']}}],
 reportContract:{type,language:'zh',population:type==='research'?'8个合成品牌的功能检查；不代表市场份额':type==='retention'?'注册当日为新用户的合成批次':'账号龄30天内的合成样本',period:type==='research'?'2026年1月合成静态快照；不是时间趋势':'2026-01-01至2026-01-14；模拟窗口',timezone:type==='research'?'静态来源期，无跨日事件':'Asia/Hong_Kong',metrics:[{dataset:'d',field,unit,definition:field==='rate'?`合成${numerator}÷合成${denominator}`:`合成${numerator}计数`,kind:field==='rate'?'ratio':'count',...(field==='rate'?{denominator,scale:'fraction',min:0,max:1}:{})}],assertions:[{kind:'ratio',dataset:'d',numerator:'n',denominator:'d',actual:'rate'}],decisions:{},openQuestions:[]},
 blocks:[{id:'title',type:'markdown',body:'# '+title},{id:'summary',type:'markdown',body:'## 执行摘要\n\n**这是模拟验收数据。** 仅检查结构与读取方式，不代表真实经营结果。\n\n**按相同规则比较。** 指标、单位与分母来自同一份合成记录。'},
 {id:'finding',type:'markdown',body:'## 01｜同口径比较\n\n这张图只用于核验模板能否清楚呈现分组结果；数据为模拟数据，不能作为实际产品结论。'},
 {id:'cb',type:'chart',chartId:'c'},{id:'tb',type:'table',tableId:'t'},
 {id:'action',type:'markdown',body:'## 02｜下一步\n\n**真实报告需要实际证据。** 填入最后确认的人群、时间和统计来源，再进行业务分析与交付验收。'}],
 charts:[{id:'c',title:'合成分组对照',type:'bar',dataset:'d',sourceId:'s',layout:'full',encodings:{x:{field:'group',type:'nominal',label:'样例'},y:{field:displayField,type:'quantitative',label:field==='rate'?'回访率（%）':`${numerator}（${unit}）`,format:'number',unit}}}],
 tables:[{id:'t',title:'合成记录与分母',dataset:'d',sourceId:'s',defaultSort:{field:'group',direction:'asc'},columns:[{field:'group',label:'样例',type:'text'},{field:'n',label:numerator,type:'number'},{field:'d',label:denominator,type:'number'},{field:'rate',label:'合成比例',type:'number',format:'percent'}]}]},
 snapshot:{version:1,generatedAt:'2026-01-15T00:00:00Z',status:'fixture',datasets:{d:rows}}};
}
export const mechanismXml='<title>机制模板验收样例（模拟数据）</title><h1>先看结论</h1><p><b>每次请求只有一个最终结果。</b> 这是一条模拟流程说明，不代表线上机制。</p><p><b>点击与结果分别记录。</b> 不可比的数据不能混算；不得上传凭据或个人资料。</p><h1>流程与验收</h1><p>进入请求 → 条件检查 → 结果确认。没有经营数据时保留流程说明，不制作经营趋势图。</p>';

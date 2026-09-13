import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const base=path.resolve("analysis/top30_tc_uidlog_2026_09_10");
const result=JSON.parse(await fs.readFile(path.join(base,"aggregate-result-final.json"),"utf8"));
const receipt=JSON.parse(await fs.readFile(path.join(base,"query-receipt-final.json"),"utf8"));
const outputDir=path.resolve("outputs/019fc549-3241-7d52-90f5-0b39c2e03530");
const outputPath=path.join(outputDir,"9月10日资产变动汇总_前30.xlsx");
const font="Arial",navy="#17324D",blue="#2F75B5",orange="#ED7D31",lightBlue="#DCEAF7",lightGray="#F3F6F8",line="#D7E0E7",green="#70AD47",red="#C0504D";
const wb=Workbook.create();
const summary=wb.worksheets.add("摘要");
const timing=wb.worksheets.add("时段明细");
const codes=wb.worksheets.add("共同变动代码");
const raw=wb.worksheets.add("聚合数据");
const notes=wb.worksheets.add("查询说明");
for(const s of [summary,timing,codes,raw,notes])s.showGridLines=false;
summary.tabColor=blue;timing.tabColor="#5B9BD5";codes.tabColor=orange;raw.tabColor="#A5A5A5";notes.tabColor="#A5A5A5";

function title(sheet,title,subtitle,lastCol){
 sheet.mergeCells(`A1:${lastCol}1`);sheet.getRange("A1").values=[[title]];sheet.getRange("A1").format.font={name:font,size:18,bold:true,color:navy};sheet.getRange("A1").format.rowHeight=30;
 sheet.mergeCells(`A2:${lastCol}2`);sheet.getRange("A2").values=[[subtitle]];sheet.getRange("A2").format.font={name:font,size:10,italic:true,color:"#5F6B76"};sheet.getRange(`A3:${lastCol}3`).format.borders={bottom:{style:"thin",color:blue}};
}
function header(range){range.format={fill:navy,font:{name:font,size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",verticalAlignment:"center",wrapText:true,borders:{insideVertical:{style:"thin",color:"#FFFFFF"},bottom:{style:"thin",color:navy}}};}
function band(sheet,range,text){sheet.mergeCells(range);const c=sheet.getRange(range.split(":")[0]);c.values=[[text]];c.format={fill:lightBlue,font:{name:font,size:11,bold:true,color:navy},verticalAlignment:"center"};}
const overall=result.find(r=>r.section==="总体");
const assets=result.filter(r=>r.section==="资产").sort((a,b)=>a.asset_key.localeCompare(b.asset_key));
const times=result.filter(r=>r.section==="时段").sort((a,b)=>a.asset_key.localeCompare(b.asset_key)||a.time_key.localeCompare(b.time_key));
const codeRows=result.filter(r=>r.section==="变动代码").sort((a,b)=>a.asset_key.localeCompare(b.asset_key)||b.event_count-a.event_count);
const displayedAssetEvents=assets.reduce((s,r)=>s+r.event_count,0);
const eventTotal=overall.event_count;
const suppressedAssetEvents=eventTotal-displayedAssetEvents;
const codeCoverage=codeRows.reduce((s,r)=>s+r.event_count,0)/eventTotal;

title(summary,"9月10日资产变动汇总","TC差值前30名用户｜2026-09-10｜Waje Special｜聚合且脱敏","H");
summary.getRange("A5:H5").values=[["样本用户","有资产事件用户","资产事件数","筛选期TC差值","筛选期充值","筛选期提现","前30门槛","最终SQL扫描"]];header(summary.getRange("A5:H5"));
summary.getRange("A6:H6").values=[[receipt.selection.count,overall.user_count,overall.event_count,receipt.selection.total_tc_gap,receipt.selection.total_recharge,receipt.selection.total_withdraw,receipt.selection.cutoff_tc_gap,receipt.query.bytes_processed]];
summary.getRange("A6:C6").format.numberFormat="#,##0";summary.getRange("D6:G6").format.numberFormat="#,##0.00";summary.getRange("H6").format.numberFormat='0.00,,"M bytes"';summary.getRange("A6:H6").format.font={name:font,size:11,bold:true,color:navy};
summary.mergeCells("A7:H7");summary.getRange("A7").values=[["注：TC差值、充值和提现来自源Excel的筛选时间段，仅用于选出前30名；下方资产变动只统计9月10日。"]];summary.getRange("A7").format={fill:"#FFF2CC",font:{name:font,size:9,color:"#7F6000"},wrapText:true};
band(summary,"A9:H9","按资产ID汇总（不同资产单位不可相加）");
summary.getRange("A10:H10").values=[["资产ID","覆盖用户","事件数","事件占比","流入","流出","净变动","净变动/总流量"]];header(summary.getRange("A10:H10"));
summary.getRange("A11:C14").values=assets.map(r=>[r.asset_key.replace("asset_id=",""),r.user_count,r.event_count]);
summary.getRange("E11:G14").values=assets.map(r=>[r.inflow,r.outflow,r.net_change]);
for(let i=11;i<=14;i++){summary.getRange(`D${i}`).formulas=[[`=C${i}/$C$6`]];summary.getRange(`H${i}`).formulas=[[`=G${i}/(E${i}+F${i})`]];}
summary.getRange("B11:C14").format.numberFormat="#,##0";summary.getRange("D11:D14").format.numberFormat="0.0%";summary.getRange("E11:G14").format.numberFormat="#,##0";summary.getRange("H11:H14").format.numberFormat="0.00%";
summary.getRange("A11:H14").format.borders={bottom:{style:"thin",color:line}};summary.getRange("H11:H14").conditionalFormats.add("cellIs",{operator:"lessThan",formula:0,format:{fill:"#FDE9E7",font:{color:red,bold:true}}});summary.getRange("H11:H14").conditionalFormats.add("cellIs",{operator:"greaterThanOrEqual",formula:0,format:{fill:"#E2F0D9",font:{color:"#38761D",bold:true}}});
band(summary,"A16:H16","结论摘要");
const asset5002=assets.find(r=>r.asset_key.endsWith("5002")),asset5001=assets.find(r=>r.asset_key.endsWith("5001"));
const findings=[
 `前30名全部匹配到9月10日资产日志，共${overall.event_count.toLocaleString()}条，覆盖00:00至23:59。`,
 `asset_id=5002占${(asset5002.event_count/eventTotal*100).toFixed(1)}%事件，asset_id=5001占${(asset5001.event_count/eventTotal*100).toFixed(1)}%；另有${suppressedAssetEvents.toLocaleString()}条事件来自不足10名用户的低覆盖资产，已合并抑制。`,
 `四类资产的净变动占总流量均在±2%以内，呈现高频流入与流出近似对冲；不能把总流水直接理解为实际盈亏。`,
 `共同变动代码（至少10名用户）覆盖${(codeCoverage*100).toFixed(1)}%事件；未达到10人的代码已合并抑制，不展示用户级记录。`,
 `BigQuery未提供页面中文原因和资产名称的完整字典，报告保留asset_id、change_type与GET/COST原始口径，不做未经验证的业务命名。`
];
findings.forEach((t,i)=>{const row=17+i;summary.mergeCells(`A${row}:H${row}`);summary.getRange(`A${row}`).values=[[`${i+1}. ${t}`]];summary.getRange(`A${row}`).format={fill:i%2?lightGray:"#FFFFFF",font:{name:font,size:10,color:navy},wrapText:true,verticalAlignment:"center"};summary.getRange(`A${row}:H${row}`).format.rowHeight=28;});
summary.getRange("A1:H21").format.columnWidth=16;summary.getRange("A1:A21").format.columnWidth=15;summary.getRange("H1:H21").format.columnWidth=18;

summary.getRange("J9:K13").values=[["资产ID","事件数"],...assets.map(r=>[r.asset_key.replace("asset_id=",""),r.event_count])];
const c1=summary.charts.add("bar",summary.getRange("J9:K13"));c1.title="事件量按资产ID";c1.titleTextStyle.fontSize=12;c1.titleTextStyle.typeface=font;c1.hasLegend=false;c1.xAxis={axisType:"textAxis",textStyle:{typeface:font,fontSize:10}};c1.yAxis={numberFormatCode:"#,##0",numberFormatSourceLinked:false,textStyle:{typeface:font,fontSize:9}};c1.setPosition("J1","Q11");c1.series.items[0].fill=blue;
summary.getRange("J16:K20").values=[["资产ID","净变动/总流量"],...assets.map((r,i)=>[r.asset_key.replace("asset_id=",""),`=H${11+i}`])];
const c2=summary.charts.add("bar",summary.getRange("J16:K20"));c2.title="净变动占总流量";c2.titleTextStyle.fontSize=12;c2.titleTextStyle.typeface=font;c2.hasLegend=false;c2.xAxis={axisType:"textAxis",textStyle:{typeface:font,fontSize:10}};c2.yAxis={numberFormatCode:"0.0%",numberFormatSourceLinked:false,textStyle:{typeface:font,fontSize:9}};c2.setPosition("J12","Q22");c2.series.items[0].fill=orange;

title(timing,"9月10日分时资产变化","每个资产ID按Africa/Lagos业务时段汇总；仅展示至少10名用户的时段","J");
timing.getRange("A5:J5").values=[["资产ID","时段","覆盖用户","事件数","流入","流出","净变动","净变动/总流量","首条时间","末条时间"]];header(timing.getRange("A5:J5"));
timing.getRange(`A6:J${5+times.length}`).values=times.map(r=>[r.asset_key.replace("asset_id=",""),r.time_key,r.user_count,r.event_count,r.inflow,r.outflow,r.net_change,null,r.first_event_time?.slice(11,19),r.last_event_time?.slice(11,19)]);
for(let i=6;i<6+times.length;i++)timing.getRange(`H${i}`).formulas=[[`=G${i}/(E${i}+F${i})`]];
timing.getRange(`C6:D${5+times.length}`).format.numberFormat="#,##0";timing.getRange(`E6:G${5+times.length}`).format.numberFormat="#,##0";timing.getRange(`H6:H${5+times.length}`).format.numberFormat="0.00%";timing.getRange(`A6:J${5+times.length}`).format.borders={bottom:{style:"thin",color:line}};
timing.getRange(`H6:H${5+times.length}`).conditionalFormats.add("colorScale",{colors:["#F4CCCC","#FFFFFF","#D9EAD3"],thresholds:["min",{type:"num",value:0},"max"]});
timing.getRange("A1:A40").format.columnWidth=12;timing.getRange("B1:B40").format.columnWidth=12;timing.getRange("C1:H40").format.columnWidth=14;timing.getRange("I1:J40").format.columnWidth=14;timing.freezePanes.freezeRows(5);
const buckets=["00–05时","06–11时","12–17时","18–23时"];
timing.getRange("L5:M9").values=[["时段","事件数"],...buckets.map(b=>[b,times.filter(r=>r.time_key===b).reduce((s,r)=>s+r.event_count,0)])];
const c3=timing.charts.add("bar",timing.getRange("L5:M9"));c3.title="各时段事件量";c3.titleTextStyle.fontSize=12;c3.titleTextStyle.typeface=font;c3.hasLegend=false;c3.xAxis={axisType:"textAxis",textStyle:{typeface:font,fontSize:10}};c3.yAxis={numberFormatCode:"#,##0",numberFormatSourceLinked:false,textStyle:{typeface:font,fontSize:9}};c3.setPosition("L11","S24");c3.series.items[0].fill=blue;

title(codes,"共同变动代码","仅展示同一代码至少覆盖10名用户的聚合结果；代码名称未映射为业务中文原因","I");
codes.getRange("A5:I5").values=[["资产ID","change_type","方向","覆盖用户","事件数","流入","流出","净变动","占该资产事件"]];header(codes.getRange("A5:I5"));
const parsed=codeRows.map(r=>{const m=r.reason_key.match(/change_type=([^|]+) \| direction=(.+)$/);const total=assets.find(a=>a.asset_key===r.asset_key).event_count;return[r.asset_key.replace("asset_id=",""),m[1].trim(),m[2].trim(),r.user_count,r.event_count,r.inflow,r.outflow,r.net_change,r.event_count/total];});
codes.getRange(`A6:I${5+parsed.length}`).values=parsed;codes.getRange(`D6:H${5+parsed.length}`).format.numberFormat="#,##0";codes.getRange(`I6:I${5+parsed.length}`).format.numberFormat="0.0%";codes.getRange(`A6:I${5+parsed.length}`).format.borders={bottom:{style:"thin",color:line}};
for(let i=6;i<6+parsed.length;i++){const dir=parsed[i-6][2];codes.getRange(`C${i}`).format={fill:dir==="GET"?"#E2F0D9":"#FCE4D6",font:{name:font,size:10,bold:true,color:dir==="GET"?"#38761D":"#9C4A09"},horizontalAlignment:"center"};}
codes.mergeCells(`A${7+parsed.length}:I${7+parsed.length}`);codes.getRange(`A${7+parsed.length}`).values=[[`以上共同代码覆盖${(codeCoverage*100).toFixed(1)}%的9月10日事件；其余代码因单组少于10人不单列。`]];codes.getRange(`A${7+parsed.length}`).format={fill:"#FFF2CC",font:{name:font,size:9,color:"#7F6000"},wrapText:true};
codes.getRange("A1:A50").format.columnWidth=12;codes.getRange("B1:B50").format.columnWidth=18;codes.getRange("C1:C50").format.columnWidth=12;codes.getRange("D1:I50").format.columnWidth=15;codes.freezePanes.freezeRows(5);

const rawHeaders=["section","asset_key","reason_key","time_key","user_count","event_count","inflow","outflow","net_change","min_after_balance","max_after_balance","first_event_time","last_event_time"];
raw.getRange("A1:M1").values=[rawHeaders];header(raw.getRange("A1:M1"));raw.getRange(`A2:M${1+result.length}`).values=result.map(r=>rawHeaders.map(k=>r[k]));raw.getRange(`E2:K${1+result.length}`).format.numberFormat="#,##0";raw.getRange("A:M").format.columnWidth=18;raw.getRange("C:C").format.columnWidth=38;raw.freezePanes.freezeRows(1);raw.tables.add(`A1:M${1+result.length}`,true,"AggregateData");

title(notes,"查询口径与限制","可复算查询信息；不保存或展示前30名UID","B");
const noteRows=[
 ["统计日期","2026-09-10（单日）"],["用户选择","源Excel按“时间段内TC差值”降序前30名"],["源文件","提现大于充值9.10.xlsx"],["源文件SHA-256",receipt.source.sha256],["源记录数",receipt.source.source_rows],["前30门槛",receipt.selection.cutoff_tc_gap],["BigQuery表","wajenigeria.origin_hfyl.realtime_event_server"],["必要过滤","target_day=2026-09-10；app_id=90006；event_type=ASSET"],["最终SQL","uidlog_aggregate_final.sql"],["BigQuery Job",receipt.query.job_id],["实际扫描字节",receipt.query.bytes_processed],["隐私处理","UID仅作为内存数组参数；查询文件、结果和工作簿均不保存UID；分组少于10人不展示"],["解释限制","资产ID与变动代码未取得业务字典；GET/COST只表示流入/流出方向，不替代业务原因"],["金额限制","不同资产ID可能使用不同单位，不跨资产求和或解释为人民币/奈拉盈亏"],["来源页面","http://35.181.27.61:3001/question/4-uid-log"]
];
notes.getRange("A5:B5").values=[["项目","内容"]];header(notes.getRange("A5:B5"));notes.getRange(`A6:B${5+noteRows.length}`).values=noteRows;notes.getRange(`A6:A${5+noteRows.length}`).format.font={name:font,size:10,bold:true,color:navy};notes.getRange(`A6:B${5+noteRows.length}`).format.borders={bottom:{style:"thin",color:line}};notes.getRange("A:A").format.columnWidth=20;notes.getRange("B:B").format.columnWidth=90;notes.getRange(`B6:B${5+noteRows.length}`).format.wrapText=true;notes.getRange(`B6:B${5+noteRows.length}`).format.rowHeight=28;

for(const s of [summary,timing,codes,raw,notes]){const used=s.getUsedRange();used.format.verticalAlignment="center";}
const checks=[];
for(const [sheetName,range] of [["摘要","A1:H21"],["时段明细",`A1:J${5+times.length}`],["共同变动代码",`A1:I${7+parsed.length}`],["查询说明",`A1:B${5+noteRows.length}`]]){
 const x=await wb.inspect({kind:"table",range:`${sheetName}!${range.split("!").pop()}`,include:"values,formulas",tableMaxRows:30,tableMaxCols:12,maxChars:9000});checks.push({sheetName,inspect:x.ndjson});
 const image=await wb.render({sheetName,autoCrop:"all",scale:1,format:"png"});await fs.writeFile(path.join(base,`preview-${sheetName}.png`),new Uint8Array(await image.arrayBuffer()));
}
const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:300},summary:"final formula error scan"});
await fs.writeFile(path.join(base,"workbook-verification.json"),JSON.stringify({checks,errorScan:errors.ndjson,assetEventTotal:eventTotal,codeCoverage},null,2));
await fs.mkdir(outputDir,{recursive:true});const out=await SpreadsheetFile.exportXlsx(wb);await out.save(outputPath);console.log(JSON.stringify({outputPath,sheets:5,charts:3,events:eventTotal,codeCoverage}));

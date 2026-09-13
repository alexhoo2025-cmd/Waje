import fs from "node:fs/promises";
import path from "node:path";
import {FileBlob,SpreadsheetFile}from"@oai/artifact-tool";
const root=path.resolve("analysis/top30_tc_uidlog_2026_09_10"),file=path.resolve("outputs/019fc549-3241-7d52-90f5-0b39c2e03530/9月10日资产变动汇总_前30.xlsx");
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(file));
const dict=JSON.parse(await fs.readFile(path.join(root,"asset-change-dictionary.json"),"utf8"));
const result=JSON.parse(await fs.readFile(path.join(root,"aggregate-result-final.json"),"utf8"));
const receipt=JSON.parse(await fs.readFile(path.join(root,"query-receipt-final.json"),"utf8"));
const font="Arial",navy="#17324D",blue="#2F75B5",lightBlue="#DCEAF7",lightGray="#F3F6F8",line="#D7E0E7",orange="#ED7D31";
const summary=wb.worksheets.getItem("摘要"),codes=wb.worksheets.getItem("共同变动代码"),notes=wb.worksheets.getItem("查询说明");
const dictionary=wb.worksheets.add("资产变动字典");dictionary.showGridLines=false;dictionary.tabColor="#8064A2";
const title=(sheet,name,sub,last)=>{sheet.mergeCells(`A1:${last}1`);sheet.getRange("A1").values=[[name]];sheet.getRange("A1").format.font={name:font,size:18,bold:true,color:navy};sheet.mergeCells(`A2:${last}2`);sheet.getRange("A2").values=[[sub]];sheet.getRange("A2").format.font={name:font,size:10,italic:true,color:"#5F6B76"};sheet.getRange(`A3:${last}3`).format.borders={bottom:{style:"thin",color:blue}};};
const header=range=>{range.format={fill:navy,font:{name:font,size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",verticalAlignment:"center",wrapText:true,borders:{insideVertical:{style:"thin",color:"#FFFFFF"},bottom:{style:"thin",color:navy}}};};
title(dictionary,"资产变动类型字典",`飞书《资产变动类型》Sheet1｜revision ${dict.metadata.revision}｜有效字典${dict.metadata.dictionary_rows}条｜${dict.metadata.retrieved_at.slice(0,10)}`,"K");
dictionary.getRange("A5:K5").values=[["ares字典值","业务说明","技术字段名","账单详情Type","账单归属","资产变更值","GameId","SubChangeType","H5","APP","源行号"]];header(dictionary.getRange("A5:K5"));
const dictRows=dict.rows.map(r=>[r.ares_code,r.description,r.technical_field,r.bill_detail_type,r.bill_group,r.change_value,r.game_id,r.sub_change_type,r.h5_status,r.app_status,r.source_row]);
dictionary.getRange(`A6:K${5+dictRows.length}`).values=dictRows;dictionary.getRange(`A6:A${5+dictRows.length}`).format.numberFormat="0";dictionary.getRange(`K6:K${5+dictRows.length}`).format.numberFormat="0";dictionary.getRange(`A6:K${5+dictRows.length}`).format.borders={bottom:{style:"thin",color:line}};dictionary.getRange(`B6:E${5+dictRows.length}`).format.wrapText=true;
dictionary.getRange("A:A").format.columnWidth=15;dictionary.getRange("B:B").format.columnWidth=38;dictionary.getRange("C:C").format.columnWidth=34;dictionary.getRange("D:E").format.columnWidth=25;dictionary.getRange("F:K").format.columnWidth=15;dictionary.freezePanes.freezeRows(5);dictionary.tables.add(`A5:K${5+dictRows.length}`,true,"AssetChangeDictionary");

const codeRows=result.filter(r=>r.section==="变动代码").sort((a,b)=>a.asset_key.localeCompare(b.asset_key)||b.event_count-a.event_count);
const assets=result.filter(r=>r.section==="资产");
codes.getRange("A1:L30").clear({applyTo:"all"});title(codes,"共同变动代码",`业务说明通过公式引用“资产变动字典”；仅展示同一代码至少覆盖10名用户的聚合结果`,"L");
codes.getRange("A5:L5").values=[["资产ID","change_type","业务说明","账单详情Type","账单归属","方向","覆盖用户","事件数","流入","流出","净变动","占资产事件"]];header(codes.getRange("A5:L5"));
const parsed=codeRows.map(r=>{const m=r.reason_key.match(/change_type=([^|]+) \| direction=(.+)$/),total=assets.find(a=>a.asset_key===r.asset_key).event_count;return[r.asset_key.replace("asset_id=",""),Number(m[1].trim()),null,null,null,m[2].trim(),r.user_count,r.event_count,r.inflow,r.outflow,r.net_change,r.event_count/total];});
codes.getRange(`A6:L${5+parsed.length}`).values=parsed;
codes.getRange("C6").formulas=[[`=IFERROR(VLOOKUP(B6,'资产变动字典'!$A$6:$E$${5+dictRows.length},2,FALSE),"未映射")`]];codes.getRange(`C6:C${5+parsed.length}`).fillDown();
codes.getRange("D6").formulas=[[`=IFERROR(VLOOKUP(B6,'资产变动字典'!$A$6:$E$${5+dictRows.length},4,FALSE),"")`]];codes.getRange(`D6:D${5+parsed.length}`).fillDown();
codes.getRange("E6").formulas=[[`=IFERROR(VLOOKUP(B6,'资产变动字典'!$A$6:$E$${5+dictRows.length},5,FALSE),"")`]];codes.getRange(`E6:E${5+parsed.length}`).fillDown();
codes.getRange(`A6:B${5+parsed.length}`).format.numberFormat="0";codes.getRange(`G6:K${5+parsed.length}`).format.numberFormat="#,##0";codes.getRange(`L6:L${5+parsed.length}`).format.numberFormat="0.0%";codes.getRange(`A6:L${5+parsed.length}`).format.borders={bottom:{style:"thin",color:line}};
for(let i=6;i<6+parsed.length;i++){const d=parsed[i-6][5];codes.getRange(`F${i}`).format={fill:d==="GET"?"#E2F0D9":"#FCE4D6",font:{name:font,size:10,bold:true,color:d==="GET"?"#38761D":"#9C4A09"},horizontalAlignment:"center"};}
const codeCoverage=codeRows.reduce((s,r)=>s+r.event_count,0)/result.find(r=>r.section==="总体").event_count;
codes.mergeCells(`A${7+parsed.length}:L${7+parsed.length}`);codes.getRange(`A${7+parsed.length}`).values=[[`以上共同代码覆盖${(codeCoverage*100).toFixed(1)}%的9月10日事件；其余代码因单组少于10人不单列。`]];codes.getRange(`A${7+parsed.length}`).format={fill:"#FFF2CC",font:{name:font,size:9,color:"#7F6000"},wrapText:true};
codes.getRange("A:A").format.columnWidth=11;codes.getRange("B:B").format.columnWidth=16;codes.getRange("C:C").format.columnWidth=24;codes.getRange("D:E").format.columnWidth=22;codes.getRange("F:F").format.columnWidth=11;codes.getRange("G:L").format.columnWidth=14;codes.freezePanes.freezeRows(5);

const count=(code,dir=null)=>codeRows.filter(r=>r.reason_key.includes(`change_type=${code} `)&&(!dir||r.reason_key.endsWith(`direction=${dir}`))).reduce((s,r)=>s+r.event_count,0);
const amount=(code,asset,field)=>codeRows.find(r=>r.asset_key===`asset_id=${asset}`&&r.reason_key.includes(`change_type=${code} `))?.[field]??0;
const tadaBet=count(9010301,"COST"),tadaReturn=count(9010302,"GET")+count(9010303,"GET"),feeRatio=amount(9000211,5002,"outflow")/amount(9000002,5002,"outflow");
const findings=[
 `1. 前30名全部匹配到9月10日资产日志，共98,031条，覆盖00:00至23:59。`,
 `2. asset_id=5002占80.4%事件，asset_id=5001占16.2%；另有60条事件来自不足10名用户的低覆盖资产，已合并抑制。`,
 `3. Tada下注代码9010301共${tadaBet.toLocaleString()}条，占全部事件${(tadaBet/98031*100).toFixed(1)}%；是当日最主要的共同变动类型。`,
 `4. Tada返还chip/cash代码9010302和9010303共${tadaReturn.toLocaleString()}条。事件数不能直接换算RTP或输赢。`,
 `5. asset_id=5002中，提现扣除9000002与提现手续费9000211均为380条；手续费变动量约为提现扣除的${(feeRatio*100).toFixed(2)}%。`,
 `6. PP下注9010400与PP cash返还9010403已映射；资产名称仍缺少独立字典，不把5001/5002/5006/5007擅自命名为chip或cash。`
];
for(let i=17;i<=22;i++){try{summary.unmergeCells(`A${i}:H${i}`);}catch{}summary.mergeCells(`A${i}:H${i}`);summary.getRange(`A${i}`).values=[[findings[i-17]]];summary.getRange(`A${i}`).format={fill:i%2?"#FFFFFF":lightGray,font:{name:font,size:10,color:navy},wrapText:true,verticalAlignment:"center"};summary.getRange(`A${i}:H${i}`).format.rowHeight=28;}

const notesData=[
 ["变动类型字典","飞书《资产变动类型》Sheet1，revision 1108"],
 ["字典来源","https://ksg964l11fam.sg.larksuite.com/wiki/SNqfwcET8ivMd6kUdIUlatXXgMc"],
 ["字典入库","283条有效映射；19个重复代码按源表保留；本次使用9个代码均唯一匹配"],
 ["解释口径","change_type按ares字典值匹配业务说明、账单详情Type和账单归属；GET/COST保留为流入/流出方向"],
 ["资产名称限制","该字典不包含asset_id名称，5001/5002/5006/5007仍按原始编号展示"]
];
notes.getRange("A18:B18").values=[["解释限制","变动类型已按飞书字典revision 1108映射；资产ID名称仍缺少独立字典"]];
notes.getRange("A21:B25").values=notesData;notes.getRange("A21:A25").format.font={name:font,size:10,bold:true,color:navy};notes.getRange("A21:B25").format.borders={bottom:{style:"thin",color:line}};notes.getRange("B21:B25").format.wrapText=true;notes.getRange("B21:B25").format.rowHeight=28;

const inspect=await wb.inspect({kind:"table",range:`共同变动代码!A1:L${7+parsed.length}`,include:"values,formulas",tableMaxRows:30,tableMaxCols:14,maxChars:12000});
const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:300},summary:"dictionary integration formula error scan"});
for(const sheetName of["摘要","共同变动代码","资产变动字典","查询说明"]){const image=await wb.render({sheetName,autoCrop:"all",scale:1,format:"png"});await fs.writeFile(path.join(root,`preview-${sheetName}-字典.png`),new Uint8Array(await image.arrayBuffer()));}
await fs.writeFile(path.join(root,"dictionary-integration-verification.json"),JSON.stringify({sourceRevision:dict.metadata.revision,dictionaryRows:dictRows.length,usedCodes:Object.keys(dict.used_code_mapping),inspect:inspect.ndjson,errorScan:errors.ndjson},null,2));
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(file);console.log(JSON.stringify({file,sheets:6,dictionaryRows:dictRows.length,codeRows:parsed.length,tadaBet,tadaReturn,feeRatio}));

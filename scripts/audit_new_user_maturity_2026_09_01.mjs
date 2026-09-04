#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

const runDir = path.resolve("data/outputs/lark_quality/2026-09-01-new-user-maturity-audit");
const backupDir = path.join(runDir, "cells");
const sheets = [
  ["WajeSpecial-facebook", "9cd78d"],
  ["WajeSpecial-googleadwords_int", "xWsChb"],
  ["WajeSpecial-Google商店", "Cfkonh"],
  ["WAJEIOS-AppStore商店", "25iiEi"],
  ["WAJEBETH5", "GrWEoo"],
  ["wajeH5-facebook", "vkV1SD"],
  ["wajeH5ga-googlewords_int", "ef19NP"],
  ["PWA", "gjy6I1"],
];
const fileNames = { "WajeSpecial-facebook": "WajeSpecial-facebook.json", "WajeSpecial-googleadwords_int": "WajeSpecial-googleadwords_int.json", "WajeSpecial-Google商店": "WajeSpecial-Google_.json", "WAJEIOS-AppStore商店": "WAJEIOS-AppStore_.json", WAJEBETH5: "WAJEBETH5.json", "wajeH5-facebook": "wajeH5-facebook.json", "wajeH5ga-googlewords_int": "wajeH5ga-googlewords_int.json", PWA: "PWA.json" };
const fields = [
  ["次日", 1], ["3日", 3], ["4日", 4], ["5日", 5], ["6日", 6], ["7日", 7], ["8日", 8], ["9日", 9], ["10日", 10], ["11日", 11], ["12日", 12], ["13日", 13], ["14日", 14], ["15日", 15], ["30日", 30], ["60日", 60],
  ["次留", 1], ["3日留", 3], ["7日留", 7], ["15日留", 15], ["30日留", 30], ["60日留", 60],
  ["首充次留", 1], ["首充3日留", 3], ["首充7日留", 7], ["首充15日留", 15], ["首充30日留", 30], ["首充60日留", 60],
];
const expectedIssueCount = 470;
function normalize(v) { return String(v ?? "").replace(/[\s\u00a0]+/g, "").trim(); }
function columnName(n) { let x=n+1,out="";while(x>0){const r=(x-1)%26;out=String.fromCharCode(65+r)+out;x=Math.floor((x-1)/26);}return out; }
function dateFrom(v) {
  const text=String(v??"").trim();
  const m=text.replaceAll("/","-").match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if(m)return `${m[1]}-${m[2].padStart(2,"0")}-${m[3].padStart(2,"0")}`;
  if(/^\d+(?:\.\d+)?$/.test(text)){const n=Number(text);if(n>20000&&n<100000)return new Date(Date.UTC(1899,11,30)+Math.round(n)*86400000).toISOString().slice(0,10);}
  return null;
}
function addDays(date, days) { return new Date(Date.parse(`${date}T00:00:00Z`) + days*86400000).toISOString().slice(0,10); }
function value(cell) { return cell?.value ?? ""; }
function blank(v) { return v===null||v===undefined||String(v).trim()===""; }
function assert(ok,msg){if(!ok)throw new Error(msg);}
const issues=[]; const sheetReports={}; const rangeItems=[];
for(const [sheet,id] of sheets){
  const payload=JSON.parse(await fs.readFile(path.join(backupDir,fileNames[sheet]),"utf8"));
  assert(payload.has_more===false,`${sheet}: backup truncated`);
  const cells=payload.ranges?.[0]?.cells||[];
  const headers=cells[0]?.map(value)||[];
  const headerMap=new Map(headers.map((h,i)=>[normalize(h),i]));
  const data=[];
  for(let i=1;i<cells.length;i++){const date=dateFrom(value(cells[i]?.[0]));if(date)data.push({row:i+1,date,cells:cells[i]});}
  assert(data.length>0,`${sheet}: no date rows`);
  const asOf=data.map(x=>x.date).sort().at(-1);
  const perSheet=[];
  for(const [field,days] of fields){
    const ci=headerMap.get(normalize(field));
    assert(ci!==undefined,`${sheet}: missing header ${field}`);
    for(const item of data){
      const cell=item.cells[ci]; const v=value(cell);
      if(blank(v))continue;
      const matureOn=addDays(item.date,days);
      if(matureOn<=asOf)continue;
      assert(!cell?.formula,`${sheet}!${columnName(ci)}${item.row}: invalid maturity value is a formula; refusing to clear formula`);
      const issue={sheet,sheet_id:id,cell:`${columnName(ci)}${item.row}`,row:item.row,date:item.date,field, column:columnName(ci),column_index:ci+1,maturity_days:days,mature_on:matureOn,as_of:asOf,value:v,formula:cell?.formula||null,status:"immature_statistical_window",action:"clear_content_only"};
      issues.push(issue); perSheet.push(issue);
    }
  }
  const byField={};for(const x of perSheet)byField[x.field]=(byField[x.field]||0)+1;
  sheetReports[sheet]={sheet_id:id,backup_file:fileNames[sheet],as_of:asOf,data_rows:data.length,issue_count:perSheet.length,affected_fields:byField,first_issue:perSheet[0]?.cell||null,last_issue:perSheet.at(-1)?.cell||null};
}
assert(issues.length===expectedIssueCount,`expected ${expectedIssueCount} issues, found ${issues.length}; refusing to create execute plan`);
const groups=new Map();
for(const x of issues){const key=`${x.sheet}|${x.column}`;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(x.row);}
for(const [key,rows] of groups){const [sheet,column]=key.split("|");rows.sort((a,b)=>a-b);let start=rows[0],end=rows[0];for(let i=1;i<=rows.length;i++){if(rows[i]===end+1){end=rows[i];continue;}rangeItems.push({sheet,column,start,end,range:`${sheet}!${column}${start}:${column}${end}`,cell_count:end-start+1});if(i<rows.length){start=rows[i];end=rows[i];}}}
const bySheet={};for(const item of rangeItems)(bySheet[item.sheet]??=[]).push(item);
const ranges=rangeItems.map(x=>x.range);
const before={schema_version:1,status:"ready_for_dry_run",generated_at:new Date().toISOString(),workbook:{title:"新包新增用户分析",token:"At8gwdbXUiPa0WkXvKqlSUNKg5d",revision:751},rule:"clear nonblank maturity value when cohort_date + maturity_days > sheet_max_date",as_of_policy:"per sheet max valid date; current max is 2026-08-30",expected_issue_count:expectedIssueCount,issue_count:issues.length,sheets:sheetReports,issues};
const plan={schema_version:1,status:"ready_for_dry_run",generated_at:new Date().toISOString(),workbook:before.workbook,scope:"content only; no rows/columns/formulas/styles/layout/conditional formats",expected_issue_count:expectedIssueCount,issue_count:issues.length,range_count:ranges.length,ranges,by_sheet:bySheet,batch_count:Math.ceil(ranges.length/100),batch_sizes:Array.from({length:Math.ceil(ranges.length/100)},(_,i)=>ranges.slice(i*100,i*100+100).length),assertions:["issue_count == 470","all ranges are exact grouped issue cells","no issue cell has formula","scope=content only","revision must remain 751 before execute"]};
await fs.writeFile(path.join(runDir,"maturity-audit-before.json"),JSON.stringify(before,null,2)+"\n");
await fs.writeFile(path.join(runDir,"maturity-clear-plan.json"),JSON.stringify(plan,null,2)+"\n");
console.log(JSON.stringify({status:"ok",issue_count:issues.length,range_count:ranges.length,batch_count:plan.batch_count,per_sheet:Object.fromEntries(Object.entries(sheetReports).map(([k,v])=>[k,v.issue_count]))},null,2));

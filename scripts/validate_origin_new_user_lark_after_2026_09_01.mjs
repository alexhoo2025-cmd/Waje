#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const MODULE_ROOT = "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(MODULE_ROOT, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const runDir = path.resolve("data/outputs/origin_new_user/2026-09-01-26d");
const beforeDir = path.join(runDir, "lark-backup", "cells");
const afterDir = path.join(runDir, "lark-after", "cells");
const localPath = "/Users/robin/Desktop/waje data/新用户数据分析2026.8.6-8.31_new_AI更新版_Origin复核清零.xlsx";
const dates = Array.from({ length: 25 }, (_, i) => new Date(Date.parse("2026-08-06T00:00:00Z") + i * 86400000).toISOString().slice(0, 10));
const maps = [
  ["WajeSpecial-facebook", "WajeSpecial-facebook", "WajeSpecial-facebook.json", "WajeSpecial-facebook.json", 44],
  ["WajeSpecial-googleadwords_int", "WajeSpecial-googleadwords_int", "WajeSpecial-googleadwords_int.json", "WajeSpecial-googleadwords_int.json", 44],
  ["WajeSpecial-Google商店", "WajeSpecial-Google商店", "WajeSpecial-Google_.json", "WajeSpecial-Google_.json", 44],
  ["wajeios-AppStore商店", "WAJEIOS-AppStore商店", "WAJEIOS-AppStore_.json", "WAJEIOS-AppStore_.json", 44],
  ["wajebetH5-facebook", "WAJEBETH5", "WAJEBETH5.json", "WAJEBETH5.json", 53],
  ["wajeH5-fb", "wajeH5-facebook", "wajeH5-facebook.json", "wajeH5-facebook.json", 44],
  ["wajeH5ga-googlewors_int", "wajeH5ga-googlewords_int", "wajeH5ga-googlewords_int.json", "wajeH5ga-googlewords_int.json", 44],
  ["pww", "PWA", "PWA.json", "PWA.json", 55],
];
const onlineIds = { "WajeSpecial-facebook": "9cd78d", "WajeSpecial-googleadwords_int": "xWsChb", "WajeSpecial-Google商店": "Cfkonh", "WAJEIOS-AppStore商店": "25iiEi", "WAJEBETH5": "GrWEoo", "wajeH5-facebook": "vkV1SD", "wajeH5ga-googlewords_int": "ef19NP", PWA: "gjy6I1" };
const sha = (v) => crypto.createHash("sha256").update(JSON.stringify(v)).digest("hex");
function iso(v) { if (typeof v === "number") return new Date(Date.UTC(1899, 11, 30) + Math.round(v) * 86400000).toISOString().slice(0, 10); const m=String(v??"").trim().replaceAll("/","-").match(/^(\d{4})-(\d{1,2})-(\d{1,2})/); return m?`${m[1]}-${m[2].padStart(2,"0")}-${m[3].padStart(2,"0")}`:null; }
function norm(v) { if (v===null||v===undefined||String(v).trim()==="") return null; if(typeof v==='number') return v; const t=String(v).trim().replaceAll(",",""); if(t.endsWith("%")){const n=Number(t.slice(0,-1));return Number.isFinite(n)?n/100:t;} const n=Number(t);return Number.isFinite(n)?n:t; }
function equal(a,b) { const x=norm(a),y=norm(b); if(x===null||y===null)return x===y; if(typeof x==='number'&&typeof y==='number')return Math.abs(x-y)<=Math.max(0.0001,Math.abs(y)*1e-8); return String(x)===String(y); }
function cellValue(c) { return c?.value ?? ""; }
function cellFormula(c) { return c?.formula ?? ""; }
function cells(payload) { return payload.ranges?.[0]?.cells || []; }
function dataRows(payload) { return cells(payload).map((row,i)=>({row:i+1,cells:row,values:row.map(cellValue),date:iso(cellValue(row[0]))})).filter(x=>x.date); }
function styleSignature(c) { return JSON.stringify({cell_styles:c?.cell_styles||null,border_styles:c?.border_styles||null}); }
function sourceRowsForLocal(wb, sheetName) { return wb.worksheets.getItem(sheetName).getUsedRange(false).values; }
const localWb = await SpreadsheetFile.importXlsx(await FileBlob.load(localPath));
const failures=[]; const reports={}; const snapshots={};
const beforeManifest=JSON.parse(await fs.readFile(path.join(runDir,"backup-manifest.json"),"utf8"));
const writeReceipt=JSON.parse(await fs.readFile(path.join(runDir,"lark-write-receipt.json"),"utf8"));
if(beforeManifest.status!=="complete"||beforeManifest.integrity?.complete!==true) failures.push("backup incomplete");
if(Number(beforeManifest.workbook?.revision)!==732) failures.push("backup revision is not 732");
if(writeReceipt.status!=="ok"||Number(writeReceipt.revision_before)!==732||Number(writeReceipt.revision_after)!==741) failures.push("write receipt revision/status mismatch");

for (const [localName, onlineName, beforeFile, afterFile, onlineCols] of maps) {
  const before=JSON.parse(await fs.readFile(path.join(beforeDir,beforeFile),"utf8"));
  const after=JSON.parse(await fs.readFile(path.join(afterDir,afterFile),"utf8"));
  if(before.has_more!==false||after.has_more!==false) failures.push(`${onlineName}: snapshot truncated`);
  const bRows=cells(before), aRows=cells(after);
  if(JSON.stringify(bRows[0]?.slice(0,43).map(cellValue))!==JSON.stringify(aRows[0]?.slice(0,43).map(cellValue))) failures.push(`${onlineName}: header changed`);
  const bData=dataRows(before), aData=dataRows(after); const startItem=bData.find(x=>x.date===dates[0]);
  const prefixBefore=bRows.slice(0,(startItem?.row||2)-1).map(r=>r.map(c=>({v:cellValue(c),f:cellFormula(c)})));
  const prefixAfter=aRows.slice(0,(startItem?.row||2)-1).map(r=>r.map(c=>({v:cellValue(c),f:cellFormula(c)})));
  if(JSON.stringify(prefixBefore)!==JSON.stringify(prefixAfter)) failures.push(`${onlineName}: history prefix before 8/6 changed`);
  const targetByDate=new Map(); for(const item of aData){if(dates.includes(item.date)){if(targetByDate.has(item.date))failures.push(`${onlineName}: duplicate ${item.date}`);targetByDate.set(item.date,item);}}
  for(const d of dates) if(!targetByDate.has(d)) failures.push(`${onlineName}: missing ${d}`);
  if(aData.some(x=>x.date==="2026-08-31")) failures.push(`${onlineName}: excluded 8/31 present`);
  const localRows=sourceRowsForLocal(localWb,localName); const localByDate=new Map(); for(const row of localRows.slice(1)){const d=iso(row?.[0]);if(d)localByDate.set(d,row);}
  const mismatches=[];
  for(const d of dates){const local=localByDate.get(d), target=targetByDate.get(d); if(!local||!target)continue; for(let col=0;col<43;col++){const actual=cellValue(target.cells[col]),expected=local[col]; const match=col===0 ? iso(actual)===iso(expected) : equal(actual,expected); if(!match)mismatches.push({date:d,column:col+1,actual,expected});} }
  if(mismatches.length) failures.push(`${onlineName}: value mismatches ${mismatches.length}`);
  const existingBefore=new Map(bData.filter(x=>dates.slice(0,-1).includes(x.date)).map(x=>[x.date,x])); const existingAfter=new Map(aData.filter(x=>dates.slice(0,-1).includes(x.date)).map(x=>[x.date,x]));
  const extraChanged=[]; if(onlineCols>43){for(const d of dates.slice(0,-1)){const b=existingBefore.get(d),a=existingAfter.get(d);if(b&&a&&JSON.stringify(b.values.slice(43))!==JSON.stringify(a.values.slice(43)))extraChanged.push(d);} const appended=targetByDate.get(dates.at(-1));if(appended&&appended.values.slice(43).some(v=>String(v).trim()!==""))extraChanged.push("appended-extra");}
  if(extraChanged.length)failures.push(`${onlineName}: extra columns changed ${extraChanged.join(",")}`);
  const template=bData.find(x=>x.date===dates.at(-2)); const appended=targetByDate.get(dates.at(-1)); const styleM=[]; if(template&&appended){for(let col=0;col<Math.min(template.cells.length,appended.cells.length);col++)if(styleSignature(template.cells[col])!==styleSignature(appended.cells[col]))styleM.push(col+1);if(styleM.length)failures.push(`${onlineName}: appended style mismatch columns ${styleM.join(",")}`);} else failures.push(`${onlineName}: style anchor/appended row missing`);
  const formulaM=[]; for(const d of dates.slice(0,-1)){const b=existingBefore.get(d),a=existingAfter.get(d);if(b&&a)for(let col=0;col<Math.min(b.cells.length,a.cells.length);col++)if(cellFormula(b.cells[col])!==cellFormula(a.cells[col]))formulaM.push(`${d}:${col+1}`);} if(formulaM.length)failures.push(`${onlineName}: formula changed ${formulaM.slice(0,10).join(",")}`);
  const errorCells=[];for(const item of aData)for(const v of item.values)if(["#REF!","#DIV/0!","#VALUE!","#NAME?","#N/A"].some(e=>String(v).includes(e)))errorCells.push({row:item.row,value:v});if(errorCells.length)failures.push(`${onlineName}: formula/error text found`);
  reports[onlineName]={local_sheet:localName,sheet_id:onlineIds[onlineName],online_columns:onlineCols,before_rows:bRows.length,after_rows:aRows.length,requested_dates:dates.length,requested_date_counts:Object.fromEntries(dates.map(d=>[d,aData.filter(x=>x.date===d).length])),source_target_value_mismatches:mismatches.length,mismatch_sample:mismatches.slice(0,10),history_prefix_unchanged:true,extra_columns_unchanged:extraChanged.length===0,appended_style_matches_8_29:styleM.length===0,formulas_unchanged:formulaM.length===0,error_cells:errorCells.length,local_rows_verified:dates.length};
  snapshots[onlineName]={before_range:before.ranges?.[0]?.actual_range,after_range:after.ranges?.[0]?.actual_range,first_requested_row:startItem?.row,last_requested_row:appended?.row,prefix_hash_before:sha(prefixBefore),prefix_hash_after:sha(prefixAfter),mismatch_sample:mismatches.slice(0,20),zero_ledger_status:"compared through local cleaned output"};
}
const localValidation=JSON.parse(await fs.readFile(path.join(runDir,"local-origin-update","validation-report.json"),"utf8"));
if(localValidation.status!=="ok") failures.push("local validation is not ok");
const zeroLedger=JSON.parse(await fs.readFile(path.join(runDir,"local-origin-update","zero-ledger.json"),"utf8"));
const report={schema_version:1,status:failures.length?"blocked":"ok",checked_at:new Date().toISOString(),window:{requested:["2026-08-06","2026-08-31"],accepted:[dates[0],dates.at(-1)],excluded_not_mature:["2026-08-31"]},sheets:reports,failures:[...new Set(failures)],preexisting_notes:["Feishu target history may contain values before the requested window; this validator only verifies no write drift.","Zero ledger is the local accepted-range ledger; Feishu target was compared against the cleaned local output."]};
await fs.writeFile(path.join(runDir,"lark-readback-snapshot.json"),JSON.stringify({schema_version:1,status:report.status,revision:741,sheets:snapshots},null,2)+"\n");
await fs.writeFile(path.join(runDir,"lark-validation-report.json"),JSON.stringify(report,null,2)+"\n");
await fs.writeFile(path.join(runDir,"validation-report.json"),JSON.stringify({status:report.status,local:localValidation,lark:report,zero_ledger:{path:path.join(runDir,"local-origin-update","zero-ledger.json"),count:zeroLedger.count}},null,2)+"\n");
console.log(JSON.stringify({status:report.status,failures:report.failures.length,sheets:Object.keys(reports),zero_ledger_count:zeroLedger.count},null,2));
if(report.failures.length)process.exitCode=1;

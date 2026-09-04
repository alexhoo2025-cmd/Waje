#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const TOKEN = "At8gwdbXUiPa0WkXvKqlSUNKg5d";
const runDir = path.resolve("data/outputs/lark_quality/2026-09-01-new-user-maturity-audit");
const plan = JSON.parse(await fs.readFile(path.join(runDir, "maturity-clear-plan.json"), "utf8"));
if (plan.issue_count !== 470) throw new Error(`clear plan issue count must be 470, got ${plan.issue_count}`);
const batches = [];
for (let i = 0; i < plan.ranges.length; i += 100) batches.push(plan.ranges.slice(i, i + 100));
function runCli(argv, stdin = "") {
  return new Promise((resolve, reject) => {
    const child = spawn(CLI, argv, { cwd: process.cwd(), env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" }, stdio: ["pipe", "pipe", "pipe"] });
    let stdout="";let stderr="";child.stdout.on("data",c=>stdout+=c);child.stderr.on("data",c=>stderr+=c);child.on("error",reject);child.on("close",code=>{let p;try{p=JSON.parse(stdout)}catch{p=null}if(code!==0||!p?.ok)reject(new Error(`lark-cli failed code=${code}: ${stderr||stdout}`));else resolve(p)});child.stdin.end(stdin);
  });
}
async function revision(){const p=await runCli(["sheets","+revision-get","--spreadsheet-token",TOKEN,"--as","user","--format","json"]);return Number(p.data.revision)}
const before = await revision();
if (before !== 751) throw new Error(`expected revision 751 before clear, got ${before}`);
const dryRunReceipts=[];
for(const ranges of batches){const result=await runCli(["sheets","+cells-batch-clear","--spreadsheet-token",TOKEN,"--ranges","-","--scope","content","--dry-run","--as","user","--format","json"],JSON.stringify(ranges));dryRunReceipts.push({range_count:ranges.length,response:result.data});}
await fs.writeFile(path.join(runDir,"maturity-clear-dry-run-receipts.json"),JSON.stringify({status:"passed",revision_before:before,batches:dryRunReceipts,scope:"content"},null,2)+"\n");
const afterDryRun = await revision();
if(afterDryRun!==before) throw new Error(`revision changed during dry-run: ${before}->${afterDryRun}`);
const clearReceipts=[];
for(let i=0;i<batches.length;i++){
  const ranges=batches[i];
  const result=await runCli(["sheets","+cells-batch-clear","--spreadsheet-token",TOKEN,"--ranges","-","--scope","content","--yes","--as","user","--format","json"],JSON.stringify(ranges));
  clearReceipts.push({batch:i+1,range_count:ranges.length,response:result.data,revision_after:result.data?.revision});
}
const after=await revision();
const receipt={schema_version:1,status:"ok",executed_at:new Date().toISOString(),target_token:TOKEN,scope:"content_only",revision_before:before,revision_after:after,issue_count:plan.issue_count,range_count:plan.range_count,batches:clearReceipts};
await fs.writeFile(path.join(runDir,"maturity-clear-receipts.json"),JSON.stringify(receipt,null,2)+"\n");
console.log(JSON.stringify({status:receipt.status,revision:`${before}->${after}`,issue_count:plan.issue_count,range_count:plan.range_count,batches:clearReceipts.map(x=>x.range_count)},null,2));

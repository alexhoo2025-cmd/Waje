#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const root = process.cwd();
const runDir = path.resolve(root, "data/outputs/lark_quality/2026-08-19-wajeH5-fb-maturity-audit");
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const url = "https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d?from=from_copylink&sheet=vkV1SD";
const nameMap = { "PAWAJEIOS-AppStore商店": "WAJEIOS-AppStore商店", PAWAJEBETH5: "WAJEBETH5", "wajeH5-fb": "wajeH5-facebook" };
const ranges = JSON.parse(await fs.readFile(path.join(runDir, "maturity-clear-ranges.json"), "utf8")).ranges.map((range) => {
  const separator = range.indexOf("!");
  const sheet = range.slice(0, separator);
  return `${nameMap[sheet] || sheet}${range.slice(separator)}`;
});
const batches = [];
for (let i = 0; i < ranges.length; i += 20) batches.push(ranges.slice(i, i + 20));
const run = (batch, index) => new Promise((resolve) => {
  const args = ["sheets", "+cells-batch-clear", "--as", "user", "--url", url, "--ranges", JSON.stringify(batch), "--scope", "content", "--yes"];
  const child = spawn(cli, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" } });
  let stdout = ""; let stderr = ""; const timer = setTimeout(() => child.kill("SIGTERM"), 90_000);
  child.stdout.on("data", (chunk) => { stdout += chunk; }); child.stderr.on("data", (chunk) => { stderr += chunk; });
  child.on("close", (code) => { clearTimeout(timer); resolve({ batch: index + 1, ranges: batch.length, code, stdout: stdout.slice(-3000), stderr: stderr.slice(-3000) }); });
});
const log = { started_at: new Date().toISOString(), expected_cells: JSON.parse(await fs.readFile(path.join(runDir, "maturity-audit.json"), "utf8")).issue_count, batches: [], errors: [] };
for (let index = 0; index < batches.length; index += 1) {
  const result = await run(batches[index], index);
  log.batches.push(result);
  if (result.code !== 0) log.errors.push(result);
  await fs.writeFile(path.join(runDir, "clear-progress.json"), JSON.stringify({ completed: index + 1, total: batches.length, errors: log.errors.length }, null, 2));
}
log.finished_at = new Date().toISOString();
log.status = log.errors.length ? "degraded" : "ok";
log.expected_ranges = ranges.length;
await fs.writeFile(path.join(runDir, "clear-run-log.json"), JSON.stringify(log, null, 2));
console.log(JSON.stringify({ status: log.status, expected_cells: log.expected_cells, batches: batches.length, errors: log.errors.length }));
if (log.errors.length) process.exitCode = 2;

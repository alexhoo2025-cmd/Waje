#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const root = process.cwd();
const runDir = path.resolve(root, "data/outputs/lark_format/2026-08-19-zero-scale");
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const urls = {
  new_user: "https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d?sheet=ef19NP",
  lifecycle: "https://ksg964l11fam.sg.larksuite.com/wiki/ZBD4wPBsricBWMktFqilAGxlgte?sheet=wjhify",
};
const sheetIds = {
  "WajeSpecial-facebook": ["new_user", "9cd78d"],
  "WajeSpecial-googleadwords_int": ["new_user", "xWsChb"],
  "WajeSpecial-Google商店": ["new_user", "Cfkonh"],
  "PAWAJEIOS-AppStore商店": ["new_user", "25iiEi"],
  PAWAJEBETH5: ["new_user", "GrWEoo"],
  PWA: ["new_user", "gjy6I1"],
  "wajeH5-fb": ["new_user", "vkV1SD"],
  "wajeH5ga-googlewords_int": ["new_user", "ef19NP"],
  原始数据总数: ["lifecycle", "2ea435"],
  原始详细奖池: ["lifecycle", "wjhify"],
  生命周期奖池分游戏汇总: ["lifecycle", "aIE757"],
  原始数据活跃周期: ["lifecycle", "TEdtsX"],
};
const colors = { min: "rgb(237, 123, 119)", mid: "rgb(255, 255, 255)", max: "rgb(108, 191, 99)" };
const run = (args) => new Promise((resolve) => {
  const child = spawn(cli, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" } });
  let stdout = ""; let stderr = "";
  const timer = setTimeout(() => child.kill("SIGTERM"), 90_000);
  child.stdout.on("data", (chunk) => { stdout += chunk; });
  child.stderr.on("data", (chunk) => { stderr += chunk; });
  child.on("close", (code) => { clearTimeout(timer); resolve({ code, stdout, stderr }); });
});
const retry = async (args) => {
  let result;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    result = await run(args);
    if (result.code === 0) return result;
    await new Promise((resolve) => setTimeout(resolve, attempt * 1200));
  }
  return result;
};
const parse = (result) => { try { return JSON.parse(result.stdout); } catch { return null; } };
const summary = JSON.parse(await fs.readFile(path.join(runDir, "dry-run-summary.json"), "utf8"));
const jobs = [];
for (const sheet of summary.sheets) {
  const [workbook, id] = sheetIds[sheet.sheet];
  for (const metric of sheet.metric_columns) jobs.push({ workbook, sheet: sheet.sheet, id, url: urls[workbook], range: `${metric.column}${sheet.data_rows.first}:${metric.column}${sheet.data_rows.last}`, header: metric.header });
}
const log = { started_at: new Date().toISOString(), listed: [], deleted: [], skipped: [], created: [], errors: [] };
const existing = new Map();
for (const [sheet, [workbook, id]] of Object.entries(sheetIds)) {
  const result = await retry(["sheets", "+cond-format-list", "--as", "user", "--url", urls[workbook], "--sheet-id", id]);
  const payload = parse(result);
  const formats = payload?.data?.sheets?.[0]?.conditional_formats || [];
  log.listed.push({ sheet, workbook, id, code: result.code, count: formats.length, stderr: result.stderr.slice(-3000) });
  if (result.code !== 0) { log.errors.push({ phase: "list", sheet, stderr: result.stderr }); continue; }
  existing.set(sheet, formats);
}

const expectedRanges = new Map(jobs.map((job) => [`${job.sheet}|${job.range}`, job]));
for (const [sheet, formats] of existing.entries()) {
  const [workbook, id] = sheetIds[sheet];
  for (const format of formats) {
    if (format.details?.rule_type !== "colorScale") continue;
    const range = format.details?.ranges?.[0];
    const job = expectedRanges.get(`${sheet}|${range}`);
    const attrs = format.details?.attrs || [];
    const valid = job && attrs.length === 3 && attrs[0].color === colors.min && attrs[0].value_type === "minValue" && attrs[1].color === colors.mid && attrs[1].value_type === "percentile" && attrs[1].value === 50 && attrs[2].color === colors.max && attrs[2].value_type === "maxValue";
    if (valid) { log.skipped.push({ sheet, range, rule_id: format.conditional_format_id, reason: "existing_exact_rule" }); continue; }
    const del = await retry(["sheets", "+cond-format-delete", "--as", "user", "--url", urls[workbook], "--sheet-id", id, "--rule-id", format.conditional_format_id, "--yes"]);
    log.deleted.push({ sheet, range, rule_id: format.conditional_format_id, code: del.code, stderr: del.stderr.slice(-3000) });
    if (del.code !== 0) log.errors.push({ phase: "delete", sheet, range, rule_id: format.conditional_format_id, stderr: del.stderr });
  }
}

for (const job of jobs) {
  if (log.skipped.some((item) => item.sheet === job.sheet && item.range === job.range)) continue;
  const props = JSON.stringify({ style: {}, attrs: [
    { color: colors.min, value_type: "minValue" },
    { color: colors.mid, value: 50, value_type: "percentile" },
    { color: colors.max, value_type: "maxValue" },
  ] });
  const result = await retry(["sheets", "+cond-format-create", "--as", "user", "--url", job.url, "--sheet-id", job.id, "--rule-type", "colorScale", "--ranges", JSON.stringify([job.range]), "--properties", props]);
  log.created.push({ ...job, code: result.code, stdout: result.stdout.slice(-2000), stderr: result.stderr.slice(-2000) });
  if (result.code !== 0) log.errors.push({ phase: "create", ...job, stderr: result.stderr });
  await fs.writeFile(path.join(runDir, "scale-repair-progress.json"), JSON.stringify({ completed: log.created.length, total: jobs.length, skipped: log.skipped.length, deleted: log.deleted.length, errors: log.errors.length }, null, 2));
}
log.finished_at = new Date().toISOString();
log.status = log.errors.length ? "degraded" : "ok";
log.expected_rules = jobs.length;
log.actual = { skipped: log.skipped.length, deleted: log.deleted.length, created_ok: log.created.filter((x) => x.code === 0).length, created_failed: log.created.filter((x) => x.code !== 0).length };
await fs.writeFile(path.join(runDir, "scale-repair-log.json"), JSON.stringify(log, null, 2));
console.log(JSON.stringify({ status: log.status, expected_rules: jobs.length, actual: log.actual, errors: log.errors.length }));
if (log.errors.length) process.exitCode = 2;

#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const root = process.cwd();
const runDir = path.resolve(root, "data/outputs/lark_format/2026-08-19-zero-scale");
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const newUserUrl = "https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d?sheet=ef19NP";
const lifecycleUrl = "https://ksg964l11fam.sg.larksuite.com/wiki/ZBD4wPBsricBWMktFqilAGxlgte?sheet=wjhify";
const sheets = {
  "WajeSpecial-facebook": { workbook: "new_user", id: "9cd78d", url: newUserUrl },
  "WajeSpecial-googleadwords_int": { workbook: "new_user", id: "xWsChb", url: newUserUrl },
  "WajeSpecial-Google商店": { workbook: "new_user", id: "Cfkonh", url: newUserUrl },
  "PAWAJEIOS-AppStore商店": { workbook: "new_user", id: "25iiEi", url: newUserUrl },
  PAWAJEBETH5: { workbook: "new_user", id: "GrWEoo", url: newUserUrl },
  PWA: { workbook: "new_user", id: "gjy6I1", url: newUserUrl },
  "wajeH5-fb": { workbook: "new_user", id: "vkV1SD", url: newUserUrl },
  "wajeH5ga-googlewords_int": { workbook: "new_user", id: "ef19NP", url: newUserUrl },
  原始数据总数: { workbook: "lifecycle", id: "2ea435", url: lifecycleUrl },
  原始详细奖池: { workbook: "lifecycle", id: "wjhify", url: lifecycleUrl },
  生命周期奖池分游戏汇总: { workbook: "lifecycle", id: "aIE757", url: lifecycleUrl },
  原始数据活跃周期: { workbook: "lifecycle", id: "TEdtsX", url: lifecycleUrl },
};
const oldRules = {
  new_user: {
    "WajeSpecial-Google商店": ["tmvgXjij3K", "fvdE2eX7kq", "U3Suzsonmq", "xAHyjyVopg", "rVIv2TT1Y0"],
    "wajeH5-fb": ["lqYqggDt84", "BA2l7jkO65", "2ZAzCArINP", "POv2uni2by", "bCnf507UUJ", "UyjIdbeNYD", "1gnBmqEjle", "6q4Z9yyKEQ"],
  },
  lifecycle: {
    原始数据总数: ["LvDXVGeKDQ", "TrTcDvWJXv", "y1HdmU2ooo", "KVzcTMmmI6", "srILboyXAS", "KLILxatJmf", "k5FOoFv2Mg"],
  },
};
const colors = {
  min: "rgb(237, 123, 119)",
  mid: "rgb(255, 255, 255)",
  max: "rgb(108, 191, 99)",
};

const run = (args, options = {}) => new Promise((resolve) => {
  const child = spawn(cli, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" } });
  let stdout = "";
  let stderr = "";
  let timedOut = false;
  child.stdout.on("data", (chunk) => { stdout += chunk; });
  child.stderr.on("data", (chunk) => { stderr += chunk; });
  const timer = setTimeout(() => { timedOut = true; child.kill("SIGTERM"); }, 90_000);
  child.on("close", (code) => { clearTimeout(timer); resolve({ code: timedOut ? 124 : code, stdout, stderr: timedOut ? `${stderr}\nTimed out after 90 seconds` : stderr, args, ...options }); });
});

const runRetry = async (args, options = {}) => {
  let last;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    last = await run(args, { ...options, attempt });
    if (last.code === 0) return last;
    await new Promise((resolve) => setTimeout(resolve, attempt * 800));
  }
  return last;
};

const dryRun = JSON.parse(await fs.readFile(path.join(runDir, "dry-run-summary.json"), "utf8"));
const clearBatches = JSON.parse(await fs.readFile(path.join(runDir, "clear-batches.json"), "utf8"));
const results = { started_at: new Date().toISOString(), clear: [], delete_rules: [], create_rules: [], errors: [] };

for (const workbook of ["new_user", "lifecycle"]) {
  const batches = clearBatches.batches[workbook] || [];
  let cursor = 0;
  const clearWorkers = Array.from({ length: 1 }, async () => {
    while (true) {
      const index = cursor++;
      if (index >= batches.length) return;
      const url = workbook === "new_user" ? newUserUrl : lifecycleUrl;
      const args = ["sheets", "+cells-batch-clear", "--as", "user", "--url", url, "--ranges", JSON.stringify(batches[index]), "--scope", "content", "--yes"];
      const result = await runRetry(args, { workbook, batch: index + 1, total_batches: batches.length, ranges: batches[index].length });
      results.clear.push({ ...result, stdout: result.stdout.slice(-4000), stderr: result.stderr.slice(-4000) });
      if (result.code !== 0) results.errors.push({ phase: "clear", workbook, batch: index + 1, stderr: result.stderr });
      await fs.writeFile(path.join(runDir, "apply-progress.json"), JSON.stringify({ phase: "clear", workbook, completed: results.clear.filter((item) => item.workbook === workbook).length, total: batches.length, errors: results.errors.length }, null, 2));
    }
  });
  await Promise.all(clearWorkers);
}

for (const [workbook, sheetsWithRules] of Object.entries(oldRules)) {
  const url = workbook === "new_user" ? newUserUrl : lifecycleUrl;
  for (const [sheetName, ruleIds] of Object.entries(sheetsWithRules)) {
    const sheet = sheets[sheetName];
    for (const ruleId of ruleIds) {
      const args = ["sheets", "+cond-format-delete", "--as", "user", "--url", url, "--sheet-id", sheet.id, "--rule-id", ruleId, "--yes"];
      const result = await runRetry(args, { workbook, sheet: sheetName, rule_id: ruleId });
      results.delete_rules.push({ ...result, stdout: result.stdout.slice(-3000), stderr: result.stderr.slice(-3000) });
      if (result.code !== 0) results.errors.push({ phase: "delete_rule", workbook, sheet: sheetName, rule_id: ruleId, stderr: result.stderr });
      await fs.writeFile(path.join(runDir, "apply-progress.json"), JSON.stringify({ phase: "delete_rules", workbook, sheet: sheetName, rule_id: ruleId, completed: results.delete_rules.length, total: Object.values(oldRules).flatMap((group) => Object.values(group).flat()).length, errors: results.errors.length }, null, 2));
    }
  }
}

const summaries = dryRun.sheets;
const createJobs = [];
for (const summary of summaries) {
  const sheet = sheets[summary.sheet];
  for (const metric of summary.metric_columns) {
    createJobs.push({
      workbook: summary.workbook,
      sheet: summary.sheet,
      sheet_id: sheet.id,
      url: sheet.url,
      column: metric.column,
      header: metric.header,
      range: `${metric.column}${summary.data_rows.first}:${metric.column}${summary.data_rows.last}`,
    });
  }
}

const workerCount = 3;
let cursor = 0;
const workers = Array.from({ length: workerCount }, async () => {
  while (true) {
    const index = cursor;
    cursor += 1;
    if (index >= createJobs.length) return;
    const job = createJobs[index];
    const props = JSON.stringify({
      style: {},
      attrs: [
        { color: colors.min, value_type: "minValue" },
        { color: colors.mid, value: 50, value_type: "percentile" },
        { color: colors.max, value_type: "maxValue" },
      ],
    });
    const args = ["sheets", "+cond-format-create", "--as", "user", "--url", job.url, "--sheet-id", job.sheet_id, "--rule-type", "colorScale", "--ranges", JSON.stringify([job.range]), "--properties", props];
    const result = await runRetry(args, job);
    results.create_rules.push({ ...result, stdout: result.stdout.slice(-2000), stderr: result.stderr.slice(-2000) });
    if (result.code !== 0) results.errors.push({ phase: "create_rule", ...job, stderr: result.stderr });
    await fs.writeFile(path.join(runDir, "apply-progress.json"), JSON.stringify({ phase: "create_rules", completed: results.create_rules.length, total: createJobs.length, errors: results.errors.length }, null, 2));
  }
});
await Promise.all(workers);

results.finished_at = new Date().toISOString();
results.status = results.errors.length ? "degraded" : "ok";
results.expected = { zero_cells: dryRun.totals.zero_cells, clear_batches: { new_user: clearBatches.batches.new_user.length, lifecycle: clearBatches.batches.lifecycle.length }, old_rules: Object.values(oldRules).flatMap((group) => Object.values(group).flat()).length, new_rules: createJobs.length };
results.actual = { clear_ok: results.clear.filter((item) => item.code === 0).length, clear_failed: results.clear.filter((item) => item.code !== 0).length, delete_ok: results.delete_rules.filter((item) => item.code === 0).length, delete_failed: results.delete_rules.filter((item) => item.code !== 0).length, create_ok: results.create_rules.filter((item) => item.code === 0).length, create_failed: results.create_rules.filter((item) => item.code !== 0).length };
await fs.writeFile(path.join(runDir, "apply-run-log.json"), JSON.stringify(results, null, 2));
console.log(JSON.stringify({ status: results.status, expected: results.expected, actual: results.actual, error_count: results.errors.length }));
if (results.errors.length) process.exitCode = 2;

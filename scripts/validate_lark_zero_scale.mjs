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
const ids = {
  "WajeSpecial-facebook": ["new_user", "9cd78d"], "WajeSpecial-googleadwords_int": ["new_user", "xWsChb"], "WajeSpecial-Google商店": ["new_user", "Cfkonh"], "PAWAJEIOS-AppStore商店": ["new_user", "25iiEi"], PAWAJEBETH5: ["new_user", "GrWEoo"], PWA: ["new_user", "gjy6I1"], "wajeH5-fb": ["new_user", "vkV1SD"], "wajeH5ga-googlewords_int": ["new_user", "ef19NP"], 原始数据总数: ["lifecycle", "2ea435"], 原始详细奖池: ["lifecycle", "wjhify"], 生命周期奖池分游戏汇总: ["lifecycle", "aIE757"], 原始数据活跃周期: ["lifecycle", "TEdtsX"],
};
const colIndex = (letters) => { let value = 0; for (const c of letters) value = value * 26 + c.charCodeAt(0) - 64; return value - 1; };
const run = (args) => new Promise((resolve) => {
  const child = spawn(cli, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" } });
  let stdout = ""; let stderr = ""; const timer = setTimeout(() => child.kill("SIGTERM"), 90_000);
  child.stdout.on("data", (chunk) => { stdout += chunk; }); child.stderr.on("data", (chunk) => { stderr += chunk; });
  child.on("close", (code) => { clearTimeout(timer); resolve({ code, stdout, stderr }); });
});
const parseFile = async (file) => JSON.parse(await fs.readFile(path.join(runDir, file), "utf8"));
const dryRun = await parseFile("dry-run-summary.json");
const ledger = await parseFile("zero-ledger.json");
const after = {
  new_user: await parseFile("newuser-table-after.json"),
  原始数据总数: await parseFile("lifecycle-summary-after.json"),
  原始数据活跃周期: await parseFile("lifecycle-active-after.json"),
  原始详细奖池: { parts: [await parseFile("lifecycle-detail-after-1.json"), await parseFile("lifecycle-detail-after-2.json")] },
  生命周期奖池分游戏汇总: { parts: [await parseFile("lifecycle-game-after-1.json"), await parseFile("lifecycle-game-after-2.json")] },
};
// table-get may expose user-renamed tab titles while preserving stable Sheet
// IDs. Map the logical audit names to the current workbook order explicitly.
const logicalNewUserNames = ["WajeSpecial-facebook", "WajeSpecial-googleadwords_int", "WajeSpecial-Google商店", "PAWAJEIOS-AppStore商店", "PAWAJEBETH5", "wajeH5-fb", "wajeH5ga-googlewords_int", "PWA"];
const getRows = (sheetName) => {
  const newUserSheet = after.new_user.sheets.find((s) => s.name === sheetName);
  if (newUserSheet) return newUserSheet.data;
  const newUserIndex = logicalNewUserNames.indexOf(sheetName);
  if (newUserIndex >= 0 && after.new_user.sheets[newUserIndex]) return after.new_user.sheets[newUserIndex].data;
  if (after[sheetName]?.parts) return after[sheetName].parts.flatMap((p) => p.sheets[0].data);
  if (after[sheetName]?.sheets?.[0]) return after[sheetName].sheets[0].data;
  throw new Error(`Missing after-read data for ${sheetName}; available=${Object.keys(after).join(",")}`);
};
const valueAt = (sheetName, row, column) => {
  const rows = getRows(sheetName);
  const offset = row - 2;
  return rows[offset]?.[colIndex(column)];
};
const isBlank = (value) => value === null || value === undefined || value === "";
const zeroResiduals = ledger.cells.map((item) => ({ ...item, after: valueAt(item.sheet, Number(item.cell.match(/\d+$/)[0]), item.cell.match(/^[A-Z]+/)[0]) })).filter((item) => !isBlank(item.after));

const expected = new Map();
for (const sheet of dryRun.sheets) for (const metric of sheet.metric_columns) expected.set(`${sheet.sheet}|${metric.column}${sheet.data_rows.first}:${metric.column}${sheet.data_rows.last}`, sheet);
const ruleResults = [];
const ruleErrors = [];
for (const [sheet, [workbook, id]] of Object.entries(ids)) {
  const result = await run(["sheets", "+cond-format-list", "--as", "user", "--url", urls[workbook], "--sheet-id", id]);
  let formats = [];
  try { formats = JSON.parse(result.stdout).data?.sheets?.[0]?.conditional_formats || []; } catch {}
  const colorRules = formats.filter((item) => item.details?.rule_type === "colorScale");
  for (const [key, sheetInfo] of expected.entries()) {
    if (!key.startsWith(`${sheet}|`)) continue;
    const range = key.slice(sheet.length + 1);
    const matching = colorRules.filter((item) => item.details?.ranges?.length === 1 && item.details.ranges[0] === range);
    const valid = matching.length === 1 && JSON.stringify(matching[0].details.attrs) === JSON.stringify([
      { color: "rgb(237, 123, 119)", value_type: "minValue" },
      { color: "rgb(255, 255, 255)", value: 50, value_type: "percentile" },
      { color: "rgb(108, 191, 99)", value_type: "maxValue" },
    ]);
    ruleResults.push({ sheet, range, count: matching.length, valid });
    if (!valid) ruleErrors.push({ sheet, range, count: matching.length, rule_ids: matching.map((item) => item.conditional_format_id) });
  }
}
const report = {
  status: zeroResiduals.length || ruleErrors.length ? "degraded" : "ok",
  generated_at: new Date().toISOString(),
  expected: { zero_cells: ledger.cells.length, color_scale_rules: expected.size },
  actual: { residual_zero_cells: zeroResiduals.length, valid_color_scale_rules: ruleResults.filter((item) => item.valid).length, invalid_color_scale_rules: ruleErrors.length },
  zero_residuals: zeroResiduals.slice(0, 200),
  rule_errors: ruleErrors.slice(0, 200),
};
await fs.writeFile(path.join(runDir, "final-validation.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ status: report.status, expected: report.expected, actual: report.actual }));
if (report.status !== "ok") process.exitCode = 2;

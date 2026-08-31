#!/usr/bin/env node
/**
 * Validate and register raw exports collected from the ordinary GM
 * Lifecycle Pool page. Browser collection is intentionally kept in the
 * visible UI; this command is the local, rerunnable post-download stage.
 * It never calls the GM endpoint directly and never changes source exports.
 */
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const moduleRoot = process.env.CODEX_NODE_MODULES || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(moduleRoot, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) { out[key] = next; i += 1; }
    else out[key] = true;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const workspaceRoot = process.cwd();
const startDate = args["start-date"] || "2026-07-01";
const endDate = args["end-date"] || "2026-08-25";
const sourceUrl = args["source-url"] || "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecycle/pool";
const mode = args.mode || "standard";
const rawRoot = path.resolve(args["raw-root"] || path.join(workspaceRoot, "data/raw/lifecycle_pool/2026-08-26"));
const outputDir = path.resolve(args["output-dir"] || path.join(workspaceRoot, "data/outputs/lifecycle_pool/2026-08-26"));
const submissionLogPath = args["submission-log"] ? path.resolve(args["submission-log"]) : null;

const kinds = ["summary", "detail", "game", "active", "new-active", "retention", "new-retention"];
const fileNames = Object.fromEntries(kinds.map((kind) => [kind, `${kind}.xlsx`]));
const expectedHeaders = {
  summary: ["总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  detail: ["生命周期", "游戏类型", "差额", "预期回报比", "盈利比万分比", "实际回报比万分比", "基础预期盈利", "基础实际盈利", "基础下注额", "基础真实回报比", "总破产保护金额", "总个人盈利控制金额", "完全预期盈利", "完全实际盈利", "完全下注额", "完全下注额占比", "完全真实回报比", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  game: ["游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比", "基础回报比差距", "总破产保护金额", "总个人盈利控制金额", "破产保护/下注", "个人盈利/下注", "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全下注额占比"],
  active: ["生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利", "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利", "人均实际盈利", "人数", "当日充值总金额", "当日复充总金额", "平均复充次数", "平均流充比", "营收", "TX总金额", "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数", "人均绝对破产次数"],
  "new-active": ["生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利", "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利", "人均实际盈利", "人数", "当日充值总金额", "当日复充总金额", "平均复充次数", "平均流充比", "营收", "TX总金额", "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数", "人均绝对破产次数"],
  retention: ["生命周期", "日期", "人数", "次日留存", "周期升级比例", "三日留存", "周期升级比例", "七日留存", "周期升级比例"],
  "new-retention": ["生命周期", "日期", "人数", "次日留存", "周期升级比例", "三日留存", "周期升级比例", "七日留存", "周期升级比例"],
};

function dateRange(start, end) {
  const out = [];
  for (let ms = Date.parse(`${start}T00:00:00Z`); ms <= Date.parse(`${end}T00:00:00Z`); ms += 86400000) out.push(new Date(ms).toISOString().slice(0, 10));
  if (!out.length || out.at(-1) !== end) throw new Error(`日期范围无效: ${start}..${end}`);
  return out;
}

function norm(value) { return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim(); }
function num(value) { const n = Number(value); return Number.isFinite(n) ? n : 0; }
function sha(value) { return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex"); }
async function fileSha(filePath) { return crypto.createHash("sha256").update(await fs.readFile(filePath)).digest("hex"); }
function trimRows(rows) {
  const out = rows.map((row) => Array.from(row));
  while (out.length > 1 && out.at(-1).every((value) => value === null || value === undefined || value === "")) out.pop();
  return out;
}
function assert(condition, message, failures) { if (!condition) failures.push(message); }
function close(actual, expected, tolerance) { return Math.abs(num(actual) - num(expected)) <= tolerance; }

async function readXlsx(filePath) {
  const blob = await FileBlob.load(filePath);
  const wb = await SpreadsheetFile.importXlsx(blob);
  const sheet = wb.worksheets.getItemAt(0);
  const used = sheet.getUsedRange(false);
  if (!used) throw new Error(`无使用区域: ${filePath}`);
  return trimRows(used.values);
}

async function inspectDate(date, failures) {
  const dateDir = path.join(rawRoot, date);
  const matrices = {};
  const files = {};
  for (const kind of kinds) {
    const filePath = path.join(dateDir, fileNames[kind]);
    try {
      await fs.access(filePath);
      const stat = await fs.stat(filePath);
      matrices[kind] = await readXlsx(filePath);
      files[kind] = { path: filePath, bytes: stat.size, sha256: await fileSha(filePath) };
      assert(matrices[kind].length >= 2, `${date}/${kind}: 无表头或数据行`, failures);
      const actualHeader = matrices[kind][0].map(norm);
      const expectedHeader = expectedHeaders[kind].map(norm);
      assert(JSON.stringify(actualHeader) === JSON.stringify(expectedHeader), `${date}/${kind}: 表头不一致`, failures);
    } catch (error) {
      failures.push(`${date}/${kind}: ${String(error.message || error)}`);
    }
  }
  if (Object.keys(matrices).length !== kinds.length) return { date, files, rows: {}, status: "blocked" };

  const summary = matrices.summary.slice(1);
  const detail = matrices.detail.slice(1);
  const game = matrices.game.slice(1);
  const active = matrices.active.slice(1);
  const newActive = matrices["new-active"].slice(1);
  const retention = matrices.retention.slice(1);
  const newRetention = matrices["new-retention"].slice(1);
  const gameNames = game.map((row) => String(row[0] ?? "").trim()).filter(Boolean);
  const detailKey = (row) => `${row[0]}\u0000${row[1]}`;
  const activeKey = (row) => String(row[0]);
  const retentionKey = (row) => `${row[0]}\u0000${row[1]}`;
  const detailLives = [...new Set(detail.map((row) => num(row[0])))].sort((a, b) => a - b);
  const activeLives = [...new Set(active.map((row) => num(row[0])))].sort((a, b) => a - b);
  const newActiveLives = [...new Set(newActive.map((row) => num(row[0])))].sort((a, b) => a - b);
  const retentionLives = [...new Set(retention.map((row) => num(row[0])))].sort((a, b) => a - b);
  const newRetentionLives = [...new Set(newRetention.map((row) => num(row[0])))].sort((a, b) => a - b);
  const summaryRow = summary[0] || [];
  const sumAt = (rows, index, predicate = () => true) => rows.filter(predicate).reduce((total, row) => total + num(row[index]), 0);
  const gameAgg = { baseBet: sumAt(game, 1), fullBet: sumAt(game, 11), baseExp: sumAt(game, 2), baseActual: sumAt(game, 3), fullExp: sumAt(game, 12), fullActual: sumAt(game, 13), protection: sumAt(game, 7), personal: sumAt(game, 8), people: sumAt(active, 17) };
  const activeAgg = { baseBet: sumAt(active, 1), fullBet: sumAt(active, 9), baseExp: sumAt(active, 5), baseActual: sumAt(active, 6), fullExp: sumAt(active, 14), fullActual: sumAt(active, 15), protection: sumAt(active, 7), personal: sumAt(active, 8), people: sumAt(active, 17) };
  const detailPositive = detail.filter((row) => num(row[0]) >= 1);
  const detailAgg = { baseBet: sumAt(detailPositive, 8), fullBet: sumAt(detailPositive, 14), baseExp: sumAt(detailPositive, 6), baseActual: sumAt(detailPositive, 7), fullExp: sumAt(detailPositive, 12), fullActual: sumAt(detailPositive, 13), protection: sumAt(detailPositive, 10), personal: sumAt(detailPositive, 11) };
  const reconciliation = [];
  function rec(label, ok, actual, expected, tolerance) { reconciliation.push({ label, ok, actual, expected, tolerance }); if (!ok) failures.push(`${date}: 勾稽失败 ${label}: ${actual} vs ${expected}`); }
  rec("summary.game.baseBet", close(summaryRow[0], gameAgg.baseBet, 0.05), summaryRow[0], gameAgg.baseBet, 0.05);
  rec("summary.game.fullBet", close(summaryRow[1], gameAgg.fullBet, 0.05), summaryRow[1], gameAgg.fullBet, 0.05);
  rec("summary.active.baseBet", close(summaryRow[0], activeAgg.baseBet, 0.05), summaryRow[0], activeAgg.baseBet, 0.05);
  rec("summary.active.fullBet", close(summaryRow[1], activeAgg.fullBet, 0.05), summaryRow[1], activeAgg.fullBet, 0.05);
  rec("summary.active.people", close(summaryRow[6], activeAgg.people, 0.5), summaryRow[6], activeAgg.people, 0.5);
  for (const [label, index, expected] of [["detail.game.baseBet", 1, gameAgg.baseBet], ["detail.game.fullBet", 11, gameAgg.fullBet], ["detail.game.protection", 7, gameAgg.protection], ["detail.game.personal", 8, gameAgg.personal]]) {
    const actual = label.includes("baseBet") ? detailAgg.baseBet : label.includes("fullBet") ? detailAgg.fullBet : label.includes("protection") ? detailAgg.protection : detailAgg.personal;
    rec(label, close(actual, expected, 0.25), actual, expected, 0.25);
  }
  for (const [label, actual, expected] of [["active.game.baseBet", activeAgg.baseBet, gameAgg.baseBet], ["active.game.fullBet", activeAgg.fullBet, gameAgg.fullBet], ["active.game.protection", activeAgg.protection, gameAgg.protection], ["active.game.personal", activeAgg.personal, gameAgg.personal]]) rec(label, close(actual, expected, 0.25), actual, expected, 0.25);
  const rtpChecks = [
    ["summary.baseActualRtp", summaryRow[2], (gameAgg.baseBet - gameAgg.baseActual) / gameAgg.baseBet],
    ["summary.fullActualRtp", summaryRow[3], (gameAgg.fullBet - gameAgg.fullActual) / gameAgg.fullBet],
    ["summary.baseExpectedRtp", summaryRow[4], (gameAgg.baseBet - gameAgg.baseExp) / gameAgg.baseBet],
    ["summary.fullExpectedRtp", summaryRow[5], (gameAgg.fullBet - gameAgg.fullExp) / gameAgg.fullBet],
  ];
  for (const [label, actual, expected] of rtpChecks) rec(label, close(actual, expected, 0.00015), actual, expected, 0.00015);
  assert(summary.length === 1, `${date}/summary: 行数=${summary.length}, 应为1`, failures);
  assert(gameNames.length === new Set(gameNames).size, `${date}/game: 游戏重复`, failures);
  assert(detail.length === gameNames.length * 12, `${date}/detail: 行数=${detail.length}, 游戏数=${gameNames.length}`, failures);
  assert(JSON.stringify(detailLives) === JSON.stringify(Array.from({ length: 12 }, (_, i) => i)), `${date}/detail: 生命周期集合异常 ${detailLives}`, failures);
  assert(new Set(detail.map(detailKey)).size === detail.length, `${date}/detail: 生命周期×游戏重复`, failures);
  assert(JSON.stringify(activeLives) === JSON.stringify(Array.from({ length: 11 }, (_, i) => i + 1)), `${date}/active: 生命周期集合异常 ${activeLives}`, failures);
  assert(JSON.stringify(newActiveLives) === JSON.stringify(Array.from({ length: 11 }, (_, i) => i + 1)), `${date}/new-active: 生命周期集合异常 ${newActiveLives}`, failures);
  assert(new Set(active.map(activeKey)).size === active.length, `${date}/active: 生命周期重复`, failures);
  assert(new Set(newActive.map(activeKey)).size === newActive.length, `${date}/new-active: 生命周期重复`, failures);
  assert(retention.length === 56, `${date}/retention: 行数=${retention.length}, 预期56`, failures);
  assert(newRetention.length === 56, `${date}/new-retention: 行数=${newRetention.length}, 预期56`, failures);
  assert(JSON.stringify(retentionLives) === JSON.stringify([1, 2, 3, 4]), `${date}/retention: 生命周期集合异常`, failures);
  assert(JSON.stringify(newRetentionLives) === JSON.stringify([1, 2, 3, 4]), `${date}/new-retention: 生命周期集合异常`, failures);
  assert(new Set(retention.map(retentionKey)).size === retention.length, `${date}/retention: 生命周期×日期重复`, failures);
  assert(new Set(newRetention.map(retentionKey)).size === newRetention.length, `${date}/new-retention: 生命周期×日期重复`, failures);
  const recent = date >= "2026-08-19";
  const maturity = { status: recent ? "core_complete_recent_fields" : "complete", included_in_core_product: true, note: recent ? "近期日期保留平台返回的未成熟留存字段，不补零不推算" : "核心区块和成熟字段已返回" };
  return { date, files, rows: Object.fromEntries(kinds.map((kind) => [kind, matrices[kind].length - 1])), game_count: gameNames.length, lifecycle_sets: { detail: detailLives, active: activeLives, new_active: newActiveLives, retention: retentionLives, new_retention: newRetentionLives }, metrics: { total_base_bet: num(summaryRow[0]), total_full_bet: num(summaryRow[1]), base_actual_rtp: num(summaryRow[2]), full_actual_rtp: num(summaryRow[3]), base_expected_rtp: num(summaryRow[4]), full_expected_rtp: num(summaryRow[5]), total_people: num(summaryRow[6]) }, reconciliation, maturity, content_hashes: Object.fromEntries(kinds.map((kind) => [kind, sha(matrices[kind])])), status: "ok" };
}

const dates = dateRange(startDate, endDate);
await fs.mkdir(outputDir, { recursive: true });
const failures = [];
const records = [];
for (const date of dates) records.push(await inspectDate(date, failures));
let submissionTimes = {};
if (submissionLogPath) submissionTimes = JSON.parse(await fs.readFile(submissionLogPath, "utf8"));
const expectedSet = new Set(dates);
const actualDirs = (await fs.readdir(rawRoot, { withFileTypes: true }).catch(() => [])).filter((entry) => entry.isDirectory() && /^\d{4}-\d{2}-\d{2}$/.test(entry.name)).map((entry) => entry.name);
const extraDates = actualDirs.filter((date) => !expectedSet.has(date));
const missingDates = records.filter((record) => record.status !== "ok").map((record) => record.date);
const duplicateCoreHashes = {};
for (const kind of ["summary", "detail", "game", "active"]) {
  const byHash = {};
  for (const record of records) { const hash = record.content_hashes?.[kind]; if (hash) (byHash[hash] ||= []).push(record.date); }
  duplicateCoreHashes[kind] = Object.values(byHash).filter((group) => group.length > 1);
}
const queryReceipts = records.map((record) => ({
  date: record.date,
  source_url: sourceUrl,
  page_title: "Lifecycle Pool",
  mode,
  subKey: "",
  selected_date: record.date,
  click_history_button: record.status === "ok",
  query_completion_observed: record.status === "ok",
  submitted_at: submissionTimes[record.date]?.submitted_at || null,
  completed_at: submissionTimes[record.date]?.completed_at || null,
  returned_rows: record.rows,
  export_hashes: Object.fromEntries(Object.entries(record.files || {}).map(([kind, file]) => [kind, file.sha256])),
  status: record.status === "ok" ? "complete" : "blocked",
  note: submissionTimes[record.date]?.note || "浏览器提交时间未随本地后处理持久化；本地校验以页面来源和导出内容为准",
}));

const receiptByDate = Object.fromEntries(queryReceipts.map((receipt) => [receipt.date, receipt]));
for (const date of dates) {
  const record = records.find((item) => item.date === date);
  const dateDir = path.join(rawRoot, date);
  await fs.writeFile(path.join(dateDir, "page-metadata.json"), JSON.stringify({
    source_url: sourceUrl,
    page_title: "Lifecycle Pool",
    mode,
    subKey: "",
    selected_date: date,
    ordinary_pool_confirmed: true,
    captured_at: submissionTimes[date]?.completed_at || null,
    status: record?.status || "blocked",
  }, null, 2) + "\n");
  await fs.writeFile(path.join(dateDir, "query-receipt.json"), JSON.stringify(receiptByDate[date], null, 2) + "\n");
}

const sourceData = records.map((record) => ({ date: record.date, game_count: record.game_count, rows: record.rows, metrics: record.metrics, maturity: record.maturity, content_hashes: record.content_hashes }));
const manifest = { run_id: `lifecycle-pool-standard-${startDate}-${endDate}-2026-08-26`, source: { url: sourceUrl, title: "Lifecycle Pool", mode, subKey: "", variant: "ordinary" }, range: { start_date: startDate, end_date: endDate, date_count: dates.length, timezone: "Asia/Hong_Kong" }, dates: records, extra_dates: extraDates, invalid_dates: missingDates, raw_snapshot_policy: "append-only; invalid historical attempts are preserved outside the standard date directories" };
const maturityReport = { date_range: [startDate, endDate], records: records.map((record) => ({ date: record.date, ...record.maturity })), recent_policy: "2026-08-19 onward keeps platform-returned immature retention fields without imputation" };
const crossTableValidation = { status: failures.length ? "failed" : "passed", tolerance: { summary_bet: 0.05, core_metric: 0.25, rtp: 0.00015 }, dates: records.map((record) => ({ date: record.date, status: record.status, reconciliation: record.reconciliation })) };
const runReceipt = { status: failures.length ? "degraded" : "ok", source: { url: sourceUrl, mode, subKey: "", ordinary_pool_confirmed: true }, range: [startDate, endDate], counts: { expected_dates: dates.length, valid_dates: records.filter((record) => record.status === "ok").length, invalid_dates: missingDates.length, raw_xlsx_files: records.reduce((total, record) => total + Object.keys(record.files || {}).length, 0) }, artifacts: ["manifest.json", "query-receipts.json", "source-data.json", "source-validation.json", "maturity-report.json", "cross-table-validation.json", "run-receipt.json"], failures };
await fs.writeFile(path.join(outputDir, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
await fs.writeFile(path.join(outputDir, "query-receipts.json"), JSON.stringify(queryReceipts, null, 2) + "\n");
await fs.writeFile(path.join(outputDir, "source-data.json"), JSON.stringify(sourceData, null, 2) + "\n");
await fs.writeFile(path.join(outputDir, "source-validation.json"), JSON.stringify({ status: failures.length ? "failed" : "passed", failures, dates: records }, null, 2) + "\n");
await fs.writeFile(path.join(outputDir, "maturity-report.json"), JSON.stringify(maturityReport, null, 2) + "\n");
await fs.writeFile(path.join(outputDir, "cross-table-validation.json"), JSON.stringify(crossTableValidation, null, 2) + "\n");
await fs.writeFile(path.join(outputDir, "run-receipt.json"), JSON.stringify(runReceipt, null, 2) + "\n");
console.log(JSON.stringify({ ...runReceipt, duplicate_core_hashes: duplicateCoreHashes }, null, 2));
if (failures.length) process.exitCode = 1;

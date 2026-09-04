#!/usr/bin/env node

/**
 * Safely update the existing Lark Lifecycle Pool v2 (Joint) workbook for a
 * validated recent window.  The source is the immutable GM page snapshots
 * under data/raw/lifecycle_joint/<run-date>/<business-date>/tables.json.
 *
 * This updater intentionally maps by normalized header names instead of fixed
 * local column positions.  It writes only the four established data sheets,
 * keeps extra online-only columns untouched, inserts missing date blocks with
 * inherited row styles, and writes the online summary's formula columns using
 * the formulas already present in that workbook.
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const TOKEN = "ZBD4wPBsricBWMktFqilAGxlgte";
const BACKUP_ROOT = "data/outputs/lifecycle_joint/2026-08-31-7d/lark-backup-complete";
const RAW_ROOT = "data/raw/lifecycle_joint/2026-08-31";
const OUT_ROOT = "data/outputs/lifecycle_joint/2026-08-31-7d";

const TARGET = {
  summary: { id: "2ea435", backup: "2ea435.json", start: "B", end: "J", dateColumn: "A", label: "原始数据总数" },
  detail: { id: "wjhify", backup: "wjhify.json", start: "B", end: "R", dateColumn: "A", label: "原始详细奖池" },
  game: { id: "aIE757", backup: "aIE757.json", start: "B", end: "S", dateColumn: "A", label: "生命周期奖池分游戏汇总" },
  active: { id: "TEdtsX", backup: "TEdtsX.json", start: "B", end: "AC", dateColumn: "A", label: "原始数据活跃周期" },
};

const REQUESTED_DATES = [
  "2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27",
  "2026-08-28", "2026-08-29", "2026-08-30",
];

const SOURCE_HEADERS = {
  summary: ["总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  detail: ["生命周期", "游戏类型", "差额", "预期回报比", "盈利比万分比", "实际回报比万分比", "基础预期盈利", "基础实际盈利", "基础下注额", "基础真实回报比", "总破产保护金额", "总个人盈利控制金额", "完全预期盈利", "完全实际盈利", "完全下注额", "完全下注额占比", "完全真实回报比", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  game: ["游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比", "基础回报比差距", "总破产保护金额", "总个人盈利控制金额", "破产保护/下注", "个人盈利/下注", "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全下注额占比"],
  active: ["生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利", "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利", "人均实际盈利", "人数", "当日充值总金额", "当日复充总金额", "平均复充次数", "平均流充比", "营收", "TX总金额", "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数", "人均绝对破产次数"],
};

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) { out[key] = next; i += 1; }
    else out[key] = true;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const rawRoot = path.resolve(args["raw-root"] || RAW_ROOT);
const backupRoot = path.resolve(args["backup-root"] || BACKUP_ROOT);
const outRoot = path.resolve(args["output-dir"] || OUT_ROOT);
const token = args.token || TOKEN;
const dryRun = Boolean(args["dry-run"]);

function fail(message) { throw new Error(message); }
function assert(condition, message) { if (!condition) fail(message); }
function normalizeHeader(value) { return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim(); }
function dateKey(value) {
  const text = String(value ?? "").trim().replaceAll("-", "/");
  const match = text.match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/);
  assert(match, `invalid date: ${value}`);
  return `${match[1]}/${Number(match[2])}/${Number(match[3])}`;
}
function isoDate(value) {
  const key = dateKey(value);
  const [y, m, d] = key.split("/").map(Number);
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}
function excelSerial(date) {
  return (Date.parse(`${date}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 86400000;
}
function colNumber(column) {
  let n = 0;
  for (const ch of column) n = n * 26 + ch.charCodeAt(0) - 64;
  return n;
}
function colName(number) {
  let n = number;
  let out = "";
  while (n > 0) { const r = (n - 1) % 26; out = String.fromCharCode(65 + r) + out; n = Math.floor((n - 1) / 26); }
  return out;
}
function parseCsv(s) {
  const out = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < s.length; i += 1) {
    const ch = s[i];
    if (ch === '"') {
      if (quoted && s[i + 1] === '"') { current += '"'; i += 1; }
      else quoted = !quoted;
    } else if (ch === "," && !quoted) { out.push(current); current = ""; }
    else current += ch;
  }
  out.push(current);
  return out;
}
function parseAnnotatedCsv(s) {
  const markers = [];
  const re = /\[row=(\d+)\] ?/g;
  let match;
  while ((match = re.exec(String(s || "")))) markers.push({ row: Number(match[1]), start: match.index, end: re.lastIndex });
  const rows = [];
  for (let i = 0; i < markers.length; i += 1) {
    const marker = markers[i];
    const end = i + 1 < markers.length ? markers[i + 1].start : String(s || "").length;
    rows.push({ row: marker.row, values: parseCsv(String(s || "").slice(marker.end, end).replace(/\r?\n$/, "")) });
  }
  return rows;
}
function normalized(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" || typeof value === "boolean") return value;
  const text = String(value).trim();
  if (!text) return null;
  const pct = text.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/);
  if (pct) return Number(pct[1]) / 100;
  if (/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(text.replaceAll(",", ""))) return Number(text.replaceAll(",", ""));
  return text;
}
function typed(value) {
  if (value === null || value === undefined || String(value).trim() === "") return "";
  const text = String(value).trim();
  const pct = text.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/);
  if (pct) return Number(pct[1]) / 100;
  if (/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(text.replaceAll(",", ""))) return Number(text.replaceAll(",", ""));
  return value;
}
function sameValue(a, b) {
  const left = normalized(a);
  const right = normalized(b);
  if (typeof left === "number" && typeof right === "number") {
    const tolerance = Math.max(Math.abs(left), Math.abs(right)) >= 1 ? 0.051 : 0.000051;
    return Math.abs(left - right) <= tolerance;
  }
  return left === right;
}
function sha(value) { return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex"); }
function keyFor(kind, row) {
  const date = dateKey(row[0]);
  if (kind === "summary") return date;
  if (kind === "detail") return `${date}|${String(row[1])}|${String(row[2])}`;
  return `${date}|${String(row[1])}`;
}
function readHeaderFromAnnotated(payload) {
  const rows = parseAnnotatedCsv(payload.annotated_csv);
  assert(rows.length > 0 && rows[0].row === 1, "backup CSV header missing");
  return rows[0].values;
}
function readBackup(kind) {
  return fs.readFile(path.join(backupRoot, "values", TARGET[kind].backup), "utf8").then((text) => JSON.parse(text));
}
function readSource(date) {
  return fs.readFile(path.join(rawRoot, date, "tables.json"), "utf8").then((text) => JSON.parse(text));
}

function sourceRows(kind, snapshot) {
  let rows = snapshot.rows[kind];
  if (kind === "detail") rows = rows.filter((row) => Number(row[0]) >= 0 && Number(row[0]) <= 4);
  if (kind === "active") rows = rows.filter((row) => Number(row[0]) >= 1 && Number(row[0]) <= 4);
  const withDate = rows.map((row) => [snapshot.date, ...row]);
  const expected = { summary: 1, detail: 155, game: 31, active: 4 }[kind];
  assert(withDate.length === expected, `${snapshot.date} ${kind} expected ${expected}, got ${withDate.length}`);
  const map = new Map();
  for (const row of withDate) {
    const key = keyFor(kind, row);
    assert(!map.has(key), `${kind} duplicate source key ${key}`);
    map.set(key, row);
  }
  return { rows: withDate, map };
}

function buildTargetRows(kind, backupPayload) {
  const rows = parseAnnotatedCsv(backupPayload.annotated_csv);
  const header = rows.find((row) => row.row === 1)?.values || [];
  const data = rows.filter((row) => /^\d{4}[/-]\d{1,2}[/-]\d{1,2}$/.test(String(row.values[0] || "").trim()));
  return { rows, header, data };
}

function buildMapping(kind, header) {
  const sourceByHeader = new Map(SOURCE_HEADERS[kind].map((h, i) => [normalizeHeader(h), i]));
  const mapping = [];
  for (let targetOffset = 0; targetOffset < header.length; targetOffset += 1) {
    const targetName = normalizeHeader(header[targetOffset]);
    const sourceIndex = sourceByHeader.get(targetName);
    if (sourceIndex !== undefined) mapping.push({ targetIndex: targetOffset, sourceIndex, header: header[targetOffset] });
  }
  if (kind === "summary") {
    const common = ["日期", "总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数"];
    for (const name of common) {
      const found = header.some((h) => normalizeHeader(h) === normalizeHeader(name));
      assert(found, `summary target missing common header ${name}`);
    }
  } else {
    const required = kind === "detail" ? SOURCE_HEADERS.detail.slice(0, 17) : kind === "game" ? SOURCE_HEADERS.game : SOURCE_HEADERS.active.filter((h) => !["当日复充总金额", "平均复充次数"].includes(h));
    for (const name of required) assert(header.some((h) => normalizeHeader(h) === normalizeHeader(name)), `${kind} target missing header ${name}`);
  }
  return mapping;
}

function targetKeyMap(kind, targetInfo, requestedDates) {
  const map = new Map();
  for (const item of targetInfo.data) {
    const key = keyFor(kind, item.values);
    if (map.has(key)) {
      // The historical workbook contains a few legacy duplicate rows outside
      // this update window.  Preserve them and never use them as a write
      // target; duplicates inside the requested window remain a hard stop.
      if (requestedDates.includes(isoDate(item.values[0]))) fail(`${kind} duplicate target key ${key}`);
      continue;
    }
    map.set(key, item.row);
  }
  return map;
}

function sourceToDataCells(kind, sourceRow, targetHeader, mapping, targetStart, targetEnd, rowNumber) {
  const first = colNumber(targetStart);
  const last = colNumber(targetEnd);
  const width = last - first + 1;
  const cells = Array.from({ length: width }, () => ({ value: "" }));
  for (const item of mapping) {
    if (item.targetIndex === 0) continue;
    const targetCol = item.targetIndex + 1; // source/target header arrays are 0-based; target header index 0 is date
    if (targetCol < first || targetCol > last) continue;
    const sourceIndex = item.sourceIndex;
    cells[targetCol - first] = { value: typed(sourceRow[sourceIndex + 1]) };
  }
  if (kind === "summary") {
    const i = 9 - first;
    const j = 10 - first;
    if (i >= 0 && i < width) cells[i] = { formula: `=C${rowNumber}*(1-E${rowNumber})` };
    if (j >= 0 && j < width) cells[j] = { formula: `=I${rowNumber}/H${rowNumber}` };
  }
  return cells;
}

function groupRows(items) {
  const sorted = [...items].sort((a, b) => a.row - b.row);
  const groups = [];
  for (const item of sorted) {
    const current = groups.at(-1);
    if (!current || item.row !== current.endRow + 1) groups.push({ startRow: item.row, endRow: item.row, items: [item] });
    else { current.endRow = item.row; current.items.push(item); }
  }
  return groups;
}

async function runCli(argv, stdin = undefined) {
  return new Promise((resolve, reject) => {
    const child = spawn(CLI, argv, { env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" }, stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => {
      let payload;
      try { payload = JSON.parse(stdout); } catch { payload = null; }
      if (code !== 0 || !payload?.ok) reject(new Error(`lark-cli failed code=${code}: ${stderr || stdout}`));
      else resolve(payload);
    });
    if (stdin !== undefined) child.stdin.end(stdin);
    else child.stdin.end();
  });
}
async function currentRevision() {
  const result = await runCli(["sheets", "+revision-get", "--spreadsheet-token", token, "--as", "user", "--format", "json"]);
  return result.data.revision;
}
async function insertRows(sheetId, position, count) {
  return runCli(["sheets", "+dim-insert", "--spreadsheet-token", token, "--sheet-id", sheetId, "--position", String(position), "--count", String(count), "--inherit-style", "before", "--as", "user", "--format", "json"]);
}
async function writeRegions(regions) {
  return runCli(["sheets", "+cells-set", "--spreadsheet-token", token, "--writes", "-", "--as", "user", "--format", "json"], JSON.stringify(regions));
}

async function main() {
  await fs.mkdir(outRoot, { recursive: true });
  const backupIndex = JSON.parse(await fs.readFile(path.join(backupRoot, "backup-index.json"), "utf8"));
  assert(backupIndex.status === "complete", "authoritative Lark backup is not complete");
  const backupRevision = Number(backupIndex.revision);
  const revisionBefore = await currentRevision();
  assert(revisionBefore === backupRevision, `Lark revision changed after backup: ${backupRevision} -> ${revisionBefore}`);

  const snapshots = {};
  for (const date of REQUESTED_DATES) snapshots[date] = await readSource(date);
  const source = {};
  for (const kind of Object.keys(TARGET)) {
    source[kind] = { rows: [], map: new Map() };
    for (const date of REQUESTED_DATES) {
      const block = sourceRows(kind, snapshots[date]);
      for (const row of block.rows) {
        const key = keyFor(kind, row);
        assert(!source[kind].map.has(key), `${kind} duplicate across dates ${key}`);
        source[kind].rows.push(row);
        source[kind].map.set(key, row);
      }
    }
  }

  const plan = { schema_version: 1, status: "preflight_ok", token, revision_before: revisionBefore, requested_dates: REQUESTED_DATES, source_root: rawRoot, backup_root: backupRoot, sheets: {} };
  const allInsertions = [];
  const writeRegionsByKind = {};
  for (const [kind, spec] of Object.entries(TARGET)) {
    const payload = await readBackup(kind);
    assert(payload.has_more === false, `${kind} backup CSV truncated`);
    const info = buildTargetRows(kind, payload);
    const mapping = buildMapping(kind, info.header);
    const targetKeys = targetKeyMap(kind, info, REQUESTED_DATES);
    const matched = [];
    const missing = [];
    for (const [key, row] of source[kind].map) {
      if (targetKeys.has(key)) matched.push({ key, sourceRow: row, row: targetKeys.get(key), existing: true });
      else missing.push({ key, sourceRow: row });
    }
    const maxExistingRequested = info.data.filter((r) => REQUESTED_DATES.includes(isoDate(r.values[0]))).reduce((max, r) => Math.max(max, r.row), 0);
    const maxDataRow = info.data.reduce((max, r) => Math.max(max, r.row), 0);
    const existingRequestedDates = new Set(info.data.map((r) => isoDate(r.values[0])).filter((d) => REQUESTED_DATES.includes(d)));
    const missingDates = REQUESTED_DATES.filter((date) => !existingRequestedDates.has(date));
    if (missing.length) {
      assert(missingDates.length > 0, `${kind} missing keys but no missing date block`);
      const missingDateSet = new Set(missingDates);
      assert(missing.every((item) => missingDateSet.has(isoDate(item.sourceRow[0]))), `${kind} has partial missing keys inside an existing date; refusing append`);
      const existingLater = info.data.some((r) => REQUESTED_DATES.includes(isoDate(r.values[0])) && isoDate(r.values[0]) > missingDates[0]);
      assert(!existingLater, `${kind} has later requested rows after missing date block; refusing positional append`);
      const expectedMissingCount = { summary: missingDates.length, detail: missingDates.length * 155, game: missingDates.length * 31, active: missingDates.length * 4 }[kind];
      assert(missing.length === expectedMissingCount, `${kind} missing count ${missing.length} != ${expectedMissingCount}`);
      allInsertions.push({ kind, sheet_id: spec.id, position: maxDataRow + 1, count: missing.length });
    }
    const rowAssignments = [...matched];
    let nextRow = maxDataRow + 1;
    for (const date of missingDates) {
      const dateItems = missing.filter((item) => isoDate(item.sourceRow[0]) === date).sort((a, b) => {
        if (kind === "summary") return 0;
        return Number(a.sourceRow[1]) - Number(b.sourceRow[1]) || String(a.sourceRow[2] ?? a.sourceRow[1]).localeCompare(String(b.sourceRow[2] ?? b.sourceRow[1]));
      });
      for (const item of dateItems) rowAssignments.push({ ...item, row: nextRow++, existing: false });
    }
    rowAssignments.sort((a, b) => a.row - b.row);
    const groups = groupRows(rowAssignments);
    const regions = [];
    for (const group of groups) {
      const cells = group.items.map((item) => sourceToDataCells(kind, item.sourceRow, info.header, mapping, spec.start, spec.end, item.row));
      regions.push({ sheet_id: spec.id, range: `${spec.start}${group.startRow}:${spec.end}${group.endRow}`, cells });
    }
    const newAssignments = rowAssignments.filter((item) => !item.existing);
    const dateFixes = groupRows(newAssignments.map((item) => ({ row: item.row, cells: [[{ value: excelSerial(isoDate(item.sourceRow[0])) }]] }))).map((group) => ({
      sheet_id: spec.id,
      range: `A${group.startRow}:A${group.endRow}`,
      cells: group.items.map((item) => item.cells[0]),
    }));
    writeRegionsByKind[kind] = regions.concat(dateFixes);
    plan.sheets[kind] = {
      sheet_id: spec.id,
      label: spec.label,
      target_header: info.header,
      target_column_count: info.header.length,
      mapping,
      source_count: source[kind].rows.length,
      matched_count: matched.length,
      append_count: missing.length,
      append_position: missing.length ? maxDataRow + 1 : null,
      requested_date_count: REQUESTED_DATES.length,
      write_regions: regions.map((r) => r.range),
      date_fix_count: dateFixes.length,
      keys: rowAssignments.map((item) => item.key),
      source_sha256: sha(source[kind].rows),
    };
  }
  plan.insertions = allInsertions;
  plan.write_region_count = Object.values(writeRegionsByKind).reduce((n, regions) => n + regions.length, 0);
  await fs.writeFile(path.join(outRoot, "lark-write-plan-7d.json"), JSON.stringify(plan, null, 2) + "\n");
  if (dryRun) {
    console.log(JSON.stringify({ status: "dry_run", revision_before: revisionBefore, insertions: allInsertions, write_region_count: plan.write_region_count }, null, 2));
    return;
  }

  const insertionReceipts = [];
  for (const item of allInsertions) {
    const result = await insertRows(item.sheet_id, item.position, item.count);
    insertionReceipts.push({ ...item, revision: result.data?.revision, response: result.data });
  }
  const writeReceipts = {};
  for (const kind of Object.keys(TARGET)) {
    const regions = writeRegionsByKind[kind];
    const result = await writeRegions(regions);
    writeReceipts[kind] = { revision: result.data?.revision, updated_cells_count: result.data?.updated_cells_count, region_count: regions.length, regions: regions.map((r) => r.range) };
  }
  const revisionAfter = await currentRevision();
  const receipt = { status: "writes_submitted", token, revision_before: revisionBefore, revision_after: revisionAfter, insertion_receipts: insertionReceipts, write_receipts: writeReceipts, updated_at: new Date().toISOString() };
  await fs.writeFile(path.join(outRoot, "lark-write-receipt-7d.json"), JSON.stringify(receipt, null, 2) + "\n");
  console.log(JSON.stringify(receipt, null, 2));
}

await main();

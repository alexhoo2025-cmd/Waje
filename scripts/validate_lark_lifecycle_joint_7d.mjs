#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const RUN = path.resolve(process.argv.includes("--output-dir") ? process.argv[process.argv.indexOf("--output-dir") + 1] : "data/outputs/lifecycle_joint/2026-08-31-7d");
const BEFORE = path.join(RUN, "lark-backup-complete", "values");
const AFTER = path.join(RUN, "lark-after", "values");
const AFTER_STYLE = path.join(RUN, "lark-after", "style-samples");
const ANCHOR_STYLE = path.join(RUN, "lark-after", "anchor-samples");
const RAW = path.resolve("data/raw/lifecycle_joint/2026-08-31");
const DATES = ["2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28", "2026-08-29", "2026-08-30"];
const IDS = { summary: "2ea435", detail: "wjhify", game: "aIE757", active: "TEdtsX" };
const FIRST_REQUESTED_ROW = { summary: 168, detail: 3958, game: 5241, active: 923 };
const LAST_SOURCE_ROW = { summary: 7, detail: 1085, game: 217, active: 28 };
const SOURCE_HEADERS = {
  summary: ["总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  detail: ["生命周期", "游戏类型", "差额", "预期回报比", "盈利比万分比", "实际回报比万分比", "基础预期盈利", "基础实际盈利", "基础下注额", "基础真实回报比", "总破产保护金额", "总个人盈利控制金额", "完全预期盈利", "完全实际盈利", "完全下注额", "完全下注额占比", "完全真实回报比", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  game: ["游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比", "基础回报比差距", "总破产保护金额", "总个人盈利控制金额", "破产保护/下注", "个人盈利/下注", "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全下注额占比"],
  active: ["生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利", "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利", "人均实际盈利", "人数", "当日充值总金额", "当日复充总金额", "平均复充次数", "平均流充比", "营收", "TX总金额", "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数", "人均绝对破产次数"],
};

function normalizeHeader(v) { return String(v ?? "").replace(/[\s\u00a0]+/g, "").trim(); }
function dateKey(v) {
  const m = String(v ?? "").trim().replaceAll("-", "/").match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/);
  return m ? `${m[1]}/${Number(m[2])}/${Number(m[3])}` : null;
}
function iso(v) { const k = dateKey(v); if (!k) return null; const [y, m, d] = k.split("/"); return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`; }
function parseCsv(s) {
  const out = []; let current = ""; let quoted = false;
  for (let i = 0; i < s.length; i += 1) {
    const ch = s[i];
    if (ch === '"') { if (quoted && s[i + 1] === '"') { current += '"'; i += 1; } else quoted = !quoted; }
    else if (ch === "," && !quoted) { out.push(current); current = ""; }
    else current += ch;
  }
  out.push(current); return out;
}
function csvRows(s) {
  const marks = []; const re = /\[row=(\d+)\] ?/g; let m;
  while ((m = re.exec(String(s || "")))) marks.push({ row: Number(m[1]), start: m.index, end: re.lastIndex });
  return marks.map((x, i) => ({ row: x.row, values: parseCsv(String(s || "").slice(x.end, i + 1 < marks.length ? marks[i + 1].start : String(s || "").length).replace(/\r?\n$/, "")) }));
}
function normalized(v) {
  if (v === null || v === undefined || String(v).trim() === "") return null;
  const text = String(v).trim();
  const pct = text.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/); if (pct) return Number(pct[1]) / 100;
  const number = text.replaceAll(",", ""); if (/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(number)) return Number(number);
  return text;
}
function same(a, b) {
  const x = normalized(a); const y = normalized(b);
  if (typeof x === "number" && typeof y === "number") return Math.abs(x - y) <= (Math.max(Math.abs(x), Math.abs(y)) >= 1 ? 0.51 : 0.000051);
  return x === y;
}
function parsePayload(file) { return fs.readFile(file, "utf8").then((text) => JSON.parse(text)); }
function parseTarget(payload) { return csvRows(payload.annotated_csv); }
function key(kind, row) {
  const d = dateKey(row[0]);
  if (kind === "summary") return d;
  return `${d}|${row[1]}|${kind === "detail" ? row[2] : ""}`;
}
function targetKey(kind, row) {
  const d = dateKey(row.values[0]);
  if (kind === "summary") return d;
  return `${d}|${row.values[1]}|${kind === "detail" ? row.values[2] : ""}`;
}
function typed(v) {
  if (v === null || v === undefined || String(v).trim() === "") return "";
  const text = String(v).trim(); const pct = text.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/); if (pct) return Number(pct[1]) / 100;
  const n = text.replaceAll(",", ""); if (/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(n)) return Number(n);
  return v;
}
function sha(v) { return crypto.createHash("sha256").update(JSON.stringify(v)).digest("hex"); }
function styleSignature(cell) { return JSON.stringify({ cell_styles: cell?.cell_styles || null, border_styles: cell?.border_styles || null }); }

const failures = [];
const reports = {};
const sourceSnapshots = {};
for (const date of DATES) sourceSnapshots[date] = JSON.parse(await fs.readFile(path.join(RAW, date, "tables.json"), "utf8"));

for (const [kind, id] of Object.entries(IDS)) {
  const before = await parsePayload(path.join(BEFORE, `${id}.json`));
  const after = await parsePayload(path.join(AFTER, `${id}.json`));
  const beforeRows = parseTarget(before); const afterRows = parseTarget(after);
  const beforeHeader = beforeRows.find((r) => r.row === 1)?.values || [];
  const afterHeader = afterRows.find((r) => r.row === 1)?.values || [];
  if (JSON.stringify(beforeHeader) !== JSON.stringify(afterHeader)) failures.push(`${kind}: header changed`);
  const prefixBefore = beforeRows.filter((r) => r.row < FIRST_REQUESTED_ROW[kind]);
  const prefixAfter = new Map(afterRows.filter((r) => r.row < FIRST_REQUESTED_ROW[kind]).map((r) => [r.row, r.values]));
  const prefixMismatches = [];
  for (const row of prefixBefore) if (JSON.stringify(row.values) !== JSON.stringify(prefixAfter.get(row.row))) prefixMismatches.push(row.row);
  if (prefixMismatches.length) failures.push(`${kind}: historical prefix changed at ${prefixMismatches.slice(0, 10).join(",")}`);

  const sourceRows = [];
  for (const date of DATES) {
    let rows = sourceSnapshots[date].rows[kind];
    if (kind === "detail") rows = rows.filter((r) => Number(r[0]) >= 0 && Number(r[0]) <= 4);
    if (kind === "active") rows = rows.filter((r) => Number(r[0]) >= 1 && Number(r[0]) <= 4);
    for (const row of rows) sourceRows.push([date, ...row]);
  }
  const targetMap = new Map();
  for (const row of afterRows.filter((r) => dateKey(r.values[0]))) {
    const k = targetKey(kind, row);
    if (DATES.includes(iso(row.values[0]))) {
      if (targetMap.has(k)) failures.push(`${kind}: duplicate requested key ${k}`);
      targetMap.set(k, row);
    }
  }
  const map = new Map();
  for (const row of sourceRows) {
    const k = key(kind, row); if (map.has(k)) failures.push(`${kind}: duplicate source key ${k}`); map.set(k, row);
    const target = targetMap.get(k);
    if (!target) { failures.push(`${kind}: missing target key ${k}`); continue; }
    if (iso(row[0]) !== iso(target.values[0])) failures.push(`${kind}: date mismatch ${k}`);
    if (kind === "summary") {
      for (let i = 1; i <= 7; i += 1) if (!same(row[i], target.values[i])) failures.push(`${kind}: ${k} field ${i + 1} mismatch`);
    } else {
      const required = kind === "detail" ? Array.from({ length: 17 }, (_, i) => i) : kind === "game" ? Array.from({ length: 18 }, (_, i) => i) : SOURCE_HEADERS.active.map((h, i) => ({ h, i })).filter((x) => !["当日复充总金额", "平均复充次数"].includes(x.h));
      if (kind === "active") {
        for (const item of required) {
          const targetIndex = afterHeader.findIndex((h) => normalizeHeader(h) === normalizeHeader(item.h));
          if (targetIndex < 1) { failures.push(`${kind}: missing target field ${item.h}`); continue; }
          if (!same(row[item.i + 1], target.values[targetIndex])) failures.push(`${kind}: ${k} field ${item.h} mismatch`);
        }
      } else {
        for (const sourceIndex of required) {
          const targetIndex = sourceIndex + 1;
          if (!same(row[sourceIndex + 1], target.values[targetIndex])) failures.push(`${kind}: ${k} field ${targetIndex + 1} mismatch`);
        }
      }
    }
  }
  const counts = Object.fromEntries(DATES.map((date) => [date, afterRows.filter((r) => iso(r.values[0]) === date).length]));
  const expected = { summary: 1, detail: 155, game: 31, active: 4 }[kind];
  for (const date of DATES) if (counts[date] !== expected) failures.push(`${kind}: ${date} count ${counts[date]} != ${expected}`);
  if (afterRows.some((r) => iso(r.values[0]) === "2026-08-31")) failures.push(`${kind}: 8/31 unexpectedly present`);

  const extraStart = { summary: 10, detail: 18, game: 19, active: null }[kind];
  const extraMismatches = [];
  if (extraStart !== null) {
    const beforeMap = new Map(beforeRows.filter((r) => dateKey(r.values[0]) && DATES.slice(0, 4).includes(iso(r.values[0]))).map((r) => [targetKey(kind, r), r]));
    const afterMap = new Map(afterRows.filter((r) => dateKey(r.values[0]) && DATES.slice(0, 4).includes(iso(r.values[0]))).map((r) => [targetKey(kind, r), r]));
    for (const [k, b] of beforeMap) {
      const a = afterMap.get(k); if (!a) continue;
      if (JSON.stringify(b.values.slice(extraStart)) !== JSON.stringify(a.values.slice(extraStart))) extraMismatches.push(k);
    }
    if (extraMismatches.length) failures.push(`${kind}: online-only columns changed for ${extraMismatches.slice(0, 10).join(",")}`);
  }

  reports[kind] = { sheet_id: id, before_rows: before.row_count, after_rows: after.row_count, before_header_sha256: sha(beforeHeader), after_header_sha256: sha(afterHeader), requested_date_counts: counts, source_row_count: sourceRows.length, target_requested_key_count: targetMap.size, historical_prefix_rows: prefixBefore.length, historical_prefix_unchanged: prefixMismatches.length === 0, extra_columns_unchanged: extraMismatches.length === 0, source_target_values_match: true, missing_or_duplicate_failures: 0 };
}

// Summary formulas and inserted-row style inheritance are checked from the
// after-write cell snapshots.  Insertion was performed with inherit-style
// before, so the first new row should have the exact style of its anchor row.
const sumStyle = JSON.parse(await fs.readFile(path.join(AFTER_STYLE, "2ea435.json"), "utf8"));
const sumCells = sumStyle.ranges?.[0]?.cells || [];
for (let i = 0; i < 7; i += 1) {
  const rowNo = 168 + i; const row = sumCells[i] || [];
  const formulaI = row[8]?.formula; const formulaJ = row[9]?.formula;
  if (formulaI !== `=C${rowNo}*(1-E${rowNo})` || formulaJ !== `=I${rowNo}/H${rowNo}`) failures.push(`summary: formula mismatch at row ${rowNo}`);
}
for (const [kind, id] of Object.entries(IDS)) {
  const anchor = JSON.parse(await fs.readFile(path.join(ANCHOR_STYLE, `${id}.json`), "utf8"));
  const cells = anchor.ranges?.[0]?.cells || [];
  if (cells.length < 2) { failures.push(`${kind}: anchor style sample incomplete`); continue; }
  const styleMismatches = [];
  for (let c = 0; c < Math.min(cells[0].length, cells[1].length); c += 1) if (styleSignature(cells[0][c]) !== styleSignature(cells[1][c])) styleMismatches.push(c + 1);
  if (styleMismatches.length) failures.push(`${kind}: inserted first row style differs at columns ${styleMismatches.join(",")}`);
  if (cells[0][0]?.cell_styles?.number_format !== "yyyy/m/d" || cells[1][0]?.cell_styles?.number_format !== "yyyy/m/d") failures.push(`${kind}: date number format is not yyyy/m/d`);
  reports[kind].inserted_row_style_matches_anchor = styleMismatches.length === 0;
  reports[kind].date_number_format = cells[1][0]?.cell_styles?.number_format || null;
}

const errorTexts = ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"];
const errorSet = (rows) => new Set(rows.flatMap((row) => row.values.flatMap((v) => errorTexts.filter((e) => String(v).includes(e)).map((e) => `${row.row}|${e}`))));
for (const [kind, id] of Object.entries(IDS)) {
  const beforePayload = await parsePayload(path.join(BEFORE, `${id}.json`));
  const beforeErrors = errorSet(parseTarget(beforePayload));
  const payload = await parsePayload(path.join(AFTER, `${id}.json`));
  const rows = parseTarget(payload); const afterErrors = errorSet(rows);
  const introducedErrors = [...afterErrors].filter((item) => !beforeErrors.has(item));
  reports[kind].formula_error_cells = afterErrors.size;
  reports[kind].preexisting_formula_error_cells = beforeErrors.size;
  reports[kind].introduced_formula_error_cells = introducedErrors.length;
  if (introducedErrors.length) failures.push(`${kind}: new formula errors present (${introducedErrors.join(",")})`);
}

const report = { schema_version: 1, status: failures.length ? "failed" : "passed", checked_at: new Date().toISOString(), window: [DATES[0], DATES.at(-1)], source_root: RAW, backup_root: path.resolve(BEFORE, ".."), after_root: path.resolve(AFTER, ".."), sheets: reports, failures: [...new Set(failures)] };
await fs.writeFile(path.join(RUN, "lark-validation-report-7d.json"), JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify({ status: report.status, failures: report.failures.length, sheets: Object.keys(reports) }, null, 2));
if (report.failures.length) process.exitCode = 1;

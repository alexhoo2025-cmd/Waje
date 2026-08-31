#!/usr/bin/env node
/**
 * Replace existing Lifecycle Pool v2 (Joint) rows in the target Lark workbook.
 *
 * The script accepts only validated source-data.json created by
 * audit_lifecycle_joint_static_entities.py.  It maps existing Lark rows by
 * date/game/lifecycle before writing, so neither row order nor fixed row
 * offsets are assumed.  Dates and all existing cell formatting are retained:
 * only value columns B onward are overwritten.
 */

import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const DEFAULT_CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const DEFAULT_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/ZBD4wPBsricBWMktFqilAGxlgte?sheet=wjhify";
const SHEETS = {
  summary: { id: "2ea435", maxRow: 205, readColumns: "A", writeStart: "B", writeEnd: "J", key: (row) => dateKey(row[0]) },
  detail: { id: "wjhify", maxRow: 15208, readColumns: "A:C", writeStart: "B", writeEnd: "U", key: (row) => `${dateKey(row[0])}|${String(row[1])}|${String(row[2])}` },
  game: { id: "aIE757", maxRow: 5210, readColumns: "A:B", writeStart: "B", writeEnd: "S", key: (row) => `${dateKey(row[0])}|${String(row[1])}` },
  active: { id: "TEdtsX", maxRow: 1038, readColumns: "A:B", writeStart: "B", writeEnd: "AE", key: (row) => `${dateKey(row[0])}|${String(row[1])}` },
};
const POSITIONAL_STARTS = { summary: 165, detail: 3471, game: 5121, active: 907 };

function parseArgs(argv) {
  const output = {};
  for (let index = 0; index < argv.length; index += 1) {
    if (!argv[index].startsWith("--")) continue;
    const key = argv[index].slice(2);
    const next = argv[index + 1];
    if (next && !next.startsWith("--")) { output[key] = next; index += 1; }
    else output[key] = true;
  }
  return output;
}

const args = parseArgs(process.argv.slice(2));
if (!args["source-data"] || !args["output-dir"]) {
  throw new Error("Required: --source-data <validated-source-data.json> --output-dir <run-dir>");
}
const cli = args.cli || DEFAULT_CLI;
const workbookUrl = args.url || DEFAULT_URL;
const sourcePath = path.resolve(args["source-data"]);
const outputDir = path.resolve(args["output-dir"]);

function dateKey(value) {
  const [year, month, day] = String(value).trim().replaceAll("-", "/").split("/");
  if (!year || !month || !day) throw new Error(`Invalid date value: ${value}`);
  return `${Number(year)}/${Number(month)}/${Number(day)}`;
}

function runCli(parameters, stdin) {
  return new Promise((resolve, reject) => {
    const child = spawn(cli, parameters, {
      env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => {
      let payload;
      try { payload = JSON.parse(stdout); } catch { payload = null; }
      if (code !== 0 || !payload?.ok) {
        reject(new Error(`lark-cli failed code=${code}: ${stderr || stdout}`));
        return;
      }
      resolve(payload);
    });
    child.stdin.end(stdin ?? "");
  });
}

function csvRows(annotatedCsv) {
  const result = [];
  for (const line of String(annotatedCsv || "").split(/\r?\n/)) {
    const match = line.match(/^\[row=(\d+)\]\s?(.*)$/);
    if (!match) continue;
    result.push({ row: Number(match[1]), values: parseCsvLine(match[2]) });
  }
  return result;
}

function parseCsvLine(line) {
  const output = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"') {
      if (quoted && line[index + 1] === '"') { current += '"'; index += 1; }
      else quoted = !quoted;
    } else if (character === "," && !quoted) {
      output.push(current);
      current = "";
    } else current += character;
  }
  output.push(current);
  return output;
}

function normalized(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" || typeof value === "boolean") return value;
  const text = String(value).trim();
  const percentage = text.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/);
  if (percentage) return Number(percentage[1]) / 100;
  if (/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(text)) return Number(text);
  return text;
}

function sameValue(first, second) {
  const left = normalized(first);
  const right = normalized(second);
  if (typeof left === "number" && typeof right === "number") {
    const tolerance = Math.max(Math.abs(left), Math.abs(right)) >= 1 ? 0.051 : 0.000051;
    return Math.abs(left - right) <= tolerance;
  }
  return left === right;
}

function sha(value) {
  return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

async function revision() {
  const result = await runCli(["sheets", "+revision-get", "--as", "user", "--url", workbookUrl]);
  return result.data.revision;
}

async function readKeyRows(kind) {
  const spec = SHEETS[kind];
  const [startColumn, endColumn = spec.readColumns] = spec.readColumns.split(":");
  const result = await runCli([
    "sheets", "+csv-get", "--as", "user", "--url", workbookUrl,
    "--sheet-id", spec.id, "--range", `${startColumn}1:${endColumn}${spec.maxRow}`,
    "--max-chars", "800000",
  ]);
  if (result.data.has_more) throw new Error(`${kind} key read was truncated`);
  return { receipt: { actual_range: result.data.actual_range, revision: result.data.revision, row_count: result.data.row_count }, rows: csvRows(result.data.annotated_csv) };
}

async function readValueRows(kind, plan) {
  const spec = SHEETS[kind];
  const startRow = plan.positional_start_row ?? Math.min(...plan.writes.map((item) => Number(item.range.match(/\d+/)[0])));
  const endRow = startRow + plan.mapped_count - 1;
  const result = await runCli([
    "sheets", "+csv-get", "--as", "user", "--url", workbookUrl,
    "--sheet-id", spec.id, "--range", `A${startRow}:${spec.writeEnd}${endRow}`,
    "--max-chars", "800000",
  ]);
  if (result.data.has_more) throw new Error(`${kind} readback was truncated`);
  return { receipt: { actual_range: result.data.actual_range, revision: result.data.revision, row_count: result.data.row_count }, rows: csvRows(result.data.annotated_csv) };
}

function sourceMap(kind, rows) {
  const spec = SHEETS[kind];
  const map = new Map();
  for (const row of rows) {
    const key = spec.key(row);
    if (map.has(key)) throw new Error(`${kind} source duplicate key ${key}`);
    map.set(key, row);
  }
  return map;
}

function targetMap(kind, rows, allowedKeys) {
  const spec = SHEETS[kind];
  const map = new Map();
  for (const row of rows) {
    if (!/^\d{4}[/-]\d{1,2}[/-]\d{1,2}$/.test(String(row.values[0] || "").trim())) continue;
    const key = spec.key(row.values);
    if (!allowedKeys.has(key)) continue;
    if (map.has(key)) throw new Error(`${kind} Lark duplicate key ${key}`);
    map.set(key, row.row);
  }
  return map;
}

function secondaryKey(kind, values) {
  if (kind === "detail") return `${String(values[1])}|${String(values[2])}`;
  if (kind === "game" || kind === "active") return String(values[1]);
  return "";
}

function excelSerial(date) {
  const [year, month, day] = dateKey(date).split("/").map(Number);
  return (Date.UTC(year, month - 1, day) - Date.UTC(1899, 11, 30)) / 86400000;
}

function rangeFor(spec, startRow, endRow) {
  return `${spec.writeStart}${startRow}:${spec.writeEnd}${endRow}`;
}

function fullRangeFor(spec, startRow, endRow) {
  return `A${startRow}:${spec.writeEnd}${endRow}`;
}

function toCell(value) {
  return value === null || value === undefined ? { value: "" } : { value };
}

function planWrites(kind, sourceRows, targetRows) {
  const spec = SHEETS[kind];
  const source = sourceMap(kind, sourceRows);
  const target = targetMap(kind, targetRows, new Set(source.keys()));
  if (source.size !== sourceRows.length) throw new Error(`${kind} unexpected source key count`);
  const mapped = [];
  const missing = [];
  const usedRows = new Set();
  for (const [key, sourceRow] of source) {
    const targetRow = target.get(key);
    if (!targetRow) { missing.push({ key, sourceRow }); continue; }
    usedRows.add(targetRow);
    mapped.push({ row: targetRow, key, values: sourceRow.slice(1).map(toCell), date_fix: null });
  }
  const validTargets = targetRows.filter((row) => /^\d{4}[/-]\d{1,2}[/-]\d{1,2}$/.test(String(row.values[0] || "").trim()));
  const mappedRows = mapped.map((item) => item.row);
  const lowerBound = Math.max(1, Math.min(...mappedRows) - 30);
  const upperBound = Math.max(...mappedRows) + 30;
  const unresolved = [];
  for (const item of missing) {
    const candidates = validTargets.filter((row) => row.row >= lowerBound && row.row <= upperBound && !usedRows.has(row.row) && secondaryKey(kind, row.values) === secondaryKey(kind, item.sourceRow));
    if (candidates.length !== 1) { unresolved.push(item.key); continue; }
    const targetRow = candidates[0].row;
    usedRows.add(targetRow);
    mapped.push({ row: targetRow, key: item.key, values: item.sourceRow.slice(1).map(toCell), date_fix: item.sourceRow[0] });
  }
  if (unresolved.length) throw new Error(`${kind} target Lark rows missing (${unresolved.length}): ${unresolved.slice(0, 12).join(", ")}`);
  mapped.sort((left, right) => left.row - right.row);
  const groups = [];
  for (const item of mapped) {
    const current = groups.at(-1);
    if (!current || item.row !== current.endRow + 1 || current.items.length >= 50) {
      groups.push({ startRow: item.row, endRow: item.row, items: [item] });
    } else {
      current.endRow = item.row;
      current.items.push(item);
    }
  }
  return {
    mapped_count: mapped.length,
    source_count: source.size,
    target_match_count: mapped.length,
    date_fixes: mapped.filter((item) => item.date_fix).map((item) => ({ sheet_id: spec.id, range: `A${item.row}`, cells: [[{ value: excelSerial(item.date_fix) }]], key: item.key })),
    writes: groups.map((group) => ({ sheet_id: spec.id, range: rangeFor(spec, group.startRow, group.endRow), cells: group.items.map((item) => item.values), keys: group.items.map((item) => item.key) })),
  };
}

function planPositionalWrites(kind, sourceRows) {
  const spec = SHEETS[kind];
  const start = POSITIONAL_STARTS[kind];
  const expected = { summary: 3, detail: 450, game: 90, active: 12 }[kind];
  if (sourceRows.length !== expected) throw new Error(`${kind} source rows ${sourceRows.length}; expected ${expected}`);
  const expectedDates = ["2026/8/21", "2026/8/22", "2026/8/23"];
  const expectedPerDate = expected / 3;
  for (let index = 0; index < sourceRows.length; index += 1) {
    const expectedDate = expectedDates[Math.floor(index / expectedPerDate)];
    if (dateKey(sourceRows[index][0]) !== dateKey(expectedDate)) throw new Error(`${kind} source order mismatch at ${index + 1}`);
  }
  const writes = [];
  for (let offset = 0; offset < sourceRows.length; offset += 50) {
    const rows = sourceRows.slice(offset, offset + 50);
    const startRow = start + offset;
    const endRow = startRow + rows.length - 1;
    writes.push({
      sheet_id: spec.id,
      range: fullRangeFor(spec, startRow, endRow),
      cells: rows.map((row) => [toCell(excelSerial(row[0])), ...row.slice(1).map(toCell)]),
      keys: rows.map((row) => spec.key(row)),
    });
  }
  return { mapped_count: sourceRows.length, source_count: sourceRows.length, target_match_count: sourceRows.length, date_fixes: [], writes, positional_start_row: start };
}

async function executeWrites(kind, plan) {
  const receipts = [];
  for (const group of plan.writes) {
    const payload = [{ sheet_id: group.sheet_id, range: group.range, cells: group.cells }];
    const result = await runCli(["sheets", "+cells-set", "--as", "user", "--url", workbookUrl, "--writes", "-"], JSON.stringify(payload));
    receipts.push({ range: group.range, revision: result.data?.revision, updated_cells_count: result.data?.updated_cells_count });
  }
  for (let index = 0; index < plan.date_fixes.length; index += 50) {
    const payload = plan.date_fixes.slice(index, index + 50).map(({ sheet_id, range, cells }) => ({ sheet_id, range, cells }));
    const result = await runCli(["sheets", "+cells-set", "--as", "user", "--url", workbookUrl, "--writes", "-"], JSON.stringify(payload));
    receipts.push({ range: payload.map((item) => item.range).join(","), revision: result.data?.revision, updated_cells_count: result.data?.updated_cells_count, date_fix: true });
  }
  return receipts;
}

async function main() {
  await fs.mkdir(outputDir, { recursive: true });
  const source = JSON.parse(await fs.readFile(sourcePath, "utf8"));
  const expected = { summary: 3, detail: 450, game: 90, active: 12 };
  for (const [kind, count] of Object.entries(expected)) {
    if ((source.target_rows?.[kind] || []).length !== count) throw new Error(`${kind} source row count mismatch`);
  }
  const revisionBefore = await revision();
  const keyReads = {};
  for (const kind of Object.keys(SHEETS)) keyReads[kind] = await readKeyRows(kind);
  const plans = {};
  for (const kind of Object.keys(SHEETS)) {
    plans[kind] = args.mode === "positional" ? planPositionalWrites(kind, source.target_rows[kind]) : planWrites(kind, source.target_rows[kind], keyReads[kind].rows);
  }
  for (const [kind, plan] of Object.entries(plans)) {
    if (plan.mapped_count !== expected[kind] || plan.target_match_count !== expected[kind]) throw new Error(`${kind} preflight mapping incomplete`);
  }
  await fs.writeFile(path.join(outputDir, "lark-write-plan.json"), JSON.stringify({ revision_before: revisionBefore, source: sourcePath, plans }, null, 2) + "\n");
  if (args["dry-run"]) {
    process.stdout.write(JSON.stringify({ status: "dry_run", revision_before: revisionBefore, expected, planned_ranges: Object.fromEntries(Object.entries(plans).map(([kind, plan]) => [kind, plan.writes.map((item) => item.range)])) }) + "\n");
    return;
  }
  const writeReceipts = {};
  for (const kind of Object.keys(SHEETS)) writeReceipts[kind] = await executeWrites(kind, plans[kind]);
  const revisionAfter = await revision();
  const readback = {};
  for (const kind of Object.keys(SHEETS)) {
    const now = await readValueRows(kind, plans[kind]);
    const expectedRows = source.target_rows[kind];
    const actualRows = now.rows.filter((row) => /^\d{4}[/-]\d{1,2}[/-]\d{1,2}$/.test(String(row.values[0] || "").trim()));
    const mismatches = [];
    if (actualRows.length !== expectedRows.length) mismatches.push({ reason: "row_count", expected: expectedRows.length, actual: actualRows.length });
    for (let index = 0; index < Math.min(expectedRows.length, actualRows.length); index += 1) {
      const expectedRow = expectedRows[index];
      const actual = actualRows[index];
      const datesMatch = dateKey(expectedRow[0]) === dateKey(actual.values[0]);
      if (!datesMatch || expectedRow.length !== actual.values.length || expectedRow.some((value, fieldIndex) => fieldIndex > 0 && !sameValue(value, actual.values[fieldIndex]))) {
        mismatches.push({ row: actual.row, key: SHEETS[kind].key(expectedRow), reason: datesMatch ? "values" : "date" });
      }
    }
    readback[kind] = { expected: expectedRows.length, actual_matches: expectedRows.length - mismatches.length, mismatches: mismatches.slice(0, 20), receipt: now.receipt, display_precision_tolerance: "0.051 for values >=1; 0.000051 for rates" };
    if (mismatches.length) throw new Error(`${kind} readback mismatch count=${mismatches.length}`);
  }
  const receipt = { status: "ok", updated_window: source.window, revision_before: revisionBefore, revision_after: revisionAfter, source_sha256: sha(source.target_rows), write_receipts: writeReceipts, readback };
  await fs.writeFile(path.join(outputDir, "lark-update-receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
  process.stdout.write(JSON.stringify(receipt) + "\n");
}

await main();

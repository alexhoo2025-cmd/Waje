#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const CLI = process.env.LARK_CLI_BIN || "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const ROOT = process.cwd();

const SOURCE_FIELDS = {
  summary: [
    "总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比",
    "总基础预期回报比", "总完全预期回报比", "总人数",
  ],
  detail: [
    "生命周期", "游戏类型", "差额", "预期回报比", "盈利比万分比", "实际回报比万分比",
    "基础预期盈利", "基础实际盈利", "基础下注额", "基础真实回报比", "总破产保护金额",
    "总个人盈利控制金额", "完全预期盈利", "完全实际盈利", "完全下注额", "完全下注额占比",
    "完全真实回报比", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改",
  ],
  game: [
    "游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比",
    "基础回报比差距", "总破产保护金额", "总个人盈利控制金额", "破产保护/下注", "个人盈利/下注",
    "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比",
    "完全回报比差距", "完全下注额占比",
  ],
  active: [
    "生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利",
    "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比",
    "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利",
    "人均实际盈利", "人数", "当日充值总金额", "平均流充比", "营收", "TX总金额",
    "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数", "人均绝对破产次数",
  ],
};

const TARGET_HEADERS = {
  summary: ["日期", ...SOURCE_FIELDS.summary, "当日完全盈利", "人均盈利"],
  detail: ["日期", ...SOURCE_FIELDS.detail.slice(0, 17)],
  game: ["日期", ...SOURCE_FIELDS.game],
  active: ["日期", ...SOURCE_FIELDS.active],
};

const SEMANTIC_SIGNATURES = {
  summary: ["日期", "总基础下注额", "总完全下注额", "总人数", "当日完全盈利", "人均盈利"],
  detail: ["日期", "生命周期", "游戏类型", "基础下注额", "完全下注额", "完全真实回报比"],
  game: ["日期", "游戏", "基础下注额", "完全下注额", "完全真实回报比"],
  active: ["日期", "生命周期", "基础下注额", "人数", "完全下注额", "人均实际盈利"],
};

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) { out[key] = next; i += 1; }
    else out[key] = true;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const token = args.token || "ZBD4wPBsricBWMktFqilAGxlgte";
const sourcePath = path.resolve(args["source-data"] || "data/outputs/lifecycle_joint/2026-08-28-30d/source-data.json");
  const sourceAuditPath = path.resolve(args["source-audit"] || "data/outputs/lifecycle_joint/2026-08-28-30d/source-audit/raw-audit.json");
const outputDir = path.resolve(args["output-dir"] || "data/outputs/lifecycle_joint/2026-08-28-30d");
const backupDir = outputDir;
const startDate = args["start-date"] || "2026-07-29";
const endDate = args["end-date"] || "2026-08-27";
const execute = Boolean(args.execute || args["verify-only"]);
const maxWriteRows = 50;

function normHeader(value) { return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim(); }

function parseDate(value) {
  const text = String(value ?? "").trim().replaceAll("-", "/");
  const match = text.match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/);
  if (!match) return null;
  return `${match[1]}-${String(Number(match[2])).padStart(2, "0")}-${String(Number(match[3])).padStart(2, "0")}`;
}

function excelSerial(iso) {
  const [year, month, day] = iso.split("-").map(Number);
  return (Date.UTC(year, month - 1, day) - Date.UTC(1899, 11, 30)) / 86400000;
}

function dateRange(start, end) {
  const out = [];
  for (let ms = Date.parse(`${start}T00:00:00Z`); ms <= Date.parse(`${end}T00:00:00Z`); ms += 86400000) out.push(new Date(ms).toISOString().slice(0, 10));
  return out;
}

function columnLetter(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

function parseCsvRecord(record) {
  const values = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < record.length; i += 1) {
    const ch = record[i];
    if (ch === '"') {
      if (quoted && record[i + 1] === '"') { current += '"'; i += 1; }
      else quoted = !quoted;
    } else if (ch === "," && !quoted) {
      values.push(current);
      current = "";
    } else current += ch;
  }
  values.push(current);
  return values;
}

function parseAnnotatedCsv(text) {
  const rows = [];
  let position = 0;
  while (position < text.length) {
    while (position < text.length && (text[position] === "\n" || text[position] === "\r")) position += 1;
    const prefix = text.slice(position).match(/^\[row=(\d+)\]\s?/);
    if (!prefix) break;
    const rowNumber = Number(prefix[1]);
    const start = position + prefix[0].length;
    let cursor = start;
    let quoted = false;
    for (; cursor < text.length; cursor += 1) {
      const ch = text[cursor];
      if (ch === '"') {
        if (quoted && text[cursor + 1] === '"') cursor += 1;
        else quoted = !quoted;
      } else if (ch === "\n" && !quoted) break;
    }
    const record = text.slice(start, cursor).replace(/\r$/, "");
    rows.push({ row: rowNumber, values: parseCsvRecord(record) });
    position = cursor + 1;
  }
  return rows;
}

function normalizeValue(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" || typeof value === "boolean") return value;
  let text = String(value).trim().replace(/\s+/g, " ");
  const percent = text.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/);
  if (percent) return Number(percent[1]) / 100;
  const numeric = text.replaceAll(",", "");
  if (/^-?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$/.test(numeric)) return Number(numeric);
  return text;
}

function sameValue(left, right) {
  const a = normalizeValue(left);
  const b = normalizeValue(right);
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= Math.max(1e-8, Math.max(Math.abs(a), Math.abs(b)) * 1e-9);
  return a === b;
}

function canonical(value) { return JSON.stringify(normalizeValue(value)); }

function toCell(value) { return value === null || value === undefined ? { value: "" } : { value }; }

function readJson(file) { return fs.readFile(file, "utf8").then((raw) => JSON.parse(raw)); }

async function writeJson(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function runCli(argv, stdin = "") {
  return new Promise((resolve, reject) => {
    const child = spawn(CLI, argv, {
      cwd: ROOT,
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
      if (code !== 0 || !payload?.ok) reject(new Error(`lark-cli failed code=${code}: ${stderr || stdout}`));
      else resolve(payload);
    });
    child.stdin.end(stdin);
  });
}

async function getRevision() {
  const result = await runCli(["sheets", "+revision-get", "--spreadsheet-token", token, "--as", "user"]);
  return result.data?.revision;
}

async function getWorkbookInfo() {
  return runCli(["sheets", "+workbook-info", "--spreadsheet-token", token, "--as", "user"]);
}

async function getCsv(sheetId) {
  return runCli(["sheets", "+csv-get", "--spreadsheet-token", token, "--sheet-id", sheetId, "--max-chars", "20000000", "--as", "user"]);
}

async function getCells(sheetId, range) {
  return runCli(["sheets", "+cells-get", "--spreadsheet-token", token, "--sheet-id", sheetId, "--range", range, "--include", "value,formula,style", "--as", "user"]);
}

function targetSignatureMatches(headers, semantic) {
  const normalized = new Set(headers.map(normHeader));
  return SEMANTIC_SIGNATURES[semantic].every((header) => normalized.has(normHeader(header)));
}

function selectSemanticSheets(workbook, csvById) {
  const candidates = [];
  for (const sheet of workbook.data?.sheets || []) {
    if (sheet.resource_type !== "sheet") continue;
    const csv = csvById[sheet.sheet_id];
    const rows = parseAnnotatedCsv(csv.data.annotated_csv);
    const headers = rows[0]?.values || [];
    candidates.push({ sheet_id: sheet.sheet_id, title: sheet.sheet_name || sheet.title || sheet.sheet_id, row_count: sheet.row_count, column_count: sheet.column_count, headers, rows, csv });
  }
  const mapping = {};
  const used = new Set();
  const failures = [];
  for (const semantic of Object.keys(SOURCE_FIELDS)) {
    const matches = candidates.filter((item) => targetSignatureMatches(item.headers, semantic));
    if (matches.length !== 1) { failures.push(`${semantic}: semantic sheet candidate count=${matches.length}`); continue; }
    const selected = matches[0];
    if (used.has(selected.sheet_id)) { failures.push(`${semantic}: sheet reused ${selected.sheet_id}`); continue; }
    used.add(selected.sheet_id);
    mapping[semantic] = selected;
  }
  if (failures.length) throw new Error(`Sheet semantic mapping failed: ${failures.join("; ")}`);
  return mapping;
}

function mapTargetHeaders(item, semantic) {
  const byHeader = new Map();
  item.headers.forEach((header, index) => {
    const key = normHeader(header);
    if (!key) return;
    if (!byHeader.has(key)) byHeader.set(key, []);
    byHeader.get(key).push(index);
  });
  const selectedFields = semantic === "summary"
    ? SOURCE_FIELDS.summary
    : semantic === "detail"
      ? SOURCE_FIELDS.detail.slice(0, 17)
      : SOURCE_FIELDS[semantic];
  const fieldMaps = [];
  const failures = [];
  for (let sourceIndex = 0; sourceIndex < selectedFields.length; sourceIndex += 1) {
    const key = normHeader(selectedFields[sourceIndex]);
    const matches = byHeader.get(key) || [];
    if (matches.length !== 1) failures.push(`${semantic}.${selectedFields[sourceIndex]} target matches=${matches.length}`);
    else fieldMaps.push({ sourceIndex, source_field: selectedFields[sourceIndex], targetIndex: matches[0] });
  }
  if (failures.length) throw new Error(`Header mapping failed: ${failures.join("; ")}`);
  const dateMatches = byHeader.get(normHeader("日期")) || [];
  if (dateMatches.length !== 1) throw new Error(`${semantic}.日期 target matches=${dateMatches.length}`);
  const formulaFields = semantic === "summary" ? ["当日完全盈利", "人均盈利"] : [];
  const formulas = formulaFields.map((field) => {
    const matches = byHeader.get(normHeader(field)) || [];
    if (matches.length !== 1) throw new Error(`${semantic}.${field} target matches=${matches.length}`);
    return { field, targetIndex: matches[0] };
  });
  return { dateIndex: dateMatches[0], fieldMaps, formulas, targetHeaders: item.headers };
}

function sourceValues(semantic, rawRow) {
  if (semantic === "summary") return rawRow.slice(1, 8);
  if (semantic === "detail") return rawRow.slice(1, 21);
  if (semantic === "game") return rawRow.slice(1, 19);
  if (semantic === "active") return [...rawRow.slice(1, 20), ...rawRow.slice(22)];
  throw new Error(`unknown semantic ${semantic}`);
}

function keyFor(semantic, row) {
  const date = parseDate(row[0]);
  if (!date) return null;
  if (semantic === "summary") return date;
  if (semantic === "detail") return `${date}|${String(row[1])}|${String(row[2])}`;
  if (semantic === "game") return `${date}|${String(row[1])}`;
  if (semantic === "active") return `${date}|${String(row[1])}`;
  return null;
}

function buildTargetMap(item, semantic) {
  const map = new Map();
  const dataRows = [];
  for (const record of item.rows.slice(1)) {
    const key = keyFor(semantic, record.values);
    if (!key) continue;
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(record.row);
    dataRows.push({ key, rowNumber: record.row, values: record.values });
  }
  if (!dataRows.length) throw new Error(`${semantic}: no existing date rows to anchor append`);
  const duplicateKeys = [...map.entries()]
    .filter(([, rows]) => rows.length > 1)
    .map(([key, rows]) => ({ key, rows }));
  return { map, dataRows, duplicateKeys, maxDataRow: Math.max(...dataRows.map((item) => item.rowNumber)) };
}

function sourceRowsFor(source, semantic, dates) {
  const rows = source.target_rows?.[semantic] || [];
  const allowed = new Set(dates);
  const filtered = rows.filter((row) => allowed.has(parseDate(row[0])));
  if (filtered.length !== rows.length) throw new Error(`${semantic}: source rows contain dates outside ${startDate}..${endDate}`);
  return filtered;
}

function segmentFields(fieldMaps) {
  const segments = [];
  for (const mapping of fieldMaps) {
    const previous = segments.at(-1);
    if (!previous || mapping.targetIndex !== previous.at(-1).targetIndex + 1) segments.push([mapping]);
    else previous.push(mapping);
  }
  return segments;
}

function contiguousGroups(items) {
  const groups = [];
  for (const item of items) {
    const previous = groups.at(-1);
    if (!previous || item.rowNumber !== previous.at(-1).rowNumber + 1 || previous.length >= maxWriteRows) groups.push([item]);
    else previous.push(item);
  }
  return groups;
}

function makeRange(startColumn, endColumn, startRow, endRow) {
  return `${columnLetter(startColumn)}${startRow}:${columnLetter(endColumn)}${endRow}`;
}

function makeValueOperations(semantic, item, planItems, fieldMaps) {
  const operations = [];
  for (const segment of segmentFields(fieldMaps)) {
    for (const group of contiguousGroups(planItems)) {
      operations.push({
        semantic,
        purpose: "source_metrics",
        sheet_id: item.sheet_id,
        range: makeRange(segment[0].targetIndex, segment.at(-1).targetIndex, group[0].rowNumber, group.at(-1).rowNumber),
        cells: group.map((entry) => segment.map((mapping) => toCell(entry.sourceValues[mapping.sourceIndex]))),
      });
    }
  }
  return operations;
}

function makeDateOperations(semantic, item, planItems, dateIndex) {
  const newItems = planItems.filter((entry) => entry.isNew);
  return contiguousGroups(newItems).map((group) => ({
    semantic,
    purpose: "new_row_date",
    sheet_id: item.sheet_id,
    range: makeRange(dateIndex, dateIndex, group[0].rowNumber, group.at(-1).rowNumber),
    cells: group.map((entry) => [toCell(excelSerial(entry.date))]),
  }));
}

function makeFormulaOperations(semantic, item, planItems, headerMap) {
  if (semantic !== "summary") return [];
  const newItems = planItems.filter((entry) => entry.isNew);
  if (!newItems.length) return [];
  const fullBet = headerMap.fieldMaps.find((m) => m.source_field === "总完全下注额")?.targetIndex;
  const fullActual = headerMap.fieldMaps.find((m) => m.source_field === "总完全真实回报比")?.targetIndex;
  const people = headerMap.fieldMaps.find((m) => m.source_field === "总人数")?.targetIndex;
  const profit = headerMap.formulas.find((m) => m.field === "当日完全盈利")?.targetIndex;
  const perPerson = headerMap.formulas.find((m) => m.field === "人均盈利")?.targetIndex;
  if ([fullBet, fullActual, people, profit, perPerson].some((value) => value === undefined)) throw new Error("summary formula dependencies are not mapped");
  const formulaItems = newItems.map((entry) => ({ ...entry, formulaValues: [
    { targetIndex: profit, formula: `=${columnLetter(fullBet)}${entry.rowNumber}*(1-${columnLetter(fullActual)}${entry.rowNumber})` },
    { targetIndex: perPerson, formula: `=${columnLetter(profit)}${entry.rowNumber}/${columnLetter(people)}${entry.rowNumber}` },
  ] }));
  const groups = contiguousGroups(formulaItems);
  return groups.map((group) => ({
    semantic,
    purpose: "derived_summary_formulas",
    sheet_id: item.sheet_id,
    range: makeRange(profit, perPerson, group[0].rowNumber, group.at(-1).rowNumber),
    cells: group.map((entry) => entry.formulaValues.sort((a, b) => a.targetIndex - b.targetIndex).map((value) => ({ formula: value.formula }))),
  }));
}

function hashRows(rows) {
  return crypto.createHash("sha256").update(JSON.stringify(rows.map((item) => [item.rowNumber, item.values.map(normalizeValue)]))).digest("hex");
}

function preparePlans(source, mapping, dates) {
  const plans = {};
  for (const semantic of Object.keys(SOURCE_FIELDS)) {
    const item = mapping[semantic];
    const headerMap = mapTargetHeaders(item, semantic);
    const target = buildTargetMap(item, semantic);
    const rawRows = sourceRowsFor(source, semantic, dates);
    const sourceKeySet = new Set();
    const sourceEntries = [];
    for (const rawRow of rawRows) {
      const key = keyFor(semantic, rawRow);
      if (sourceKeySet.has(key)) throw new Error(`${semantic}: duplicate source key ${key}`);
      sourceKeySet.add(key);
      sourceEntries.push({ key, date: parseDate(rawRow[0]), rawRow, sourceValues: sourceValues(semantic, rawRow), existingRows: target.map.get(key) || [] });
    }
    const missing = sourceEntries.filter((entry) => entry.existingRows.length === 0);
    const missingByAnchor = new Map();
    for (const entry of missing) {
      const laterRows = target.dataRows
        .filter((row) => parseDate(row.values[0]) > entry.date)
        .map((row) => row.rowNumber);
      const anchor = laterRows.length ? Math.min(...laterRows) : target.maxDataRow + 1;
      if (!missingByAnchor.has(anchor)) missingByAnchor.set(anchor, []);
      missingByAnchor.get(anchor).push(entry);
    }
    const insertGroupsAscending = [...missingByAnchor.entries()]
      .sort((left, right) => left[0] - right[0])
      .map(([basePosition, entries]) => ({ basePosition, entries, count: entries.length }));
    let cumulative = 0;
    for (const group of insertGroupsAscending) {
      group.finalPosition = group.basePosition + cumulative;
      cumulative += group.count;
    }
    const shiftForOriginalRow = (rowNumber) => insertGroupsAscending
      .filter((group) => group.basePosition <= rowNumber)
      .reduce((sum, group) => sum + group.count, 0);
    const planItems = [];
    for (const entry of sourceEntries) {
      if (entry.existingRows.length) {
        for (const beforeRow of entry.existingRows) {
          planItems.push({ ...entry, before_row_number: beforeRow, rowNumber: beforeRow + shiftForOriginalRow(beforeRow), isNew: false });
        }
      } else {
        const group = insertGroupsAscending.find((candidate) => candidate.entries.includes(entry));
        const offset = group.entries.indexOf(entry);
        planItems.push({ ...entry, before_row_number: null, rowNumber: group.finalPosition + offset, isNew: true });
      }
    }
    planItems.sort((left, right) => left.rowNumber - right.rowNumber);
    const newDates = [...new Set(missing.map((entry) => entry.date))];
    const existingDates = new Set(target.dataRows.map((row) => parseDate(row.values[0])));
    const expectedDateSet = new Set(dates);
    const sourceDates = new Set(planItems.map((entry) => entry.date));
    if (sourceDates.size !== expectedDateSet.size || [...expectedDateSet].some((date) => !sourceDates.has(date))) throw new Error(`${semantic}: source date set incomplete`);
    const operations = [
      ...makeDateOperations(semantic, item, planItems, headerMap.dateIndex),
      ...makeValueOperations(semantic, item, planItems, headerMap.fieldMaps),
      ...makeFormulaOperations(semantic, item, planItems, headerMap),
    ];
    const lastTargetColumn = Math.max(item.headers.length - 1, ...headerMap.fieldMaps.map((m) => m.targetIndex), headerMap.dateIndex, ...headerMap.formulas.map((m) => m.targetIndex));
    plans[semantic] = {
      semantic,
      sheet_id: item.sheet_id,
      sheet_title: item.title,
      current_row_count: item.row_count,
      current_column_count: item.column_count,
      current_max_data_row: target.maxDataRow,
      header_map: headerMap,
      target_rows_before: target.dataRows,
      plan_items: planItems,
      existing_source_row_count: sourceEntries.filter((entry) => entry.existingRows.length).length,
      new_source_row_count: missing.length,
      new_date_set: newDates,
      preexisting_duplicate_keys: target.duplicateKeys,
      expected_dates: dates,
      insertions: insertGroupsAscending.map((group) => ({ position: group.finalPosition, base_position: group.basePosition, count: group.count, inherit_style: "before", dates: [...new Set(group.entries.map((entry) => entry.date))] })),
      last_target_column: lastTargetColumn,
      operations,
      source_date_count: sourceDates.size,
      existing_date_count_before: existingDates.size,
    };
  }
  return plans;
}

function publicMapping(plans) {
  return Object.fromEntries(Object.entries(plans).map(([semantic, plan]) => [semantic, {
    sheet_id: plan.sheet_id,
    sheet_title: plan.sheet_title,
    current_row_count: plan.current_row_count,
    current_column_count: plan.current_column_count,
    current_max_data_row: plan.current_max_data_row,
    expected_dates: plan.expected_dates,
    new_date_set: plan.new_date_set,
    header_map: plan.header_map,
    insertions: plan.insertions,
    preexisting_duplicate_keys: plan.preexisting_duplicate_keys,
    existing_source_row_count: plan.existing_source_row_count,
    new_source_row_count: plan.new_source_row_count,
    operation_count: plan.operations.length,
    planned_target_rows: plan.plan_items.length,
    operation_ranges: plan.operations.map((operation) => ({ purpose: operation.purpose, range: operation.range })),
  }]));
}

async function readCurrentWorkbook() {
  const revision = await getRevision();
  const workbook = await getWorkbookInfo();
  const csvById = {};
  for (const sheet of workbook.data?.sheets || []) {
    if (sheet.resource_type !== "sheet") continue;
    csvById[sheet.sheet_id] = await getCsv(sheet.sheet_id);
  }
  const mapping = selectSemanticSheets(workbook, csvById);
  for (const [semantic, item] of Object.entries(mapping)) await writeJson(path.join(outputDir, `lark-before-live-${semantic}.json`), item.csv);
  await writeJson(path.join(outputDir, "lark-workbook-info-live-before.json"), workbook);
  await writeJson(path.join(outputDir, "lark-revision-live-before.json"), { revision });
  return { revision, workbook, mapping };
}

function ensureSource(source, audit, dates) {
  const auditStatus = audit.raw_export_audit?.status || audit.quality_status;
  if (auditStatus !== "passed" && auditStatus !== "passed_with_static_entity_anomaly") throw new Error(`source audit status not passed: ${auditStatus}`);
  if (source.window?.start !== startDate || source.window?.end !== endDate) throw new Error(`source window mismatch: ${source.window?.start}..${source.window?.end}`);
  const expected = new Set(dates);
  for (const semantic of Object.keys(SOURCE_FIELDS)) {
    const rows = source.target_rows?.[semantic] || [];
    const actualDates = new Set(rows.map((row) => parseDate(row[0])));
    if (actualDates.size !== expected.size || [...expected].some((date) => !actualDates.has(date))) throw new Error(`${semantic}: source target rows do not cover all dates`);
  }
}

async function dryRunInsertions(plans) {
  const receipts = [];
  for (const plan of Object.values(plans)) {
    for (const insertion of [...plan.insertions].sort((left, right) => right.base_position - left.base_position)) {
      const result = await runCli(["sheets", "+dim-insert", "--spreadsheet-token", token, "--sheet-id", plan.sheet_id, "--position", String(insertion.base_position), "--count", String(insertion.count), "--inherit-style", "before", "--dry-run", "--as", "user"]);
      receipts.push({ semantic: plan.semantic, request: { position: insertion.base_position, final_position: insertion.position, count: insertion.count, inherit_style: "before", dates: insertion.dates }, result });
    }
  }
  await writeJson(path.join(outputDir, "dim-insert-dry-run.json"), receipts);
  return receipts;
}

function splitOperations(operations) {
  const batches = [];
  let current = [];
  for (const operation of operations) {
    if (current.length >= 15) { batches.push(current); current = []; }
    current.push(operation);
  }
  if (current.length) batches.push(current);
  return batches;
}

async function executePlan(plans) {
  const insertReceipts = [];
  for (const plan of Object.values(plans)) {
    for (const insertion of [...plan.insertions].sort((left, right) => right.base_position - left.base_position)) {
      const result = await runCli(["sheets", "+dim-insert", "--spreadsheet-token", token, "--sheet-id", plan.sheet_id, "--position", String(insertion.base_position), "--count", String(insertion.count), "--inherit-style", "before", "--as", "user"]);
      insertReceipts.push({ semantic: plan.semantic, request: { position: insertion.base_position, final_position: insertion.position, count: insertion.count, inherit_style: "before", dates: insertion.dates }, result });
    }
  }
  await writeJson(path.join(outputDir, "dim-insert-receipts.json"), insertReceipts);
  const writeReceipts = [];
  for (const plan of Object.values(plans)) {
    const batches = splitOperations(plan.operations);
    for (let index = 0; index < batches.length; index += 1) {
      const batch = batches[index];
      const payload = batch.map(({ semantic, purpose, sheet_id, range, cells }) => ({ sheet_id, range, cells }));
      await writeJson(path.join(outputDir, `write-payload-${plan.semantic}-${String(index + 1).padStart(3, "0")}.json`), payload);
      const result = await runCli(["sheets", "+cells-set", "--spreadsheet-token", token, "--writes", "-", "--as", "user"], JSON.stringify(payload));
      writeReceipts.push({ semantic: plan.semantic, batch: index + 1, operation_count: payload.length, ranges: batch.map((operation) => ({ purpose: operation.purpose, range: operation.range })), result });
    }
  }
  await writeJson(path.join(outputDir, "write-receipts.json"), writeReceipts);
  return { insertReceipts, writeReceipts };
}

async function backupFormulaErrors(plan) {
  const manifest = await readJson(path.join(backupDir, "backup-manifest.json"));
  const sheet = manifest.sheet_snapshots?.find((item) => item.sheet_id === plan.sheet_id);
  const errors = [];
  if (!sheet) return errors;
  for (const chunk of sheet.cells_chunks || []) {
    const payload = await readJson(path.join(ROOT, chunk.data));
    const rows = payload.ranges?.[0]?.cells || [];
    const startRow = Number(chunk.start || 1);
    for (let rowIndex = 0; rowIndex < rows.length; rowIndex += 1) {
      for (let colIndex = 0; colIndex < rows[rowIndex].length; colIndex += 1) {
        const value = rows[rowIndex][colIndex]?.value;
        if (typeof value === "string" && /^#(?:REF!|DIV\/0!|VALUE!|NAME\?|N\/A|NUM!|NULL!)/.test(value.trim())) {
          errors.push(`'${plan.sheet_title}'!${columnLetter(colIndex)}${startRow + rowIndex}`);
        }
      }
    }
  }
  return errors;
}

async function formulaVerifyPlan(plan) {
  const ranges = plan.semantic === "detail"
    ? ["A1:AA5000", "A5001:AA10000", "A10001:AA16000"]
    : [null];
  const results = [];
  const errors = [];
  const baseline = new Set(await backupFormulaErrors(plan));
  for (const range of ranges) {
    try {
      const argv = ["sheets", "+formula-verify", "--spreadsheet-token", token, "--sheet-id", plan.sheet_id, "--as", "user"];
      if (range) argv.push("--range", range);
      const result = await runCli(argv);
      results.push(result);
      const status = result.data?.status;
      if (status === "partial" || result.data?.has_more) errors.push(`${plan.semantic}: formula verify partial for ${range || "current_region"}`);
      if (status === "errors_found") {
        const locations = Object.values(result.data?.error_summary || {}).flatMap((item) => item.locations || []);
        const newLocations = locations.filter((location) => !baseline.has(location));
        if (newLocations.length) errors.push(`${plan.semantic}: new formula errors ${newLocations.join(", ")}`);
      }
    } catch (error) {
      errors.push(`${plan.semantic}: formula verify request failed: ${String(error.message || error)}`);
    }
  }
  const statuses = results.map((result) => result.data?.status);
  const hasPreexisting = results.some((result) => result.data?.status === "errors_found") && baseline.size > 0;
  return { status: errors.length ? "failed" : hasPreexisting ? "success_with_preexisting_errors" : "success", baseline_errors: [...baseline], results, errors };
}

async function verifyPost(source, before, plans) {
  const after = {};
  const failures = [];
  const values = {};
  for (const [semantic, plan] of Object.entries(plans)) {
    try {
      const csv = await getCsv(plan.sheet_id);
      await writeJson(path.join(outputDir, `lark-after-live-${semantic}.json`), csv);
      const parsed = parseAnnotatedCsv(csv.data.annotated_csv);
      after[semantic] = { csv, rows: parsed, headers: parsed[0]?.values || [] };
      const afterMap = new Map();
      for (const record of parsed.slice(1)) {
        const key = keyFor(semantic, record.values);
        if (key) {
          if (!afterMap.has(key)) afterMap.set(key, []);
          afterMap.get(key).push(record);
        }
      }
      const duplicateAfterKeys = [...afterMap.entries()]
        .filter(([, records]) => records.length > 1)
        .map(([key, records]) => ({ key, rows: records.map((record) => record.row) }));
      let compared = 0;
      for (const entry of plan.plan_items) {
        const record = (afterMap.get(entry.key) || []).find((candidate) => candidate.row === entry.rowNumber);
        if (!record) { failures.push(`${semantic}: missing after key ${entry.key}`); continue; }
        for (const mapping of plan.header_map.fieldMaps) {
          if (!sameValue(entry.sourceValues[mapping.sourceIndex], record.values[mapping.targetIndex])) failures.push(`${semantic}:${entry.key}:${mapping.source_field} source/target mismatch`);
        }
        compared += 1;
      }
      values[semantic] = { expected_keys: plan.plan_items.length, compared_keys: compared, after_rows: parsed.length - 1, actual_range: csv.data.actual_range, has_more: csv.data.has_more || false, preexisting_duplicate_keys: plan.preexisting_duplicate_keys, duplicate_after_keys: duplicateAfterKeys };
      if (compared !== plan.plan_items.length) failures.push(`${semantic}: compared key count ${compared} != ${plan.plan_items.length}`);
      if (csv.data.has_more) failures.push(`${semantic}: after read truncated`);

      const beforeRows = before.mapping[semantic].rows.slice(1).filter((record) => parseDate(record.values[0]) && parseDate(record.values[0]) < startDate);
      const afterRows = parsed.slice(1).filter((record) => parseDate(record.values[0]) && parseDate(record.values[0]) < startDate);
      const beforePrefix = beforeRows.map((record) => ({ rowNumber: record.row, values: record.values }));
      const afterPrefix = afterRows.map((record) => ({ rowNumber: record.row, values: record.values }));
      const prefixBeforeHash = hashRows(beforePrefix);
      const prefixAfterHash = hashRows(afterPrefix);
      values[semantic].historical_prefix = { before_hash: prefixBeforeHash, after_hash: prefixAfterHash, unchanged: prefixBeforeHash === prefixAfterHash, before_rows: beforePrefix.length, after_rows: afterPrefix.length };
      if (prefixBeforeHash !== prefixAfterHash) failures.push(`${semantic}: historical prefix changed`);

      const mutable = new Set([plan.header_map.dateIndex, ...plan.header_map.fieldMaps.map((m) => m.targetIndex)]);
      if (semantic === "summary") for (const formula of plan.header_map.formulas) mutable.add(formula.targetIndex);
      const beforeRowMap = new Map();
      for (const record of before.mapping[semantic].rows.slice(1)) {
        beforeRowMap.set(record.row, record);
      }
      for (const entry of plan.plan_items.filter((item) => !item.isNew)) {
        const beforeRecord = beforeRowMap.get(entry.before_row_number);
        const afterRecord = (afterMap.get(entry.key) || []).find((candidate) => candidate.row === entry.rowNumber);
        if (!beforeRecord || !afterRecord) continue;
        for (let index = 0; index < beforeRecord.values.length; index += 1) {
          if (mutable.has(index)) continue;
          if (!sameValue(beforeRecord.values[index], afterRecord.values[index])) failures.push(`${semantic}:${entry.key}:non-target column ${columnLetter(index)} changed`);
        }
      }

      const newItems = plan.plan_items.filter((item) => item.isNew);
      if (newItems.length) {
        const first = newItems[0].rowNumber;
        const last = newItems.at(-1).rowNumber;
        const lastColumn = columnLetter(Math.max(plan.current_column_count - 1, plan.last_target_column));
        const cells = await getCells(plan.sheet_id, `A${first}:${lastColumn}${last}`);
        await writeJson(path.join(outputDir, `cells-after-new-${semantic}.json`), cells);
        const firstCell = cells.data?.ranges?.[0]?.cells?.[0]?.[plan.header_map.dateIndex];
        const lastCell = cells.data?.ranges?.[0]?.cells?.at(-1)?.[plan.header_map.dateIndex];
        const styleFormats = [firstCell, lastCell].map((cell) => cell?.cell_styles?.number_format || null);
        values[semantic].new_rows_style = { first_row: first, last_row: last, date_number_formats: styleFormats, date_format_ok: styleFormats.every((format) => !format || /yyyy\/m\/d/i.test(format)) };
        if (semantic === "summary") {
          const formulaCells = cells.data?.ranges?.[0]?.cells || [];
          const formulaChecks = [];
          for (let rowIndex = 0; rowIndex < formulaCells.length; rowIndex += 1) {
            for (const formula of plan.header_map.formulas) formulaChecks.push({ row: first + rowIndex, field: formula.field, formula: formulaCells[rowIndex]?.[formula.targetIndex]?.formula || null });
          }
          values[semantic].formula_checks = formulaChecks;
          if (formulaChecks.some((item) => !item.formula)) failures.push("summary: new derived formula missing");
        }
      }
    } catch (error) { failures.push(`${semantic}: post-readback failed: ${String(error.message || error)}`); }
  }
  const formulaChecks = {};
  const formulaWarnings = [];
  for (const plan of Object.values(plans)) {
    const result = await formulaVerifyPlan(plan);
    formulaChecks[plan.semantic] = result;
    if (result.status === "success_with_preexisting_errors") formulaWarnings.push(`${plan.semantic}: only preexisting formula errors remain (${result.baseline_errors.join(", ")})`);
    if (result.errors.length) failures.push(...result.errors);
  }
  await writeJson(path.join(outputDir, "formula-verification.json"), formulaChecks);
  const duplicateWarnings = Object.values(values).flatMap((value) => (value.duplicate_after_keys || []).map((item) => `${item.key} rows=${item.rows.join(",")}`));
  const warnings = [...formulaWarnings, ...duplicateWarnings.map((item) => `preexisting duplicate key retained: ${item}`)];
  const readback = { values, formula_checks: formulaChecks, status: failures.length ? "failed" : warnings.length ? "passed_with_warnings" : "passed", failures, warnings };
  await writeJson(path.join(outputDir, "validation-report.json"), readback);
  return { after, readback };
}

async function main() {
  await fs.mkdir(outputDir, { recursive: true });
  const dates = dateRange(startDate, endDate);
  if (dates.length !== 30) throw new Error(`expected 30 dates, got ${dates.length}`);
  const source = await readJson(sourcePath);
  const audit = await readJson(sourceAuditPath);
  ensureSource(source, audit, dates);
  const backup = await readJson(path.join(backupDir, "backup-manifest.json"));
  if (!backup.complete) throw new Error("structured Lark backup is not complete");
  let before;
  const verifyOnly = Boolean(args["verify-only"]);
  if (verifyOnly) {
    const savedWorkbook = await readJson(path.join(outputDir, "lark-workbook-info-live-before.json"));
    const savedPlan = await readJson(path.join(outputDir, "write-plan.json"));
    const savedCsvById = {};
    for (const semantic of Object.keys(SOURCE_FIELDS)) {
      const saved = await readJson(path.join(outputDir, `lark-before-live-${semantic}.json`));
      const sheetId = savedPlan.semantic_mapping?.[semantic]?.sheet_id;
      if (!sheetId) throw new Error(`verify-only missing saved sheet id for ${semantic}`);
      savedCsvById[sheetId] = saved;
    }
    before = { revision: backup.revision, workbook: savedWorkbook, mapping: selectSemanticSheets(savedWorkbook, savedCsvById) };
  } else {
    before = await readCurrentWorkbook();
    if (Number(before.revision) !== Number(backup.revision)) throw new Error(`revision changed after backup: backup=${backup.revision}, live=${before.revision}`);
  }
  const plans = preparePlans(source, before.mapping, dates);
  const mappingReceipt = { schema_version: 1, generated_at: new Date().toISOString(), spreadsheet_token: token, revision_before: before.revision, source: sourcePath, source_audit: sourceAuditPath, range: { start_date: startDate, end_date: endDate, date_count: dates.length, timezone: "Asia/Hong_Kong" }, semantic_sheets: publicMapping(plans) };
  await writeJson(path.join(outputDir, "sheet-alias-mapping.json"), mappingReceipt);
  const planReceipt = { schema_version: 1, generated_at: new Date().toISOString(), status: execute ? "execute_ready" : "dry_run_ready", revision_before: before.revision, source: sourcePath, range: mappingReceipt.range, insertions: Object.fromEntries(Object.entries(plans).map(([semantic, plan]) => [semantic, plan.insertions])), operations: Object.fromEntries(Object.entries(plans).map(([semantic, plan]) => [semantic, plan.operations.map((operation) => ({ purpose: operation.purpose, range: operation.range, rows: operation.cells.length, columns: operation.cells[0]?.length || 0 }))])), semantic_mapping: publicMapping(plans) };
  await writeJson(path.join(outputDir, "write-plan.json"), planReceipt);
  if (!execute) {
    await dryRunInsertions(plans);
    await writeJson(path.join(outputDir, "run-receipt.json"), { status: "dry_run_ready", revision_before: before.revision, output_dir: outputDir, next_step: "rerun with --execute only after reviewing write-plan.json" });
    process.stdout.write(`${JSON.stringify({ status: "dry_run_ready", revision_before: before.revision, mapping: publicMapping(plans) }, null, 2)}\n`);
    return;
  }
  const writes = verifyOnly ? { insertReceipts: [], writeReceipts: [] } : await executePlan(plans);
  const post = await verifyPost(source, before, plans);
  const revisionAfter = await getRevision();
  await writeJson(path.join(outputDir, "lark-revision-live-after.json"), { revision: revisionAfter });
  const status = post.readback.status === "passed" ? "ok" : post.readback.status === "passed_with_warnings" ? "degraded" : "blocked";
  const updatedCellCount = writes.writeReceipts.reduce((sum, item) => sum + (item.result.data?.results || []).reduce((inner, result) => inner + Number(result.data?.updated_cells_count || 0), 0), 0);
  const receipt = { schema_version: 1, status, run_id: `lifecycle-joint-lark-30d-${startDate}-${endDate}`, completed_at: new Date().toISOString(), verification_only: verifyOnly, target: { spreadsheet_token: token, revision_before: before.revision, revision_after: revisionAfter, sheets: Object.fromEntries(Object.entries(plans).map(([semantic, plan]) => [semantic, { sheet_id: plan.sheet_id, sheet_title: plan.sheet_title, updated_source_rows: plan.plan_items.length, inserted_rows: plan.new_source_row_count, updated_date_range: [startDate, endDate], preexisting_duplicate_keys: plan.preexisting_duplicate_keys }])) }, source: { path: sourcePath, audit: sourceAuditPath, dates: dates.length }, backup: { manifest: path.join(outputDir, "backup-manifest.json"), revision: backup.revision, complete: backup.complete }, write_summary: { insertions: writes.insertReceipts.length, write_batches: writes.writeReceipts.length, updated_cells: updatedCellCount }, validation: { path: path.join(outputDir, "validation-report.json"), status: post.readback.status, failures: post.readback.failures, warnings: post.readback.warnings }, artifacts: ["backup-manifest.json", "sheet-alias-mapping.json", "write-plan.json", "write-receipts.json", "run-receipt-write-attempt.json", "lark-after-live-summary.json", "lark-after-live-detail.json", "lark-after-live-game.json", "lark-after-live-active.json", "formula-verification.json", "validation-report.json"] };
  await writeJson(path.join(outputDir, "run-receipt.json"), receipt);
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
  if (status !== "ok") process.exitCode = 1;
}

await main();

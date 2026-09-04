#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const moduleRoot = process.env.CODEX_NODE_MODULES || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { SpreadsheetFile, Workbook } = await import(pathToFileURL(path.join(moduleRoot, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const rawRoot = process.env.RAW_ROOT || "data/raw/lifecycle_joint/2026-08-31";
const dates = (process.env.DATES || "2026-08-24,2026-08-25,2026-08-26,2026-08-27,2026-08-28,2026-08-29,2026-08-30").split(",").map((value) => value.trim()).filter(Boolean);
const kinds = ["summary", "detail", "game", "active"];
const numericColumns = {
  summary: new Set([0, 1, 2, 3, 4, 5, 6, 7, 8]),
  detail: new Set([0, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]),
  game: new Set(Array.from({ length: 17 }, (_v, i) => i + 1)),
  active: new Set(Array.from({ length: 30 }, (_v, i) => i)),
};
function typedValue(value, kind, index) {
  if (value === null || value === undefined || value === "" || value === "-") return null;
  if (!numericColumns[kind].has(index)) return String(value);
  if (typeof value === "number") return value;
  const text = String(value).trim().replace(/,/g, "");
  if (!text || text === "-") return null;
  if (text.endsWith("%")) {
    const n = Number(text.slice(0, -1));
    return Number.isFinite(n) ? n / 100 : text;
  }
  const n = Number(text);
  return Number.isFinite(n) ? n : text;
}
for (const date of dates) {
  const dir = path.join(rawRoot, date);
  const payload = JSON.parse(await fs.readFile(path.join(dir, "tables.json"), "utf8"));
  for (const kind of kinds) {
    const wb = Workbook.create();
    const sheet = wb.worksheets.add(kind);
    const values = [payload.headers[kind], ...payload.rows[kind].map((row) => row.map((value, index) => typedValue(value, kind, index)))];
    sheet.getRangeByIndexes(0, 0, values.length, values[0].length).values = values;
    const blob = await SpreadsheetFile.exportXlsx(wb);
    await blob.save(path.join(dir, `${kind}.xlsx`));
  }
}
console.log(JSON.stringify({ status: "ok", raw_root: rawRoot, dates, files_per_date: 4 }, null, 2));

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
const sheetInfo = {
  "WajeSpecial-facebook": { workbook: "new_user", id: "9cd78d", columns: 44, start: 2, dataFile: "newuser-table.json" },
  "WajeSpecial-googleadwords_int": { workbook: "new_user", id: "xWsChb", columns: 44, start: 2, dataFile: "newuser-table.json" },
  "WajeSpecial-Google商店": { workbook: "new_user", id: "Cfkonh", columns: 44, start: 2, dataFile: "newuser-table.json" },
  "PAWAJEIOS-AppStore商店": { workbook: "new_user", id: "25iiEi", columns: 44, start: 2, dataFile: "newuser-table.json" },
  PAWAJEBETH5: { workbook: "new_user", id: "GrWEoo", columns: 44, start: 2, dataFile: "newuser-table.json" },
  PWA: { workbook: "new_user", id: "gjy6I1", columns: 44, start: 2, dataFile: "newuser-table.json" },
  "wajeH5-fb": { workbook: "new_user", id: "vkV1SD", columns: 44, start: 2, dataFile: "newuser-table.json" },
  "wajeH5ga-googlewords_int": { workbook: "new_user", id: "ef19NP", columns: 44, start: 2, dataFile: "newuser-table.json" },
  原始数据总数: { workbook: "lifecycle", id: "2ea435", columns: 10, start: 2, end: 161, dataFile: "lifecycle-summary-table.json" },
  原始详细奖池: { workbook: "lifecycle", id: "wjhify", columns: 21, start: 2, end: 3050, dataFile: ["lifecycle-detail-1.json", "lifecycle-detail-2.json"] },
  生命周期奖池分游戏汇总: { workbook: "lifecycle", id: "aIE757", columns: 19, start: 2, end: 5036, dataFile: ["lifecycle-game-1.json", "lifecycle-game-2.json"] },
  原始数据活跃周期: { workbook: "lifecycle", id: "TEdtsX", columns: 31, start: 2, end: 894, dataFile: "lifecycle-active-table.json" },
};

const columnIndex = (letters) => {
  let value = 0;
  for (const char of letters) value = value * 26 + char.charCodeAt(0) - 64;
  return value - 1;
};
const letters = (index) => {
  let value = index + 1;
  let output = "";
  while (value > 0) { const remainder = (value - 1) % 26; output = String.fromCharCode(65 + remainder) + output; value = Math.floor((value - 1) / 26); }
  return output;
};
const readJson = async (file) => JSON.parse(await fs.readFile(path.join(runDir, file), "utf8"));
const runWithStdin = (args, input) => new Promise((resolve) => {
  const child = spawn(cli, args, { cwd: root, stdio: ["pipe", "pipe", "pipe"], env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" } });
  let stdout = ""; let stderr = "";
  const timer = setTimeout(() => child.kill("SIGTERM"), 120_000);
  child.stdout.on("data", (chunk) => { stdout += chunk; });
  child.stderr.on("data", (chunk) => { stderr += chunk; });
  child.stdin.on("error", (error) => { stderr += `\nstdin: ${error.message}`; });
  child.on("close", (code) => { clearTimeout(timer); resolve({ code, stdout, stderr }); });
  child.stdin.end(input);
});

const zeroLedger = JSON.parse(await fs.readFile(path.join(runDir, "zero-ledger.json"), "utf8"));
const zeroCells = new Set(zeroLedger.cells.map((item) => `${item.sheet}!${item.cell}`));
const tableCache = new Map();
const getRows = async (dataFile, sheetName) => {
  if (typeof dataFile === "string") {
    const key = `${dataFile}|${sheetName}`;
    if (!tableCache.has(key)) tableCache.set(key, (await readJson(dataFile)).sheets.find((sheet) => sheet.name === sheetName).data);
    return tableCache.get(key);
  }
  const key = dataFile.join("|");
  if (!tableCache.has(key)) {
    const first = (await readJson(dataFile[0])).sheets[0].data;
    const second = (await readJson(dataFile[1])).sheets[0].data;
    tableCache.set(key, [...first, ...second]);
  }
  return tableCache.get(key);
};

const log = { started_at: new Date().toISOString(), sheets: [], errors: [] };
for (const [sheetName, info] of Object.entries(sheetInfo)) {
  const rows = await getRows(info.dataFile, sheetName);
  const end = info.end ?? info.start + rows.length - 1;
  if (end - info.start + 1 !== rows.length) throw new Error(`${sheetName}: expected ${end - info.start + 1} rows, got ${rows.length}`);
  const cells = rows.map((row, rowOffset) => row.map((value, columnOffset) => {
    const cell = `${letters(columnOffset)}${info.start + rowOffset}`;
    return { value: zeroCells.has(`${sheetName}!${cell}`) ? null : value };
  }));
  const range = `A${info.start}:${letters(info.columns - 1)}${end}`;
  const payloadFile = path.join(runDir, `cells-payload-${String(log.sheets.length + 1).padStart(2, "0")}-${encodeURIComponent(sheetName)}.json`);
  await fs.writeFile(payloadFile, JSON.stringify(cells));
  const relativePayloadFile = path.relative(root, payloadFile);
  const args = ["sheets", "+cells-set", "--as", "user", "--url", urls[info.workbook], "--sheet-id", info.id, "--range", range, "--cells", `@${relativePayloadFile}`];
  const result = await runWithStdin(args, "");
  const entry = { sheet: sheetName, workbook: info.workbook, range, rows: rows.length, zero_cells_in_sheet: zeroLedger.cells.filter((item) => item.sheet === sheetName).length, code: result.code, stdout: result.stdout.slice(-3000), stderr: result.stderr.slice(-3000) };
  log.sheets.push(entry);
  if (result.code !== 0) log.errors.push(entry);
  await fs.writeFile(path.join(runDir, "cells-set-progress.json"), JSON.stringify({ completed: log.sheets.length, total: Object.keys(sheetInfo).length, errors: log.errors.length, last: entry }, null, 2));
}
log.finished_at = new Date().toISOString();
log.status = log.errors.length ? "degraded" : "ok";
await fs.writeFile(path.join(runDir, "cells-set-run-log.json"), JSON.stringify(log, null, 2));
console.log(JSON.stringify({ status: log.status, completed: log.sheets.length, errors: log.errors.length }));
if (log.errors.length) process.exitCode = 2;

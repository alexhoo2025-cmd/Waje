import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const moduleRoot = process.env.CODEX_NODE_MODULES || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(moduleRoot, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const JSZip = (await import(pathToFileURL(path.join(moduleRoot, "jszip/lib/index.js")).href)).default;

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
const INPUT_PATH = args.input || "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.7.27-8.10_Joint修正版.xlsx";
const freshOutput = args["fresh-output"] === true;
const startDate = args["start-date"];
const endDate = args["end-date"];
if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate || "") || !/^\d{4}-\d{2}-\d{2}$/.test(endDate || "")) {
  throw new Error("必须提供 --start-date YYYY-MM-DD 和 --end-date YYYY-MM-DD");
}
function dateRange(start, end) {
  const result = [];
  for (let ms = Date.parse(`${start}T00:00:00Z`); ms <= Date.parse(`${end}T00:00:00Z`); ms += 86400000) result.push(new Date(ms).toISOString().slice(0, 10));
  if (!result.length || result.at(-1) !== end) throw new Error(`日期范围无效: ${start}..${end}`);
  return result;
}
const dates = dateRange(startDate, endDate);
const runDate = args["run-date"] || new Date().toISOString().slice(0, 10);
const rawRoot = args["raw-root"] || path.join(process.cwd(), "data/raw/lifecycle_joint", runDate);
const outputDir = args["output-dir"] || path.join(process.cwd(), "outputs", `waje-lifecycle-joint-${runDate}`);
const formatDatePart = (date) => {
  const [y, m, d] = date.split("-");
  return `${y}.${Number(m)}.${Number(d)}`;
};
const endLabel = formatDatePart(endDate).split(".").slice(1).join(".");
const outputName = args["output-name"] || `新包生命周期V2 - 含联运${formatDatePart(startDate)}-${endLabel}_Joint修正版.xlsx`;
const OUTPUT_DIR = outputDir;
const OUTPUT_PATH = path.join(OUTPUT_DIR, outputName);
const DESKTOP_DIR = args["desktop-dir"] || "/Users/robin/Desktop/waje data";
const DESKTOP_PATH = path.join(DESKTOP_DIR, outputName);
const VALIDATION_PATH = path.join(OUTPUT_DIR, "validation-report.json");
const QA_DIR = path.join(OUTPUT_DIR, "qa-previews");

const sourceConfigs = dates.map((date) => ({
  date,
  summary: path.join(rawRoot, date, "summary.xlsx"),
  detail: path.join(rawRoot, date, "detail.xlsx"),
  game: path.join(rawRoot, date, "game.xlsx"),
  active: path.join(rawRoot, date, "active.xlsx"),
}));

const targetSheets = {
  summary: { names: ["原始数据总数"], columns: 15, sourceColumns: 11, expectedRows: 1 },
  detail: { names: ["原始详细奖池", "生命周期详细奖池"], columns: 21, sourceColumns: 21, expectedRows: 105 },
  game: { names: ["原始游戏数据", "生命周期奖池分游戏汇总"], columns: 19, sourceColumns: 19, expectedRows: 21 },
  active: { names: ["原始数据活跃周期", "（活跃用户）生命周期奖池分周期汇总"], columns: 31, sourceColumns: 31, expectedRows: 4 },
};

const expectedSourceHeaders = {
  summary: ["总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  detail: ["生命周期", "游戏类型", "差额", "预期回报比", "盈利比万分比", "实际回报比万分比", "基础预期盈利", "基础实际盈利", "基础下注额", "基础真实回报比", "总破产保护金额", "总个人盈利控制金额", "完全预期盈利", "完全实际盈利", "完全下注额", "完全下注额占比", "完全真实回报比", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  game: ["游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比", "基础回报比差距", "总破产保护金额", "总个人盈利控制金额", "破产保护/下注", "个人盈利/下注", "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全下注额占比"],
  active: ["生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利", "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利", "人均实际盈利", "人数", "当日充值总金额", "当日复充总金额", "平均复充次数", "平均流充比", "营收", "TX总金额", "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数", "人均绝对破产次数"],
};

const expectedTargetHeaders = {
  summary: ["日期", "总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数", "盈利调整幅度", "盈利扣除幅度", "修改"],
  detail: ["日期", ...expectedSourceHeaders.detail],
  game: ["日期", ...expectedSourceHeaders.game],
  active: ["日期", ...expectedSourceHeaders.active],
};

function normalizeHeader(value) {
  return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim();
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function assertClose(actual, expected, tolerance, label) {
  const a = Number(actual);
  const e = Number(expected);
  assert(Number.isFinite(a) && Number.isFinite(e), `${label}: non-numeric value (${actual}, ${expected})`);
  const delta = Math.abs(a - e);
  assert(delta <= tolerance, `${label}: ${a} != ${e} (delta=${delta}, tolerance=${tolerance})`);
}

function getTargetSheet(workbook, spec) {
  for (const name of spec.names) {
    const sheet = workbook.worksheets.items.find((item) => item.name === name);
    if (sheet) return sheet;
  }
  throw new Error(`Target sheet missing; expected one of ${spec.names.join(", ")}`);
}
function sheetLabel(spec) { return spec.names.join("/"); }

function excelSerial(date) {
  return (Date.parse(`${date}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 86400000;
}

function parseUiValue(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value !== "string") return value;
  const trimmed = value.trim();
  if (trimmed === "") return null;
  if (/^-?\d+(?:\.\d+)?%$/.test(trimmed)) return Number(trimmed.slice(0, -1)) / 100;
  if (/^-?\d+(?:\.\d+)?$/.test(trimmed)) return Number(trimmed);
  return trimmed;
}

function normalizeRows(rows) {
  return rows.map((row) => row.map(parseUiValue));
}

function sum(rows, index) {
  return rows.reduce((total, row) => total + Number(row[index] ?? 0), 0);
}

function sha(value) {
  return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

async function fileSha(filePath) {
  return crypto.createHash("sha256").update(await fs.readFile(filePath)).digest("hex");
}

async function readExport(filePath) {
  const input = await FileBlob.load(filePath);
  const workbook = await SpreadsheetFile.importXlsx(input);
  assert(workbook.worksheets.items.length >= 1, `No worksheet in ${filePath}`);
  const sheet = workbook.worksheets.getItemAt(0);
  const used = sheet.getUsedRange(false);
  assert(used, `No used range in ${filePath}`);
  return used.values;
}

function validateHeader(kind, actual) {
  const normalizedActual = actual.map(normalizeHeader);
  const normalizedExpected = expectedSourceHeaders[kind].map(normalizeHeader);
  assert(JSON.stringify(normalizedActual) === JSON.stringify(normalizedExpected), `${kind} source header mismatch\nactual=${JSON.stringify(normalizedActual)}\nexpected=${JSON.stringify(normalizedExpected)}`);
}

function validateTargetHeader(kind, actual) {
  const normalizedActual = actual.slice(0, expectedTargetHeaders[kind].length).map(normalizeHeader);
  const normalizedExpected = expectedTargetHeaders[kind].map(normalizeHeader);
  assert(JSON.stringify(normalizedActual) === JSON.stringify(normalizedExpected), `${kind} target header mismatch\nactual=${JSON.stringify(normalizedActual)}\nexpected=${JSON.stringify(normalizedExpected)}`);
}

async function loadDataset(config) {
  const serial = excelSerial(config.date);
  const summaryValues = await readExport(config.summary);
  const detailValues = await readExport(config.detail);
  const gameValues = await readExport(config.game);
  let activeValues;
  if (config.active) {
    activeValues = await readExport(config.active);
  } else {
    const snapshot = JSON.parse(await fs.readFile(config.activeJson, "utf8"));
    assert(snapshot.date === config.date, `Active JSON date mismatch for ${config.date}`);
    activeValues = normalizeRows(snapshot.active);
  }

  validateHeader("summary", summaryValues[0]);
  validateHeader("detail", detailValues[0]);
  validateHeader("game", gameValues[0]);
  validateHeader("active", activeValues[0]);

  const summary = [[serial, ...summaryValues[1]]];
  const detailAll = detailValues.slice(1).map((row) => [serial, ...row]);
  const detail = detailAll.filter((row) => Number(row[1]) >= 0 && Number(row[1]) <= 4);
  const game = gameValues.slice(1).map((row) => [serial, ...row]);
  const activeAll = activeValues.slice(1).map((row) => [serial, ...row]);
  const active = activeAll.filter((row) => Number(row[1]) >= 1 && Number(row[1]) <= 4);

  assert(summary.length === 1 && summary[0].length === 11, `${config.date}: summary shape invalid`);
  assert(detail.length === game.length * 5 && detail.every((row) => row.length === 21), `${config.date}: detail shape invalid (${detail.length})`);
  assert(game.length > 0 && game.every((row) => row.length === 19), `${config.date}: game shape invalid (${game.length})`);
  assert(active.length === 4 && active.every((row) => row.length === 31), `${config.date}: active shape invalid (${active.length})`);

  const gameNames = game.map((row) => String(row[1]));
  assert(new Set(gameNames).size === game.length, `${config.date}: duplicate game summary rows`);
  for (const lifecycle of [0, 1, 2, 3, 4]) {
    const lifecycleRows = detail.filter((row) => Number(row[1]) === lifecycle);
    assert(lifecycleRows.length === game.length, `${config.date}: lifecycle ${lifecycle} detail count=${lifecycleRows.length}`);
    assert(new Set(lifecycleRows.map((row) => String(row[2]))).size === game.length, `${config.date}: lifecycle ${lifecycle} duplicate games`);
  }
  assert(new Set(active.map((row) => Number(row[1]))).size === 4, `${config.date}: duplicate active lifecycle rows`);

  const activeIncluded = activeAll.filter((row) => Number(row[1]) > 0);
  const activeAmounts = { baseBet: sum(activeIncluded, 2), baseExpected: sum(activeIncluded, 6), baseActual: sum(activeIncluded, 7), protection: sum(activeIncluded, 8), control: sum(activeIncluded, 9), entireBet: sum(activeIncluded, 10), entireExpected: sum(activeIncluded, 15), entireActual: sum(activeIncluded, 16), people: sum(activeIncluded, 18) };
  const gameAmounts = { baseBet: sum(game, 2), baseExpected: sum(game, 3), baseActual: sum(game, 4), protection: sum(game, 8), control: sum(game, 9), entireBet: sum(game, 12), entireExpected: sum(game, 13), entireActual: sum(game, 14) };

  for (const key of ["baseBet", "baseExpected", "baseActual", "protection", "control", "entireBet", "entireExpected", "entireActual"]) {
    assertClose(activeAmounts[key], gameAmounts[key], 0.25, `${config.date}: active/game ${key}`);
  }
  assertClose(summary[0][1], activeAmounts.baseBet, 0.05, `${config.date}: summary base bet`);
  assertClose(summary[0][2], activeAmounts.entireBet, 0.05, `${config.date}: summary entire bet`);
  assertClose(summary[0][7], activeAmounts.people, 0, `${config.date}: summary people`);
  assertClose(summary[0][3], 1 - activeAmounts.baseActual / activeAmounts.baseBet, 0.00015, `${config.date}: summary base actual RTP`);
  assertClose(summary[0][4], 1 - activeAmounts.entireActual / activeAmounts.entireBet, 0.00015, `${config.date}: summary entire actual RTP`);
  assertClose(summary[0][5], 1 - activeAmounts.baseExpected / activeAmounts.baseBet, 0.00015, `${config.date}: summary base expected RTP`);
  assertClose(summary[0][6], 1 - activeAmounts.entireExpected / activeAmounts.entireBet, 0.00015, `${config.date}: summary entire expected RTP`);

  for (const gameRow of game) {
    const name = String(gameRow[1]);
    const detailRows = detailAll.filter((row) => Number(row[1]) > 0 && String(row[2]) === name);
    assert(detailRows.length > 0, `${config.date}: ${name} has no positive-lifecycle detail rows`);
    assert(new Set(detailRows.map((row) => Number(row[1]))).size === detailRows.length, `${config.date}: ${name} duplicate lifecycle detail rows`);
    const pairs = [
      [sum(detailRows, 9), gameRow[2], "baseBet"],
      [sum(detailRows, 7), gameRow[3], "baseExpected"],
      [sum(detailRows, 8), gameRow[4], "baseActual"],
      [sum(detailRows, 11), gameRow[8], "protection"],
      [sum(detailRows, 12), gameRow[9], "control"],
      [sum(detailRows, 15), gameRow[12], "entireBet"],
      [sum(detailRows, 13), gameRow[13], "entireExpected"],
      [sum(detailRows, 14), gameRow[14], "entireActual"],
    ];
    for (const [actual, expected, metric] of pairs) assertClose(actual, expected, 0.25, `${config.date}: detail/game ${name} ${metric}`);
    if (Number(gameRow[2]) !== 0) {
      assertClose(gameRow[5], 1 - Number(gameRow[4]) / Number(gameRow[2]), 0.00015, `${config.date}: ${name} base RTP`);
      assertClose(gameRow[6], 1 - Number(gameRow[3]) / Number(gameRow[2]), 0.00015, `${config.date}: ${name} base expected RTP`);
    }
    if (Number(gameRow[12]) !== 0) {
      assertClose(gameRow[15], 1 - Number(gameRow[14]) / Number(gameRow[12]), 0.00015, `${config.date}: ${name} entire RTP`);
      assertClose(gameRow[16], 1 - Number(gameRow[13]) / Number(gameRow[12]), 0.00015, `${config.date}: ${name} entire expected RTP`);
    }
  }

  const sourceFiles = [config.summary, config.detail, config.game, config.active ?? config.activeJson];
  return {
    date: config.date,
    serial,
    summary,
    detail,
    detailAll,
    game,
    active,
    activeAll,
    sourceFiles,
    metrics: {
      totalBaseBet: summary[0][1],
      totalEntireBet: summary[0][2],
      baseActualRtp: summary[0][3],
      entireActualRtp: summary[0][4],
      totalPeople: summary[0][7],
    },
  };
}

function findRowsBySerial(sheet, serial) {
  const used = sheet.getUsedRange(false);
  const values = used.values;
  const rows = [];
  for (let i = 0; i < values.length; i += 1) {
    if (Number(values[i][0]) === serial) rows.push(i);
  }
  return rows;
}

function rangeHash(range) {
  return sha({ address: range.address, values: range.values, formulas: range.formulas });
}

function sheetHash(sheet) {
  const used = sheet.getUsedRange(false);
  if (!used) return sha({ name: sheet.name, empty: true });
  return sha({ name: sheet.name, address: used.address, values: used.values, formulas: used.formulas });
}

async function truncateWorkbookRows(filePath, maxRowsBySheet) {
  const zip = await JSZip.loadAsync(await fs.readFile(filePath));
  const workbookXml = await zip.file("xl/workbook.xml").async("string");
  const relationshipsXml = await zip.file("xl/_rels/workbook.xml.rels").async("string");
  const relationships = Object.fromEntries(
    [...relationshipsXml.matchAll(/<(?:Relationship|x:Relationship)\b[^>]*\/>/g)]
      .map((match) => {
        const id = match[0].match(/\bId="([^"]+)"/)?.[1];
        const rawTarget = match[0].match(/\bTarget="([^"]+)"/)?.[1];
        if (!id || !rawTarget) return null;
        const target = rawTarget.replace(/^\//, "");
        return [id, target.startsWith("xl/") ? target : `xl/${target}`];
      })
      .filter(Boolean),
  );
  const sheetPaths = Object.fromEntries(
    [...workbookXml.matchAll(/<(?:sheet|x:sheet)\b[^>]*\bname="([^"]+)"[^>]*\br:id="([^"]+)"[^>]*\/>/g)]
      .map((match) => [match[1], relationships[match[2]]])
      .filter(([, sheetPath]) => sheetPath),
  );

  for (const [sheetName, maxRow] of Object.entries(maxRowsBySheet)) {
    const sheetPath = sheetPaths[sheetName];
    assert(sheetPath && zip.file(sheetPath), `Cannot locate worksheet XML for ${sheetName}`);
    let xml = await zip.file(sheetPath).async("string");
    xml = xml.replace(/<(?:x:)?row\b[^>]*\br="(\d+)"[^>]*>[\s\S]*?<\/(?:x:)?row>/g, (rowXml, rowNumber) => (
      Number(rowNumber) > maxRow ? "" : rowXml
    ));
    xml = xml.replace(/<dimension\b[^>]*\bref="([A-Z]+\d+):([A-Z]+)\d+"[^>]*\/>/, (_match, first, lastColumn) => (
      `<dimension ref="${first}:${lastColumn}${maxRow}"/>`
    ));
    zip.file(sheetPath, xml);
  }

  await fs.writeFile(filePath, await zip.generateAsync({
    type: "nodebuffer",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  }));
}

function applyAppendedFormats(sheet, kind, baseStart, rowCount) {
  const body = sheet.getRangeByIndexes(baseStart, 0, rowCount, targetSheets[kind].columns);
  body.format.font = { name: "Segoe UI", size: 12, color: "#212529" };
  body.format.horizontalAlignment = "center";
  body.format.verticalAlignment = "center";
  body.format.wrapText = true;
  body.format.borders = { preset: "all", style: "medium", color: "#808080" };

  const dateColumn = sheet.getRangeByIndexes(baseStart, 0, rowCount, 1);
  dateColumn.format.font = { name: "宋体", size: 11, color: "#212529" };
  dateColumn.format.horizontalAlignment = "center";
  dateColumn.format.wrapText = false;
  dateColumn.format.numberFormat = "m/d/yy";

  const formats = {
    summary: [[1, 2, "0.0_ "], [3, 6, "0.00%"], [7, 7, "0"], [11, 11, "0.00"], [12, 12, "0.000000"]],
    detail: [[1, 1, "0"], [4, 4, "0.00%"], [5, 5, "0"], [7, 15, "0.00"], [16, 17, "0.00%"], [18, 19, "0.00"]],
    game: [[2, 4, "0.00"], [5, 7, "0.00%"], [8, 9, "0.00"], [10, 11, "0.00%"], [12, 14, "0.00"], [15, 18, "0.00%"]],
    active: [[1, 1, "0"], [2, 2, "0.00"], [3, 5, "0.00%"], [6, 16, "0.00"], [17, 17, "0"], [18, 25, "0.00"], [26, 27, "0.00%"], [28, 29, "0"], [30, 30, "0.00"]],
  };
  for (const [startCol, endCol, numberFormat] of formats[kind]) {
    sheet.getRangeByIndexes(baseStart, startCol, rowCount, endCol - startCol + 1).format.numberFormat = numberFormat;
  }
}

async function renderQa(workbook, sheetName, range, outputName) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(QA_DIR, outputName), new Uint8Array(await preview.arrayBuffer()));
}

await fs.mkdir(OUTPUT_DIR, { recursive: true });
await fs.mkdir(QA_DIR, { recursive: true });
await fs.access(INPUT_PATH);
if (await fs.stat(OUTPUT_PATH).then(() => true).catch(() => false)) throw new Error(`输出文件已存在，拒绝覆盖: ${OUTPUT_PATH}`);

for (const config of sourceConfigs) {
  for (const filePath of [config.summary, config.detail, config.game, config.active ?? config.activeJson]) {
    await fs.access(filePath);
  }
}
const datasets = [];
for (const config of sourceConfigs) datasets.push(await loadDataset(config));

const inputBlob = await FileBlob.load(INPUT_PATH);
const workbook = await SpreadsheetFile.importXlsx(inputBlob);
const allSheetNames = workbook.worksheets.items.map((sheet) => sheet.name);
const sheetMapping = Object.fromEntries(Object.entries(targetSheets).map(([kind, spec]) => [kind, getTargetSheet(workbook, spec).name]));
assert(Object.values(sheetMapping).every((name) => allSheetNames.includes(name)), `Target workbook is missing required source sheets: ${JSON.stringify(sheetMapping)}`);

const targetNameSet = new Set(Object.values(sheetMapping));
const nonTargetHashesBefore = Object.fromEntries(workbook.worksheets.items.filter((sheet) => !targetNameSet.has(sheet.name)).map((sheet) => [sheet.name, sheetHash(sheet)]));
assert(Object.keys(nonTargetHashesBefore).length === 0, `检测到非目标 Sheet（${Object.keys(nonTargetHashesBefore).join(", ")}），为避免导出过程改变既有内容，拒绝写回；请使用已整理的 Joint 修正版 4-sheet 文件作为输入`);
const targetPrefixHashesBefore = {};
const originalUsedRanges = {};
const baseStarts = {};
const templateStarts = {};
const appendMode = {};

for (const [kind, spec] of Object.entries(targetSheets)) {
  const sheet = getTargetSheet(workbook, spec);
  const used = sheet.getUsedRange(false);
  originalUsedRanges[kind] = used.address;
  validateTargetHeader(kind, sheet.getRangeByIndexes(0, 0, 1, spec.sourceColumns).values[0]);
  const firstDataRows = used.values.map((row, index) => ({ row, index })).filter(({ row, index }) => index > 0 && Number.isFinite(Number(row[0])));
  assert(firstDataRows.length > 0, `${sheetLabel(spec)}: existing data rows missing`);
  templateStarts[kind] = firstDataRows[0].index;
  const requestedRows = Object.fromEntries(sourceConfigs.map((config) => [config.date, findRowsBySerial(sheet, excelSerial(config.date))]));
  const existingDates = Object.values(requestedRows).filter((rows) => rows.length > 0).length;
  const totalRows = datasets.reduce((n, d) => n + d[kind].length, 0);
  if (freshOutput) {
    baseStarts[kind] = 1;
    appendMode[kind] = false;
  } else if (existingDates === 0) {
    baseStarts[kind] = used.rowCount;
    appendMode[kind] = true;
  } else {
    assert(existingDates === sourceConfigs.length, `${sheetLabel(spec)}: 日期范围部分已存在，拒绝混合覆盖；请提供完整范围或新输入文件`);
    const rowsStart = requestedRows[startDate];
    assert(rowsStart.length > 0, `${sheetLabel(spec)}: ${startDate} rows missing`);
    assert(rowsStart.every((row, index) => index === 0 || row === rowsStart[index - 1] + 1), `${sheetLabel(spec)}: ${startDate} rows are not contiguous`);
    const laterRows = firstDataRows.filter(({ row }) => Number(row[0]) > excelSerial(endDate));
    assert(laterRows.length === 0, `${sheetLabel(spec)}: 查询范围之后已有数据，拒绝覆盖后续历史；请使用包含后续日期的输入范围`);
    assert(used.rowCount - rowsStart[0] === totalRows, `${sheetLabel(spec)}: 已存在日期的尾部行数与本次源数据不一致，拒绝覆盖`);
    baseStarts[kind] = rowsStart[0];
    appendMode[kind] = false;
  }
  targetPrefixHashesBefore[kind] = rangeHash(sheet.getRangeByIndexes(0, 0, baseStarts[kind], spec.sourceColumns));
}

for (const [kind, spec] of Object.entries(targetSheets)) {
  const sheet = getTargetSheet(workbook, spec);
  const baseStart = baseStarts[kind];
  const originalTailEnd = sheet.getUsedRange(false).rowCount;
  const totalRows = datasets.reduce((n, d) => n + d[kind].length, 0);
  const templateRowCount = Math.min(spec.expectedRows, originalTailEnd - templateStarts[kind]);
  assert(templateRowCount > 0, `${sheetLabel(spec)}: no template rows available`);
  const templateRange = sheet.getRangeByIndexes(templateStarts[kind], 0, templateRowCount, spec.columns);
  if (appendMode[kind]) assert(baseStart === originalTailEnd, `${sheetLabel(spec)}: append position is not end of used range`);
  for (let i = 0, at = 0; i < datasets.length; i++) {
    const rowsForDate = datasets[i][kind].length;
    const dest = sheet.getRangeByIndexes(baseStart + at, 0, rowsForDate, spec.columns);
    for (let j = 0; j < rowsForDate; j++) sheet.getRangeByIndexes(baseStart + at + j, 0, 1, spec.columns).copyFrom(templateRange.getRow(j % templateRowCount), "all");
    sheet.getRangeByIndexes(baseStart + at, 0, rowsForDate, spec.sourceColumns).values = datasets[i][kind];
    at += rowsForDate;
  }
  // In fresh-output mode the style template still contains its old Joint
  // rows below the newly written ordinary-pool data. Clear that tail before
  // validation; otherwise the same dates can be found twice in memory and
  // the output would be validated against stale template values. The XML
  // truncation below remains as a second, file-level guard.
  if (freshOutput && baseStart + totalRows < originalTailEnd) {
    sheet
      .getRangeByIndexes(baseStart + totalRows, 0, originalTailEnd - (baseStart + totalRows), spec.columns)
      .clear({ applyTo: "all" });
  }
  // Reapply imported body/number formats because copyFrom copies values/formulas,
  // not imported cell styles. Source dates remain Excel serial values.
  applyAppendedFormats(sheet, kind, baseStart, totalRows);
}

for (const [name, hash] of Object.entries(nonTargetHashesBefore)) {
  assert(sheetHash(workbook.worksheets.getItem(name)) === hash, `${name}: non-target sheet changed in memory`);
}
for (const [kind, spec] of Object.entries(targetSheets)) {
  const sheet = getTargetSheet(workbook, spec);
  const prefix = sheet.getRangeByIndexes(0, 0, baseStarts[kind], spec.sourceColumns);
  assert(rangeHash(prefix) === targetPrefixHashesBefore[kind], `${sheetLabel(spec)}: historical prefix changed`);
  for (const dataset of datasets) {
    const rows = findRowsBySerial(sheet, dataset.serial);
    assert(rows.length === dataset[kind].length, `${sheetLabel(spec)}: ${dataset.date} row count=${rows.length}`);
    const actual = sheet.getRangeByIndexes(rows[0], 0, dataset[kind].length, spec.sourceColumns).values;
    assert(sha(actual) === sha(dataset[kind]), `${sheetLabel(spec)}: ${dataset.date} values differ from source`);
  }
}

await renderQa(workbook, sheetMapping.summary, "A1:O20", "summary-preview.png");
await renderQa(workbook, sheetMapping.detail, "A1:U30", "detail-preview.png");
await renderQa(workbook, sheetMapping.game, "A1:S30", "game-preview.png");
await renderQa(workbook, sheetMapping.active, "A1:AE20", "active-preview.png");

const outputBlob = await SpreadsheetFile.exportXlsx(workbook);
await outputBlob.save(OUTPUT_PATH);
if (freshOutput) {
  const maxRowsBySheet = {};
  for (const [kind, spec] of Object.entries(targetSheets)) {
    const totalRows = datasets.reduce((count, dataset) => count + dataset[kind].length, 0);
    maxRowsBySheet[sheetMapping[kind]] = 1 + totalRows;
  }
  await truncateWorkbookRows(OUTPUT_PATH, maxRowsBySheet);
}
await fs.copyFile(OUTPUT_PATH, DESKTOP_PATH);

const verifyBlob = await FileBlob.load(OUTPUT_PATH);
const verifyWorkbook = await SpreadsheetFile.importXlsx(verifyBlob);
assert(Object.values(sheetMapping).every((name) => verifyWorkbook.worksheets.items.some((sheet) => sheet.name === name)), "Exported workbook lost a required source sheet");
for (const [name, hash] of Object.entries(nonTargetHashesBefore)) {
  assert(sheetHash(verifyWorkbook.worksheets.getItem(name)) === hash, `${name}: changed after export/reimport`);
}
for (const [kind, spec] of Object.entries(targetSheets)) {
  const sheet = getTargetSheet(verifyWorkbook, spec);
  assert(rangeHash(sheet.getRangeByIndexes(0, 0, baseStarts[kind], spec.sourceColumns)) === targetPrefixHashesBefore[kind], `${sheetLabel(spec)}: historical prefix changed after export`);
  for (const dataset of datasets) {
    const rows = findRowsBySerial(sheet, dataset.serial);
    assert(rows.length === dataset[kind].length, `${sheetLabel(spec)}: exported ${dataset.date} row count=${rows.length}`);
    const actual = sheet.getRangeByIndexes(rows[0], 0, dataset[kind].length, spec.sourceColumns).values;
    assert(sha(actual) === sha(dataset[kind]), `${sheetLabel(spec)}: exported ${dataset.date} values differ from source`);
  }
}

const formulaErrors = await verifyWorkbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
assert(!formulaErrors.ndjson.includes('"kind":"match"'), `Formula errors detected: ${formulaErrors.ndjson}`);

const finalCounts = {};
for (const [kind, spec] of Object.entries(targetSheets)) {
  const sheet = getTargetSheet(verifyWorkbook, spec);
  finalCounts[kind] = {
    sheet: sheetMapping[kind],
    usedRangeBefore: originalUsedRanges[kind],
    usedRangeAfter: sheet.getUsedRange(false).address,
    perDate: Object.fromEntries(datasets.map((dataset) => [dataset.date, findRowsBySerial(sheet, dataset.serial).length])),
  };
}

const sourceManifest = [];
for (const dataset of datasets) {
  sourceManifest.push({
    date: dataset.date,
    files: await Promise.all(dataset.sourceFiles.map(async (filePath) => ({ path: filePath, sha256: await fileSha(filePath) }))),
    metrics: dataset.metrics,
  });
}

const report = {
  status: "ok",
  input: { path: INPUT_PATH, sha256: await fileSha(INPUT_PATH), unchanged: true },
  output: { path: OUTPUT_PATH, desktopPath: DESKTOP_PATH, sha256: await fileSha(OUTPUT_PATH) },
  dates: datasets.map((dataset) => dataset.date),
  sheetMapping,
  sourceManifest,
  finalCounts,
  invariants: {
    freshOutput,
    nonTargetSheetsUnchanged: true,
    historicalRowsBeforeQueryRangeUnchanged: true,
    sourceHeadersValidated: true,
    crossTableReconciliationPassed: true,
    duplicateKeysAbsent: true,
    formulaErrorScanPassed: true,
  },
};
await fs.writeFile(VALIDATION_PATH, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import JSZip from "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/jszip/lib/index.js";

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    out[key] = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const inputPath = args.input;
const outputPath = args.output;
if (!inputPath || !outputPath) throw new Error("必须提供 --input 和 --output");

const targetNames = new Set([
  "原始数据总数",
  "原始详细奖池",
  "生命周期详细奖池",
  "原始游戏数据",
  "生命周期奖池分游戏汇总",
  "原始数据活跃周期",
  "（活跃用户）生命周期奖池分周期汇总",
]);

function attrs(tag) {
  return new Map([...tag.matchAll(/([:\w-]+)="([^"]*)"/g)].map((m) => [m[1], m[2]]));
}
function column(cellRef) { return cellRef?.match(/^[A-Z]+/)?.[0]; }
function rowBlocks(xml) {
  return [...xml.matchAll(/<(?:x:)?row\b[^>]*\br="(\d+)"[^>]*>[\s\S]*?<\/(?:x:)?row>/g)].map((m) => ({ row: Number(m[1]), xml: m[0] }));
}
function styleMap(rowXml) {
  return Object.fromEntries((rowXml.match(/<(?:x:)?c\b[^>]*>/g) || []).map((tag) => {
    const a = attrs(tag);
    return [column(a.get("r")), a.get("s")];
  }).filter(([col, style]) => col && style));
}
function applyStyle(rowXml, styles) {
  return rowXml.replace(/<(?:x:)?c\b[^>]*>/g, (tag) => {
    const a = attrs(tag);
    const col = column(a.get("r"));
    const style = styles[col];
    if (!style) return tag;
    if (/\ss="/.test(tag)) return tag.replace(/\ss="[^"]*"/, ` s="${style}"`);
    if (/\/>$/.test(tag)) return `${tag.slice(0, -2)} s="${style}" />`;
    return `${tag.slice(0, -1)} s="${style}">`;
  });
}
function sha(data) { return crypto.createHash("sha256").update(data).digest("hex"); }

const inputZip = await JSZip.loadAsync(await fs.readFile(inputPath));
const outputZip = await JSZip.loadAsync(await fs.readFile(outputPath));
const workbookXml = await inputZip.file("xl/workbook.xml").async("string");
const relsXml = await inputZip.file("xl/_rels/workbook.xml.rels").async("string");
const relationships = Object.fromEntries([...relsXml.matchAll(/<(?:Relationship|x:Relationship)\b[^>]*\bId="([^"]+)"[^>]*\bTarget="([^"]+)"[^>]*\/>/g)].map((m) => [m[1], `xl/${m[2].replace(/^\//, "")}`]));
const targetSheets = [...workbookXml.matchAll(/<(?:sheet|x:sheet)\b[^>]*\bname="([^"]+)"[^>]*\br:id="([^"]+)"[^>]*\/>/g)]
  .filter((m) => targetNames.has(m[1]))
  .map((m) => relationships[m[2]])
  .filter(Boolean);
if (targetSheets.length !== 4) throw new Error(`需要定位 4 个目标 Sheet，实际找到 ${targetSheets.length}`);
const patched = [];
for (const sheetPath of targetSheets) {
  const inputXml = await inputZip.file(sheetPath).async("string");
  let outputXml = await outputZip.file(sheetPath).async("string");
  const inputRows = rowBlocks(inputXml);
  const outputRows = rowBlocks(outputXml);
  const lastInputRow = inputRows.at(-1);
  if (!lastInputRow) throw new Error(`${sheetPath}: input has no data rows`);
  const styles = styleMap(lastInputRow.xml);
  const newRows = outputRows.filter((item) => item.row > lastInputRow.row);
  for (const item of newRows) outputXml = outputXml.replace(item.xml, applyStyle(item.xml, styles));
  outputZip.file(sheetPath, outputXml);
  patched.push({ sheetPath, templateRow: lastInputRow.row, patchedRows: newRows.length, styleColumns: Object.keys(styles).length });
}

const bytes = await outputZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 6 } });
await fs.writeFile(outputPath, bytes);
console.log(JSON.stringify({ status: "ok", output: outputPath, sha256: sha(bytes), patched }, null, 2));

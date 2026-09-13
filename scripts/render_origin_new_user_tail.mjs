#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const modules = process.env.CODEX_NODE_MODULES || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(modules, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);

const [inputPath, outputDir] = process.argv.slice(2);
if (!inputPath || !outputDir) throw new Error("usage: render_origin_new_user_tail.mjs <xlsx> <output-dir>");
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
await fs.mkdir(outputDir, { recursive: true });

function isDate(value) {
  if (value instanceof Date && !Number.isNaN(value.valueOf())) return true;
  return /^(20\d\d)[/-]\d{1,2}[/-]\d{1,2}/.test(String(value ?? "").trim());
}
const receipt = { status: "ok", workbook: inputPath, sheets: {} };
for (const sheet of workbook.worksheets.items) {
  const used = sheet.getUsedRange(false);
  const values = used?.values || [];
  let last = values.length - 1;
  while (last > 0 && !isDate(values[last]?.[0])) last -= 1;
  const start = Math.max(1, last - 5);
  const range = `A${start + 1}:AQ${last + 1}`;
  const blob = await workbook.render({ sheetName: sheet.name, range, scale: 1, format: "png" });
  const output = path.join(outputDir, `${sheet.name.replace(/[^\w\u4e00-\u9fff-]/g, "_")}.png`);
  await fs.writeFile(output, new Uint8Array(await blob.arrayBuffer()));
  receipt.sheets[sheet.name] = { status: "passed", range, output };
}
await fs.writeFile(path.join(outputDir, "render-receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify(receipt, null, 2));

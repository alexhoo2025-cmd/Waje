#!/usr/bin/env node
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[index + 1];
    if (next && !next.startsWith("--")) {
      result[key] = next;
      index += 1;
    } else result[key] = true;
  }
  return result;
}

const args = parseArgs(process.argv.slice(2));
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceRoot = path.dirname(scriptDir);
const startDate = args["start-date"] || "2026-07-01";
const endDate = args["end-date"] || "2026-08-25";
const template = args.template || "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.7.27-8.17_Joint修正版.xlsx";
const rawRoot = args["raw-root"] || path.join(workspaceRoot, "data/raw/lifecycle_pool/2026-08-26");
const outputDir = args["output-dir"] || path.join(workspaceRoot, "data/outputs/lifecycle_pool/2026-08-26");
const desktopDir = args["desktop-dir"] || "/Users/robin/Desktop/waje data";
const outputName = args["output-name"] || "Lifecycle Pool 2026.7.1-8.25_普通口径.xlsx";

const childArgs = [
  path.join(scriptDir, "update_workbook.mjs"),
  "--fresh-output",
  "--start-date", startDate,
  "--end-date", endDate,
  "--input", template,
  "--raw-root", rawRoot,
  "--output-dir", outputDir,
  "--desktop-dir", desktopDir,
  "--output-name", outputName,
  "--run-date", args["run-date"] || "2026-08-26",
];

const child = spawn(process.execPath, childArgs, {
  cwd: workspaceRoot,
  env: process.env,
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.stderr.write(`update_workbook terminated by ${signal}\n`);
    process.exit(1);
  }
  process.exit(code ?? 1);
});

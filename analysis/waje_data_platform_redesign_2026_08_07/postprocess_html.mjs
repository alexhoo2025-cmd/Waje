import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

const htmlPath = process.argv[2];
const diagramDir = process.argv[3];

if (!htmlPath || !diagramDir) {
  throw new Error("Usage: node postprocess_html.mjs <html-path> <diagram-dir>");
}

let html = fs.readFileSync(htmlPath, "utf8");
html = html.replace("Data Analytics report", "数据分析报告");

// The portable builder is not present in every desktop runtime. Keep the
// interactive payload and the semantic fallback synchronized with artifact.json
// so a content-only report revision remains safe to publish in those runtimes.
const artifactPath = path.join(path.dirname(new URL(import.meta.url).pathname), "artifact.json");
const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
const payload = zlib.gzipSync(Buffer.from(JSON.stringify(artifact))).toString("base64");
const payloadPattern = /(<template id="data-analytics-portable-artifact-payload-source"[^>]*>)[\s\S]*?(<\/template>)/;
if (!payloadPattern.test(html)) {
  throw new Error("Unable to locate the portable artifact payload.");
}
html = html.replace(payloadPattern, `$1\n${payload}\n$2`);

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function inlineMarkdown(value) {
  return escapeHtml(value).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function markdownToHtml(body) {
  const lines = body.split("\n");
  const output = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (line.startsWith("## ")) {
      output.push(`<h2>${inlineMarkdown(line.slice(3))}</h2>`);
      index += 1;
      continue;
    }
    if (/^- /.test(line)) {
      const items = [];
      while (index < lines.length && /^- /.test(lines[index])) {
        items.push(`<li>${inlineMarkdown(lines[index].slice(2))}</li>`);
        index += 1;
      }
      output.push(`<ul>${items.join("")}</ul>`);
      continue;
    }
    if (/^\d+\. /.test(line)) {
      const items = [];
      while (index < lines.length && /^\d+\. /.test(lines[index])) {
        items.push(`<li>${inlineMarkdown(lines[index].replace(/^\d+\. /, ""))}</li>`);
        index += 1;
      }
      output.push(`<ol>${items.join("")}</ol>`);
      continue;
    }
    if (line.trim()) output.push(`<p>${inlineMarkdown(line)}</p>`);
    index += 1;
  }
  return output.join("\n");
}

function refreshFallbackMarkdown(blockId) {
  const block = artifact.manifest.blocks.find((entry) => entry.id === blockId);
  if (!block || block.type !== "markdown") return;
  const pattern = new RegExp(`(<div class="portable-block[^>]*data-artifact-block-id="${blockId}"[^>]*><section class="portable-markdown">)[\\s\\S]*?(<\\/section><\\/div>)`);
  if (!pattern.test(html)) {
    throw new Error(`Unable to locate fallback markdown block: ${blockId}`);
  }
  html = html.replace(pattern, `$1${markdownToHtml(block.body)}$2`);
}

function refreshFallbackHtml(blockId) {
  const block = artifact.manifest.blocks.find((entry) => entry.id === blockId);
  if (!block || block.type !== "html") return;
  const srcdoc = `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: blob:; style-src 'unsafe-inline'; font-src data:; connect-src 'none'; script-src 'none'; media-src data: blob:; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"><style>html{color-scheme:light dark}body{margin:0;font:14px/1.5 system-ui,sans-serif;color:CanvasText;background:Canvas}img{max-width:100%;height:auto}</style></head><body>${block.body}</body></html>`;
  const iframe = `<iframe sandbox="" loading="lazy" referrerpolicy="no-referrer" title="Custom report content" srcdoc="${escapeHtml(srcdoc)}"></iframe>`;
  const pattern = new RegExp(`(<div class="portable-block[^>]*data-artifact-block-id="${blockId}"[^>]*>)<section class="portable-content-card portable-custom-html">[\\s\\S]*?<\\/section><\\/div>`);
  if (!pattern.test(html)) {
    throw new Error(`Unable to locate fallback HTML block: ${blockId}`);
  }
  html = html.replace(pattern, `$1<section class="portable-content-card portable-custom-html">${iframe}</section></div>`);
}

function refreshFallbackTable(blockId) {
  const block = artifact.manifest.blocks.find((entry) => entry.id === blockId);
  const table = artifact.manifest.tables.find((entry) => entry.id === block?.tableId);
  if (!block || !table) return;
  const rows = artifact.snapshot.datasets[table.dataset] || [];
  const headers = table.columns.map((column) => `<th scope="col">${escapeHtml(column.label)}</th>`).join("");
  const body = rows.map((row) => `<tr>${table.columns.map((column) => `<td>${escapeHtml(row[column.field] ?? "")}</td>`).join("")}</tr>`).join("");
  const tableHtml = `<div class="portable-table-source-region"><div class="portable-table-scroll"><table><caption>${escapeHtml(table.title)}</caption><thead><tr>${headers}</tr></thead><tbody>${body}</tbody></table></div></div>`;
  const pattern = new RegExp(`(<div class="portable-block[^>]*data-artifact-block-id="${blockId}"[^>]*>[\\s\\S]*?)<div class="portable-table-source-region">[\\s\\S]*?<\\/div><\\/section><\\/div>`);
  if (!pattern.test(html)) {
    throw new Error(`Unable to locate fallback table block: ${blockId}`);
  }
  html = html.replace(pattern, `$1${tableHtml}</section></div>`);
}

[
  "executive_summary",
  "finding_current",
  "target_architecture_intro",
  "ia_intro",
  "permission_intro",
  "next_steps",
  "further_questions",
].forEach(refreshFallbackMarkdown);
["current_architecture", "target_architecture", "information_architecture"].forEach(refreshFallbackHtml);
["platform_table", "target_roles_table", "migration_table", "roadmap_table"].forEach(refreshFallbackTable);

const fallbackReplacements = [
  ["复现当前五类系统定位、可见规模和主要问题。", "复现当前五类系统定位、可见规模和主要问题；Metabase 的云主机访问边界已按 8 月 10 日补充信息修正。"],
  ["复现当前五类系统定位、可见规模和主要问题；Metabase 的云主机访问边界已按 8 月 10 日补充信息修正。", "复现当前五类系统定位、可见规模和主要问题；纳入 8 月 10 日确认的 Metabase 访问边界、数据开发重点和架构/权限决策归口。"],
  ["Waje 平台页面盘点与数据开发负责人确认（2026年8月7日）", "Waje 平台页面盘点与数据开发重点确认（2026年8月10日）"],
  ["临时查询与临时看板", "受控业务数据访问、临时查询与看板"],
  ["受控访问 GCP/BQ、临时 SQL", "云主机受控访问 GCP/BQ；权限控制、风险隔离、临时 SQL"],
  ["缺 owner、有效期和转正式机制", "受限数据目录、角色矩阵、导出规则与审计责任仍需明确"],
  ["临时验证与短期看板", "受控业务数据访问、风险隔离、临时验证与专题看板"],
  ["受控查询工作区", "云主机受控入口、最小授权、访问审计、敏捷分析"],
  ["正式指标唯一来源和永久入口", "绕过受控入口直连受限数据；单独定义非认证指标"],
  ["Metabase临时看板", "Metabase受控专题/临时看板"],
  ["转正式系统或下线", "云主机 Metabase 或转正式系统"],
  ["有owner、数据集、有效期、访问记录", "受限数据经该入口；有角色、数据集、用途、导出规则、审计和有效期"],
];
for (const [from, to] of fallbackReplacements) html = html.replaceAll(from, to);

const printCss = `
<style id="waje-print-fixes">
  .waje-static-chart { margin: 8px 0 2px; }
  .waje-static-chart img { display: block; width: 100%; height: auto; border-radius: 12px; }
  [data-artifact-block-id="current_architecture"] iframe,
  [data-artifact-block-id="report_information_architecture"] iframe {
    height: 470px !important;
    min-height: 470px !important;
  }
  [data-artifact-block-id="target_architecture"] iframe {
    height: 510px !important;
    min-height: 510px !important;
  }
  @media print {
    @page { size: A4; margin: 10mm 9mm 11mm; }
    html, body { print-color-adjust: exact !important; -webkit-print-color-adjust: exact !important; }
    .portable-block-stack { gap: 12px !important; }
    .portable-content-card { break-inside: auto !important; page-break-inside: auto !important; }
    [data-artifact-block-type="html"],
    [data-artifact-block-type="chart"] {
      break-inside: avoid !important;
      page-break-inside: avoid !important;
    }
    [data-artifact-block-type="html"] .portable-content-card,
    [data-artifact-block-type="chart"] .portable-content-card {
      break-inside: avoid !important;
      page-break-inside: avoid !important;
    }
    .portable-table-scroll {
      overflow: visible !important;
      max-width: 100% !important;
      scrollbar-width: none !important;
    }
    .portable-table-scroll::-webkit-scrollbar { display: none !important; }
    .portable-table-scroll table {
      display: table !important;
      width: 100% !important;
      max-width: 100% !important;
      table-layout: fixed !important;
    }
    .portable-table-scroll th,
    .portable-table-scroll td {
      box-sizing: border-box !important;
      white-space: normal !important;
      overflow: visible !important;
      text-overflow: clip !important;
      overflow-wrap: anywhere !important;
      word-break: break-word !important;
      padding: 5px 5px 5px 0 !important;
      font-size: 8.4px !important;
      line-height: 1.28 !important;
    }
    .portable-table-scroll th { font-size: 8px !important; }
    .portable-table-scroll caption { font-size: 8px !important; }
    [data-artifact-block-id="report_groups_chart"] .portable-table-scroll,
    [data-artifact-block-id="engine_chart"] .portable-table-scroll {
      display: none !important;
    }
    .waje-static-chart { display: block !important; break-inside: avoid !important; }
  }
</style>`;

html = html.replace(/<style id="waje-print-fixes">[\s\S]*?<\/style>/, "");
html = html.replace("</head>", `${printCss}\n</head>`);
html = html.replace(/<div class="waje-static-chart"[\s\S]*?<\/div>/g, "");

function insertStaticChart(blockId, filename, alt) {
  const imagePath = path.join(diagramDir, filename);
  const encoded = fs.readFileSync(imagePath).toString("base64");
  const imageHtml = `<div class="waje-static-chart"><img src="data:image/png;base64,${encoded}" alt="${alt}"></div>`;
  const pattern = new RegExp(`(<div class="portable-block[^>]*data-artifact-block-id="${blockId}"[^>]*>[\\s\\S]*?<figcaption[\\s\\S]*?<\\/figcaption>)`);
  if (!pattern.test(html)) {
    throw new Error(`Unable to locate chart block: ${blockId}`);
  }
  html = html.replace(pattern, `$1${imageHtml}`);
}

insertStaticChart("report_groups_chart", "report_groups_bar.png", "起源报表集市各组条目数横向条形图");
insertStaticChart("engine_chart", "version_structure_bar.png", "起源报表版本结构横向条形图");

fs.writeFileSync(htmlPath, html);
console.log(htmlPath);

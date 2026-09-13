import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { deliverPortableArtifact } from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/deliver_portable_artifact.mjs';
import { buildPortableArtifact, readPackagedReaderRuntime } from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
const run = dirname(fileURLToPath(import.meta.url));
const css = '<style id="x7-overflow-fix">html,body{overflow-x:hidden!important;max-width:100%!important}.portable-page-header{max-width:100%!important}</style>';
const readingTheme = '<style id="waje-reading-theme">' + readFileSync(join(run,'reading-theme.css'),'utf8') + '</style>';
// The packaged scatter renderer omits x-axis domain/percent formatting.
// Apply the requested viewport to this chart only; keep the shared renderer.
function withRtpScatterAxis(html) {
  const axis = /axisLine:!1,dataKey:([A-Za-z_$][\w$]*)\.xField,label:[^,]+,name:\1\.xAxisTitle\?\?\1\.xField,tickLine:!1,tickMargin:[^,]+,tickSize:[^,]+,type:\x60number\x60/g;
  const matches = [...html.matchAll(axis)];
  if (matches.length !== 1) throw new Error('Scatter renderer changed; axis patch requires review.');
  return html.replace(axis, (original, chart) => original +
    `,domain:${chart}.id==="rtp-net-scatter"?[0.5,1.2]:void 0` +
    `,ticks:${chart}.id==="rtp-net-scatter"?[0.5,0.6,0.7,0.8,0.9,1,1.1,1.2]:void 0` +
    `,allowDataOverflow:${chart}.id==="rtp-net-scatter"` +
    `,tickFormatter:${chart}.id==="rtp-net-scatter"?(value=>Math.round(Number(value)*100)+"%"):void 0`);
}
function withReadableBarLabels(html) {
  const formatter = /function [A-Za-z_$][\w$]*\(([A-Za-z_$][\w$]*),([A-Za-z_$][\w$]*),([A-Za-z_$][\w$]*)\)\{let ([A-Za-z_$][\w$]*)=([A-Za-z_$][\w$]*\(\1,\2\.valueFormat,\2\.unit\));return \3&&\1>0/g;
  if ([...html.matchAll(formatter)].length !== 1) throw new Error('Bar label formatter changed; review required.');
  return html.replace(formatter, (original, value, chart, sign, label, fallback) =>
    original.replace(`let ${label}=${fallback};`,
      `let ${label}=${chart}.id==="top-bet-games"?(${value}/1e8).toFixed(2)+"亿":${chart}.id==="top-bet-share"?(${value}*100).toFixed(2)+"%":${fallback};`));
}
const runtimeHtml = withReadableBarLabels(withRtpScatterAxis(readPackagedReaderRuntime().html))
  .replaceAll('Data access blockers', '数据范围与待补充项')
  .replaceAll('Data access issues', '数据范围与待补充项')
  .replaceAll('Some report data could not load because the source query could not complete.', '部分数据尚未取得，相关分析需补充数据后完成。')
  .replace('</head>', readingTheme + '</head>');
const build = (input, options = {}) => buildPortableArtifact(input, { ...options, runtimeHtml })
  .replaceAll('Data access issues', '数据范围与待补充项')
  .replace('</head>', css + readingTheme + '</head>');
const result = await deliverPortableArtifact({inputPath:join(run,'artifact.json'),outputPath:join(run,'report.html'),readyTimeoutMs:15000,actionTimeoutMs:4000,timeoutMs:30000},{build});
writeFileSync(join(run,'delivery-receipt.json'),JSON.stringify({...result,validated_at:new Date().toISOString(),rtp_x_axis:{domain:[0.5,1.2],display:'50%–120%',statistics_recomputed:false}},null,2));
console.log(JSON.stringify(result));
if (!result.ok) process.exitCode = 1;

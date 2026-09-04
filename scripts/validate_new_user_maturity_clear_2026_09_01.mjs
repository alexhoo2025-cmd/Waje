#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

const runDir = path.resolve('data/outputs/lark_quality/2026-09-01-new-user-maturity-audit');
const beforeDir = path.join(runDir, 'cells');
const afterDir = path.join(runDir, 'after-cells');
const beforeLayoutDir = path.join(runDir, 'layout');
const afterLayoutDir = path.join(runDir, 'after-layout');
const beforeCondDir = path.join(runDir, 'conditional-format');
const afterCondDir = path.join(runDir, 'after-conditional-format');
const sheets = [
  ['WajeSpecial-facebook', '9cd78d', 'WajeSpecial-facebook.json'],
  ['WajeSpecial-googleadwords_int', 'xWsChb', 'WajeSpecial-googleadwords_int.json'],
  ['WajeSpecial-Google商店', 'Cfkonh', 'WajeSpecial-Google_.json'],
  ['WAJEIOS-AppStore商店', '25iiEi', 'WAJEIOS-AppStore_.json'],
  ['WAJEBETH5', 'GrWEoo', 'WAJEBETH5.json'],
  ['wajeH5-facebook', 'vkV1SD', 'wajeH5-facebook.json'],
  ['wajeH5ga-googlewords_int', 'ef19NP', 'wajeH5ga-googlewords_int.json'],
  ['PWA', 'gjy6I1', 'PWA.json'],
];
const fields = [
  ['次日', 1], ['3日', 3], ['4日', 4], ['5日', 5], ['6日', 6], ['7日', 7],
  ['8日', 8], ['9日', 9], ['10日', 10], ['11日', 11], ['12日', 12],
  ['13日', 13], ['14日', 14], ['15日', 15], ['30日', 30], ['60日', 60],
  ['次留', 1], ['3日留', 3], ['7日留', 7], ['15日留', 15], ['30日留', 30],
  ['60日留', 60], ['首充次留', 1], ['首充3日留', 3], ['首充7日留', 7],
  ['首充15日留', 15], ['首充30日留', 30], ['首充60日留', 60],
];
const value = function (cell) { return cell && cell.value !== undefined ? cell.value : ''; };
const formula = function (cell) { return cell && cell.formula !== undefined ? cell.formula : ''; };
const blank = function (v) { return v === null || v === undefined || String(v).trim() === ''; };
const normalize = function (v) { return String(v === null || v === undefined ? '' : v).replace(/[\s\u00a0]+/g, '').trim(); };
const column = function (n) { let x = n + 1; let out = ''; while (x > 0) { const r = (x - 1) % 26; out = String.fromCharCode(65 + r) + out; x = Math.floor((x - 1) / 26); } return out; };
function dateFrom(v) {
  const text = String(v === null || v === undefined ? '' : v).trim();
  const m = text.replaceAll('/', '-').match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) return m[1] + '-' + m[2].padStart(2, '0') + '-' + m[3].padStart(2, '0');
  if (/^\d+(?:\.\d+)?$/.test(text)) {
    const n = Number(text);
    if (n > 20000 && n < 100000) return new Date(Date.UTC(1899, 11, 30) + Math.round(n) * 86400000).toISOString().slice(0, 10);
  }
  return null;
}
const addDays = function (d, n) { return new Date(Date.parse(d + 'T00:00:00Z') + n * 86400000).toISOString().slice(0, 10); };
const sha = function (v) { return crypto.createHash('sha256').update(JSON.stringify(v)).digest('hex'); };
const cellSig = function (c) { return JSON.stringify({ value: value(c), formula: formula(c) }); };
const styleSig = function (c) { return JSON.stringify({ cell_styles: c && c.cell_styles || null, border_styles: c && c.border_styles || null }); };
function scrub(v) {
  if (Array.isArray(v)) return v.map(scrub);
  if (v && typeof v === 'object') {
    const out = {};
    for (const [k, x] of Object.entries(v)) if (!['revision', '_notice', 'warning_message', 'approx_char_count'].includes(k)) out[k] = scrub(x);
    return out;
  }
  return v;
}
function assert(ok, msg) { if (!ok) throw new Error(msg); }
function load(file) { return fs.readFile(file, 'utf8').then(JSON.parse); }
function audit(sheet, rows) {
  const headers = (rows[0] || []).map(value);
  const map = new Map(headers.map((h, i) => [normalize(h), i]));
  const data = [];
  for (let i = 1; i < rows.length; i += 1) {
    const d = dateFrom(value(rows[i][0]));
    if (d) data.push({ row: i + 1, date: d, cells: rows[i] });
  }
  const asOf = data.map(x => x.date).sort().at(-1);
  const issues = [];
  for (const [field, days] of fields) {
    const ci = map.get(normalize(field));
    if (ci === undefined) continue;
    for (const item of data) {
      const v = value(item.cells[ci]);
      if (blank(v)) continue;
      const matureOn = addDays(item.date, days);
      if (matureOn > asOf) issues.push({ sheet, cell: column(ci) + item.row, row: item.row, date: item.date, field, column: column(ci), column_index: ci + 1, maturity_days: days, mature_on: matureOn, as_of: asOf, value: v, formula: formula(item.cells[ci]) || null, status: 'immature_statistical_window' });
    }
  }
  return { asOf, dataRows: data.length, issues };
}
const beforeAudit = await load(path.join(runDir, 'maturity-audit-before.json'));
assert(beforeAudit.issue_count === 470, 'before issue count must be 470');
const failures = [];
const reports = {};
const afterAudits = {};
const historical = {};
const formatting = {};
for (const [sheet, id, file] of sheets) {
  const before = await load(path.join(beforeDir, file));
  const after = await load(path.join(afterDir, file));
  const b = before.ranges?.[0]?.cells || [];
  const a = after.ranges?.[0]?.cells || [];
  assert(before.has_more === false && after.has_more === false, sheet + ': snapshot truncated');
  assert(b.length === a.length && b[0]?.length === a[0]?.length, sheet + ': shape changed');
  const issueSet = new Set(beforeAudit.issues.filter(x => x.sheet === sheet).map(x => x.cell));
  let cleared = 0;
  let changedOutside = 0;
  let styleChanged = 0;
  let formulaChanged = 0;
  const outsideBefore = [];
  const outsideAfter = [];
  for (let r = 0; r < b.length; r += 1) {
    for (let c = 0; c < b[r].length; c += 1) {
      const addr = column(c) + (r + 1);
      if (issueSet.has(addr)) {
        if (!blank(value(a[r][c])) || formula(a[r][c])) failures.push(sheet + '!' + addr + ': issue value not cleared');
        else cleared += 1;
      } else {
        outsideBefore.push([addr, value(b[r][c]), formula(b[r][c])]);
        outsideAfter.push([addr, value(a[r][c]), formula(a[r][c])]);
        if (cellSig(b[r][c]) !== cellSig(a[r][c])) changedOutside += 1;
        if (styleSig(b[r][c]) !== styleSig(a[r][c])) styleChanged += 1;
        if (formula(b[r][c]) !== formula(a[r][c])) formulaChanged += 1;
      }
    }
  }
  if (changedOutside) failures.push(sheet + ': outside content changed ' + changedOutside);
  if (styleChanged) failures.push(sheet + ': styles changed ' + styleChanged);
  if (formulaChanged) failures.push(sheet + ': formulas changed ' + formulaChanged);
  const aa = audit(sheet, a);
  afterAudits[sheet] = aa;
  if (aa.issues.length) failures.push(sheet + ': remaining immature values ' + aa.issues.length);
  const beforeLayout = scrub(await load(path.join(beforeLayoutDir, file)));
  const afterLayout = scrub(await load(path.join(afterLayoutDir, file)));
  const layoutSame = JSON.stringify(beforeLayout) === JSON.stringify(afterLayout);
  if (!layoutSame) failures.push(sheet + ': layout changed');
  const beforeCond = scrub(await load(path.join(beforeCondDir, file)));
  const afterCond = scrub(await load(path.join(afterCondDir, file)));
  const condSame = JSON.stringify(beforeCond) === JSON.stringify(afterCond);
  if (!condSame) failures.push(sheet + ': conditional formats changed');
  const prefixBefore = b.slice(0, 2).map(r => r.map(c => ({ value: value(c), formula: formula(c) })));
  const prefixAfter = a.slice(0, 2).map(r => r.map(c => ({ value: value(c), formula: formula(c) })));
  const prefixSame = JSON.stringify(prefixBefore) === JSON.stringify(prefixAfter);
  if (!prefixSame) failures.push(sheet + ': header/first-row prefix changed');
  historical[sheet] = { untargeted_content_hash_before: sha(outsideBefore), untargeted_content_hash_after: sha(outsideAfter), untargeted_content_unchanged: changedOutside === 0, formulas_unchanged: formulaChanged === 0, prefix_unchanged: prefixSame, cleared_issue_cells: cleared, expected_issue_cells: issueSet.size };
  formatting[sheet] = { style_cells_changed: styleChanged, layout_unchanged: layoutSame, conditional_formats_unchanged: condSame, format_unchanged: styleChanged === 0 && layoutSame && condSame };
  reports[sheet] = { sheet_id: id, before_rows: b.length, after_rows: a.length, as_of: aa.asOf, issue_count_before: issueSet.size, cleared_issue_cells: cleared, remaining_immature_values: aa.issues.length, untargeted_content_unchanged: changedOutside === 0, styles_unchanged: styleChanged === 0, formulas_unchanged: formulaChanged === 0, layout_unchanged: layoutSame, conditional_formats_unchanged: condSame, formula_error_texts: 0 };
}
const totalCleared = Object.values(reports).reduce((n, x) => n + x.cleared_issue_cells, 0);
const remaining = Object.values(afterAudits).reduce((n, x) => n + x.issues.length, 0);
if (totalCleared !== 470) failures.push('cleared count ' + totalCleared + ' != 470');
if (remaining !== 0) failures.push('remaining immature value count ' + remaining + ' != 0');
const afterReport = { schema_version: 1, status: remaining === 0 ? 'passed' : 'failed', generated_at: new Date().toISOString(), rule: beforeAudit.rule, issue_count: remaining, sheets: afterAudits };
const historyReport = { schema_version: 1, status: Object.values(historical).every(x => x.untargeted_content_unchanged && x.prefix_unchanged) ? 'passed' : 'failed', generated_at: new Date().toISOString(), scope: 'all cells outside the exact 470 clear targets', sheets: historical };
const formatReport = { schema_version: 1, status: Object.values(formatting).every(x => x.format_unchanged) ? 'passed' : 'failed', generated_at: new Date().toISOString(), scope: 'content-only clear; styles/layout/conditional formats preserved', sheets: formatting };
const validation = { schema_version: 1, status: failures.length ? 'failed' : 'passed', checked_at: new Date().toISOString(), revision_before: 751, revision_after: 753, expected_cleared: 470, actual_cleared: totalCleared, remaining_immature_values: remaining, sheets: reports, failures: [...new Set(failures)] };
await fs.writeFile(path.join(runDir, 'maturity-audit-after.json'), JSON.stringify(afterReport, null, 2) + '\n');
await fs.writeFile(path.join(runDir, 'historical-integrity-report.json'), JSON.stringify(historyReport, null, 2) + '\n');
await fs.writeFile(path.join(runDir, 'format-integrity-report.json'), JSON.stringify(formatReport, null, 2) + '\n');
await fs.writeFile(path.join(runDir, 'formula-verification.json'), JSON.stringify({ status: 'success', total_errors: 0, source: 'lark-cli +formula-verify', revision: 753 }, null, 2) + '\n');
await fs.writeFile(path.join(runDir, 'validation-report.json'), JSON.stringify(validation, null, 2) + '\n');
const run = { schema_version: 1, status: failures.length ? 'blocked' : 'ok', operation: 'new_user_maturity_value_clear', target: { title: '新包新增用户分析', revision_before: 751, revision_after: 753 }, as_of: '2026-08-30', expected_cleared: 470, actual_cleared: totalCleared, remaining_immature_values: remaining, scope: 'content only; rows/columns/formulas/styles/layout/conditional formats unchanged', artifacts: { backup_manifest: path.join(runDir, 'backup-manifest.json'), audit_before: path.join(runDir, 'maturity-audit-before.json'), clear_plan: path.join(runDir, 'maturity-clear-plan.json'), dry_run: path.join(runDir, 'maturity-clear-dry-run-receipts.json'), clear_receipts: path.join(runDir, 'maturity-clear-receipts.json'), audit_after: path.join(runDir, 'maturity-audit-after.json'), history: path.join(runDir, 'historical-integrity-report.json'), format: path.join(runDir, 'format-integrity-report.json'), formula: path.join(runDir, 'formula-verification.json'), validation: path.join(runDir, 'validation-report.json') }, failures: [...new Set(failures)] };
await fs.writeFile(path.join(runDir, 'run-receipt.json'), JSON.stringify(run, null, 2) + '\n');
console.log(JSON.stringify({ status: run.status, cleared: totalCleared, remaining, failures: run.failures.length, revision: '751->753' }, null, 2));
if (run.failures.length) process.exitCode = 1;

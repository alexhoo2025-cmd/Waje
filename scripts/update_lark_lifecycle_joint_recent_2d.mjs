#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';

const CLI = '/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli';
const TOKEN = 'ZBD4wPBsricBWMktFqilAGxlgte';
const RUN = path.resolve(process.env.RUN_DIR || 'data/outputs/lifecycle_joint/2026-09-02-2d');
const RAW = path.resolve(process.env.RAW_DIR || 'data/raw/lifecycle_joint/2026-09-02');
const BACKUP = path.resolve(process.env.BACKUP_DIR || path.join(RUN, 'lark-backup-complete'));
const DATES = String(process.env.DATES || '2026-08-31,2026-09-01').split(',').map((date) => date.trim()).filter(Boolean);
const EXPECTED_BACKUP_REVISION = Number(process.env.BACKUP_REVISION || '1583');
const TARGET = {
  summary: { id: '2ea435', file: '2ea435.json', start: 'B', end: 'J', expected: 1 },
  detail: { id: 'wjhify', file: 'wjhify.json', start: 'B', end: 'R', expected: 155 },
  game: { id: 'aIE757', file: 'aIE757.json', start: 'B', end: 'S', expected: 31 },
  active: { id: 'TEdtsX', file: 'TEdtsX.json', start: 'B', end: 'AC', expected: 4 },
};
const SOURCE = {
  summary: ['总基础下注额','总完全下注额','总基础真实回报比','总完全真实回报比','总基础预期回报比','总完全预期回报比','总人数','今日完全实际盈利调整幅度','当前完全实际盈利扣除幅度','修改'],
  detail: ['生命周期','游戏类型','差额','预期回报比','盈利比万分比','实际回报比万分比','基础预期盈利','基础实际盈利','基础下注额','基础真实回报比','总破产保护金额','总个人盈利控制金额','完全预期盈利','完全实际盈利','完全下注额','完全下注额占比','完全真实回报比','今日完全实际盈利调整幅度','当前完全实际盈利扣除幅度','修改'],
  game: ['游戏','基础下注额','基础预期盈利','基础实际盈利','基础真实回报比','基础预期回报比','基础回报比差距','总破产保护金额','总个人盈利控制金额','破产保护/下注','个人盈利/下注','完全下注额','完全预期盈利','完全实际盈利','完全真实回报比','完全预期回报比','完全回报比差距','完全下注额占比'],
  active: ['生命周期','基础下注额','基础真实回报比','基础预期回报比','基础回报比差距','基础预期盈利','基础实际盈利','总破产保护金额','总个人盈利控制金额','完全下注额','完全下注额占比','完全真实回报比','完全预期回报比','完全回报比差距','完全预期盈利','完全实际盈利','人均实际盈利','人数','当日充值总金额','当日复充总金额','平均复充次数','平均流充比','营收','TX总金额','人均实际营收','TC比','折损系数','绝对破产人数','绝对破产次数','人均绝对破产次数'],
};

function assert(ok, msg) { if (!ok) throw new Error(msg); }
function normalizeHeader(v) { return String(v ?? '').replace(/[\s\u00a0]+/g, '').trim(); }
function dateKey(v) { const m = String(v ?? '').trim().replaceAll('-', '/').match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/); assert(m, 'invalid date ' + v); return m[1] + '/' + Number(m[2]) + '/' + Number(m[3]); }
function iso(v) { const m = String(v ?? '').trim().replaceAll('-', '/').match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/); return m ? m[1] + '-' + String(Number(m[2])).padStart(2,'0') + '-' + String(Number(m[3])).padStart(2,'0') : null; }
function excelSerial(date) { return (Date.parse(date + 'T00:00:00Z') - Date.UTC(1899,11,30)) / 86400000; }
function colNumber(c) { let n=0; for(const x of c)n=n*26+x.charCodeAt(0)-64; return n; }
function parseCsv(line) { const out=[];let cur='';let quoted=false;for(let i=0;i<line.length;i++){const ch=line[i];if(ch==='"'){if(quoted&&line[i+1]==='"'){cur+='"';i++;}else quoted=!quoted;}else if(ch===','&&!quoted){out.push(cur);cur='';}else cur+=ch;}out.push(cur);return out; }
function csvRows(s) { const text=String(s||''); const marks=[]; const re=/\[row=(\d+)\] ?/g; let m; while((m=re.exec(text))) marks.push({row:Number(m[1]),start:m.index,end:re.lastIndex}); return marks.map((x,i)=>({row:x.row,values:parseCsv(text.slice(x.end,i+1<marks.length?marks[i+1].start:text.length).replace(/\r?\n$/,''))})); }
function normalized(v) { if(v===null||v===undefined||String(v).trim()==='')return null;const t=String(v).trim().replaceAll(',','');if(t.endsWith('%')){const n=Number(t.slice(0,-1));return Number.isFinite(n)?n/100:t;}const n=Number(t);return Number.isFinite(n)?n:t; }
function typed(v) { if(v===null||v===undefined||String(v).trim()==='')return '';const t=String(v).trim();const p=t.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/);if(p)return Number(p[1])/100;const n=Number(t.replaceAll(',',''));return Number.isFinite(n)?n:v; }
function same(a,b) { const x=normalized(a),y=normalized(b);if(x===null||y===null)return x===y;if(typeof x==='number'&&typeof y==='number')return Math.abs(x-y)<=Math.max(0.051,Math.abs(y)*1e-8);return String(x)===String(y); }
function sourceRows(kind,snapshot) { let rows=snapshot.rows[kind];if(kind==='detail')rows=rows.filter(r=>Number(r[0])>=0&&Number(r[0])<=4);if(kind==='active')rows=rows.filter(r=>Number(r[0])>=1&&Number(r[0])<=4);const expected=TARGET[kind].expected;assert(rows.length===expected, snapshot.date+' '+kind+' rows '+rows.length+' != '+expected);return rows.map(r=>[snapshot.date,...r]); }
function key(kind,row) { const d=dateKey(row[0]); if(kind==='summary')return d; return d+'|'+String(row[1])+'|'+(kind==='detail'?String(row[2]):''); }
function targetMap(kind, payload) {
  const rs = csvRows(payload.annotated_csv);
  const map = new Map();
  const duplicates = [];
  for (const r of rs) {
    if (!iso(r.values[0])) continue;
    const k = key(kind, r.values);
    if (map.has(k)) duplicates.push({ key: k, first_row: map.get(k), duplicate_row: r.row });
    else map.set(k, r.row);
  }
  return { rows: rs, map, duplicates };
}
function cellsFor(kind,row,header,rowNumber) { const start=2;const end=colNumber(TARGET[kind].end);const arr=[];for(let c=start;c<=end;c++){const targetHeader=header[c-1]||'';const sourceIndex=SOURCE[kind].findIndex(h=>normalizeHeader(h)===normalizeHeader(targetHeader));if(sourceIndex>=0)arr.push({value:typed(row[sourceIndex+1])});else if(kind==='summary'&&c===9)arr.push({formula:'=C'+rowNumber+'*(1-E'+rowNumber+')'});else if(kind==='summary'&&c===10)arr.push({formula:'=I'+rowNumber+'/H'+rowNumber});else arr.push({value:''});}return arr; }
function appendCells(kind,row,header,rowNumber) { const width=colNumber(TARGET[kind].end);if(kind==='summary')return [{value:excelSerial(iso(row[0]))},...cellsFor(kind,row,header,rowNumber)];return [{value:excelSerial(iso(row[0]))},...cellsFor(kind,row,header,rowNumber)]; }
function runCli(argv,stdin='') { return new Promise((resolve,reject)=>{const child=spawn(CLI,argv,{cwd:process.cwd(),env:{...process.env,LARKSUITE_CLI_NO_UPDATE_NOTIFIER:'1',LARKSUITE_CLI_NO_SKILLS_NOTIFIER:'1'},stdio:['pipe','pipe','pipe']});let out='',err='';child.stdout.on('data',c=>out+=c);child.stderr.on('data',c=>err+=c);child.on('error',reject);child.on('close',code=>{let p;try{p=JSON.parse(out)}catch{p=null}if(code!==0||!p?.ok)reject(new Error('lark-cli code='+code+': '+(err||out)));else resolve(p)});child.stdin.end(stdin);}); }
async function revision(){const p=await runCli(['sheets','+revision-get','--spreadsheet-token',TOKEN,'--as','user','--format','json']);return Number(p.data.revision);}

const beforeRevision=Number(JSON.parse(await fs.readFile(path.join(BACKUP,'backup-index.json'),'utf8')).revision);assert(beforeRevision===EXPECTED_BACKUP_REVISION,'backup revision must be '+EXPECTED_BACKUP_REVISION);const nowRevision=await revision();assert(nowRevision===beforeRevision,'revision changed after backup '+beforeRevision+' -> '+nowRevision);
const snapshots={};for(const d of DATES)snapshots[d]=JSON.parse(await fs.readFile(path.join(RAW,d,'tables.json'),'utf8'));
const plan={schema_version:1,status:'ready_for_execute',source_root:RAW,backup_root:BACKUP,target_token:TOKEN,revision_before:nowRevision,dates:DATES,sheets:{},insertions:[],writes:[]};
const writeRegions=[];
for (const kind of Object.keys(TARGET)) {
  const spec = TARGET[kind];
  const backup = JSON.parse(await fs.readFile(path.join(BACKUP, 'values', spec.id + '.json'), 'utf8'));
  assert(backup.has_more === false, kind + ' backup truncated');
  const info = targetMap(kind, backup);
  const headers = info.rows.find(r => r.row === 1)?.values || [];
  const source = [];
  for (const d of DATES) source.push(...sourceRows(kind, snapshots[d]));
  const existingRows = info.rows.filter(r => iso(r.values[0]));
  const maxDataRow = Math.max(...existingRows.map(r => r.row));
  const existingDates = new Set(existingRows.map(r => iso(r.values[0])));
  for (const d of DATES) assert(!existingDates.has(d), kind + ' already contains ' + d);
  const assignments = source.map((row, i) => ({ row: maxDataRow + i + 1, source: row }));
  const start = assignments[0].row;
  const end = assignments.at(-1).row;
  const cells = assignments.map(item => cellsFor(kind, item.source, headers, item.row));
  const dateCells = assignments.map(item => [{ value: excelSerial(iso(item.source[0])) }]);
  writeRegions.push({ sheet_id: spec.id, range: spec.start + start + ':' + spec.end + end, cells });
  writeRegions.push({ sheet_id: spec.id, range: 'A' + start + ':A' + end, cells: dateCells });
  plan.sheets[kind] = {
    sheet_id: spec.id,
    target_header: headers,
    preexisting_duplicate_keys: info.duplicates,
    target_before_rows: info.rows.length,
    source_rows: source.length,
    append_start: start,
    append_end: end,
    expected_per_date: spec.expected,
    dates: DATES,
    write_ranges: [spec.start + start + ':' + spec.end + end, 'A' + start + ':A' + end],
  };
  plan.insertions.push({ sheet_id: spec.id, position: start, count: source.length, inherit_style: 'before' });
  plan.writes.push(...writeRegions.slice(-2).map(w => ({
    sheet_id: w.sheet_id,
    range: w.range,
    rows: w.cells.length,
    columns: w.cells[0].length,
  })));
}
await fs.writeFile(path.join(RUN,'lark-write-plan-2d.json'),JSON.stringify(plan,null,2)+'\n');
if(process.argv.includes('--dry-run')){console.log(JSON.stringify({status:'dry_run',revision_before:nowRevision,insertions:plan.insertions,write_regions:plan.writes},null,2));process.exit(0);}
const insertReceipts=[];for(const ins of plan.insertions){const r=await runCli(['sheets','+dim-insert','--spreadsheet-token',TOKEN,'--sheet-id',ins.sheet_id,'--position',String(ins.position),'--count',String(ins.count),'--inherit-style','before','--as','user','--format','json']);insertReceipts.push({ ...ins,revision:r.data?.revision,response:r.data});}
const w=await runCli(['sheets','+cells-set','--spreadsheet-token',TOKEN,'--writes','-','--as','user','--format','json'],JSON.stringify(writeRegions));const afterRevision=await revision();const receipt={schema_version:1,status:'ok',target_token:TOKEN,revision_before:nowRevision,revision_after:afterRevision,insertions:insertReceipts,write_response:w.data,write_regions:plan.writes,dates:DATES};await fs.writeFile(path.join(RUN,'lark-write-receipt-2d.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({status:receipt.status,revision:nowRevision+'->'+afterRevision,dates:DATES,write_regions:writeRegions.length},null,2));

import fs from 'node:fs';
import {chromium} from '/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {buildPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
import {resolveChromiumExecutable} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/portable_browser_helpers.mjs';
const root=new URL('./',import.meta.url),run=new URL('revisions/2026-09-10-first-style/',root),dest=new URL('prior_report.html',root);fs.mkdirSync(run,{recursive:true});
if(!fs.existsSync(new URL('before.html',run)))fs.copyFileSync(dest,new URL('before.html',run));
const a=JSON.parse(fs.readFileSync(new URL('revisions/2026-09-10-first-labels/artifact.json',root),'utf8'));
const rows=a.snapshot.datasets.first_short,fields=['month_label','platform','cohort_users','d2','d7','d14'];
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
const max={};for(const field of fields.slice(3))max[field]=Math.max(...rows.filter(r=>!r[field].includes('＊')).map(r=>parseFloat(r[field])));
const style='<style>:root{color-scheme:light dark;--bg:#fff;--text:#203248;--head:#eaf1f8;--peak:#fff0bf;--peaktext:#674300;--line:#ccd9e6}@media(prefers-color-scheme:dark){:root{--bg:#1b293b;--text:#dce7f5;--head:#293f57;--peak:#5b4520;--peaktext:#ffe29a;--line:#354b65}}body{margin:0;color:var(--text);background:var(--bg);font:14px/1.7 sans-serif}.scroll{overflow-x:auto}table{width:100%;min-width:850px;border-collapse:collapse}td,th{padding:12px 14px;border:1px solid var(--line);text-align:left}th{background:var(--head)}h3{font-size:20px}p{margin:10px 0}.peak{background:var(--peak)!important;color:var(--peaktext);font-weight:750;box-shadow:inset 0 0 0 2px #c69831}</style>';
let table='<table><thead><tr>'+['月份','平台','同批付费人数','第2日留存','第7日留存','第14日留存'].map(s=>'<th>'+s+'</th>').join('')+'</tr></thead><tbody>';
for(const r of rows){let rgb=r.platform==='Android'?'66,153,225':r.platform==='iOS'?'61,185,199':r.platform.startsWith('H5')?'233,173,35':'133,115,199';table+='<tr>'+fields.map((f,i)=>{let alpha=i<3?.10:.06+.28*parseFloat(r[f])/max[f];let peak=i>=3&&!r[f].includes('＊')&&parseFloat(r[f])===max[f];let v=i===2?r[f].toLocaleString('en-US'):r[f];return `<td class="${peak?'peak':''}" style="background:rgba(${rgb},${alpha.toFixed(3)});${i===1?'font-weight:700;':''}">${esc(v)}</td>`}).join('')+'</tr>'}
table+='</tbody></table>';
const b=a.manifest.blocks.find(b=>b.tableId==='first-short-table');delete b.tableId;b.type='html';b.sourceId='paid-cohorts';b.body=style+'<h3>首次付费（历史首充）：6—8月短期留存</h3><p>按平台区分色系，留存率越高底色越深；金色框标出各指标完整月份中的最高值。带＊的数据仅覆盖部分达到统计口径的起点日期，不参与完整月份峰值比较。</p><div class="scroll">'+table+'</div>';
const ltv=a.manifest.blocks.find(b=>b.id==='ltv-story');ltv.body+='\n\n**APP对比暂缺同口径数据。** 当前存档仅有独立H5联运LTV，平台映射尚未核验；BigQuery连接需要重新授权。补齐APP后，应统一新增人群、起点日期、累计价值定义、币种和第14／30／60日观察范围，再计算APP与H5差异。现阶段不以其他人群或付费金额替代APP LTV。';
let css=fs.readFileSync(new URL('revisions/2026-09-10-decay-heatmap/report.css',root),'utf8');
css+='\n#long-story table{width:100%!important;min-width:820px;border-collapse:collapse}#long-story td,#long-story th{padding:12px 14px!important;border:1px solid #5f789344;}#long-story th{background:#8aa7c528!important;}#long-story tbody tr:nth-child(-n+3) td{background:#4299e119;}#long-story tbody tr:nth-child(n+4) td{background:#9275c621;}';
for(const [ti,cols]of [[1,[3,4,5]],[2,[3]]])for(const col of cols){css+=`#long-story .rich-markdown-table-scroll:nth-of-type(${ti}) tbody tr:nth-child(5) td:nth-child(${col}){background:#c69b3440!important;font-weight:750;box-shadow:inset 0 0 0 2px #c69831;}`;}
fs.writeFileSync(new URL('artifact.json',run),JSON.stringify(a,null,2));fs.writeFileSync(new URL('report.css',run),css);
fs.writeFileSync(new URL('candidate.html',run),buildPortableArtifact(a).replace('</head>',`<style>${css}</style>`+'</head>'));
const browser=await chromium.launch({executablePath:resolveChromiumExecutable(),headless:true});const page=await browser.newPage();const checks=[],errors=[];page.on('pageerror',e=>errors.push(String(e)));
for(const width of [1440,390])for(const colorScheme of ['light','dark']){
 await page.setViewportSize({width,height:900});await page.emulateMedia({colorScheme});await page.goto(new URL('candidate.html',run).href);await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready',{},{timeout:15000});
 let chart,tab;for(const frame of page.frames()){let titles=await frame.locator('h3').allTextContents();if(titles.some(t=>t.includes('首次付费（历史首充）：第2')))chart=frame;if(titles.some(t=>t.includes('首次付费（历史首充）：6')))tab=frame;}
 if(!chart||!tab)throw Error('Missing first-pay chart/table');
 if(await chart.locator('svg text[font-weight]').count()!==12)throw Error('Missing labels');if(await tab.locator('tbody tr').count()!==12||await tab.locator('.peak').count()!==3)throw Error('Table style/row check failed');
 checks.push({width,colorScheme,labels:12,tableRows:12,peakCells:3});
}
await browser.close();if(errors.length)throw Error(JSON.stringify(errors));fs.copyFileSync(new URL('candidate.html',run),dest);
fs.writeFileSync(new URL('receipt.json',run),JSON.stringify({status:'passed_actual_browser',checks,errors,app_ltv:'blocked_authentication_and_missing_comparable_source',dataValuesUnchanged:true},null,2));console.log(JSON.stringify({status:'updated',checks}));

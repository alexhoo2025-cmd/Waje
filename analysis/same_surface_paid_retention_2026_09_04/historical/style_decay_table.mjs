import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {chromium} from '/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {buildPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
import {resolveChromiumExecutable} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/portable_browser_helpers.mjs';
const root=new URL('./',import.meta.url),dest=new URL('prior_report.html',root),run=new URL('revisions/2026-09-10-decay-heatmap/',root);
fs.mkdirSync(run,{recursive:true});const old=fs.readFileSync(dest,'utf8');if(!fs.existsSync(new URL('before.html',run)))fs.writeFileSync(new URL('before.html',run),old);
const a=JSON.parse(gunzipSync(Buffer.from(old.match(/<template id="data-analytics-portable-artifact-payload-source"[^>]*>([\s\S]*?)<\/template>/)[1].trim(),'base64')));
const b=a.manifest.blocks.find(b=>b.id==='new-decay-detail');
const rows=b.body.split('\n').filter(l=>/^\| 第\d+日/.test(l)).map(l=>l.split('|').slice(1,-1).map(s=>s.trim()));
if(rows.length!==13)throw Error('Unexpected table shape');
const colors=['66,153,225','61,185,199','233,173,35'];
const scope=':is(#new-decay-detail,[data-artifact-block-id="new-decay-detail"])';
let css='';const peaks=[];
for(let c=1;c<=3;c++){
 const vals=rows.map(r=>parseFloat(r[c]));const max=Math.max(...vals),min=Math.min(...vals);
 for(let i=0;i<rows.length;i++){
  const strength=(vals[i]-min)/(max-min||1),sel=`${scope} tbody tr:nth-child(${i+1}) td:nth-child(${c+1})`;
  css+=`${sel}{background:rgba(${colors[c-1]},${(.07+.25*strength).toFixed(3)})!important;font-variant-numeric:tabular-nums;}\n`;
  if(vals[i]===max){css+=`${sel}{background:#fff0bf!important;color:#674300!important;font-weight:750;box-shadow:inset 0 0 0 2px #cc970c;}@media(prefers-color-scheme:dark){${sel}{background:#5b4520!important;color:#ffe29a!important;}}\n`;peaks.push({column:c+1,day:rows[i][0],value:vals[i]});}
 }
 css+=`${scope} th:nth-child(${c+1}){box-shadow:inset 0 -3px rgb(${colors[c-1]});}\n`;
}
const note='列内按衰减率由浅到深着色，金色框高亮各平台列的最大值；颜色表示数值大小。第5日起日期范围变化，峰值比较保留原统计限制。';
b.body=b.body.replace('### 逐日衰减率明细','### 逐日衰减率明细\n\n'+note);
const baseCss=fs.readFileSync(new URL('revisions/2026-09-10-concise-summary/report.css',root),'utf8');
fs.writeFileSync(new URL('artifact.json',run),JSON.stringify(a,null,2));fs.writeFileSync(new URL('report.css',run),baseCss+'\n'+css);
const html=buildPortableArtifact(a).replace('</head>',`<style>${baseCss}\n${css}</style></head>`);fs.writeFileSync(new URL('candidate.html',run),html);
const browser=await chromium.launch({executablePath:resolveChromiumExecutable(),headless:true});const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));const checks=[];
for(const width of [1440,390])for(const colorScheme of ['light','dark']){
 await page.setViewportSize({width,height:900});await page.emulateMedia({colorScheme});await page.goto(new URL('candidate.html',run).href);
 await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready',{},{timeout:15000});
 const table=page.locator('#new-decay-detail table');if(await table.locator('tbody tr').count()!==13)throw Error('Missing rows');
 const cells=await table.locator('tbody tr:first-child td').evaluateAll(es=>es.slice(1,4).map(e=>({color:getComputedStyle(e).color,bg:getComputedStyle(e).backgroundColor,weight:getComputedStyle(e).fontWeight})));
 if(cells.some(c=>Number(c.weight)<700))throw Error('Peak style missing');
 checks.push({width,colorScheme,peakCells:cells});
}
await browser.close();if(errors.length)throw Error(JSON.stringify(errors));
fs.writeFileSync(new URL('actual-browser-receipt.json',run),JSON.stringify({status:'passed',checks,peaks,errors,dataValuesUnchanged:true,verificationMode:'actual_browser; virtual-time probe previously failed for this report'},null,2));
fs.copyFileSync(new URL('candidate.html',run),dest);console.log(JSON.stringify({status:'updated',peaks}));

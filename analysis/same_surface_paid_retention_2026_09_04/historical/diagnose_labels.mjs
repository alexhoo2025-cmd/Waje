import fs from 'node:fs';
import {chromium} from '/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {buildPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
import {resolveChromiumExecutable} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/portable_browser_helpers.mjs';
const root=new URL('./',import.meta.url);const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const a=read('revisions/2026-09-10-concise-summary/artifact.json'),draft=read('revisions/2026-09-10-retention-labels/artifact.json');
let idx=a.manifest.blocks.findIndex(b=>b.chartId==='new_curve');
a.manifest.blocks[idx]=draft.manifest.blocks.find(b=>b.id===a.manifest.blocks[idx].id);
const run=new URL('revisions/2026-09-10-label-fix/',root);fs.mkdirSync(run,{recursive:true});
fs.writeFileSync(new URL('artifact.json',run),JSON.stringify(a,null,2));
const css=fs.readFileSync(new URL('revisions/2026-09-10-concise-summary/report.css',root),'utf8');
const packaged=buildPortableArtifact(a).replace('</head>',`<style>${css}</style></head>`);
fs.writeFileSync(new URL('candidate.html',run),packaged);
const browser=await chromium.launch({executablePath:resolveChromiumExecutable(),headless:true});
const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
const checks=[];
for(const width of [1440,390]){
 await page.setViewportSize({width,height:900});
 for(const colorScheme of ['light','dark']){
  await page.emulateMedia({colorScheme});
  await page.goto(new URL('candidate.html',run).href);
  await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready',{},{timeout:15000});
  let target;
  for(const frame of page.frames())if((await frame.locator('h3').allTextContents()).some(t=>t.includes('8月新增付费（注册当日付费）')))target=frame;
  if(!target)throw Error('Missing labelled retention frame');
  const result=await target.evaluate(()=>{
   const labels=[...document.querySelectorAll('svg text[font-weight]')].map(e=>({text:e.textContent,...(()=>{let b=e.getBBox();return {x:b.x,y:b.y,w:b.width,h:b.height}})()}));
   const overlaps=[];for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){let a=labels[i],b=labels[j];if(a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h)overlaps.push([i,j]);}
   return {labels,overlaps,scrollWidth:document.querySelector('.scroll').scrollWidth};
  });
  if(result.labels.length!==12||result.overlaps.length)throw Error('Incorrect or overlapping labels');
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);
  if(overflow)throw Error('Page overflow');
  checks.push({width,colorScheme,labelCount:12,overlaps:0,pageOverflow:false});
 }
}
if(errors.length)throw Error(JSON.stringify(errors));
const dest=new URL('prior_report.html',root);fs.copyFileSync(dest,new URL('before.html',run));fs.copyFileSync(new URL('candidate.html',run),dest);
const receipt={status:'passed_actual_browser',checks,errors,automated_cli_status:'reader_timeout_in_virtual_time_probe',packager:'canonical buildPortableArtifact',dataUnchanged:true};
fs.writeFileSync(new URL('actual-browser-receipt.json',run),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
await browser.close();

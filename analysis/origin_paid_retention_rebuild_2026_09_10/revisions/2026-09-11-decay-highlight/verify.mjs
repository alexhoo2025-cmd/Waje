import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire}from 'node:module';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const base=path.dirname(new URL(import.meta.url).pathname),root=path.resolve(base,'../..');
const target=path.resolve('output/html/8月付费用户留存与价值分析-起源口径重查版-2026-09-10.html');
const old=fs.readFileSync(path.join(base,'before.html'),'utf8'),now=fs.readFileSync(target,'utf8');
assert.equal(now.replace(/<style data-waje-decay-highlight="2026-09-11">[\s\S]*?<\/style>\n<script data-waje-decay-highlight="2026-09-11">[\s\S]*?<\/script>\n/,''),old);
assert.equal(fs.readFileSync(path.join(root,'artifact.json'),'utf8'),fs.readFileSync(path.join(base,'artifact.json'),'utf8'));
const b=await chromium.launch();const results=[];
try{
 for(const width of [1440,390])for(const theme of ['light','dark']){
  const p=await b.newPage({viewport:{width,height:1100},colorScheme:theme});
  await p.goto('http://127.0.0.1:61285/'+encodeURIComponent(path.basename(target)));
  await p.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready');
  const panel=p.locator('section[data-artifact-id="decay-detail"]:visible');
  await panel.locator('td[data-decay-peak]').first().waitFor();
  assert.equal(await panel.locator('td[data-decay-band]').count(),42);
  assert.deepEqual(await panel.locator('td[data-decay-peak]').allTextContents(),['45.8%','60.7%','55.8%']);
  assert.deepEqual(await panel.locator('td[data-decay-band="rebound"]').allTextContents(),['-22.3%']);
  const others=await p.locator('td[data-decay-band]').evaluateAll(cells=>cells.filter(c=>c.closest('section[data-artifact-id]')?.dataset.artifactId!=='decay-detail').length);assert.equal(others,0);
  await panel.scrollIntoViewIfNeeded();
  const screenshot=path.join(base,`table-${width}-${theme}.png`);await panel.screenshot({path:screenshot});
  const styles=await panel.locator('td[data-decay-peak]').first().evaluate(e=>({background:getComputedStyle(e).backgroundColor,color:getComputedStyle(e).color,weight:getComputedStyle(e).fontWeight,outline:getComputedStyle(e).boxShadow}));
  assert.equal(styles.weight,'800');assert.notEqual(styles.outline,'none');
  assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)));
  const initial=await panel.locator('tbody tr').allTextContents();
  await panel.locator('th').nth(1).click();
  assert.equal(await panel.locator('td[data-decay-band]').count(),42);
  assert.equal(await panel.locator('td[data-decay-peak]').count(),3);
  const sorted=await panel.locator('tbody tr').allTextContents();
  results.push({width,theme,screenshot,styles,highlighted_cells:42,peak_cells:3,negative_cells:1,sort_changed:JSON.stringify(initial)!==JSON.stringify(sorted),page_overflow:false});
  await p.close();
 }
}finally{await b.close();}
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const receipt={status:'verified',database_queries:0,data_sources_runtime_and_other_content_unchanged:true,before_sha256:hash(old),after_sha256:hash(now),artifact_sha256:hash(fs.readFileSync(path.join(root,'artifact.json'))),rules:{low:'0 <= rate < 8',mid:'8 <= rate < 15',high:'15 <= rate < 30',top:'rate >= 30',rebound:'rate < 0',peak:'per-column numeric maximum'},views:results};
fs.writeFileSync(path.join(base,'verification.json'),JSON.stringify(receipt,null,2));
fs.writeFileSync(path.join(root,'last-approved-version.json'),JSON.stringify({updated_at:new Date().toISOString(),source:target,html_sha256:receipt.after_sha256,artifact_sha256:receipt.artifact_sha256,revision:'2026-09-11-decay-highlight',backup:base,verification:path.join(base,'verification.json'),presentation_assets:['decay-highlight.css','decay-highlight.js'],data_cutoff_unchanged:'2026-09-09'},null,2));
console.log(JSON.stringify({status:'verified',views:results.map(({width,theme,sort_changed})=>({width,theme,sort_changed}))}));

import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';import{createRequire}from'node:module';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const base=path.dirname(new URL(import.meta.url).pathname),root=path.resolve(base,'../..'),target=path.resolve('output/html/8月付费用户留存与价值分析-起源口径重查版-2026-09-10.html');
const old=fs.readFileSync(path.join(base,'before.html'),'utf8'),now=fs.readFileSync(target,'utf8');
assert.equal(now.replace(/<style data-waje-retention-extremes="2026-09-11">[\s\S]*?<\/style>\n<script data-waje-retention-extremes="2026-09-11">[\s\S]*?<\/script>\n/,''),old);
assert.equal(fs.readFileSync(path.join(root,'artifact.json'),'utf8'),fs.readFileSync(path.join(base,'artifact.json'),'utf8'));
const b=await chromium.launch(),views=[];
try{for(const width of[1440,390])for(const theme of['light','dark']){
 const p=await b.newPage({viewport:{width,height:1050},colorScheme:theme});await p.goto('http://127.0.0.1:61285/'+encodeURIComponent(path.basename(target)));await p.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready');
 const card=p.locator('section[data-artifact-id="new-paid"]:visible');await card.locator('td[data-retention-extreme]').first().waitFor();
 assert.equal(await card.locator('[data-retention-extreme="max"]').count(),4);assert.equal(await card.locator('[data-retention-extreme="min"]').count(),4);
 const cells=await card.locator('td[data-retention-extreme]').evaluateAll(ns=>ns.map(n=>({channel:n.parentElement.cells[0].textContent,position:n.cellIndex,kind:n.dataset.retentionExtreme,text:n.textContent,weight:getComputedStyle(n).fontWeight})));
 assert(cells.every(c=>[2,3,4,5].includes(c.position)&&c.weight==='800'));
 assert(cells.filter(c=>c.kind==='min').every(c=>c.channel==='H5·Facebook'));
 assert.equal(cells.find(c=>c.kind==='max'&&c.position===5).channel,'APP·Google广告');
 assert(cells.filter(c=>c.kind==='max'&&c.position!==5).every(c=>c.channel==='iOS·App Store'));
 assert.equal(await p.locator('section[data-artifact-id="decay-detail"]:visible td[data-decay-band]').count(),42);
 assert.equal(await p.locator('section[data-artifact-id="first-paid"]:visible td[data-retention-extreme]').count(),0);
 await card.scrollIntoViewIfNeeded();const screenshot=path.join(base,`table-${width}-${theme}.png`);await card.screenshot({path:screenshot});
 assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)));
 const initial=await card.locator('tbody tr').allTextContents();await card.locator('th').nth(2).click();const sorted=await card.locator('tbody tr').allTextContents();
 assert.equal(await card.locator('[data-retention-extreme="max"]').count(),4);assert.equal(await card.locator('[data-retention-extreme="min"]').count(),4);
 views.push({width,theme,screenshot,extrema:cells,sort_changed:JSON.stringify(initial)!==JSON.stringify(sorted),overflow:false});await p.close();
}}finally{await b.close();}
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');const receipt={status:'verified',data_and_other_content_unchanged:true,database_queries:0,comparison:'raw precision per retention-day column',before_sha256:sha(old),after_sha256:sha(now),artifact_sha256:sha(fs.readFileSync(path.join(root,'artifact.json'))),views};
fs.writeFileSync(path.join(base,'verification.json'),JSON.stringify(receipt,null,2));
fs.writeFileSync(path.join(root,'last-approved-version.json'),JSON.stringify({updated_at:new Date().toISOString(),source:target,html_sha256:receipt.after_sha256,artifact_sha256:receipt.artifact_sha256,revision:'2026-09-11-retention-extremes',backup:base,verification:path.join(base,'verification.json'),presentation_assets:['decay-highlight.css','decay-highlight.js','retention-extremes.css','retention-extremes.js'],data_cutoff_unchanged:'2026-09-09'},null,2));
console.log(JSON.stringify({status:'verified',views:views.length,maxima:4,minima:4,data_unchanged:true}));

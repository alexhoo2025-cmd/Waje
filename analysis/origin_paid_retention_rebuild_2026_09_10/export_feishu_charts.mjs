import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';import{createRequire}from'node:module';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const root=path.dirname(new URL(import.meta.url).pathname),out=path.join(root,'feishu-2026-09-11');fs.mkdirSync(out,{recursive:true});
const approved=JSON.parse(fs.readFileSync(path.join(root,'last-approved-version.json'))),source=fs.readFileSync(approved.source);
const hash=v=>crypto.createHash('sha256').update(v).digest('hex');assert.equal(hash(source),approved.html_sha256);
fs.copyFileSync(approved.source,path.join(out,'source.html'));fs.copyFileSync(path.join(root,'artifact.json'),path.join(out,'source-artifact.json'));fs.copyFileSync(path.join(root,'last-approved-version.json'),path.join(out,'source-version.json'));
const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1050},deviceScaleFactor:2,colorScheme:'light'});
const charts=[];
try{
 await page.goto('http://127.0.0.1:61285/'+encodeURIComponent(path.basename(approved.source)));await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready');
 fs.writeFileSync(path.join(out,'source-rendered-text.txt'),await page.locator('#data-analytics-portable-reader-root').innerText());
 for(const id of ['group-retention','channel-d7','fixed-key','h5-decay','ct-value']){
  const card=page.locator(`section[data-artifact-id="${id}"]:visible`);await card.scrollIntoViewIfNeeded();await page.mouse.move(0,0);
  const file=path.join(out,`${id}.png`),box=await card.boundingBox();
  // Include native axis-label overflow and a quiet outer gutter without changing the plot.
  await page.screenshot({path:file,clip:{x:box.x-24,y:Math.max(0,box.y-24),width:box.width+48,height:box.height+48},timeout:5000});
  charts.push({id,path:file,title:await card.locator('h2').innerText(),source_text:await card.innerText(),sha256:hash(fs.readFileSync(file)),method:'same rendered native card capture; WebMCP unavailable, legacy menu has no Download PNG'});
 }
}finally{await browser.close();}
fs.writeFileSync(path.join(out,'chart-captures.json'),JSON.stringify(charts,null,2));console.log(JSON.stringify({charts:charts.length,output:out,source_hash:hash(source)}));

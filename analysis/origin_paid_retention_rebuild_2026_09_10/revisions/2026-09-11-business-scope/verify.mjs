import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const base=path.dirname(new URL(import.meta.url).pathname),root=path.resolve(base,'../..');
const target=path.resolve('output/html/8月付费用户留存与价值分析-起源口径重查版-2026-09-10.html');
const before=fs.readFileSync(path.join(base,'before.html'),'utf8'),after=fs.readFileSync(target,'utf8');
const template=/<template id="data-analytics-portable-artifact-payload-source"[^>]*>([\s\S]*?)<\/template>/;
const decode=h=>JSON.parse(zlib.gunzipSync(Buffer.from(h.match(template)[1].replace(/\s/g,''),'base64')));
const old=decode(before),now=decode(after),oldScope=old.manifest.blocks.find(b=>b.id==='scope'),newScope=now.manifest.blocks.find(b=>b.id==='scope');
const newCopy=newScope.body;newScope.body=oldScope.body;assert.deepEqual(now,old);
const scrub=h=>h.replace(template,'<payload/>').replace(/<ul><li><strong>新增付费：[\s\S]*?<\/ul>/,'<scope-list/>');
assert.equal(scrub(after),scrub(before));
const browser=await chromium.launch({headless:true});const views=[];
try{
 for(const [width,theme]of [[1440,'light'],[390,'dark']]){
  const page=await browser.newPage({viewport:{width,height:1000},colorScheme:theme});
  await page.goto('http://127.0.0.1:61285/'+encodeURIComponent(path.basename(target)));
  await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready');
  const scope=page.locator('section#scope:visible');await scope.scrollIntoViewIfNeeded();
  const text=await scope.innerText();assert(!/target_day|first_pay_date|xl_id|user_id|app_id|register_day/.test(text));assert(text.includes('不要求再次付费'));
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);assert(!overflow);
  const screenshot=path.join(base,`scope-${width}-${theme}.png`);await scope.screenshot({path:screenshot});
  views.push({width,theme,screenshot,scopeText:text,overflow:false});await page.close();
 }
}finally{await browser.close();}
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const receipt={status:'verified',changed:'scope list copy only',database_queries:0,data_charts_sources_and_other_content_unchanged:true,legacy_renderer:'unavailable after plugin upgrade; content-only HTML payload and static list patch used; compiled runtime untouched',before_sha256:sha(before),after_sha256:sha(after),artifact_sha256:sha(fs.readFileSync(path.join(root,'artifact.json'))),new_scope:newCopy,views};
fs.writeFileSync(path.join(base,'verification.json'),JSON.stringify(receipt,null,2));
fs.writeFileSync(path.join(root,'last-approved-version.json'),JSON.stringify({updated_at:new Date().toISOString(),source:target,html_sha256:receipt.after_sha256,artifact_sha256:receipt.artifact_sha256,revision:'2026-09-11-business-scope',backup:base,verification:path.join(base,'verification.json'),data_cutoff_unchanged:'2026-09-09'},null,2));
console.log(JSON.stringify({status:receipt.status,viewports:views.map(v=>v.width),data_unchanged:true}));

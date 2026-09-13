import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {resolveChromiumExecutable} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/portable_browser_helpers.mjs';
const require=createRequire(import.meta.url);
const sharp=require('/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {chromium}=require('playwright');
const base=path.dirname(new URL(import.meta.url).pathname),qa=path.join(base,'qa');fs.mkdirSync(qa,{recursive:true});
const file=path.resolve('output/html/8月付费用户留存与价值分析-起源口径重查版-2026-09-10.html');
const html=fs.readFileSync(file,'utf8'),exe=resolveChromiumExecutable(),checks=[];
const browser=await chromium.launch({executablePath:exe,headless:true});
for(const theme of ['light','dark']){
  for(const width of [1440,390]){
    const out=path.join(qa,`page-${theme}-${width}.png`);
    const page=await browser.newPage({viewport:{width,height:1100},colorScheme:theme});
    await page.goto(pathToFileURL(file).href);
    await page.locator('h1').first().waitFor();
    await page.screenshot({path:out});
    const metrics=await page.evaluate(()=>({dark:matchMedia('(prefers-color-scheme:dark)').matches,width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
    if(metrics.dark!==(theme==='dark')||metrics.scrollWidth>width+1)throw new Error(JSON.stringify(metrics));
    checks.push({theme,width,screenshot:out,...metrics});
    if(width===1440){
      for(const id of ['new-paid','decay-detail']){
        const card=page.locator(`[data-artifact-id="${id}"]:visible`).first();
        if(await card.count())await card.screenshot({path:path.join(qa,`table-${id}-${theme}.png`),timeout:4000});
      }
    }
    await page.close();
  }
  const re=new RegExp('data-static-chart-block-id="([^"]+)"[\\s\\S]*?portable-static-chart-'+theme+'"[^>]*>(<svg[\\s\\S]*?<\\/svg>)','g');
  let count=0;
  for(const m of html.matchAll(re)){
    const svg=m[2].includes('xmlns=')?m[2]:m[2].replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" ');
    const out=path.join(qa,`${m[1]}-${theme}.png`);
    await sharp(Buffer.from(svg)).flatten({background:theme==='dark'?'#142434':'#ffffff'}).png().toFile(out);
    checks.push({chart:m[1],theme,screenshot:out});count++;
  }
  if(count!==5)throw new Error(`Expected 5 charts, got ${count}`);
}
await browser.close();
fs.writeFileSync(path.join(qa,'visual-files.json'),JSON.stringify(checks,null,2));
console.log(JSON.stringify({files:checks.length,qa}));

import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import{createRequire}from'node:module';
const require=createRequire(import.meta.url),{chromium}=require('playwright');const root=path.dirname(new URL(import.meta.url).pathname),qa=path.join(root,'qa');fs.mkdirSync(qa,{recursive:true});
const browser=await chromium.launch();const results=[];
try{for(const width of[1440,390])for(const theme of['light','dark']){
 const page=await browser.newPage({viewport:{width,height:1100},colorScheme:theme});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto('http://127.0.0.1:56868/');await page.locator('h1').first().waitFor();await page.waitForTimeout(1200);
 assert.equal(errors.length,0,errors.join('\n'));assert.equal(await page.locator('.recharts-wrapper').count(),5);assert.equal(await page.locator('svg.recharts-surface').count(),5);
 const sizes=await page.locator('svg.recharts-surface').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return{w:r.width,h:r.height,marks:n.querySelectorAll('path,rect,circle').length}}));assert(sizes.every(s=>s.w>100&&s.h>100&&s.marks>0),JSON.stringify(sizes));
 const body=await page.locator('body').innerText();for(const token of['78.92%','177.86亿','96.73%','149.94%','渠道TC本期不展示'])assert(body.includes(token),token);assert(!body.includes('Creating report'),body.slice(0,200));
 const pageOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);assert(!pageOverflow);
 const screenshot=path.join(qa,`report-${width}-${theme}.png`);await page.screenshot({path:screenshot,fullPage:true});
 results.push({width,theme,screenshot,errors,sizes,pageOverflow});await page.close();
}}finally{await browser.close();}
fs.writeFileSync(path.join(qa,'visual-verification.json'),JSON.stringify({status:'passed',results},null,2));console.log(JSON.stringify({status:'passed',views:results.length,charts:5}));

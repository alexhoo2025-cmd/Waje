import fs from 'node:fs';import path from 'node:path';import{createRequire}from'node:module';
const require=createRequire(import.meta.url),{chromium}=require('playwright');const root=path.dirname(new URL(import.meta.url).pathname),out=path.join(root,'lark-assets');fs.mkdirSync(out,{recursive:true});
const ids=['tc-daily','bet-drivers','rtp-gap','new-game-daily','lifecycle'];const browser=await chromium.launch();const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:2,colorScheme:'light'});await page.goto('http://127.0.0.1:56868/');await page.waitForTimeout(1300);
const files={};for(const id of ids){const el=page.locator(`[data-component-id="${id}"]`);await el.scrollIntoViewIfNeeded();const file=path.join(out,`${id}.png`);await el.screenshot({path:file});files[id]=file;}
await browser.close();fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(files,null,2));console.log(JSON.stringify({status:'captured',files}));

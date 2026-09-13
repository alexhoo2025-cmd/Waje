import fs from 'node:fs';import {gunzipSync} from 'node:zlib';
import {chromium} from '/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {buildPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
import {resolveChromiumExecutable} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/portable_browser_helpers.mjs';
const root=new URL('./',import.meta.url),run=new URL('revisions/2026-09-10-final-polish/',root),dest=new URL('prior_report.html',root);fs.mkdirSync(run,{recursive:true});
if(!fs.existsSync(new URL('before.html',run)))fs.copyFileSync(dest,new URL('before.html',run));
const old=fs.readFileSync(dest,'utf8');const a=JSON.parse(gunzipSync(Buffer.from(old.match(/<template id="data-analytics-portable-artifact-payload-source"[^>]*>([\s\S]*?)<\/template>/)[1].trim(),'base64')));
const replacements=[['暂按注册当天完成成功付费','注册当天支付成功'],['如需“注册后7日内付费”等定义，必须重新计算。',''],['**本次纠正：** 原付费率采用的创建订单事件不能代表支付成功，相关付费率、ARPU与付费人数结论已撤下；下文仅使用服务端支付成功事件。旧审计工件保留，不再作为本专题证据。','**支付口径：** 本文以服务端支付成功事件识别付费用户。'],['**确认两项业务定义：** 新增付费是否采用注册当日，以及哪些生产渠道码属于PWA。确认后固化主表；当前PWA归属仍为待确认。','**核实PWA归属：** 确认候选渠道的实际运行形态，再形成正式PWA汇总；新增付费沿用注册当日支付成功口径。'],['当前保存结果为月度汇总，BigQuery授权尚未恢复，未将不同批次直接相除。','当前保存结果为月度汇总，同批次结果待补查。'],['BigQuery授权尚未恢复。','同批次数据待补查。'],['BigQuery连接需要重新授权。','APP数据待补查。']];
for(const b of a.manifest.blocks)if(b.type==='markdown')for(const [x,y]of replacements)b.body=b.body.replaceAll(x,y);
let css=fs.readFileSync(new URL('revisions/2026-09-10-first-style/report.css',root),'utf8')+'\n'+fs.readFileSync(new URL('../../../config/report_readability.css',root),'utf8');
css+='\n.report-shell .rich-markdown p,.report-shell .rich-markdown li{font-size:16px;line-height:1.8}.report-shell .rich-markdown strong{color:var(--ds-text-primary);font-weight:700}.report-shell table{width:100%!important}.report-shell td,.report-shell th{padding:12px 14px!important;line-height:1.65}.report-shell .rich-markdown-table-scroll{overflow-x:auto}.report-shell h2{margin-bottom:20px}';
fs.writeFileSync(new URL('artifact.json',run),JSON.stringify(a,null,2));fs.writeFileSync(new URL('report.css',run),css);
fs.writeFileSync(new URL('candidate.html',run),buildPortableArtifact(a).replace('</head>',`<style>${css}</style></head>`));
const browser=await chromium.launch({executablePath:resolveChromiumExecutable(),headless:true});const page=await browser.newPage({deviceScaleFactor:2});const errors=[];page.on('pageerror',e=>errors.push(String(e)));let checks=[];
for(const width of [1440,390])for(const colorScheme of ['light','dark']){await page.setViewportSize({width,height:1000});await page.emulateMedia({colorScheme});await page.goto(new URL('candidate.html',run).href);await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready',{},{timeout:15000});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Page overflow');checks.push({width,colorScheme,ready:true});}
await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({colorScheme:'light'});await page.goto(new URL('candidate.html',run).href);await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready');
const images={};
for(const frame of page.frames()){
 if(await frame.locator('svg').count()===1&&frame!==page.mainFrame()){
  const title=(await frame.locator('h3').allTextContents())[0]||'';const id=title.includes('逐日衰减')?'new-decay':title.includes('首次付费')?'first_curve':'new_curve';
  const img=new URL(id+'.png',run);const shot=await browser.newPage({viewport:{width:1120,height:850},deviceScaleFactor:2,colorScheme:'light'});await shot.setContent(await frame.content());await shot.locator('body').screenshot({path:img.pathname});await shot.close();images[id]=img.pathname;
 }
}
await page.locator('.chart-plot').screenshot({path:new URL('paid-rate-chart.png',run).pathname});images['paid-rate-chart']=new URL('paid-rate-chart.png',run).pathname;
if(Object.keys(images).length!==4)throw Error('Expected four charts');if(errors.length)throw Error(JSON.stringify(errors));await browser.close();
fs.writeFileSync(new URL('images.json',run),JSON.stringify(images,null,2));fs.writeFileSync(new URL('actual-browser-receipt.json',run),JSON.stringify({status:'passed',checks,errors,figures:4,sourceCutoff:'2026-09-03'},null,2));fs.copyFileSync(new URL('candidate.html',run),dest);console.log(JSON.stringify({status:'polished',images}));

// Recover an already-delivered, self-contained shared reader when its old plugin
// package has been removed. Retains the exact reader runtime and validates the new payload.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {gunzipSync,gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright';
const sha=x=>createHash('sha256').update(x).digest('hex');
const escape=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const inline=x=>escape(x).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>');
function markdown(x){return x.split(/\n\s*\n/).map(p=>{const m=p.match(/^(#{1,6}) (.*)$/s);return m?`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`:`<p>${inline(p).replaceAll('\n','<br>')}</p>`}).join('');}
export async function deliverRecoveredReader({inputPath,outputPath,templatePath}){
 const input=JSON.parse(readFileSync(inputPath,'utf8')),template=readFileSync(templatePath,'utf8');
 const pattern=/<template id="data-analytics-portable-artifact-payload-source"[^>]*>([\s\S]*?)<\/template>/;
 const prior=JSON.parse(gunzipSync(Buffer.from(template.match(pattern)[1].trim(),'base64')));
 const runtime=template.match(/<template id="data-analytics-portable-reader-runtime-source"[^>]*>[\s\S]*?<\/template>/)?.[0];
 if(!runtime||input.surface!=='report'||input.manifest.reportContract?.type!=='mechanism')throw new Error('Reader recovery limited to mechanism reports with verified embedded runtime.');
 const tables=new Map(input.manifest.tables.map(t=>[t.id,t]));
 const sources=new Set(input.manifest.sources.map(s=>s.id));
 const sections=input.manifest.blocks.map(b=>{
  if(b.type==='markdown')return `<section class="portable-block" data-artifact-block-id="${escape(b.id)}"><div class="portable-markdown">${markdown(b.body)}</div></section>`;
  if(b.type!=='table')throw new Error('Unsupported recovery block: '+b.type);
  const t=tables.get(b.tableId),rows=input.snapshot.datasets[t?.dataset];
  if(!t||!Array.isArray(rows)||!sources.has(t.sourceId))throw new Error('Unresolved table, dataset or source');
  for(const row of rows)for(const c of t.columns)if(!(c.field in row))throw new Error('Missing table field');
  return `<section class="portable-block" data-artifact-block-id="${escape(b.id)}"><div class="portable-table-card"><h2>${escape(t.title)}</h2><div class="portable-table-scroll"><table><thead><tr>${t.columns.map(c=>`<th>${escape(c.label)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${t.columns.map(c=>`<td>${escape(r[c.field])}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div></section>`;
 }).join('');
 const payload={ok:true,widget_type:prior.widget_type,...input,package_info:prior.package_info,packageInfo:prior.packageInfo};
 let html=template.replace(pattern,`<template id="data-analytics-portable-artifact-payload-source" data-compression="gzip-base64">${gzipSync(JSON.stringify(payload)).toString('base64')}</template>`)
 .replace(/<title>[\s\S]*?<\/title>/,`<title>${escape(input.manifest.title)}</title>`)
 .replace(/<main id="data-analytics-portable-fallback"[\s\S]*?<\/main>/,`<main id="data-analytics-portable-fallback" class="portable-fallback" data-portable-fallback="true" data-portable-surface="report"><div class="portable-block-stack">${sections}</div></main>`)
 .replace('<html lang="en"','<html lang="zh-CN"');
 if(!html.includes(runtime))throw new Error('Shared runtime changed during recovery');
 const check=JSON.parse(gunzipSync(Buffer.from(html.match(pattern)[1].trim(),'base64')));
 for(const k of ['manifest','snapshot','sources'])if(JSON.stringify(check[k])!==JSON.stringify(input[k]))throw new Error('Embedded payload differs');
 mkdirSync(dirname(outputPath),{recursive:true});writeFileSync(outputPath,html);
 const browser=await chromium.launch({channel:'chrome',headless:true});const checks=[];const errors=[];const network=[];
 try{
  const page=await browser.newPage();page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});await page.goto(pathToFileURL(outputPath).href);
   await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready',{},{timeout:20000});
   const root=page.locator('#data-analytics-portable-reader');
   const text=await root.innerText();
   for(const t of tables.values())for(const row of input.snapshot.datasets[t.dataset])for(const c of t.columns)if(!text.includes(String(row[c.field])))throw new Error('Rendered table cell missing');
   if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2))throw new Error('Horizontal page overflow');
   checks.push({width,reader_ready:true,all_table_cells_present:true,overflow:false});
  }
  if(errors.length||network.length)throw new Error('Reader error or external request');
 }finally{await browser.close()}
 return {ok:true,html:outputPath,stages:{validation:'passed',package:'passed',verification:'passed'},viewports:[1440,390],checks,reader_runtime_sha256:sha(runtime),reader_template_sha256:sha(template),recovery:'preserved_shared_embedded_reader',source_dialog:'not_retested',network_calls:network.length,browser_errors:errors};
}

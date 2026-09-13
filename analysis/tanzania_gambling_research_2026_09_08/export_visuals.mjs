import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {extractPortableChartSvgs} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/extract_portable_chart_svgs.mjs';
const base=dirname(fileURLToPath(import.meta.url));
const charts=await extractPortableChartSvgs({htmlPath:resolve(base,'../../output/html/坦桑尼亚博彩行业与产品调研报告-2026-09-08.html'),readyTimeoutMs:15000,actionTimeoutMs:4000});
const sharp=createRequire(import.meta.url)('/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/dist/index.cjs');
mkdirSync(resolve(base,'lark_assets'),{recursive:true});
let receipts=[];
const artifact=JSON.parse(readFileSync(resolve(base,'artifact.json'),'utf8'));
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
for(const visual of Object.values(charts)){
 if(!visual?.light?.svg)throw new Error('Light chart missing '+visual.chartId);
 const chart=artifact.manifest.charts.find(x=>x.id===visual.chartId);
 const box=visual.light.svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
 const[x,y,w,h]=box,W=w+75,H=h+140;
 const inner=visual.light.svg.replace(/^<svg[^>]*>/,'').replace(/<\/svg>\s*$/,'');
 const items=visual.light.legend?.items||[];
 const legend=items.map((i,n)=>`<g transform="translate(${55+n*220},${h+98})"><rect width="20" height="10" fill="${esc(i.color)}"/><text x="28" y="10" font-size="15">${esc(i.label)}</text></g>`).join('');
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><style>text{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;fill:#263f52}</style><rect width="100%" height="100%" fill="white"/><text x="55" y="29" font-size="22" font-weight="700">${esc(chart.title)}</text><text x="55" y="52" font-size="13">${esc(chart.subtitle)}</text><g transform="translate(${40-x},${72-y})">${inner}</g>${legend}</svg>`;
 const output=resolve(base,'lark_assets',visual.chartId+'.png');
 writeFileSync(resolve(base,'lark_assets',visual.chartId+'.svg'),svg);
 await sharp(Buffer.from(svg),{density:160}).flatten({background:'#ffffff'}).png().toFile(output);
 const m=await sharp(output).metadata();receipts.push({id:visual.chartId,width:m.width,height:m.height,path:output,legend:items});
}
writeFileSync(resolve(base,'visual-export-receipt.json'),JSON.stringify(receipts,null,2));
console.log(JSON.stringify(receipts));

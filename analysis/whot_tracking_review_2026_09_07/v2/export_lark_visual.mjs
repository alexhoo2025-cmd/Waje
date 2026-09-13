import {readFileSync,mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {extractPortableChartSvgs} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/extract_portable_chart_svgs.mjs';

const base=dirname(fileURLToPath(import.meta.url));
const htmlPath=resolve(base,'../../../output/html/Whot新版埋点与数据指标-V2-15项需求-2026-09-07.html');
const charts=await extractPortableChartSvgs({htmlPath,readyTimeoutMs:10000,actionTimeoutMs:4000});
const visual=Object.values(charts).find(item=>item.chartId==='scope_chart');
if(!visual?.light?.svg)throw new Error('scope_chart SVG unavailable');
const svg=visual.light.svg.replace(/viewBox="([^"]+)"/,(_,box)=>{
  const [x,y,w,h]=box.split(/\s+/).map(Number);
  return `viewBox="${x-28} ${y} ${w+28} ${h}"`;
});
const require=createRequire(import.meta.url);
const sharp=require('/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/dist/index.cjs');
const outputDir=resolve(base,'lark_assets');mkdirSync(outputDir,{recursive:true});
const output=resolve(outputDir,'数据指标覆盖的用户旅程阶段.png');
await sharp(Buffer.from(svg),{density:180}).flatten({background:'#ffffff'}).png().toFile(output);
const metadata=await sharp(output).metadata();
console.log(JSON.stringify({output,width:metadata.width,height:metadata.height}));

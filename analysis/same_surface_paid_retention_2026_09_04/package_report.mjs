import {readFileSync,writeFileSync,copyFileSync,mkdirSync,existsSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {buildPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
import {extractPortableChartSvgs} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/extract_portable_chart_svgs.mjs';
import {verifyPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/verify_portable_artifact.mjs';

const base=dirname(fileURLToPath(import.meta.url));
const artifactPath=resolve(base,'artifact.json');
const a=JSON.parse(readFileSync(artifactPath,'utf8'));
const css=readFileSync(resolve(base,'../all_platform_cohort_value_2026_09_04/report_theme.css'),'utf8')+'\n'+readFileSync(resolve(base,'reading_theme.css'),'utf8');
const theme=html=>html.replace('<html lang="en"','<html lang="zh-CN"').replace('</head>',`<style>${css}</style></head>`);
const staging=resolve(base,'report.preview.html');
writeFileSync(staging,theme(buildPortableArtifact(a)));
const staticCharts=await extractPortableChartSvgs({htmlPath:staging});
// Keep axis text inside exported vector bounds; this only changes white space.
for(const chart of Object.values(staticCharts)){
  for(const mode of ['light','dark']){
    chart[mode].svg=chart[mode].svg.replace(/viewBox="([^"]+)"/,(_,box)=>{
      const [x,y,w,h]=box.split(/\s+/).map(Number);
      return `viewBox="${x-24} ${y} ${w+24} ${h}"`;
    });
  }
}
writeFileSync(resolve(base,'static_charts.json'),JSON.stringify(staticCharts));
writeFileSync(staging,theme(buildPortableArtifact(a,{staticCharts})));
const verification=await verifyPortableArtifact({artifactPath,htmlPath:staging});
writeFileSync(resolve(base,'browser_verification.json'),JSON.stringify(verification,null,2));
if(!verification.ok)throw new Error('Browser verification failed');
const out=resolve(base,'../../output/html/Waje-全平台用户生命周期与付费价值分析-H5自然新增重点-2026-09-04.html');
mkdirSync(resolve(base,'historical'),{recursive:true});
if(existsSync(out)&&!existsSync(resolve(base,'historical/prior_report.html')))copyFileSync(out,resolve(base,'historical/prior_report.html'));
copyFileSync(staging,out);
const require=createRequire(import.meta.url);
const sharp=require('/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/dist/index.cjs');
mkdirSync(resolve(base,'charts'),{recursive:true});
const media=[];
for(const chart of a.manifest.charts){
  const data=Object.values(staticCharts).find(item=>item.chartId===chart.id);
  if(!data?.light?.svg)throw new Error(`Missing static SVG for ${chart.id}`);
  const path=resolve(base,'charts',chart.id+'.png');
  await sharp(Buffer.from(data.light.svg),{density:180}).flatten({background:'#ffffff'}).png().toFile(path);
  media.push({chart_id:chart.id,path,width:(await sharp(path).metadata()).width});
}
writeFileSync(resolve(base,'chart_media.json'),JSON.stringify(media,null,2));
copyFileSync(resolve(base,'report.md'),resolve(base,'../../knowledge/02-数据/Waje-全平台用户生命周期与付费价值分析-H5自然新增重点-2026-09-04.md'));
console.log(JSON.stringify({html:out,media:media.length,verification}));

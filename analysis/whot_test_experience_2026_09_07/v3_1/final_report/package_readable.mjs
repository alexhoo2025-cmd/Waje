import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildPortableArtifact} from '/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599/skills/build-report/scripts/build_portable_artifact.mjs';
const here=dirname(fileURLToPath(import.meta.url));
const artifact=JSON.parse(readFileSync(resolve(here,'artifact.json'),'utf8'));
artifact.manifest.blocks[1].id='summary';
let tableNumber=0;
artifact.manifest.blocks=artifact.manifest.blocks.flatMap(block=>{
 if(block.type!=='markdown')return [block];
 const pieces=block.body.split(/(\n\|[^\n]*\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n?)+)/g);
 return pieces.filter(p=>p.trim()).map((p,i)=>{
  if(!p.trim().startsWith('|'))return {...block,id:i?`${block.id}-part-${i}`:block.id,body:p.trim()};
  const lines=p.trim().split('\n');
  const cells=line=>line.trim().slice(1,-1).split('|').map(s=>s.trim());
  const headers=cells(lines[0]);const id=`readable-table-${++tableNumber}`;
  artifact.snapshot.datasets[id]=lines.slice(2).map(line=>Object.fromEntries(cells(line).map((v,j)=>[`c${j}`,v])));
  if(tableNumber===1)for(const row of artifact.snapshot.datasets[id])row.c4+=' 筹码';
  artifact.manifest.tables.push({id,title:['逐局结算记录','条件性返还比例分布','对手机器人评估'][tableNumber-1],dataset:id,sourceId:'observations',density:'spacious',layout:'full',defaultSort:{field:'c0',direction:'asc'},columns:headers.map((label,j)=>({field:`c${j}`,label,type:'text'}))});
  return {id:`${id}-block`,type:'table',tableId:id};
 });
});
const css=readFileSync('/Users/robin/Documents/wajetan_analyst/config/report_readability.css','utf8');
writeFileSync(resolve(here,'artifact-readable-v2.json'),JSON.stringify(artifact,null,2));
let html=buildPortableArtifact(artifact);
// Preserve canonical semantic content; disable the unavailable enhanced reader.
html=html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'');
const extra=`
#data-analytics-portable-reader{display:none!important}
.portable-fallback{display:block!important}
.portable-block-stack{display:flex!important;flex-direction:column;gap:24px}
.portable-page-header{position:static!important;max-width:1120px;margin:0 auto!important}
.portable-markdown{box-shadow:0 4px 20px #18344f06}
.portable-markdown p{margin:0 0 16px}
.portable-markdown h2{margin-top:0}
.portable-sources{display:block!important;max-width:1120px;margin:24px auto;overflow-wrap:anywhere}
.portable-source-summary{display:block!important}
.portable-markdown table{font-size:15px}
.portable-chart-summary{max-width:100%}
`;
html=html.replace('</head>',`<style>${css}\n${extra}</style></head>`);
writeFileSync(resolve(here,'report-readable-v2.html'),html);
writeFileSync(resolve(here,'readability-v2-receipt.json'),JSON.stringify({mode:'canonical_semantic_static',standard:'2026-09-07 with 2026-09-08 components',source:'artifact-readable-v2.json',original_source:'artifact.json',blocks:artifact.manifest.blocks.length,converted_tables:tableNumber,enhanced_reader:'unavailable_reader_timeout',scripts_removed:true,browser_visual_verification:'blocked_by_browser_url_policy',content_verification:'see readability-content-audit.json'},null,2));
console.log(resolve(here,'report-readable-v2.html'));

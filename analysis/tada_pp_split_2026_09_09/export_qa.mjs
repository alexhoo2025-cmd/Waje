import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url),sharp=require('/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const targets=[['macro','output/html/Tada与PP-宏观对比-新老用户下注与回访-2026-09-09.html'],['detail','output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html']];
const base='analysis/tada_pp_split_2026_09_09/qa';fs.mkdirSync(base,{recursive:true});
for(const [slug,file] of targets){
 const html=fs.readFileSync(file,'utf8'),re=/data-static-chart-block-id="([^"]+)"[^>]*><div class="portable-static-chart-variant portable-static-chart-light"[^>]*>(<svg[\s\S]*?<\/svg>)([\s\S]*?)(?=<div class="portable-static-chart-variant portable-static-chart-dark")/g;
 const all=[...html.matchAll(re)];assert.equal(all.length,slug==='macro'?5:6);
 for(const m of all){
  const size=m[2].match(/<svg width="([\d.]+)" height="([\d.]+)"/);assert(size);const w=Number(size[1]),h=Number(size[2]);
  const legends=[...m[3].matchAll(/style="--portable-legend-color:([^"]+)"[^>]*><\/span><span>(.*?)<\/span>/g)];
  let svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+(w+48)+'" height="'+(h+76)+'"><rect width="100%" height="100%" fill="white"/><g transform="translate(24,12)">'+m[2].replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'')+'</g>';
  const span=Math.min(180,(w-40)/Math.max(1,legends.length));let x=Math.max(20,(w+48-legends.length*span)/2);for(const l of legends){svg+='<rect x="'+x+'" y="'+(h+38)+'" width="10" height="10" fill="'+l[1]+'"/><text x="'+(x+16)+'" y="'+(h+48)+'" font-family="Arial, PingFang SC, sans-serif" font-size="13" fill="#34465c">'+l[2]+'</text>';x+=span;}svg+='</svg>';
  const name=base+'/'+slug+'-'+m[1];fs.writeFileSync(name+'.svg',svg);await sharp(Buffer.from(svg)).png().toFile(name+'.png');
 }
 console.log(JSON.stringify({slug,exported:all.length}));
}

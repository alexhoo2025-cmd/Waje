import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url),sharp=require('/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const html=fs.readFileSync('output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html','utf8');
const re=/data-static-chart-block-id="([^"]+)"[^>]*><div class="portable-static-chart-variant portable-static-chart-light"[^>]*>(<svg[\s\S]*?<\/svg>)([\s\S]*?)(?=<div class="portable-static-chart-variant portable-static-chart-dark")/g;
const m=[...html.matchAll(re)].find(m=>m[1]==='return-chart-block');assert(m,'canonical SVG missing');
const size=m[2].match(/<svg width="([\d.]+)" height="([\d.]+)"/);assert(size);
const w=Number(size[1]),h=Number(size[2]),width=w+48,height=h+72;
const inner=m[2].replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'');
const legends=[...m[3].matchAll(/style="--portable-legend-color:([^"]+)"[^>]*><\/span><span>(.*?)<\/span>/g)];assert.equal(legends.length,4);
let svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+width+'" height="'+height+'" viewBox="0 0 '+width+' '+height+'"><rect width="100%" height="100%" fill="white"/><g transform="translate(24,12)">'+inner+'</g>';
let x=width/2-250;for(const l of legends){svg+='<rect x="'+x+'" y="'+(h+35)+'" width="10" height="10" fill="'+l[1]+'"/><text x="'+(x+17)+'" y="'+(h+45)+'" font-family="Arial, PingFang SC, sans-serif" font-size="14" fill="#34465c">'+l[2]+'</text>';x+=150;}
svg+='</svg>';
const out='analysis/tada_pp_app_h5_actual_2026_09_08/lark-assets/return-chart-block';
fs.writeFileSync(out+'.svg',svg);await sharp(Buffer.from(svg),{density:160}).flatten({background:'white'}).png().toFile(out+'.png');console.log(JSON.stringify({png:out+'.png',width,height,source:'shared portable renderer SVG'}));


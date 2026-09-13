// Content-only legacy edit. The packaged reader, charts, datasets and styles stay byte-identical.
import fs from 'node:fs';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import path from 'node:path';
const root=path.resolve('analysis/origin_paid_retention_rebuild_2026_09_10');
const revision=path.join(root,'revisions/2026-09-11-business-scope');
const target=path.resolve('output/html/8月付费用户留存与价值分析-起源口径重查版-2026-09-10.html');
const html=fs.readFileSync(target,'utf8');
assert.equal(html,fs.readFileSync(path.join(revision,'before.html'),'utf8'));
const old=JSON.parse(fs.readFileSync(path.join(revision,'artifact.json')));
const current=JSON.parse(fs.readFileSync(path.join(root,'artifact.json')));
const oldBody=old.manifest.blocks.find(b=>b.id==='scope').body;
const newBody=current.manifest.blocks.find(b=>b.id==='scope').body;
const template=html.match(/<template id="data-analytics-portable-artifact-payload-source"[^>]*>([\s\S]*?)<\/template>/)[0];
const encoded=template.match(/>([\s\S]*?)<\/template>/)[1];
const payload=JSON.parse(zlib.gunzipSync(Buffer.from(encoded.replace(/\s/g,''),'base64')));
const block=payload.manifest.blocks.find(b=>b.id==='scope');
assert.equal(block.body,oldBody);block.body=newBody;
const revisedEncoded='\n'+zlib.gzipSync(JSON.stringify(payload),{level:9}).toString('base64').match(/.{1,76}/g).join('\n')+'\n';
const revisedTemplate=template.replace(encoded,revisedEncoded);
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function list(body){return '<ul>'+body.split('\n').filter(l=>l.startsWith('- **')).map(l=>{const m=l.match(/^- \*\*(.*?)\*\* (.*)$/);assert(m);return '<li><strong>'+esc(m[1])+'</strong> '+esc(m[2])+'</li>';}).join('')+'</ul>';}
const oldList=list(oldBody),newList=list(newBody);assert.equal(html.split(oldList).length,2);
function hunk(before,after){return '@@\n'+before.split('\n').map(s=>'-'+s).join('\n')+'\n'+after.split('\n').map(s=>'+'+s).join('\n')+'\n';}
process.stdout.write('*** Begin Patch\n*** Update File: '+target+'\n'+hunk(oldList,newList)+hunk(template,revisedTemplate)+'*** End Patch\n');

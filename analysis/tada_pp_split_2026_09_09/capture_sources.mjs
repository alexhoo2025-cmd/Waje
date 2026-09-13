import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=process.cwd(),out='analysis/tada_pp_split_2026_09_09',source='analysis/tada_pp_app_h5_actual_2026_09_08';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const files=[source+'/artifact.json',source+'/报告.md',source+'/build_report.py',source+'/analysis-results.json',source+'/core-corrected.json','output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html'];
const record={capturedAt:new Date().toISOString(),files:files.map(p=>({path:p,sha256:hash(p)})),source_window:['2026-08-01','2026-09-07'],original_must_remain_unchanged:true};
try{const raw=JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs','+fetch','--doc','MUmUdKO7ko3hKIxY822lBXJQggg','--detail','full','--as','user','--format','json'],{encoding:'utf8',timeout:45000,maxBuffer:10e6}));if(!raw.ok)throw Error(JSON.stringify(raw));const doc=raw.data.document;fs.writeFileSync(out+'/source-lark.json',JSON.stringify(doc,null,2));record.lark={id:doc.document_id,revision:doc.revision_id,content_sha256:crypto.createHash('sha256').update(doc.content).digest('hex'),readOnly:true};}catch(e){record.lark={status:'read_unavailable',reason:String(e.message).slice(0,300)};}
fs.writeFileSync(out+'/source-inventory.json',JSON.stringify(record,null,2));console.log(JSON.stringify(record));

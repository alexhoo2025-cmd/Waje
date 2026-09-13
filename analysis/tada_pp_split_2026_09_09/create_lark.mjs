import fs from 'node:fs';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const slug=process.argv[2];assert(['macro','detail'].includes(slug));
const base='analysis/tada_pp_split_2026_09_09/'+slug+'/';
const expected=JSON.parse(fs.readFileSync(base+'lark-expected.json','utf8'));
const run=args=>JSON.parse(execFileSync('/Users/robin/.local/node/bin/lark-cli',['docs',...args,'--as','user','--format','json'],{encoding:'utf8',timeout:240000,maxBuffer:12e6}));
const parse=run(['+script','--command','parse','--content','@./'+expected.draft]);fs.writeFileSync(base+'lark-parse.json',JSON.stringify(parse.data,null,2));assert.equal(parse.data.assessment.status,'passed');
let result;
if(fs.existsSync(base+'lark-create.json'))result=JSON.parse(fs.readFileSync(base+'lark-create.json'));
else{const response=run(['+create','--doc-format','xml','--content','@./'+expected.draft]);fs.writeFileSync(base+'lark-create-response.json',JSON.stringify(response,null,2));assert(response.ok,JSON.stringify(response));result=response.data;fs.writeFileSync(base+'lark-create.json',JSON.stringify(result,null,2));}
assert(result.document?.document_id);console.log(JSON.stringify({slug,stage:'created',document:result.document,warnings:result.warnings||[]}));
const response=run(['+fetch','--doc',result.document.document_id,'--detail','full']);assert(response.ok);fs.writeFileSync(base+'lark-readback.json',JSON.stringify(response.data.document,null,2));
fs.copyFileSync(expected.draft,base+'lark-source.xml');fs.copyFileSync(expected.draft.replace('/draft.xml','/.presentation-decision.json'),base+'lark-presentation-decision.json');
console.log(JSON.stringify({slug,stage:'readback_saved',revision:response.data.document.revision_id,url:result.document.url}));

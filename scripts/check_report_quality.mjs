#!/usr/bin/env node
import fs from 'node:fs';
import {checkFile} from './report_quality.mjs';
export function parseFlags(args){
 const flags={};
 for(let i=0;i<args.length;i++){
  const key=args[i];if(key==='--check-only'){flags[key]=true;continue;}
  if(!['--input','--output','--receipt','--format','--exceptions','--extra-css','--verification','--language'].includes(key)||!args[i+1]||args[i+1].startsWith('--'))throw Error(`Unknown or incomplete argument: ${key}`);
  flags[key]=args[++i];
 }
 return flags;
}
export function runCheck(flags){return checkFile(flags['--input'],{format:flags['--format'],language:flags['--language'],exceptions:flags['--exceptions']?JSON.parse(fs.readFileSync(flags['--exceptions'],'utf8')):[],verification:flags['--verification']?JSON.parse(fs.readFileSync(flags['--verification'],'utf8')):undefined});}
if(import.meta.url===new URL(process.argv[1]||'', 'file:').href){
 try{
  const flags=parseFlags(process.argv.slice(2));if(!flags['--input'])throw Error('--input is required');
  const result=runCheck(flags);if(flags['--receipt'])fs.writeFileSync(flags['--receipt'],JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));process.exitCode=result.errors?1:0;
 }catch(e){console.error(JSON.stringify({status:'blocked',error:e.message}));process.exitCode=1;}
}

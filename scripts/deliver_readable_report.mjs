#!/usr/bin/env node
// Canonical report builder with the user's project-wide presentation standard.
// Does not change the artifact, datasets, renderer interactions or provenance.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {parseFlags,runCheck} from './check_report_quality.mjs';
import {checkFile,digest} from './report_quality.mjs';
import {deliverWithBoundedRetry} from './report_delivery_retry.mjs';
import {enableMechanismTables} from './report_mechanism_compat.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const argv=process.argv.slice(2);
const recoveryIndex=argv.indexOf('--reader-template');
const recoveryTemplate=recoveryIndex<0?null:argv[recoveryIndex+1];
if(recoveryIndex>=0&&(!recoveryTemplate||recoveryTemplate.startsWith('--')))throw new Error('--reader-template needs a file path');
if(recoveryIndex>=0)argv.splice(recoveryIndex,2);
const flags=parseFlags(argv);
if(recoveryTemplate)flags['--reader-template']=recoveryTemplate;
if(!flags['--input']||(!flags['--check-only']&&!flags['--output']))throw new Error('Usage: --input artifact.json [--check-only | --output report.html] [--receipt receipt.json]');
const executionRunId=new Date().toISOString().replace(/[-:.TZ]/g,'');
const recordExecution=(phase,status)=>{
 if(flags['--check-only'])return {status:'not_run',reason:'check_only'};
 const args=[resolve(root,'tools/execution_graph.py'),'--root',root,'record','--job-id','report_delivery','--run-id',executionRunId,'--phase',phase,'--status',status];
 if(flags['--receipt'])args.push('--receipt',resolve(flags['--receipt']));
 if(flags['--input'])args.push('--artifact',resolve(flags['--input']));
 if(flags['--output'])args.push('--artifact',resolve(flags['--output']));
 const child=spawnSync('python3',args,{cwd:root,encoding:'utf8',timeout:60000});
 if(child.status!==0)return {status:'degraded',error_type:'execution_graph_record_failed'};
 try{return JSON.parse((child.stdout||'').trim());}catch{return {status:'degraded',error_type:'execution_graph_record_invalid'};}
};
recordExecution('started','started');
const quality=runCheck(flags);
if(flags['--check-only']||quality.errors){
 const result=flags['--check-only']?quality:{ok:false,stage:'report_quality',report_quality:quality};
 if(flags['--receipt'])writeFileSync(resolve(flags['--receipt']),JSON.stringify(result,null,2)+'\n');
 if(!flags['--check-only'])result.execution_graph=recordExecution('finished',quality.errors?'blocked':'not_run');
 console.log(JSON.stringify(result));if(quality.errors)process.exitCode=1;
}else{
const plugin=process.env.WAJE_ANALYTICS_PLUGIN_ROOT||'/Users/robin/.codex/plugins/cache/openai-curated-remote/data-analytics/0.2.10-13ceeea1f599';
const base=resolve(plugin,'skills/build-report/scripts');
if(!existsSync(resolve(base,'build_portable_artifact.mjs'))&&flags['--reader-template']){
 const {deliverRecoveredReader}=await import('./report_embedded_reader_recovery.mjs');
 const result=await deliverRecoveredReader({inputPath:resolve(flags['--input']),outputPath:resolve(flags['--output']),templatePath:resolve(flags['--reader-template'])});
 result.report_quality=quality;
 if(flags['--receipt'])writeFileSync(resolve(flags['--receipt']),JSON.stringify(result,null,2)+'\n');
 recordExecution('finished',result.ok?'ok':'failed');console.log(JSON.stringify(result));
}else{
const mechanismTableCompatibility=enableMechanismTables(plugin,JSON.parse(readFileSync(resolve(flags['--input']),'utf8')));
const {buildPortableArtifact,readPackagedReaderRuntime}=await import(pathToFileURL(resolve(base,'build_portable_artifact.mjs')));
const {deliverPortableArtifact}=await import(pathToFileURL(resolve(base,'deliver_portable_artifact.mjs')));
const extraCss=flags['--extra-css']?readFileSync(resolve(flags['--extra-css']),'utf8'):'';
const css=readFileSync(resolve(root,'config/report_readability.css'),'utf8')+(extraCss?`\n${extraCss}`:'');
const style=`<style data-waje-readability="2026-09-07">${css}</style>`;
const runtimeHtml=readPackagedReaderRuntime().html.replace('</head>',`${style}</head>`);
const build=(input,options={})=>buildPortableArtifact(input,{...options,runtimeHtml}).replace('</head>',`${style}</head>`);
const result=await deliverWithBoundedRetry(
 ()=>deliverPortableArtifact({inputPath:resolve(flags['--input']),outputPath:resolve(flags['--output']),readyTimeoutMs:10000,actionTimeoutMs:4000,timeoutMs:30000},{build}),
 ()=>digest(readFileSync(resolve(flags['--input'])))===quality.input_sha256,
);
result.report_quality=checkFile(resolve(flags['--input']),{verification:result,language:flags['--language'],format:flags['--format'],exceptions:flags['--exceptions']?JSON.parse(readFileSync(flags['--exceptions'],'utf8')):[]});
if(result.report_quality.errors)result.ok=false;
result.report_standard_version=quality.standard_version;
result.mechanism_table_compatibility=mechanismTableCompatibility;
if(flags['--receipt'])writeFileSync(resolve(flags['--receipt']),JSON.stringify({...result,readability_standard:'2026-09-07',stylesheet:'config/report_readability.css',extra_stylesheet:flags['--extra-css']||null},null,2)+'\n');
result.execution_graph=recordExecution('finished',result.ok?'ok':'failed');
console.log(JSON.stringify(result));
if(!result.ok)process.exitCode=1;
}
}

import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {fixture,mechanismXml} from '../../tests/report_quality_fixture.mjs';
import {checkFile,checkReport,digest,projectRoot} from '../../scripts/report_quality.mjs';
const out=path.dirname(fileURLToPath(import.meta.url));
const fixtures=path.join(out,'fixtures'),rendered=path.join(out,'rendered');
fs.mkdirSync(fixtures,{recursive:true});fs.mkdirSync(rendered,{recursive:true});
const receiptPath=path.join(out,'validation-receipt.json');
const startedAt=new Date().toISOString();
if(fs.existsSync(receiptPath)){
 const history=path.join(out,'validation-history');fs.mkdirSync(history,{recursive:true});
 fs.copyFileSync(receiptPath,path.join(history,startedAt.replace(/[:.]/g,'-')+'.json'));
}
const current={status:'running',started_at:startedAt,unit_tests:null,fixture_checks:[],html_verification:[]};
const flush=()=>fs.writeFileSync(receiptPath,JSON.stringify(current,null,2)+'\n');flush();
try{
const tests=spawnSync(process.execPath,['--test','tests/test_report_quality.mjs'],{cwd:projectRoot,encoding:'utf8'});
fs.writeFileSync(path.join(out,'unit-tests.txt'),tests.stdout+tests.stderr);assert.equal(tests.status,0,'Unit tests failed');
const unitCount=Number((tests.stdout.match(/(?:#|ℹ) tests (\d+)/)||[])[1]);assert.ok(unitCount>0);
current.unit_tests=unitCount;flush();
const fixtureChecks=[],deliveries=[];
current.fixture_checks=fixtureChecks;current.html_verification=deliveries;
for(const type of ['business','retention','research']){
 const a=fixture(type),input=path.join(fixtures,type+'.json');
 if(type==='retention'){
  a.manifest.reportContract.metrics.push({dataset:'d',field:'rate_pct',unit:'%',kind:'ratio',scale:'percent_points',definition:'原始rate乘100，仅用于百分数坐标',denominator:'与原始rate相同'});
  a.manifest.reportContract.assertions.push({kind:'ratio',dataset:'d',numerator:'rate_pct',denominator:'percent_base',actual:'rate'});
 }
 fs.writeFileSync(input,JSON.stringify(a,null,2)+'\n');fs.writeFileSync(path.join(fixtures,'synthetic.sql'),a.manifest.sources[0].query.sql+'\n');
 const sqlCheck=spawnSync('python3',['-c','import sys,json,sqlite3; c=sqlite3.connect(":memory:"); c.row_factory=sqlite3.Row; print(json.dumps([dict(r) for r in c.execute(sys.stdin.read())],ensure_ascii=False))'],{input:a.manifest.sources[0].query.sql,encoding:'utf8'});
 assert.equal(sqlCheck.status,0);assert.deepEqual(JSON.parse(sqlCheck.stdout),a.snapshot.datasets.d);
 const q=checkFile(input);assert.equal(q.errors,0);fixtureChecks.push({type,format:'artifact',status:q.status,source_sql:'executed_in_local_sqlite'});
 const result=spawnSync(process.execPath,['scripts/deliver_readable_report.mjs','--input',input,'--output',path.join(rendered,type+'.html'),'--receipt',path.join(rendered,type+'.receipt.json')],{cwd:projectRoot,encoding:'utf8',timeout:60000,maxBuffer:4*1024*1024});
 if(result.status!==0){
  let failure;try{failure=JSON.parse(result.stdout);}catch{failure={stage:'process',error:result.stderr.slice(-600)};}
  deliveries.push({type,status:'failed',stages:failure.stages||{},code:failure.code||'delivery_failed',error:failure.error||'delivery blocked',attempts:failure.attempts||[],input_sha256:digest(fs.readFileSync(input))});flush();continue;
 }
 const receipt=JSON.parse(fs.readFileSync(path.join(rendered,type+'.receipt.json'),'utf8'));assert.equal(receipt.ok,true);assert.equal(receipt.report_quality.errors,0);
 const html=fs.readFileSync(path.join(rendered,type+'.html'),'utf8');
 assert.ok(html.includes('prefers-color-scheme'));assert.ok(html.includes('portable-static-chart-light'));assert.ok(html.includes('portable-static-chart-dark'));
 if(type==='retention'){
  const svg=html.match(/data-static-chart-block-id="cb"[\s\S]*?(<svg[\s\S]*?<\/svg>)/)?.[1]||'';
  const labels=[...svg.matchAll(/<text\b[^>]*>([\s\S]*?)<\/text>/g)].map(m=>m[1].replace(/<[^>]+>/g,'').trim());
  assert.ok(labels.includes('10')&&labels.includes('80')&&!labels.includes('0.1'),'Static percent labels must match percent-point display values');
 }
 deliveries.push({type,status:'passed',stages:receipt.stages,viewports:receipt.viewports,sourceDialog:receipt.sourceDialog,light_dark_static:true,static_percent_labels:type==='retention'?'verified_percent_points':'not_applicable',attempts:receipt.attempts,input_sha256:digest(fs.readFileSync(input)),html_sha256:digest(fs.readFileSync(path.join(rendered,type+'.html')))});flush();
}
fs.writeFileSync(path.join(fixtures,'mechanism.xml'),mechanismXml+'\n');
fs.writeFileSync(path.join(fixtures,'mechanism.md'),'# 机制验收样例（模拟数据）\n\n## 先看结论\n\n**每次请求只有一个结果。** 此处只说明模拟机制，不代表上线效果。\n\n**点击与结果分别统计。** 不可比数据不能混算，隐私限制仍然保留。\n\n## 流程与验收\n\n进入请求 → 条件检查 → 结果确认。\n');
for(const format of ['xml','md']){const r=checkFile(path.join(fixtures,'mechanism.'+format));assert.equal(r.errors,0);assert.equal(r.coverage.declared_calculations,'not_declared');fixtureChecks.push({type:'mechanism',format,status:r.status,business_calculation:'not_applicable_to_this_text_fixture'});}
const registry=JSON.parse(fs.readFileSync(path.join(out,'baseline-registry.json'),'utf8'));
const regressions=[];
for(const report of registry.reports){
 const file=report.files.find(f=>f.path.endsWith('/artifact.json'))||report.files.find(f=>f.path.endsWith('/report.md')||f.path.endsWith('/报告.md'));
 if(!file){regressions.push({id:report.id,status:'no_local_artifact_candidate',source:'use remote revision evidence; not a passing fixture'});continue;}
 const full=path.join(projectRoot,file.path);const before=digest(fs.readFileSync(full));const check=checkFile(full);assert.equal(digest(fs.readFileSync(full)),before);assert.equal(before,file.sha256,'Historical report changed since baseline');
 regressions.push({id:report.id,path:file.path,sha256:before,status:check.status,errors:check.errors,warnings:check.warnings,issues:check.issues});
}
for(const report of registry.reports)for(const f of report.files)assert.equal(digest(fs.readFileSync(path.join(projectRoot,f.path))),f.sha256,'Historical evidence mutated');
const receipt={status:deliveries.every(r=>r.status==='passed')?'passed':'partial',started_at:startedAt,finished_at:new Date().toISOString(),unit_tests:unitCount,fixture_checks:fixtureChecks,html_verification:deliveries,historical_regressions:regressions,
 browser_executable:process.env.CHROMIUM_EXECUTABLE_PATH||'shared_builder_default',
 original_report_hashes_unchanged:true,business_queries:0,external_publications:0,
 limits:['规则检查不认证业务事实','纯Markdown/XML不认证计算或回读','旧稿问题保留为负例，不改原稿','远端修订检查与自动规则验收分别记录']};
fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({status:receipt.status,unit_tests:unitCount,fixtures:fixtureChecks.length,html:deliveries.map(r=>[r.type,r.stages.verification]),historical_reports:regressions.length,unchanged:true}));
if(receipt.status!=='passed')process.exitCode=1;
}catch(error){current.status='failed';current.finished_at=new Date().toISOString();current.error=String(error.message).slice(0,1200);flush();console.error(current.error);process.exitCode=1;}

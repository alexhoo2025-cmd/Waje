// Deterministic, local-only report preflight. Never rewrites content or queries sources.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
export const projectRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const list=v=>Array.isArray(v)?v:[];
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const nonempty=v=>typeof v==='string'&&v.trim().length>0;
const filled=v=>nonempty(v)&&!/\{\{[^}]*\}\}|\[待填写\]|^TODO$/i.test(v.trim());
const own=(o,k)=>object(o)&&Object.hasOwn(o,k);
export const digest=v=>crypto.createHash('sha256').update(v).digest('hex');
export const loadPolicy=()=>JSON.parse(fs.readFileSync(path.join(projectRoot,'config/report_output_policy.json'),'utf8'));
const plain=s=>String(s).replace(/```[\s\S]*?```/g,'').replace(/`[^`]*`/g,'').replace(/\*\*/g,'').replace(/<[^>]*>/g,'').trim();
function markdownParts(body,location){
 const blank=s=>s.replace(/[^\n]/g,' ');
 const clean=body.replace(/^---\n[\s\S]*?\n---\s*/,blank).replace(/```[\s\S]*?```/g,blank);
 const loc=offset=>location==='markdown'?`markdown:line:${clean.slice(0,offset).split('\n').length}`:location;
 return {headings:[...clean.matchAll(/^(#{1,6})\s+(.+)$/gm)].map(m=>({text:plain(m[2]),level:m[1].length,location:loc(m.index)})),
  paragraphs:[...clean.matchAll(/[^\n]+(?:\n(?!\s*\n)[^\n]+)*/g)].filter(m=>m[0].trim()&&!/^\s*(#|\||>)/.test(m[0])).map(m=>({text:m[0],location:loc(m.index)}))};
}
function parseXml(body){
 if (/<!DOCTYPE|<!ENTITY/i.test(body))throw Error('XML不得包含DTD或实体声明');
 const code=`import sys,json,xml.etree.ElementTree as E
s=sys.stdin.read(); r=E.fromstring('<document>'+s+'</document>')
def text(n): return ''.join(n.itertext()).strip()
print(json.dumps({'title':text(r.find('title')) if r.find('title') is not None else '', 'headings':[{'text':text(n),'level':int(n.tag[1:]),'location':'xml/'+n.tag} for n in r.iter() if n.tag in ['h1','h2','h3','h4','h5','h6']], 'paragraphs':[{'text':E.tostring(n,encoding='unicode'),'location':'xml/p'} for n in r.iter('p')]}))`;
 const r=spawnSync('python3',['-c',code],{input:body,encoding:'utf8',timeout:10000,maxBuffer:8*1024*1024});
 if(r.status!==0)throw Error('XML结构无法解析');
 return JSON.parse(r.stdout);
}
function sourceValid(s){return object(s)&&(filled(s.path)||filled(s.href)||filled(s.query?.sql)||(filled(s.query?.description)&&list(s.query?.tables_used).length>0));}
function unitKnown(item,source){
 const y=item.encodings?.y||{};
 return nonempty(y.unit)||y.format==='percent'||/(%|％|百分|百分点|人数|百万人|万人|品牌数|条目数|项数|项目数|功能数|订阅数|计数|次数|局数|局次|人局|款数|天|小时|分钟|秒|毫秒|MB|GB|GiB|倍|笔|NGN|TZS|USD|报表单位|原表单位|源表单位|元|万元|亿元|[（(](?:人|次|项|条|个|款|家)[）)])/i.test([y.label,item.unit,item.subtitle,...list(source?.query?.metric_definitions)].join(' '));
}
export function checkReport(input,options={}){
 const policy=options.policy||loadPolicy(),q=policy.report_quality,issues=[];
 if(!q?.rules)throw Error('report_quality policy is missing');
 const emit=(rule_id,location,message,suggestion)=>issues.push({rule_id,severity:q.rules[rule_id].severity,location,message,suggestion});
 const format=options.format||'artifact';
 const inputSha=options.sha256||digest(typeof input==='string'?input:JSON.stringify(input));
 let headings=[],paragraphs=[],title='',m={},ds={},contract={},summaryBodies=[];
 const isSummary=text=>q.summary_headings.some(t=>text.includes(t))||(/^en/i.test(contract.language||options.language||'')&&/executive summary/i.test(text));
 try{
  if(format==='artifact'){
   if(!object(input)||!object(input.manifest)||!object(input.snapshot)||!object(input.snapshot.datasets))throw Error('需要manifest、snapshot和datasets对象');
   m=input.manifest;ds=input.snapshot.datasets;contract=m.reportContract||{};
   if(!Array.isArray(m.blocks))throw Error('manifest.blocks必须为数组');
   title=m.title||'';
   for(const [i,b] of m.blocks.entries()){
    if(!object(b))throw Error(`manifest.blocks[${i}]须为对象`);
    if(b.type!=='markdown')continue;
    const p=markdownParts(String(b.body||''),`manifest.blocks[${i}]`);headings.push(...p.headings);paragraphs.push(...p.paragraphs);
    if(p.headings.some(h=>isSummary(h.text)))summaryBodies.push(...p.paragraphs);
   }
   for(const [id,rows] of Object.entries(ds))if(!Array.isArray(rows)||rows.some(r=>!object(r)))emit('R001',`snapshot.datasets.${id}`,'数据集须为对象行数组','保留有明确粒度的聚合行数组。');
  }else if(format==='markdown'){
   if(typeof input!=='string')throw Error('Markdown输入须为文本');
   ({headings,paragraphs}=markdownParts(input,'markdown'));title=headings.find(h=>h.level===1)?.text||'';
  }else if(format==='xml'){
   ({headings,paragraphs,title}=parseXml(input));
  }else throw Error('不支持的输入类型');
 }catch(e){emit('R001','input',e.message,'提供有效的canonical artifact、Markdown或飞书XML。');}
 if(!filled(title))emit('R002','title','缺少已填写的报告标题','补充一个明确标题，不能将模板占位符作为成品。');
 if(!headings.some(h=>isSummary(h.text)))emit('R002','summary','缺少适用语言的摘要标题','默认使用执行摘要；可沿用同义中文标题，英文任务按其明确语言要求。');
 if(format==='artifact'&&nonempty(title)&&headings.find(h=>h.level===1)?.text!==title)emit('R002','manifest.title','页面首标题与报告标题不一致','从同一个标题值生成manifest与首个标题块。');
 const language=contract.language||options.language||q.default_language;
 if(/^zh(?:-|$)/i.test(language))for(const h of headings){
  const name=h.text.replace(/^\d+[.、｜|]?\s*/,'').split(/[｜|：:]/)[0].trim().toLowerCase();
  if(q.english_template_headings.some(v=>v.toLowerCase()===name))emit('R003',h.location,'残留英文默认模板标题','改为中文章节名；产品名、RTP等必要术语保留。');
 }
 if(summaryBodies.length){
  const n=summaryBodies.length;
  if(n<q.thresholds.summary_min_items||n>q.thresholds.summary_max_items)emit('W005','summary',`摘要含${n}段，建议2—4条核心判断`,'按不同结论合并或拆分，不以压缩为由删除关键证据。');
  if(!summaryBodies.some(p=>/\*\*|<b[ >]/.test(p.text)))emit('W004','summary','摘要未突出核心判断','每条只加粗主题句或关键数字。');
 }
 const seen=new Map();
 for(const p of paragraphs){
  const s=plain(p.text);if(!s)continue;
  if(s.length>q.thresholds.paragraph_characters)emit('W002',p.location,'段落较长','按判断、证据、含义拆为短段。');
  if(q.discouraged_phrases.some(v=>s.includes(v)))emit('W003',p.location,'存在可简化的业务表达','参考措辞表，保留技术含义而非只替换词语。');
  if(/已回读.{0,30}revision|扫描.{0,15}GiB|模型调用回执|任务ID/.test(s))emit('W003',p.location,'过程性说明需要复核放置位置','不影响判断的记录移入来源详情；影响结论的限制仍需可见。');
  const strong=[...p.text.matchAll(/\*\*([^*]+)\*\*|<b[^>]*>(.*?)<\/b>/g)].reduce((n,x)=>n+plain(x[1]||x[2]).length,0);
  if(s.length>80&&strong/s.length>q.thresholds.emphasis_ratio)emit('W004',p.location,'加粗范围过大','保留主题句与少量关键值，正文恢复正常字重。');
  if((s.match(/不能|不产生|不允许|不得/g)||[]).length>=3&&!/不可比|观察|隐私|凭证|银行卡|不得上传|不能.*(?:推断|当作|替代|证明)/.test(s))emit('W006',p.location,'否定式说明较密集','优先说明应该如何统计；安全和证据边界保留。');
  if(/导致|必然|证明.{0,12}(提升|改善|增长)/.test(s)&&!/不能|不代表|可能|假设|待验证|无法/.test(s))emit('W007',p.location,'因果判断需要人工核实','确认是否有因果证据，否则改为关联或待验证解释。');
  if(s.length>35&&seen.has(s))emit('W008',p.location,'与前文存在重复段落','合并重复结论，保留必要的就近限制。');seen.set(s,p.location);
  if(/\{\{[^}]+\}\}|\[待填写\]|TODO/.test(s))emit('W011',p.location,'存在待填内容','模板填完后再交付，数据缺失明确说明原因。');
 }
 const allText=paragraphs.map(p=>plain(p.text)).join('\n');
 if(/统计日期当天注册为新用户/.test(allText)&&/新用户采用注册当日还是注册后N天/.test(allText))emit('W011','narrative','正文与待定清单可能对同一新用户规则重复决策','按本报告最后确认口径核对，不全局固定新用户定义。');
 if(format==='artifact'&&object(input)&&object(input.manifest)){
  const assets={chart:list(m.charts).filter(object),table:list(m.tables).filter(object),card:list(m.cards).filter(object)};
  for(const key of ['charts','tables','cards','sources'])if(m[key]!=null&&(!Array.isArray(m[key])||m[key].some(x=>!object(x))))emit('R001',`manifest.${key}`,'组件或来源列表格式无效','使用对象数组。');
  for(const [kind,rows] of Object.entries(assets)){
   const ids=rows.map(x=>x.id);if(new Set(ids).size!==ids.length)emit('R004',`manifest.${kind}s`,'组件ID重复','保持每个组件的唯一ID。');
  }
  const sources=list(m.sources).concat(list(input.sources)).filter(object);
  const used=[];
  for(const [i,b] of list(m.blocks).entries()){
   if(!object(b))continue;
   let refs=[];
   if(b.type==='chart')refs=[['chart',b.chartId]];
   if(b.type==='table')refs=[['table',b.tableId]];
   if(b.type==='metric-strip')refs=list(b.cardIds).map(id=>['card',id]);
   for(const [kind,id] of refs){
    const item=assets[kind].find(a=>a.id===id);
    if(!item){emit('R004',`manifest.blocks[${i}]`,'引用的组件不存在','修正ID；不删除原有章节来绕过。');continue;}
    used.push({kind,item,index:i});
    if(!own(ds,item.dataset)||!Array.isArray(ds[item.dataset]))emit('R004',`${kind}.${id}.dataset`,'组件数据集不存在或类型错误','统一图表与表格的数据输入。');
    const src=item.source||sources.find(s=>s.id===item.sourceId);
    if(!sourceValid(src))emit('R008',`${kind}.${id}.source`,'缺少可定位的来源','声明实际来源文件、URL或查询，不能编造来源。');
    if(kind==='chart'){
     const fields=[item.encodings?.x?.field,item.encodings?.y?.field,...list(item.encodings?.y?.fields),item.encodings?.color?.field].filter(Boolean);
     for(const f of fields)if(list(ds[item.dataset]).length&&!list(ds[item.dataset]).every(r=>own(r,f)))emit('R004',`chart.${id}.${f}`,'图表字段与数据不一致','修正字段映射，保留同一分析数据源。');
     if(!fields.length)emit('R004',`chart.${id}.encodings`,'缺少图表字段绑定','使用canonical encodings。');
     const declared=list(contract.metrics).some(v=>v.dataset===item.dataset&&(v.field===item.encodings?.y?.field||list(item.encodings?.y?.fields).includes(v.field))&&nonempty(v.unit));
     if(!unitKnown(item,src)&&!declared)emit('R006',`chart.${id}.unit`,'缺少可识别的量纲','在轴标签、单位或对应指标声明中明确单位。');
     const neighbors=[m.blocks[i-1],m.blocks[i+1]];
     if(!neighbors.some(n=>n?.type==='markdown'&&plain(n.body||'').replace(/^#+[^\n]*\n?/,'').length>=20))emit('R015',`chart.${id}`,'缺少相邻正文解读','紧邻图表说明判断、含义和必要限制；标题不替代解读。');
     if(item.type==='line'&&!/最高|最低|最新/.test(allText))emit('W009',`chart.${id}`,'趋势图关键点待核对','标出最高、最低与最新值，可通过相邻关键点表辅助阅读。');
     if(item.type==='scatter'&&!item.encodings?.label?.field)emit('W009',`chart.${id}`,'散点缺少直接名称标注','保留异常点名称和值，不能仅依赖悬停。');
    }
    if(kind==='table'){
     const cols=list(item.columns).map(c=>c.field);
     if(!item.defaultSort)emit('W011',`table.${id}.defaultSort`,'未显式声明默认排序','建议按比较或时间顺序选择现有列；缺省排序不等于数据引用错误。');
     else if(!cols.includes(item.defaultSort.field))emit('R004',`table.${id}.defaultSort`,'默认排序引用了不存在的列','按比较或时间顺序选择现有列。');
     for(const f of cols)if(list(ds[item.dataset]).length&&!list(ds[item.dataset]).every(r=>own(r,f)))emit('R004',`table.${id}.${f}`,'表格字段与数据不一致','修正数据和列名对应关系。');
    }
   }
  }
  if(!object(contract)||!q.profiles.includes(contract.type||'generic'))emit('R014','manifest.reportContract','报告类型声明无效','使用business、retention、research、mechanism或generic。');
  if(!m.reportContract)emit('W001','manifest.reportContract','旧格式缺少结构化报告口径，按兼容模式检查','补充本报告参数；兼容通过不代表口径已认证。');
  else if(contract.type!=='mechanism')for(const key of ['population','period','timezone'])if(!filled(contract[key]))emit('R005',`manifest.reportContract.${key}`,'缺少已填写的本报告关键口径','填写本任务最后确认的口径；不套用别的报告定义。');
  for(const k of ['metrics','assertions','openQuestions'])if(contract[k]!=null&&!Array.isArray(contract[k]))emit('R014',`manifest.reportContract.${k}`,'声明须为数组','按检查器接口示例填写。');
  for(const [i,metric] of list(contract.metrics).entries()){
   const loc=`manifest.reportContract.metrics[${i}]`;
   if(!object(metric)){emit('R014',loc,'指标声明须为对象','按接口填写指标声明。');continue;}
   if(metric.scale!=null&&!['fraction','percent_points','native'].includes(metric.scale))emit('R014',loc,'未知指标尺度','使用fraction、percent_points或native。');
   if(['min','max'].some(k=>metric[k]!=null&&(typeof metric[k]!=='number'||!Number.isFinite(metric[k])))||(metric.min!=null&&metric.max!=null&&metric.min>metric.max))emit('R014',loc,'指标上下界无效','上下界须为有限数值，且min不大于max。');
   if(!filled(metric.dataset)||!filled(metric.field)||!filled(metric.unit)||!filled(metric.definition))emit('R005',loc,'指标缺少已填写的字段、定义或单位','声明dataset、field、unit、definition。');
   if(metric.kind==='ratio'&&!nonempty(metric.denominator))emit('R006',loc,'比例没有说明分母','区分同端全部游戏与两厂商合计等不同分母。');
   const formats=[];
   for(const {kind,item} of used)if(item.dataset===metric.dataset){
    if(kind==='chart'&&(item.encodings?.y?.field===metric.field||list(item.encodings?.y?.fields).includes(metric.field)))formats.push(item.encodings?.y?.format);
    if(kind==='table')formats.push(...list(item.columns).filter(c=>c.field===metric.field).map(c=>c.format));
    if(kind==='card')formats.push(...list(item.metrics).filter(c=>c.field===metric.field).map(c=>c.format));
   }
   if(formats.includes('percent')&&metric.scale==='percent_points')emit('R007',loc,'百分数值又使用了fraction百分比格式','0.58配percent；58配number及%单位。不要双重乘100。');
   if(!own(ds,metric.dataset)||!list(ds[metric.dataset]).every(r=>own(r,metric.field)))emit('R004',loc,'指标声明引用的字段不存在','修正dataset和field，不默认忽略。');
   for(const [j,r] of list(ds[metric.dataset]).entries())if(object(r)&&typeof r[metric.field]==='number'&&((metric.min!=null&&r[metric.field]<metric.min)||(metric.max!=null&&r[metric.field]>metric.max)))emit('R007',`${loc}.rows[${j}]`,'数值超出该指标明确声明的范围','复核分母、尺度和定义；RTP可超过100%，不能套用渗透率上限。');
  }
  for(const question of list(contract.openQuestions)){
   if(!object(question)){emit('R014','manifest.reportContract.openQuestions','待定项须为对象','填写parameter和问题。');continue;}
   if(contract.decisions?.[question.parameter]?.status==='confirmed')emit('R012',`manifest.reportContract.openQuestions.${question.parameter}`,'已确认参数又被列为待定','删除过时待定项，或明确记录此次重新决策的依据。');
  }
  function rows(ref){if(!object(ref)||!Array.isArray(ds[ref.dataset]))throw Error('断言引用的数据集不存在');return ds[ref.dataset].filter(r=>Object.entries(ref.where||{}).every(([k,v])=>r[k]===v));}
  function value(ref){const r=rows(ref);if(r.length!==1||!own(r[0],ref.field))throw Error('单值断言须通过where唯一定位现有字段');return r[0][ref.field];}
  const close=(a,b,t)=>a===null||b===null?a===b:typeof a==='number'&&typeof b==='number'?Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=t:a===b;
  for(const [i,a] of list(contract.assertions).entries()){
   const loc=`manifest.reportContract.assertions[${i}]`;
   try{
    const tol=a.tolerance??1e-8;if(typeof tol!=='number'||tol<0)throw Error('tolerance须为非负数');
    if(a.kind==='equal'||a.kind==='sum'){
     const expected=value(a.right);const selected=rows(a.left);if(!selected.length)throw Error('合计断言没有匹配行，未执行');
     const actual=a.kind==='equal'?value(a.left):selected.reduce((n,r)=>{if(typeof r[a.left.field]!=='number')throw Error('sum只接受数值');return n+r[a.left.field];},0);
     if(!close(actual,expected,tol))emit('R009',loc,'跨表或合计数值不一致','复算同口径来源；不要只修改正文或图形遮盖差异。');
    }else if(['ratio','difference_pp','relative_change'].includes(a.kind)){
     const selected=rows(a);if(!selected.length)throw Error('公式断言没有匹配行，未执行');
     for(const [j,r] of selected.entries()){
      const x=r[a.numerator||a.after],y=r[a.denominator||a.before];
      if(typeof x!=='number'||typeof y!=='number'||!own(r,a.actual))throw Error('公式字段须存在，输入须为数值');
      const expected=a.kind==='ratio'?(y===0?null:x/y):a.kind==='difference_pp'?(x-y)*100:(y===0?null:x/y-1);
      if(!close(r[a.actual],expected,tol))emit('R009',`${loc}.rows[${j}]`,'比例、百分点或相对变化计算不一致','明确公式与尺度；零分母留空，不填成0。');
     }
    }else throw Error('不支持的断言类型');
   }catch(e){emit('R014',loc,e.message,'修正声明，不能把未执行的检查当作通过。');}
  }
  for(const [id,rows] of Object.entries(ds))for(const r of list(rows))if(object(r)&&Object.keys(r).some(k=>/^(user_id|device_id|phone|email|openid|open_id|order_id|order_no|bank_account)$/i.test(k))){emit('R011',`snapshot.datasets.${id}`,'检测到禁止交付的个人或订单明细字段','在受控环境聚合后再交付；检查结果不会输出字段值。');break;}
 }
 const serialized=typeof input==='string'?input:JSON.stringify(input);
 if(/Bearer\s+[A-Za-z0-9_-]{20,}|["']?(?:api[_-]?key|secret|password)["']?\s*[=:]\s*["']?(?:sk-|[A-Za-z0-9_-]{24,})/i.test(serialized))emit('R011','input','疑似包含凭据','移除凭据并核对来源；不在回执中复述敏感值。');
 const verification=options.verification;
 if(verification){
  if(verification.ok===false||verification.status==='failed'||Object.values(verification.stages||{}).includes('failed')||Object.values(verification.checks||{}).includes(false))emit('R013','delivery','渲染或交付验证失败','修复具体失败后再交付。');
  if(verification.stages?.verification==='structural_only')emit('W010','delivery','仅结构验证，尚未完成视觉检查','保留真实验证状态，不声称桌面或窄屏已验收。');
 }
 if(format!=='artifact')emit('W010','coverage','仅完成文本和结构检查，未验证业务计算或跨载体一致性','使用结构化artifact或补充人工复核与回读。');
 const applied=[];
 if(options.exceptions!==undefined&&!Array.isArray(options.exceptions))emit('R010','exceptions','例外列表格式无效','使用按报告哈希和位置限定的例外数组。');
 for(const [i,e] of list(options.exceptions).entries()){
  try{
   if(!object(e)||e.report_sha256!==inputSha||!nonempty(e.reason)||!nonempty(e.approved_by)||!nonempty(e.location)||e.location.includes('*')||q.exceptions_nonwaivable.includes(e.rule_id))throw Error('例外缺少精确范围、理由或不允许豁免');
   const ref=e.approval_reference;if(!object(ref)||!nonempty(ref.path)||!nonempty(ref.sha256))throw Error('缺少批准证据引用及哈希');
   const baseRoot=fs.realpathSync(options.root||projectRoot);
   const file=fs.realpathSync(path.resolve(baseRoot,ref.path));const rel=path.relative(baseRoot,file);
   if(rel.startsWith('..')||path.isAbsolute(rel)||digest(fs.readFileSync(file))!==ref.sha256)throw Error('批准证据路径或哈希无效');
   const matched=issues.filter(v=>v.rule_id===e.rule_id&&v.location===e.location);
   if(!matched.length)throw Error('例外没有对应的实际问题');
   for(const issue of matched){issue.waived=true;issue.exception={reason:e.reason,approved_by:e.approved_by,approval_reference:ref};}
   applied.push({rule_id:e.rule_id,location:e.location});
  }catch{emit('R010',`exceptions[${i}]`,'例外无效，未跳过检查','提供与本文件哈希、具体规则和位置对应的项目内批准记录。');}
 }
 const errors=issues.filter(i=>i.severity==='error'&&!i.waived).length,warnings=issues.filter(i=>i.severity==='warning'&&!i.waived).length;
 return {version:1,standard_version:policy.standard_version,format,input_sha256:inputSha,status:errors?'blocked':warnings?'passed_with_warnings':'passed',errors,warnings,issues,exceptions_applied:applied,
  coverage:{structure:'checked',text:'checked',declared_calculations:format==='artifact'&&list(contract.assertions).length?(issues.some(i=>['R009','R014'].includes(i.rule_id))?'failed_or_incomplete':'checked'):'not_declared',business_truth:'manual_review_required',visual:verification?.stages?.verification||'not_checked',lark_readback:verification?.document_id&&(/verified|passed/.test(verification.status||''))&&!Object.values(verification.checks||{}).includes(false)?'verified_from_supplied_receipt':'not_checked'},network_calls:0,content_modified:false};
}
export function checkFile(inputPath,options={}){
 const raw=fs.readFileSync(inputPath,'utf8'),format=options.format||(inputPath.endsWith('.md')?'markdown':inputPath.endsWith('.xml')?'xml':'artifact');
 let input=raw;
 if(format==='artifact')try{input=JSON.parse(raw);}catch{return checkReport(null,{...options,format,sha256:digest(raw)});}
 return checkReport(input,{...options,format,sha256:digest(raw)});
}

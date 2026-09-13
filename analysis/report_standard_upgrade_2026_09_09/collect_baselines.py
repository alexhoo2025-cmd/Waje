"""Read-only report inventory. Only compact version evidence is retained."""
from pathlib import Path
import json,re,hashlib,subprocess,datetime,concurrent.futures

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
CASES=[
 ('h5-lightgame','H5轻量化用户行为与留存','analysis/h5_lightgame_report_reorg_2026_08_31'),
 ('paid-retention','三端付费留存','analysis/all_platform_cohort_value_2026_09_04'),
 ('whot-tracking','Whot十五项埋点最终修改版','analysis/whot_tracking_review_2026_09_07/v2'),
 ('whot-phases','Whot一二期拆分','analysis/whot_two_phase_tracking_2026_09_07'),
 ('whot-phase1','Whot一期','analysis/whot_two_phase_tracking_2026_09_07/phase1'),
 ('whot-phase2','Whot二期','analysis/whot_two_phase_tracking_2026_09_07/phase2'),
 ('whot-comparison','Whot旧版与一期对照','analysis/whot_legacy_vs_phase1_2026_09_07'),
 ('whot-robot','Whot机器人机制','analysis/whot_robot_explainer_2026_09_08'),
 ('x7','X7汇总与关联分析','analysis/x7_hot_tada_currency_summary_2026_09_04'),
 ('tanzania','坦桑行业与产品调研','analysis/tanzania_gambling_research_2026_09_08'),
 ('tanzania-nigeria','坦桑与尼日利亚对比','analysis/tanzania_nigeria_rmg_2026_09_08'),
 ('tada-pp','Tada/PP下注与回访','analysis/tada_pp_app_h5_actual_2026_09_08'),
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def walk(obj):
 if isinstance(obj,dict):
  yield obj
  for v in obj.values():yield from walk(v)
 elif isinstance(obj,list):
  for v in obj:yield from walk(v)
def inspect_case(case):
 ident,name,rel=case;p=ROOT/rel
 row={'id':ident,'name':name,'directory':rel,'basis':'delivery_pointer_and_current_local_snapshot_not_mtime','files':[],'receipts':[],'document_candidates':[]}
 if not p.exists():row['status']='missing';return row
 for f in sorted(p.glob('*.json')):
  if not re.search(r'artifact|receipt|verification|readback|split',f.name):continue
  if 'before' in f.name or f.stat().st_size>8_000_000:continue
  try:x=json.loads(f.read_text())
  except (ValueError,UnicodeError):continue
  if not isinstance(x,dict):continue
  row['files'].append({'path':str(f.relative_to(ROOT)),'sha256':sha(f)})
  if f.name=='artifact.json':
   m=x.get('manifest',{});row['title']=m.get('title');row['headings']=[b.get('body','').splitlines()[0] for b in m.get('blocks',[]) if b.get('type')=='markdown' and b.get('body','').startswith('#')]
  if re.search(r'receipt|verification',f.name):
   row['receipts'].append({'path':str(f.relative_to(ROOT)),**{k:x[k] for k in ['status','revision','revision_id','stages','url'] if k in x}})
  # Only use top-level/report document pointers, not nested image/source provenance URLs.
  for obj in [x,x.get('document',{}),x.get('data',{}),x.get('data',{}).get('document',{})]:
   if not isinstance(obj,dict):continue
   url=obj.get('url');token=obj.get('document_id');revision=obj.get('revision_id',obj.get('revision'))
   if url and re.search(r'/docx/[A-Za-z0-9]+',url):token=re.search(r'/docx/([A-Za-z0-9]+)',url)[1]
   if token and re.search(r'lark|readback|create|final',f.name):row['document_candidates'].append({'token':token,'url':url,'cached_revision':revision,'from':str(f.relative_to(ROOT))})
  html=x.get('html')
  if isinstance(html,str) and Path(html).is_file():row['files'].append({'path':str(Path(html).relative_to(ROOT)),'sha256':sha(Path(html))})
 for name in ['report.md','报告.md','report.xml','lark-source.xml','lark_release_candidate.xml','lark-release.xml']:
  f=p/name
  if f.is_file():row['files'].append({'path':str(f.relative_to(ROOT)),'sha256':sha(f)})
 row['status']='local_snapshot_recorded';return row
def remote(token):
 args=['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc',token,'--scope','outline','--max-depth','2','--as','user','--format','json']
 try:
  r=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=40)
  x=json.loads(r.stdout)
  if not x.get('ok'):return {'document_id':token,'status':'unavailable','error_type':x.get('error',{}).get('type')}
  d=x.get('data',{}).get('document',{})
  return {'document_id':token,'status':'revision_checked','revision':d.get('revision_id'),'outline_sha256':hashlib.sha256(d.get('content','').encode()).hexdigest(),'outline':re.sub('<[^>]+>',' ',d.get('content',''))[:1600]}
 except Exception as e:return {'document_id':token,'status':'unavailable','error_type':type(e).__name__}
def main():
 registry=[inspect_case(c) for c in CASES]
 candidates=[]
 pattern=re.compile(r'用户.{0,8}(修改|调整|表述|配色|阅读|高亮)|人工修改|浏览器批注|用户批注')
 scanned=0;skipped=0
 for folder in ['analysis','knowledge','scripts','config']:
  for p in sorted((ROOT/folder).rglob('*')):
   if not p.is_file() or p.suffix not in ['.md','.py','.mjs','.json']:continue
   if OUT in p.parents or any(x in p.parts for x in ['_generated','.venv','node_modules','queries','results','raw','transcripts']):continue
   if '分析报告' in p.name or p.name in ['report_quality.mjs','check_report_quality.mjs']:continue
   if p.stat().st_size>2_000_000:skipped+=1;continue
   scanned+=1
   try:lines=p.read_text().splitlines()
   except (UnicodeError,OSError):continue
   hits=[{'line':i+1,'excerpt':line[:180]} for i,line in enumerate(lines) if pattern.search(line)]
   if hits:candidates.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'matches':hits[:8] if p.suffix=='.md' else [{'line':h['line']} for h in hits[:8]],'classification':'candidate_only_not_automatically_a_user_preference'})
 tokens=sorted({d['token'] for r in registry for d in r['document_candidates']})
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(remote,tokens))
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for name,obj in [('baseline-registry.json',{'checked_at':stamp,'reports':registry,'remote_checks':checks,'original_reports_modified':False}),('discovery-candidates.json',{'scan_roots':['analysis','knowledge','scripts','config'],'scanned_text_files':scanned,'large_files_skipped':skipped,'excluded':['raw/transcripts/user details','generated graph','this upgrade outputs'],'checked_at':stamp,'files':candidates})]:
  (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'reports':len(registry),'candidate_files':len(candidates),'remote_checks':len(checks),'remote_available':sum(c['status']=='revision_checked' for c in checks),'mutations':'audit files only'},ensure_ascii=False))
if __name__=='__main__':main()

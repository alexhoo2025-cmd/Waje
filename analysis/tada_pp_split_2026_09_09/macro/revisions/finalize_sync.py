"""Verify source stability and register a completed render; no remote writes."""
import argparse,datetime,hashlib,json,re,runpy,subprocess,xml.etree.ElementTree as E
from pathlib import Path
base=Path(__file__).resolve().parent;macro=base.parent;root=macro.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True);args=parser.parse_args()
run=base/('lark-revision-'+args.revision)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads((run/'readback.json').read_text())
fresh=json.loads(subprocess.check_output(['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc',doc['document_id'],'--detail','full','--as','user','--format','json']))['data']['document']
assert fresh['revision_id']==doc['revision_id'] and fresh['content']==doc['content'],'Source changed during render; compare and resync'
a=json.loads((macro/'artifact.json').read_text()); old=json.loads((run/'before-artifact.json').read_text())
assert a['snapshot']==old['snapshot']
receipt=json.loads((run/'html-receipt.json').read_text())
assert receipt['ok'] and receipt['stages']['verification']=='passed'
norm=lambda s: re.sub(r'\s|\*','',s)
bodies='\n'.join(b.get('body','') for b in a['manifest']['blocks'])
chart_text='\n'.join(c['title']+c.get('subtitle','') for c in a['manifest']['charts'])
visible=norm(re.sub('<[^>]+>','',bodies)+chart_text)
missing=[]
for p in E.fromstring('<doc>'+doc['content']+'</doc>').iter('p'):
    t=norm(''.join(p.itertext()))
    if t and t not in visible: missing.append(t)
assert not missing,missing
prev=json.loads((base/'from-lark-latest/readback.json').read_text())
def images(d): return [n.attrib for n in E.fromstring('<doc>'+d['content']+'</doc>').iter('img')]
assert images(doc)==images(prev),'Image references changed: inspect before chart reuse'
output=root/'output/html/Tada与PP-宏观对比-新老用户下注与回访-2026-09-09.html'
record={'source_url':'https://ksg964l11fam.sg.larksuite.com/docx/'+doc['document_id'],'source_revision':doc['revision_id'],'source_snapshot':str((run/'readback.json').relative_to(root)),'source_sha256':sha(run/'readback.json'),'verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_sha256':sha(macro/'artifact.json'),'html_path':str(output.relative_to(root)),'html_sha256':sha(output),'receipt':str((run/'html-receipt.json').relative_to(root)),'status':'synced','source_rechecked':True,'paragraph_preservation':'passed','image_references_unchanged':True,'dataset_unchanged':True,'feishu_written':False}
(macro/'last-approved-version.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
builder=runpy.run_path(str(macro.parent/'build_reports.py'))
try: builder['Report']('macro','test','test')
except RuntimeError as e: record['legacy_generator_guard']=str(e)
else: raise AssertionError('Guard missing')
assert sha(macro/'artifact.json')==record['artifact_sha256']
(run/'final-verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False))

import json,subprocess,hashlib,xml.etree.ElementTree as E,re
from pathlib import Path
P=Path(__file__).resolve().parent;OUT=P/'feishu-2026-09-11';ROOT=P.parents[1];CLI='/Users/robin/.local/node/bin/lark-cli'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((OUT/'source-version.json').read_text())
assert sha(Path(source['source']))==source['html_sha256'],'Source changed during conversion'
release=OUT/'release.xml';assert release.read_bytes()==(ROOT/'draft_6db4a0f1_folder/draft.xml').read_bytes()
receipt=OUT/'create.json'
if receipt.exists():
 result=json.loads(receipt.read_text());assert result.get('ok'),'Previous result requires inspection; do not blindly create again'
else:
 run=subprocess.run([CLI,'docs','+create','--doc-format','xml','--content','@./draft_6db4a0f1_folder/draft.xml','--parent-position','my_library','--as','user','--format','json'],capture_output=True,text=True,timeout=240)
 result=json.loads(run.stdout);receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2));assert result.get('ok'),result
doc=result['data']['document'];token=doc['document_id'];print(json.dumps({'document_id':token,'url':doc.get('url'),'warnings':result['data'].get('warnings')},ensure_ascii=False),flush=True)
read=json.loads(subprocess.check_output([CLI,'docs','+fetch','--doc',token,'--detail','full','--as','user','--format','json'],text=True,timeout=180))
(OUT/'readback.json').write_text(json.dumps(read,ensure_ascii=False,indent=2));assert read.get('ok'),read
expected=E.fromstring('<doc>'+release.read_text()+'</doc>');actual=E.fromstring('<doc>'+read['data']['document']['content']+'</doc>')
norm=lambda t:re.sub(r'\s+','',''.join(t.itertext()))
counts={tag:{'expected':len(list(expected.iter(tag))),'actual':len(list(actual.iter(tag)))}for tag in ['h1','table','img','callout']}
assert all(v['expected']==v['actual']for v in counts.values()),counts
def cells(root):return [c for t in root.iter('table')for c in t.iter()if c.tag in ['th','td']]
ec,ac=cells(expected),cells(actual);assert [norm(c)for c in ec]==[norm(c)for c in ac],'Table text differs'
assert norm(expected)==norm(actual),'Full document text differs'
styles=[]
for i,(e,c)in enumerate(zip(ec,ac)):
 if e.attrib.get('background-color'):
  styles.append({'cell':i,'expected':e.attrib['background-color'],'actual':c.attrib.get('background-color')})
assert all(s['actual'] for s in styles),'Cell fill missing'
color_map={'light-gray':'rgba(245,246,247,0.9)','light-blue':'rgb(240,244,255)','light-orange':'rgb(255,245,235)','light-yellow':'rgb(254,255,240)'}
assert all(s['actual']==color_map[s['expected']]for s in styles),'Cell fill differs from requested native palette'
verification={'status':'passed','url':doc.get('url'),'document_id':token,'revision':read['data']['document']['revision_id'],'source_revision':source['revision'],'source_html_sha256':source['html_sha256'],'release_sha256':sha(release),'counts':counts,'all_table_cell_text_equal':True,'full_text_equal':True,'colored_cells':styles,'images':[{k:v for k,v in im.attrib.items()}for im in actual.iter('img')],'warnings':result['data'].get('warnings',[]),'database_queries':0,'original_html_unchanged':sha(Path(source['source']))==source['html_sha256']}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2));print(json.dumps({'status':'passed','url':verification['url'],'revision':verification['revision'],'counts':counts,'colored_cells':len(styles)},ensure_ascii=False))

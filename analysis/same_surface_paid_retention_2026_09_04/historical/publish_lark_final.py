import json,subprocess,xml.etree.ElementTree as E
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-final-polish';cli='/Users/robin/.local/node/bin/lark-cli'
receipt=R/'lark-create.json'
if receipt.exists():result=json.loads(receipt.read_text())
else:
    result=json.loads(subprocess.check_output([cli,'docs','+create','--doc-format','xml','--content','@./draft_98863e35_folder/draft.xml','--as','user','--format','json']))
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2))
assert result.get('ok'),result
doc=result['data']['document'];id=doc['document_id'];print(json.dumps({'id':id,'url':doc.get('url'),'warnings':result['data'].get('warnings')},ensure_ascii=False),flush=True)
read=json.loads(subprocess.check_output([cli,'docs','+fetch','--doc',id,'--detail','full','--as','user','--format','json']))
(R/'lark-readback.json').write_text(json.dumps(read,ensure_ascii=False,indent=2));assert read.get('ok'),read
actual=E.fromstring('<doc>'+read['data']['document']['content']+'</doc>');expected=E.fromstring('<doc>'+(R/'lark-release.xml').read_text()+'</doc>')
metrics={}
for tag in ['table','img','h1','h2']:
    x,y=len(list(expected.iter(tag))),len(list(actual.iter(tag)));metrics[tag]={'expected':x,'actual':y};assert x==y,(tag,x,y)
def cells(root):return [''.join(c.itertext()).strip() for t in root.iter('table') for c in t.iter() if c.tag in ('th','td')]
assert cells(expected)==cells(actual),'Table values differ'
want=['49.5%','19.2%','24.3%','第14','APP对比暂缺同口径数据'];text=''.join(actual.itertext())
for s in want:assert s in text,s
verification={'status':'passed','url':doc.get('url'),'revision':read['data']['document']['revision_id'],'counts':metrics,'table_cells_equal':True,'key_claims_present':True}
(R/'lark-verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2));print(json.dumps(verification,ensure_ascii=False))

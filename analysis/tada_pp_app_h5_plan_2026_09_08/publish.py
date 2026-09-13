from pathlib import Path
import subprocess,json,re,xml.etree.ElementTree as ET,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1];CLI='/Users/robin/.local/node/bin/lark-cli'
def save(n,o):(P/n).write_text(json.dumps(o,ensure_ascii=False,indent=2))
def call(args):
 r=subprocess.run([CLI,*args,'--as','user','--format','json'],cwd=ROOT,capture_output=True,text=True,timeout=300)
 j=json.loads(r.stdout or r.stderr)
 if not j.get('ok'):raise RuntimeError(str(j.get('error'))[:1200])
 return j
def norm(e):return re.sub(r'\s+','',''.join(e.itertext()))
rp=P/'lark-create-receipt.json'
if rp.exists():j=json.loads(rp.read_text())
else:
 assert not (P/'lark-create-attempt.json').exists(),'Existing creation attempt must be inspected before retry'
 save('lark-create-attempt.json',{'status':'started','xml_sha256':hashlib.sha256((P/'release.xml').read_bytes()).hexdigest()})
 j=call(['docs','+create','--doc-format','xml','--content','@./draft_b3c51a76_folder/draft.xml']);save(rp.name,j)
d=j['data']['document'];rb=call(['docs','+fetch','--doc',d['document_id'],'--detail','full']);save('lark-readback.json',rb)
actual=ET.fromstring('<root>'+rb['data']['document']['content']+'</root>');expected=ET.fromstring('<root>'+(P/'release.xml').read_text()+'</root>')
def cells(root):return [[norm(c) for c in t.iter() if c.tag in ['th','td']] for t in root.iter('table')]
missing=[norm(e) for e in expected if e.tag in ['p','title','h1','h2','ol','ul'] and norm(e) not in norm(actual)]
checks={'table_cells_exact':cells(actual)==cells(expected),'tables_8':len(cells(actual))==8,'image_1':len(list(actual.iter('img')))==1,'all_text_present':not missing,'no_warnings':not j['data'].get('warnings')}
v={'status':'passed' if all(checks.values()) else 'needs_review','url':d.get('url'),'document_id':d['document_id'],'revision':rb['data']['document'].get('revision_id'),'checks':checks,'table_cells':sum(map(len,cells(actual))),'missing_text':missing}
save('lark-verification.json',v);print(json.dumps(v,ensure_ascii=False))

"""Create once, preserve receipt, then verify every native table cell by API."""
from pathlib import Path
import subprocess,json,xml.etree.ElementTree as ET,re,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1];CLI='/Users/robin/.local/node/bin/lark-cli'
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2))
def call(args):
    r=subprocess.run([CLI,*args,'--as','user','--format','json'],cwd=ROOT,capture_output=True,text=True,timeout=600)
    text=r.stdout.strip() or r.stderr.strip();p=json.loads(text)
    if not p.get('ok'):raise RuntimeError(str(p.get('error'))[:1000])
    return p
def normalize(s):return re.sub(r'\s+','',s)
def tree(s):return ET.fromstring('<root>'+s+'</root>')
def tablecells(root):return [[normalize(''.join(c.itertext())) for c in t.iter() if c.tag in ['td','th']] for t in root.iter('table')]
def main():
    receipt=P/'lark-create-receipt.json';attempt=P/'lark-create-attempt.json'
    if receipt.exists():created=json.loads(receipt.read_text())
    else:
        if attempt.exists():raise RuntimeError('Creation already attempted without a complete receipt; inspect before any retry')
        save(attempt.name,{'draft_sha256':hashlib.sha256((P/'lark-release.xml').read_bytes()).hexdigest(),'status':'creation_started'})
        created=call(['docs','+create','--doc-format','xml','--content','@./draft_fc010586_folder/draft.xml'])
        save(receipt.name,created)
    doc=created['data']['document'];readback=call(['docs','+fetch','--doc',doc['document_id'],'--detail','full']);save('lark-readback.json',readback)
    actual=tree(readback['data']['document']['content']);expected=tree((P/'lark-release.xml').read_text())
    expected_cells=tablecells(expected);actual_cells=tablecells(actual)
    paragraphs=[normalize(''.join(p.itertext())) for p in expected if p.tag in ['p','h1','h2','title','ol']]
    alltext=normalize(''.join(actual.itertext()))
    missing=[p for p in paragraphs if p not in alltext]
    checks={'title':normalize(doc.get('title') or ''.join(expected.find('title').itertext())) in alltext,'tables_19':len(actual_cells)==19,'table_cells_exact':actual_cells==expected_cells,'images_8':len(list(actual.iter('img')))==8,'all_narrative_present':not missing,'creation_warnings_empty':not created['data'].get('warnings')}
    verification={'status':'passed' if all(checks.values()) else 'needs_review','url':doc.get('url'),'document_id':doc['document_id'],'revision_id':readback['data']['document'].get('revision_id'),'checks':checks,'missing_text':missing,'expected_table_cells':sum(map(len,expected_cells)),'actual_table_cells':sum(map(len,actual_cells)),'warnings':created['data'].get('warnings',[])}
    save('lark-verification.json',verification);print(json.dumps(verification,ensure_ascii=False))
    return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())

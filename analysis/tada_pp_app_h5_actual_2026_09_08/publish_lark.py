"""Create once, then read back and verify the requested Lark report."""
from pathlib import Path
import subprocess,json,sys,re,xml.etree.ElementTree as ET,hashlib

ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
CLI='/Users/robin/.local/node/bin/lark-cli'
def call(args):
    p=subprocess.run([CLI,*args],cwd=ROOT,text=True,capture_output=True)
    try:r=json.loads(p.stdout)
    except json.JSONDecodeError:raise RuntimeError('Lark response is not JSON; inspect the live operation before retrying')
    if not r.get('ok'):raise RuntimeError(json.dumps(r.get('error',{}),ensure_ascii=False))
    return r
def text(node):return re.sub(r'\s+',' ',''.join(node.itertext())).strip()
def matrix(t):return [[text(c) for c in row if c.tag in ['th','td']] for row in t.findall('.//tr')]

def main():
    assert json.loads((P/'delivery-receipt.json').read_text())['stages']['verification']=='passed'
    assert json.loads((P/'final-validation.json').read_text())['status']=='share_with_caveats'
    draft='@./draft_bad6327b_folder/draft.xml'
    profile=call(['docs','+script','--command','parse','--content',draft,'--format','json'])
    assert profile['data']['assessment']['status']=='passed'
    (P/'lark-profile-check.json').write_text(json.dumps(profile['data'],ensure_ascii=False,indent=2)+'\n')
    saved=P/'lark-create.json';started=P/'lark-create-started.json'
    if saved.exists():created=json.loads(saved.read_text())
    else:
        if started.exists():raise RuntimeError('Prior creation started without a receipt; resolve document identity before retrying')
        started.write_text(json.dumps({'status':'create_started','draft':'draft_bad6327b_folder/draft.xml'}))
        response=call(['docs','+create','--doc-format','xml','--content',draft,'--as','user','--format','json'])
        created=response['data'];saved.write_text(json.dumps(created,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'stage':'created','document':created['document'].get('url'),'warnings':created.get('warnings',[])},ensure_ascii=False),flush=True)
    doc=created['document'];token=doc['document_id']
    result=call(['docs','+fetch','--doc',token,'--detail','full','--as','user','--format','json'])['data']['document']
    (P/'lark-readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    original=ET.fromstring('<document>'+(P/'lark-source.xml').read_text()+'</document>')
    fetched=ET.fromstring('<document>'+result['content']+'</document>')
    a=original.findall('.//table');b=fetched.findall('.//table')
    assert len(a)==len(b)==9,(len(a),len(b))
    for index,(ta,tb) in enumerate(zip(a,b)):assert matrix(ta)==matrix(tb),('table mismatch',index)
    assert len(original.findall('.//img'))==len(fetched.findall('.//img'))==7
    assert len(fetched.findall('.//h1'))==11
    assert len(fetched.findall('.//source'))==3
    assert text(original.find('title'))==text(fetched.find('title'))
    fetched_text=text(fetched)
    for n in original.findall('.//h1'):assert text(n) in fetched_text
    for value in ['28.7倍','19.4倍','14.84%','12.32%','7.33%','4.45%','115.49亿NGN','23.70亿NGN','到账TC未计算']:
        assert value in fetched_text,value
    assert all(any(k in img.attrib for k in ['src','ref','token']) for img in fetched.findall('.//img'))
    warnings=created.get('warnings',[])
    receipt={'status':'readback_verified' if not warnings else 'readback_verified_with_warnings',
      'url':doc.get('url'),'document_id':token,'revision':result.get('revision_id'),'charts':7,'tables':9,'attachments':3,'chapters':11,
      'table_cells_verified':sum(len(r) for t in a for r in matrix(t)),
      'key_claims_verified':10,'warnings':warnings,
      'source_artifact_sha256':hashlib.sha256((P/'artifact.json').read_bytes()).hexdigest(),
      'readback_sha256':hashlib.sha256(result['content'].encode()).hexdigest(),
      'full_game_table_delivery':'same canonical rows attached as 共同游戏对照.csv; HTML keeps native full table',
      'external_messages_sent':False}
    (P/'lark-delivery-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False),flush=True)

if __name__=='__main__':main()

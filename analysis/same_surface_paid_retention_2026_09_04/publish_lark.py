"""Create exactly once, then read back; never send messages or alter sharing."""
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CLI='/Users/robin/.local/node/bin/lark-cli'
def call(args):
    r=subprocess.run([CLI,*args,'--as','user','--format','json'],cwd=ROOT.parents[1],capture_output=True,text=True,timeout=240)
    try:a=json.loads(r.stdout)
    except ValueError:a={'ok':False,'error':(r.stderr or r.stdout)[:600]}
    return a

def main():
    validation=json.loads((ROOT/'validation.json').read_text())
    assert validation['status']=='partial' and all(c['status']=='passed' for c in validation['checks'])
    path=ROOT/'lark_create_receipt.json'
    if path.exists():
        creation=json.loads(path.read_text())
    else:
        creation=call(['docs','+create','--doc-format','xml','--content','@./draft_13d5a181_folder/draft.xml'])
        path.write_text(json.dumps(creation,ensure_ascii=False,indent=2),encoding='utf-8')
    if not creation.get('ok'):
        print(json.dumps(creation,ensure_ascii=False));return 1
    doc=creation['data']['document'];print(json.dumps({'created':doc.get('url'),'document_id':doc['document_id'],'warnings':creation['data'].get('warnings')},ensure_ascii=False),flush=True)
    readback=call(['docs','+fetch','--doc',doc['document_id'],'--detail','with-ids'])
    (ROOT/'lark_readback.json').write_text(json.dumps(readback,ensure_ascii=False,indent=2),encoding='utf-8')
    if not readback.get('ok'):
        print(json.dumps(readback,ensure_ascii=False));return 2
    content=readback['data']['document']['content']
    checks={'title':doc.get('title','') or json.loads((ROOT/'artifact.json').read_text())['manifest']['title'],
      'key_values':all(v in content for v in ['49.18%','5,242','2,578','11,246,238']),
      'tables':content.count('<table'),'images':content.count('<img'),
      'partial_label':'阶段' in content,'url':doc.get('url'),'revision':readback['data']['document'].get('revision_id')}
    checks['passed']=checks['key_values'] and checks['tables']==7 and checks['images']==2 and checks['partial_label'] and checks['title'] in content
    (ROOT/'lark_verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False))
    return 0 if checks['passed'] else 3
if __name__=='__main__':raise SystemExit(main())

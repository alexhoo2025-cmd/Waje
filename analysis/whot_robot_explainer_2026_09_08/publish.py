from pathlib import Path
import subprocess,json,re,xml.etree.ElementTree as ET,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1];CLI='/Users/robin/.local/node/bin/lark-cli'
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2))
def call(args):
 r=subprocess.run([CLI,*args,'--as','user','--format','json'],cwd=ROOT,capture_output=True,text=True,timeout=300)
 j=json.loads(r.stdout or r.stderr)
 if not j.get('ok'):raise RuntimeError(str(j.get('error'))[:1300])
 return j
def text(e):return re.sub(r'\s+','',''.join(e.itertext()))
def main():
 rp=P/'create-receipt.json'
 if rp.exists():created=json.loads(rp.read_text())
 else:
  assert not (P/'create-attempt.json').exists(),'Prior create attempt needs inspection'
  save('create-attempt.json',{'status':'started','source_revision':16})
  created=call(['docs','+create','--doc-format','xml','--content','@./draft_24935f41_folder/draft.xml']);save('create-receipt.json',created)
 d=created['data']['document'];rb=call(['docs','+fetch','--doc',d['document_id'],'--detail','full']);save('readback.json',rb)
 actual=ET.fromstring('<r>'+rb['data']['document']['content']+'</r>');expected=ET.fromstring('<r>'+(P/'release.xml').read_text()+'</r>')
 def cells(root):return [[text(c) for c in t.iter() if c.tag in ['th','td']] for t in root.iter('table')]
 missing=[text(e) for e in expected if e.tag in ['p','title','h1','h2','ol','ul'] and text(e) not in text(actual)]
 boards=list(actual.iter('whiteboard'));checks={'tables_exact':cells(actual)==cells(expected),'tables_5':len(list(actual.iter('table')))==5,'diagrams_2':len(boards)==2,'all_text_present':not missing,'no_warnings':not created['data'].get('warnings')}
 exports=[]
 for i,b in enumerate(boards,1):
  dest=f'analysis/whot_robot_explainer_2026_09_08/board-preview-{i}.png'
  if not list(P.glob(f'board-preview-{i}.*')):
   error_path=P/f'board-export-{i}-gap.json'
   if not error_path.exists():
    try:
     out=call(['whiteboard','+export','--whiteboard-token',b.get('token') or b.get('src'),'--output-type','preview','--output',dest]);save(f'board-export-{i}.json',out)
    except RuntimeError as e:save(error_path.name,{'status':'unavailable','reason':str(e),'fallback':'已登录浏览器目视验证，不扩大权限'})
  exports.append({'board_token':b.get('token') or b.get('src'),'files':[str(x.relative_to(ROOT)) for x in P.glob(f'board-preview-{i}.*')]})
 visual=json.loads((P/'visual-qa.json').read_text()) if (P/'visual-qa.json').exists() else {}
 checks['visual_verified']=all(e['files'] for e in exports) or visual.get('browser_boards_visible')==2
 verification={'status':'passed' if all(checks.values()) else 'needs_review','url':d.get('url'),'document_id':d['document_id'],'revision':rb['data']['document'].get('revision_id'),'checks':checks,'missing':missing,'exports':exports,'visual_qa':visual,'source_revision':16}
 save('verification.json',verification);print(json.dumps(verification,ensure_ascii=False))
if __name__=='__main__':main()

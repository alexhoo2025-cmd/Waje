"""Inspect newer remote report revisions without persisting full report bodies."""
from pathlib import Path
import json,subprocess,hashlib,re,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
registry=json.loads((P/'baseline-registry.json').read_text())
out=[]
for remote in registry['remote_checks']:
 if remote['status']!='revision_checked':continue
 matches=[r for r in registry['reports'] if any(d['token']==remote['document_id'] for d in r['document_candidates'])]
 cached=[d['cached_revision'] for r in matches for d in r['document_candidates'] if d['token']==remote['document_id'] and isinstance(d['cached_revision'],int)]
 if cached and max(cached)==remote['revision']:continue
 r=subprocess.run(['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc',remote['document_id'],'--detail','full','--as','user','--format','json'],cwd=ROOT,text=True,capture_output=True,timeout=50)
 data=json.loads(r.stdout)
 if not data.get('ok'):out.append({'document_id':remote['document_id'],'status':'unavailable'});continue
 d=data['data']['document'];content=d['content'];tree=ET.fromstring('<document>'+content+'</document>')
 def txt(n):return re.sub(r'\s+',' ',''.join(n.itertext())).strip()
 paragraphs=[]
 for n in tree:
  if n.tag=='p' and txt(n):paragraphs.append(txt(n)[:280])
  if n.tag=='callout':paragraphs.extend(txt(p)[:280] for p in n.findall('p') if txt(p))
 item={'document_id':remote['document_id'],'revision':d['revision_id'],'status':'newer_remote_inspected',
  'content_sha256':hashlib.sha256(content.encode()).hexdigest(),'title':txt(tree.find('title')) if tree.find('title') is not None else '',
  'headings':[txt(n) for n in tree.iter() if n.tag in ['h1','h2','h3']],
  'style_summary':{'tables':len(tree.findall('.//table')),'images':len(tree.findall('.//img')),'callouts':len(tree.findall('.//callout')),
    'bold_nodes':len(tree.findall('.//b')),'header_backgrounds':sorted({n.get('background-color','unspecified') for n in tree.findall('.//th')})},
  'selected_opening_paragraphs':paragraphs[:6],
  'preference_status':'final_version_evidence_not_automatic_user_approval'}
 out.append(item)
(P/'remote-final-style.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False))

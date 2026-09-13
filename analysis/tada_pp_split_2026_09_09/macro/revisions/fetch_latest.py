"""Archive full Lark response by revision and show a content diff; no remote writes."""
import difflib,json,subprocess,xml.etree.ElementTree as E
from pathlib import Path
base=Path(__file__).resolve().parent
r=json.loads(subprocess.check_output(['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc','HWzVdQfWVoHhZRxiwcBlIJ55grh','--detail','full','--as','user','--format','json']))
assert r.get('ok'),r
d=r['data']['document']; dest=base/('lark-revision-'+str(d['revision_id']))
dest.mkdir(exist_ok=True)
p=dest/'readback.json'
if p.exists(): assert json.loads(p.read_text())==d,'Revision content changed'
else: p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
old=json.loads((base/'from-lark-latest/readback.json').read_text())
def lines(x):
    return [E.tostring(n,encoding='unicode') for n in E.fromstring('<doc>'+x+'</doc>')]
diff='\n'.join(difflib.unified_diff(lines(old['content']),lines(d['content']),fromfile='revision181',tofile='revision'+str(d['revision_id'])))
(dest/'source.diff').write_text(diff)
print(dest)
for n in E.fromstring('<doc>'+d['content']+'</doc>'):
    if n.tag not in ('table','img') and E.tostring(n,encoding='unicode') not in lines(old['content']): print(''.join(n.itertext()))
print('images',[(n.get('name'),n.get('token')) for n in E.fromstring('<doc>'+d['content']+'</doc>').iter('img')])

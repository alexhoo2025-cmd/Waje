from pathlib import Path
import subprocess,json,hashlib,xml.etree.ElementTree as ET,datetime
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
r=subprocess.run(['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc','IMquduff5ouFw2xL7vrlDmwSgfc','--detail','full','--as','user','--format','json'],capture_output=True,text=True,cwd=ROOT,timeout=60)
j=json.loads(r.stdout or r.stderr)
assert j.get('ok'),j.get('error')
d=j['data']['document'];root=ET.fromstring('<root>'+d['content']+'</root>');boards=list(root.iter('whiteboard'))
assert len(boards)==1 and boards[0].get('type')=='mermaid'
assert not list(root.iter('cite')),'Inspect sensitive mentions before saving'
(P/'source.xml').write_text(d['content'])
(P/'source-flow.mmd').write_text(boards[0].text)
meta={'title':root.find('title').text,'source_url':'https://ksg964l11fam.sg.larksuite.com/wiki/L2AAwTNlviiVIXkr0Kslw7uZgbf','document_id':d['document_id'],'revision':d['revision_id'],'read_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(d['content'].encode()).hexdigest(),'content_type':'one Mermaid board; no explanatory prose','user_context':'用户指认为Whot机器人机制与策略','boundary':'匹配/补位/降级规则；不是局内出牌算法或生产验证'}
(P/'source-receipt.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print(json.dumps(meta,ensure_ascii=False))

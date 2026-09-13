import json,subprocess,xml.etree.ElementTree as E
from pathlib import Path
P=Path(__file__).resolve().parent;O=P/'feishu-2026-09-11';R=P.parents[1];cli='/Users/robin/.local/node/bin/lark-cli'
read=json.loads((O/'readback.json').read_text())['data']['document'];doc=read['document_id'];actual=E.fromstring('<doc>'+read['content']+'</doc>');expected=E.fromstring('<doc>'+(O/'release.xml').read_text()+'</doc>')
table_id=list(actual.iter('table'))[4].attrib['id'];replacement=E.tostring(list(expected.iter('table'))[4],encoding='unicode')
path=R/'draft_6db4a0f1_folder/table-repair.xml';path.write_text(replacement)
res=json.loads(subprocess.check_output([cli,'docs','+update','--doc',doc,'--command','block_replace','--block-id',table_id,'--revision-id',str(read['revision_id']),'--doc-format','xml','--content','@./draft_6db4a0f1_folder/table-repair.xml','--as','user','--format','json'],text=True,timeout=120))
(O/'color-repair.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));assert res.get('ok'),res;print(json.dumps(res,ensure_ascii=False))

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from publish_lark import call

ROOT=Path(__file__).resolve().parent
creation=json.loads((ROOT/'lark_create_receipt.json').read_text());doc=creation['data']['document']['document_id']
readback=call(['docs','+fetch','--doc',doc,'--detail','full'])
assert readback['ok']
content=readback['data']['document']['content']
tree=ET.fromstring('<doc>'+content+'</doc>')
targets=[(e.attrib['id'],e.attrib['name'],e.attrib.get('caption','')) for e in tree.findall('.//img')]
receipts=[]
for id_,name,caption in targets:
    before=call(['docs','+fetch','--doc',doc,'--scope','range','--start-block-id',id_,'--end-block-id',id_,'--detail','full'])
    assert before['ok']
    node=ET.Element('img',{'path':'@./analysis/same_surface_paid_retention_2026_09_04/charts/'+name,'width':'1000','caption':caption.strip()})
    result=call(['docs','+update','--doc',doc,'--command','block_replace','--block-id',id_,'--doc-format','xml','--content',ET.tostring(node,encoding='unicode')])
    receipts.append(result);assert result['ok'] and result['data']['result']=='success'
(ROOT/'lark_chart_repair.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'repaired_images':len(receipts)}))

"""Insert three bounded additions into the existing phase-2 Lark document and verify."""
import json, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CLI='/Users/robin/.local/node-v24.18.1-darwin-arm64/lib/node_modules/@larksuite/cli/bin/lark-cli'
DOC='O8uod8284o4Qv0xFkDBl96qqgQV'

def call(*args):
    result=json.loads(subprocess.check_output([CLI,'docs',*args,'--as','user'],cwd=ROOT,text=True))
    if not result.get('ok'):raise RuntimeError(result)
    return result['data']
def fetch():return call('+fetch','--doc',DOC,'--detail','full')['document']
def root(d):return ET.fromstring('<root>'+d['content']+'</root>')
def visible(e):return ''.join(e.itertext()).strip()

receipts=[]
for key,heading,next_heading in [
    ('overview','新增需求16｜机器人胜负偏离与整局回放','核心数据指标及算法'),
    ('metrics','需求16｜统计对象、核心指标及算法','具体埋点实现'),
    ('implementation','需求16｜机器人胜负偏离与整局回放实现',None),
]:
    current=fetch();r=root(current)
    if any(e.tag=='h2' and visible(e)==heading for e in r):
        print(key,'already present; verifying only',flush=True)
        continue
    nodes=list(r)
    anchor=nodes[-1].attrib['id'] if next_heading is None else nodes[next(i for i,e in enumerate(nodes) if e.tag=='h1' and visible(e)==next_heading)-1].attrib['id']
    res=call('+update','--doc',DOC,'--command','block_insert_after','--block-id',anchor,'--revision-id',str(current['revision_id']),'--content','@./'+str((HERE/(key+'.xml')).relative_to(ROOT)))
    (HERE/(key+'_write_receipt.json')).write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
    assert res.get('result')=='success',res
    fresh=fetch()
    assert any(e.tag=='h2' and visible(e)==heading for e in root(fresh)),heading
    receipts.append({'section':key,'revision_id':fresh['revision_id'],'warnings':res.get('warnings',[])})
    print(key,'verified',fresh['revision_id'],flush=True)

old='二期新增08—15的详细行为；'
new='二期覆盖原需求08—15，并新增需求16“机器人胜负偏离与整局回放”；'
current=fetch()
if old in current['content']:
    res=call('+update','--doc',DOC,'--command','str_replace','--pattern',old,'--content',new,'--revision-id',str(current['revision_id']))
    assert res.get('result')=='success',res
    (HERE/'scope_write_receipt.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
final=fetch();(HERE/'phase2_after.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
r=root(final)
for key in ['overview','metrics','implementation']:
    desired=ET.fromstring('<root>'+(HERE/(key+'.xml')).read_text()+'</root>')
    # Compare every paragraph, heading and individual table cell, not just the section marker.
    wanted=[visible(e) for e in desired.iter() if e.tag in ['p','h2'] and visible(e)]
    actual=[visible(e) for e in r.iter() if e.tag in ['p','h2'] and visible(e)]
    missing=[x for x in wanted if x not in actual]
    assert not missing,(key,missing[:3])
before=root(json.loads((HERE/'phase2_before.json').read_text()))
old_text=[visible(e).replace(old,new) for e in before.iter() if e.tag in ['p','h1','h2','h3'] and visible(e)]
final_text=[visible(e) for e in r.iter() if e.tag in ['p','h1','h2','h3'] and visible(e)]
assert all(x in final_text for x in old_text),'pre-existing content changed unexpectedly'
headings=[visible(e) for e in r if e.tag=='h1']
assert headings==['总体方案','核心数据指标及算法','具体埋点实现'],headings
receipt={'status':'passed','checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),'document_id':DOC,'url':'https://ksg964l11fam.sg.larksuite.com/docx/'+DOC,'revision_id':final['revision_id'],'pre_existing_content_preserved':True,'all_addition_text_readback':True,'main_headings':headings,'section_receipts':receipts,'tables':len(list(r.iter('table'))),'phase1_modified':False}
(HERE/'publish_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False))

"""Add requirement 16 to all phase-2 local surfaces while preserving existing blocks."""
import copy, hashlib, html, json, re, shutil
from pathlib import Path
from datetime import datetime
from addition import OVERVIEW, METRICS, IMPLEMENTATION, GROUP
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
PHASE=HERE.parent/'phase2'
NOW=datetime.now().astimezone().isoformat(timespec='seconds')

def xml(s):
    if s[0]=='h':return f'<h{s[1]} seq="auto">{html.escape(s[2])}</h{s[1]}>'
    if s[0]=='p':return '<p>'+html.escape(s[1])+'</p>'
    headers,rows=s[1:]
    def cells(values,tag):return ''.join(f'<{tag}><p>{html.escape(str(v))}</p></{tag}>' for v in values)
    return '<table><thead><tr>'+cells(headers,'th')+'</tr></thead><tbody>'+''.join('<tr>'+cells(row,'td')+'</tr>' for row in rows)+'</tbody></table>'

def markdown(s):
    if s[0]=='h':return '#'* (s[1]+1)+' '+s[2]
    if s[0]=='p':return s[1]
    return '| '+' | '.join(s[1])+' |\n| '+' | '.join('---' for _ in s[1])+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('|','／') for v in r)+' |' for r in s[2])

def build():
    backup=HERE/'before_local';backup.mkdir(exist_ok=True)
    names=['artifact.json','report.md','report.xml','requirements.json','html_receipt.json']
    for name in names:
        if not (backup/name).exists():shutil.copy2(PHASE/name,backup/name)
    old_html=ROOT/'output/html/Whot二期埋点计划-2026-09-07.html'
    if not (backup/'report.html').exists():shutil.copy2(old_html,backup/'report.html')
    additions={'overview':OVERVIEW,'metrics':METRICS,'implementation':IMPLEMENTATION}
    for key,sections in additions.items():
        (HERE/(key+'.xml')).write_text('\n'.join(map(xml,sections))+'\n')
    (HERE/'addition.md').write_text('\n\n'.join(markdown(s) for sections in additions.values() for s in sections)+'\n')
    artifact=json.loads((backup/'artifact.json').read_text())
    original=copy.deepcopy(artifact['manifest']['blocks'])
    blocks=artifact['manifest']['blocks']
    new_ids=[]
    for key,sections in additions.items():
        new=[]
        for i,s in enumerate(sections):
            block={'id':f'robot_{key}_{i:02d}','type':'markdown','body':markdown(s)}
            # Keep each heading with following content, using same canonical markdown reader.
            if new and new[-1]['body'].startswith('### ') and '\n\n' not in new[-1]['body']:
                new[-1]['body']+='\n\n'+block['body']
            else:new.append(block)
        new_ids.extend(b['id'] for b in new)
        if key=='overview':index=next(i for i,b in enumerate(blocks) if b.get('body','').startswith('## 核心数据指标'))
        elif key=='metrics':index=next(i for i,b in enumerate(blocks) if b.get('body','').startswith('## 具体埋点'))
        else:index=len(blocks)
        blocks[index:index]=new
    old='二期新增08—15的详细行为；'
    replacement='二期覆盖原需求08—15，并新增需求16“机器人胜负偏离与整局回放”；'
    for b in blocks:
        if 'body' in b:b['body']=b['body'].replace(old,replacement)
    artifact['manifest']['generatedAt']=NOW
    artifact['snapshot']['generatedAt']=NOW
    artifact['snapshot']['datasets']['scope'].append({'topic':'机器人回放','entries':len(GROUP['events'])})
    source={'id':'robot_requirement','label':'新增需求16与Whot玩法/机器人策略','description':'2026-09-08用户需求；机器人策略revision 69、玩法revision 5738；设计待实现。原8项加本次1项，共9项。','path':'analysis/whot_two_phase_tracking_2026_09_07/robot_replay_2026_09_08/addition.md'}
    artifact['manifest']['sources'].append(source)
    artifact['sources'].append(copy.deepcopy(source))
    for target in [artifact['sources'],artifact['manifest']['sources']]:
        for src in target:
            if src.get('id')=='reviewed':src['description']='二期原08—15加新增16；一期01—07保持。新增需求16为2026年9月8日授权设计。'
    # Preserve every pre-existing block except the explicit dependent scope sentence.
    lookup={b['id']:b for b in blocks}
    for b in original:
        expected=copy.deepcopy(b)
        if 'body' in expected:expected['body']=expected['body'].replace(old,replacement)
        assert lookup[b['id']]==expected, b['id']
    (PHASE/'artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
    for suffix in ['md','xml']:
        text=(backup/('report.'+suffix)).read_text()
        conv=markdown if suffix=='md' else xml
        pieces={k:'\n\n'.join(map(conv,v))+'\n\n' for k,v in additions.items()}
        for key,title in [('overview','核心数据指标及算法'),('metrics','具体埋点实现')]:
            anchor='## '+title if suffix=='md' else f'<h1 seq="auto">{title}</h1>'
            assert text.count(anchor)==1
            text=text.replace(anchor,pieces[key]+anchor,1)
        text=text.rstrip()+'\n\n'+pieces['implementation']
        text=text.replace(old,replacement)
        (PHASE/('report.'+suffix)).write_text(text)
    req=json.loads((backup/'requirements.json').read_text());req['groups'].append(GROUP)
    req['revision_date']='2026-09-08';req['schema_state']='proposed_not_deployed'
    (PHASE/'requirements.json').write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n')
    h1=re.findall(r'<h1[^>]*>(.*?)</h1>',(PHASE/'report.xml').read_text())
    assert h1==['总体方案','核心数据指标及算法','具体埋点实现']
    receipt={'generated_at':NOW,'status':'local_built','phase1_unchanged':True,'original_blocks_preserved':True,'added_requirement_id':16,'phase2_requirement_ids':[g['requirement_id'] for g in req['groups']],'phase2_event_contract_count':sum(len(g['events']) for g in req['groups']),'new_logical_event_count':7,'main_headings':h1,'added_block_ids':new_ids,'source_revisions':{'robot_policy':69,'game_rules':5738,'phase2_before':22},'production_deployed':False}
    (HERE/'build_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='added_block_ids'},ensure_ascii=False))

if __name__=='__main__':build()

"""Recompute the bounded 9006 snapshot and package the technical report input."""
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
db = ROOT / 'samples.sqlite3'
if Path(str(db)+'-wal').exists():
    raise RuntimeError('live_wal_requires_consistent_backup')
before = hashlib.sha256(db.read_bytes()).hexdigest()
c = sqlite3.connect(f'file:{db}?immutable=1', uri=True)
c.row_factory = sqlite3.Row
rows = []
for r in c.execute("select id,phase,settlement from matches where game='9006' order by rowid"):
    s = json.loads(r['settlement'] or '{}')
    if s.get('visible') is True and s.get('result') in ('win','loss','draw'):
        rows.append(dict(round=f'R{len(rows)+1}', result=s['result'],
            stake_displayed=s.get('stake'), recorded_return=s.get('gross_return_displayed'),
            player_points=s.get('player_points'), opponent_points=s.get('opponent_points'),
            end_reason=s.get('end_reason'), autoplay_entries=None,
            qualification='unknown_autoplay_count', source_record=r['id']))
c.close()
assert hashlib.sha256(db.read_bytes()).hexdigest() == before
assert len(rows) == 3 and sum(r['result']=='win' for r in rows) == 2
out=ROOT/'final_report';out.mkdir(exist_ok=True)
with (out/'rounds.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
stake=sum(r['stake_displayed'] for r in rows)
returned=sum(r['recorded_return'] for r in rows)
summary={'completed_observations':len(rows),'wins':2,'losses':1,
    'stake_displayed_total':stake,'recorded_return_total':returned,
    'conditional_net':round(returned-stake,6),'conditional_rtp':returned/stake,
    'certified_rtp':None,'autoplay_le3_qualified':None,
    'latest_continuation_new_completed':0,'latest_stop':'insufficient_game_balance',
    'latest_home_balance':200.8,'latest_game_balance':0.8,
    'source_sha256':before,'four_player_matches':0}
(out/'analysis.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
md=(ROOT/'final_test_report.md').read_text()
parts=md.split('\n## ')
blocks=[{'id':'title','type':'markdown','body':parts[0].strip()}]
for i,p in enumerate(parts[1:]):
    blocks.append({'id':f'section-{i}','type':'markdown','body':'## '+p.strip()})
at=datetime.now(timezone.utc).isoformat()
source={'id':'observations','label':'9006 test observations and execution audit',
    'path':'analysis/whot_test_experience_2026_09_07/v3_1/samples.sqlite3',
    'query':{'engine':'SQLite','language':'sql','tables_used':['matches','events'],
    'description':'Visible settlements only; game 9006; excludes lobby and aborted entries',
    'sql':"SELECT phase, settlement FROM matches WHERE game='9006' AND json_extract(settlement,'$.visible')=1;"}}
artifact={'surface':'report','manifest':{'version':1,'surface':'report',
    'title':parts[0].strip().lstrip('# '),'description':'测试结束后的机制、数据和执行流程复盘',
    'generatedAt':at,'blocks':blocks,'cards':[],'charts':[],'tables':[],'sources':[source]},
    'snapshot':{'version':1,'generatedAt':at,'status':'ready','datasets':{'rounds':rows}},
    'sources':[source]}
chart={'id':'return-distribution','title':'三局条件性返还比例分布',
    'subtitle':'以胜局1.8为总返还的假设；不是认证RTP',
    'intent':'distribution','question':'已保存三局的返还比例有哪些观察值？',
    'rationale':'只有两个离散结果，用条形频数展示，不拟合概率密度。',
    'type':'horizontalBar','dataset':'distribution','sourceId':'observations',
    'encodings':{'x':{'field':'ratio','type':'nominal','label':'条件性返还比例'},
                 'y':{'field':'count','type':'quantitative','label':'局数'}},
    'layout':'full','valueFormat':'number','palette':{'kind':'sequential','name':'blue'}}
artifact['manifest']['charts']=[chart]
artifact['manifest']['blocks'].insert(5,{'id':'distribution-block','type':'chart','chartId':'return-distribution'})
artifact['snapshot']['datasets']['distribution']=[{'ratio':'0%','count':1},{'ratio':'180%','count':2}]
(out/'artifact.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))

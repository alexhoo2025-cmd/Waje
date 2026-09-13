"""Equivalent union consolidation derived from live view definitions.
Keep the same app/date/xl_id event set; do not replace Origin activity with DAU.
"""
from pathlib import Path
import json,re
P=Path(__file__).resolve().parent
definitions=json.loads((P/'active-view-definitions.json').read_text())
assert "event_type = 'AL'" in definitions['view_metaevent_al']
assert "event_type = 'AQ'" in definitions['view_metaevent_aq']
for key in ['login','logout','register']:
    assert 'view_event_server' in definitions['view_metaevent_'+key] and 'view_event_client' in definitions['view_metaevent_'+key]
windows=[('2026-08-02','2026-08-15'),('2026-08-16','2026-08-29'),('2026-08-30','2026-09-09')]
for n,(start,end) in enumerate(windows,2):
    src=P/f'0{n}_origin_returns.sql';s=src.read_text()
    old=f"""SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.view_metaevent_active_events`
WHERE target_day BETWEEN DATE '{start}' AND DATE '{end}' AND app_id=90006
GROUP BY activity_date,xl_id"""
    branches=[]
    for table,events in [('view_event_server',["LOGIN","LOGOUT","REGISTER"]),('view_event_client',["LOGIN","LOGOUT","REGISTER","AL","AQ"]),('view_event_web',["AL","AQ","PD"])]:
        quoted=','.join("'"+e+"'" for e in events)
        branches.append(f"SELECT target_day AS activity_date,xl_id FROM `wajenigeria.origin_hfyl.{table}` WHERE target_day BETWEEN DATE '{start}' AND DATE '{end}' AND app_id=90006 AND event_type IN ({quoted})")
    new='SELECT activity_date,xl_id FROM (\n'+'\nUNION ALL\n'.join(branches)+'\n) GROUP BY activity_date,xl_id'
    assert old in s
    dest=P/f'0{n}_origin_returns_optimized.sql';dest.write_text(s.replace(old,new,1));dest.with_suffix('.scope.json').write_text(src.with_suffix('.scope.json').read_text())
(P/'scan-authorization.json').write_text(json.dumps({'user_approved':'不用考虑5GiB的限制，执行查询，数据准确第一','per_query_limit':'waived for this task','cumulative_limit_gib':25,'optimization':'Merge repeated physical-source reads with identical event filters; final activity date/xl_id DISTINCT unchanged'},ensure_ascii=False,indent=2))

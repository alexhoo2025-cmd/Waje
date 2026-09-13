"""Efficiency guard for explicitly declared query windows, not a SQL parser.

Complements the read-only SQL validator and BigQuery dry-run. It catches literal
date bounds outside the task window; parameterized/dynamic dates need manual review.
"""
import datetime,json,re
from pathlib import Path

def check(sql_path):
    p=Path(sql_path);spec=p.with_suffix('.scope.json')
    if not spec.exists():raise ValueError('Missing query window declaration: '+str(spec))
    c=json.loads(spec.read_text());start=datetime.date.fromisoformat(c['start']);end=datetime.date.fromisoformat(c['end'])
    if start>end:raise ValueError('Invalid query window')
    sql=re.sub(r'/\*.*?\*/|--[^\n]*',' ',p.read_text(),flags=re.S)
    dates=[datetime.date.fromisoformat(x) for x in re.findall(r"\bDATE\s*'([0-9]{4}-[0-9]{2}-[0-9]{2})'",sql,re.I)]
    if not dates:raise ValueError('No literal DATE bounds; resolve parameter/dynamic windows before execution')
    outside=sorted(set(str(d) for d in dates if d<start or d>end))
    if outside:raise ValueError('Query date outside declared task window: '+', '.join(outside))
    return {'start':str(start),'end':str(end),'literal_dates_checked':len(dates),'scope':'literal bounds only; per-table pruning verified by dry-run and review'}

if __name__=='__main__':
    import sys
    try:print(json.dumps(check(sys.argv[1]),ensure_ascii=False))
    except (ValueError,KeyError) as e:print('BLOCKED: '+str(e));raise SystemExit(2)

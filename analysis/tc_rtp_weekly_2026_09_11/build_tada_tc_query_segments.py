#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;query=(ROOT/'queries/11_tada_player_same_day_tc_optimized.sql').read_text()
segments=[('12a_tada_tc_0903_0905','2026-09-03','2026-09-05'),('12b_tada_tc_0906_0908','2026-09-06','2026-09-08'),('12c_tada_tc_0909_0910','2026-09-09','2026-09-10')]
for name,start,end in segments:
    sql=query.replace("DATE '2026-09-03' AND DATE '2026-09-10'",f"DATE '{start}' AND DATE '{end}'")
    (ROOT/'queries'/f'{name}.sql').write_text(sql)
    (ROOT/'queries'/f'{name}.scope.json').write_text(json.dumps({'start':start,'end':end,'purpose':f'Google Cloud BigQuery API aggregate segment for Tada same-day recharge, withdrawal and TC: {start} through {end}'},ensure_ascii=False))
print(json.dumps({'segments':segments}))

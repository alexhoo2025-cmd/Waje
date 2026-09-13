"""Idempotently append an observed round and UI submission evidence."""
import json,sys
from pathlib import Path
from lab import Store, ROOT
path=Path(sys.argv[1]);r=json.loads(path.read_text())
s=Store(ROOT/'samples.sqlite3')
exists=s.c.execute("select id from matches where json_extract(meta,'$.recording_source')=?",(path.name,)).fetchone()
if exists:
 print(json.dumps({'status':'already_recorded','id':exists[0]}));raise SystemExit()
mid=s.begin({'client_game_id':'9006','phase':'scenario' if r['stake']>1 else 'calibration','strategy_arm':r.get('strategy','first_legal_play'),'policy_variant':r.get('policy_variant'),'recording_source':path.name,'actual_player_count':r.get('players',2),'room_id':f"standard_{r['stake']}_{r.get('players',2)}p",'stake':r['stake']})
for i,e in enumerate(r['events'],2):
 s.append(mid,i,{'type':'ui_submission','kind':e[0],'selected':bool(e[1]),'timestamp_ms':e[2],'submitted':e[3]})
s.finish(mid,{'visible':True,'result':r['result'],'end_reason':r.get('end_reason','unknown'),'stake':r['stake'],'settlement_display':r['settlement_display'],'player_points':r['player_points'],'opponent_points':r['opponent_points'],'autoplay_observed':r.get('autoplay_observed'),'quality':'observed_unverified_coverage'})
print(json.dumps({'id':mid,'events':len(r['events']),'status':'saved'}))

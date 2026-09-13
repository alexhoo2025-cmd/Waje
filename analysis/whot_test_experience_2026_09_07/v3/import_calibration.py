"""Idempotent recovery of calibration logs captured outside the formal scheduler."""
import argparse
import json
from pathlib import Path
from lab import ROOT,Store,digest,encoded,eligibility,now


def ingest(store,log_path,settlement_path):
    rows=[json.loads(x) for x in log_path.read_text().splitlines() if x.strip()]
    settlement=json.loads(settlement_path.read_text());source_hash=digest(rows)
    # A redacted settlement evidence file is authoritative for visibility when
    # it contains a result and end reason. Normalize that fact explicitly, but
    # keep its quality/coverage fields unchanged so an uncontrolled or
    # incomplete calibration can never become formal merely by importing it.
    if settlement.get('result') in ('win','loss','draw') and settlement.get('end_reason'):
        settlement.setdefault('visible',True)
    id_='calibration-log:'+source_hash
    previous=store.c.execute('select source_hash from matches where id=?',(id_,)).fetchone()
    complete_hash=digest([rows,settlement])
    if previous:
        if previous[0]!=complete_hash:raise ValueError('existing_calibration_evidence_changed')
        return {'status':'skipped','match_id':id_}
    meta=dict(client_game_id='6001',phase='calibration',strategy_arm='first_legal_play',
              ruleset_version='observed_matching_calibration',game_build='unknown',
              vision_profile_version='6001-pixel-calibration',controller_version='visible-controller-v3.0',
              actual_player_count=2,room_id='low_room',stake=settlement['stake'],
              source_log_hash=source_hash,timing_source='observed_log_utc',imported_after_completion=True,
              settlement_time_source='recorded_at_only',actual_settlement_at=settlement.get('observed_at'))
    quality=eligibility(meta,settlement,rows)
    with store.c:
        store.c.execute('insert into matches values(?,?,?,?,?,?,?,?,?,?)',
            (id_,'6001','calibration',meta['strategy_arm'],rows[0]['observed_at'],settlement.get('observed_at') or now(),
             encoded(meta),encoded(settlement),encoded(quality),complete_hash))
        for seq,row in enumerate(rows,1):
            store.c.execute('insert into events values(?,?,?,?,?)',(id_,seq,row['type'],encoded(row),digest(row)))
    return {'status':'inserted','match_id':id_,'quality':quality}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('settlement',type=Path)
    p.add_argument('--db',type=Path,default=ROOT/'samples.sqlite3');a=p.parse_args()
    print(json.dumps(ingest(Store(a.db),a.log,a.settlement),ensure_ascii=False,indent=2))

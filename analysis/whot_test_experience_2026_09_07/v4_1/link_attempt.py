"""Link immutable operation evidence to an existing settlement; never add a match."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

def link(db_path, source_path):
    path=Path(source_path)
    raw=path.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    data=json.loads(raw)
    with sqlite3.connect(db_path) as db:
        row=db.execute('SELECT payload FROM live_matches WHERE id=?', (data['match_id'],)).fetchone()
        if row is None: raise ValueError('settlement_not_found')
        settlement=json.loads(row[0])
        for key in ('match_id','game_id','bet','actual_players','balance_before','balance_after_debit'):
            if key not in data or key not in settlement or data[key]!=settlement[key]:
                raise ValueError('identity_mismatch:'+key)
        expected=settlement.get('attempt_source')
        if expected!=path.name: raise ValueError('unreferenced_source')
        events=data.get('events')
        if not isinstance(events,list) or not events: raise ValueError('events_missing')
        if any(not isinstance(e,dict) or not isinstance(e.get('kind'),str) for e in events):
            raise ValueError('invalid_event')
        db.execute('CREATE TABLE IF NOT EXISTS operation_sources (hash TEXT PRIMARY KEY, match_id TEXT NOT NULL, filename TEXT NOT NULL, raw_json TEXT NOT NULL, UNIQUE(match_id,filename))')
        db.execute('CREATE TABLE IF NOT EXISTS operation_events (source_hash TEXT NOT NULL, source_seq INTEGER NOT NULL, match_id TEXT NOT NULL, observed_at TEXT, kind TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(source_hash,source_seq))')
        prior=db.execute('SELECT hash FROM operation_sources WHERE match_id=? AND filename=?',(data['match_id'],path.name)).fetchone()
        if prior and prior[0]!=digest: raise ValueError('source_changed_requires_revision')
        if prior:
            return {'status':'skipped','match_id':data['match_id'],'source_hash':digest,'inserted_events':0}
        db.execute('INSERT INTO operation_sources VALUES (?,?,?,?)',(digest,data['match_id'],path.name,raw.decode()))
        for seq,event in enumerate(events,1):
            db.execute('INSERT INTO operation_events VALUES (?,?,?,?,?,?)',(digest,seq,data['match_id'],event.get('at'),event['kind'],json.dumps(event)))
        return {'status':'inserted','match_id':data['match_id'],'source_hash':digest,'inserted_events':len(events)}

if __name__=='__main__':
    print(json.dumps(link(Path(__file__).with_name('derived.sqlite3'),sys.argv[1])))

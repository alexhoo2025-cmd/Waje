"""Append live CUA observations and replayable event records, idempotently."""
import hashlib,json,sqlite3,sys
from pathlib import Path

def ingest(path):
    raw=Path(path).read_bytes();d=json.loads(raw);h=hashlib.sha256(raw).hexdigest()
    db=sqlite3.connect(Path(__file__).with_name('derived.sqlite3'))
    db.execute('CREATE TABLE IF NOT EXISTS live_matches(id TEXT PRIMARY KEY,source_hash TEXT NOT NULL UNIQUE,payload TEXT NOT NULL)')
    prior=db.execute('SELECT source_hash FROM live_matches WHERE id=?',(d['match_id'],)).fetchone()
    if prior and prior[0]!=h:raise ValueError('source_changed_requires_revision')
    with db:
        db.execute('INSERT OR IGNORE INTO live_matches VALUES(?,?,?)',(d['match_id'],h,raw.decode()))
        for seq,e in enumerate(d['events'],1):
            db.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?)',
             (d['match_id']+':'+str(seq),d['match_id'],seq,e.get('action_id'),e['kind'],json.dumps(e)))
    print(json.dumps({'match_id':d['match_id'],'source_hash':h,'events':db.execute('SELECT count(*) FROM events WHERE match_id=?',(d['match_id'],)).fetchone()[0]}))
    db.close()
if __name__=='__main__':ingest(sys.argv[1])

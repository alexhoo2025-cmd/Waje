"""Rebuild derived V3.1 projections without modifying V3 evidence or its database."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from lab import Store,ROOT,digest,encoded,eligibility,now,VERSION


def migrate(source, destination):
    if Path(source).resolve()==Path(destination).resolve():raise ValueError('source_must_remain_immutable')
    old=sqlite3.connect(f'file:{Path(source).resolve()}?mode=ro',uri=True);old.row_factory=sqlite3.Row
    old.execute('pragma query_only=ON');old.execute('BEGIN')
    new=Store(destination);new.init_schedule()
    new.c.executescript('''CREATE TABLE IF NOT EXISTS source_records(
      source_id TEXT, sha256 TEXT, original TEXT NOT NULL, PRIMARY KEY(source_id,sha256));
    CREATE TABLE IF NOT EXISTS assessment_revisions(
      source_id TEXT,source_sha256 TEXT,evaluator_sha256 TEXT,assessment TEXT NOT NULL,
      PRIMARY KEY(source_id,source_sha256,evaluator_sha256));
    CREATE TABLE IF NOT EXISTS observation_sessions(
      source_sha256 TEXT PRIMARY KEY,relative_path TEXT NOT NULL,record_count INTEGER NOT NULL,
      frame_count INTEGER NOT NULL,submitted_count INTEGER NOT NULL,accepted_count INTEGER NOT NULL);''')
    counts=dict(read=0,inserted=0,updated=0,skipped=0,rejected=0)
    evaluator=hashlib.sha256((ROOT/'lab.py').read_bytes()).hexdigest()
    with new.c:
        for row in old.execute('select * from matches order by id'):
            counts['read']+=1;raw=dict(row);source_sha=digest(raw);key='v3:'+row['id']
            existing=new.c.execute('select source_hash from matches where id=?',(key,)).fetchone()
            raw_meta=json.loads(row['meta']);meta=dict(raw_meta)
            meta.update(source_generation='v3',claimed_strategy=row['arm'],actual_control_source='unknown',
                        evidence_eligible_for_formal=False,imported_at=now())
            # Legacy loop recording times are not event timestamps; preserve their origin explicitly.
            if row['phase']=='calibration':
                meta.update(actual_settlement_at=None,claimed_recorded_finish=row['finished_at'])
            settlement=json.loads(row['settlement'] or '{}')
            if settlement.get('end_reason')=='settlement_visible':settlement['end_reason']='unknown'
            ev=[json.loads(e[0]) for e in old.execute('select payload from events where match_id=? order by seq',(row['id'],))]
            quality=eligibility(meta,settlement,ev)
            quality['eligible']=False
            quality['reasons']=sorted(set(quality['reasons']+['legacy_execution_unverified']))
            prior=new.c.execute('select 1 from assessment_revisions where source_id=? and source_sha256=? and evaluator_sha256=?',(key,source_sha,evaluator)).fetchone()
            new.c.execute('insert or ignore into source_records values(?,?,?)',(key,source_sha,encoded(raw)))
            new.c.execute('insert or ignore into assessment_revisions values(?,?,?,?)',(key,source_sha,evaluator,encoded(quality)))
            if existing and existing[0]==source_sha and prior:
                counts['skipped']+=1;continue
            phase=row['phase'] if row['phase']!='formal' else 'historical'
            values=(key,row['game'],phase,'unknown',row['started_at'],row['finished_at'],encoded(meta),encoded(settlement),encoded(quality),source_sha)
            if existing:
                new.c.execute('update matches set game=?,phase=?,arm=?,started_at=?,finished_at=?,meta=?,settlement=?,quality=?,source_hash=? where id=?',values[1:]+(key,))
                counts['updated']+=1
            else:
                new.c.execute('insert into matches values(?,?,?,?,?,?,?,?,?,?)',values);counts['inserted']+=1
                for seq,e in enumerate(ev,1):new.c.execute('insert into events values(?,?,?,?,?)',(key,seq,e['type'],encoded(e),digest(e)))
        sessions=0
        for path in sorted((Path(source).parent/'calibration_runs').glob('*/observations.jsonl')):
            raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
            rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
            new.c.execute('insert or ignore into observation_sessions values(?,?,?,?,?,?)',
                          (sha,str(path.relative_to(Path(source).parent)),len(rows),sum(r['type']=='frame' for r in rows),
                           sum(r['type']=='action_submitted' for r in rows),sum(r['type']=='action_confirmed' and r.get('accepted') is True for r in rows)))
            sessions+=1
    old.close()
    receipt=dict(status='migrated',counts=counts,observation_sessions=sessions,evaluator_sha256=evaluator,
                 version=VERSION,source_readonly=True,progress=new.progress())
    new.c.close();return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT.parent/'v3/samples.sqlite3')
    p.add_argument('--db',type=Path,default=ROOT/'samples.sqlite3');a=p.parse_args()
    print(json.dumps(migrate(a.source,a.db),ensure_ascii=False,indent=2))

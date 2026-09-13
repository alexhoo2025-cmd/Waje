"""Rebuild a derived evidence ledger without changing V3.2 sources."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'v3_2'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def old_digest(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())

def rebuild():
    snapshot = ROOT / 'frozen'
    snapshot.mkdir(exist_ok=True)
    manifest = {}
    files = sorted(SOURCE.glob('*.json')) + sorted(SOURCE.glob('*.py'))
    for p in files:
        data = p.read_bytes(); h = sha(data)
        target = snapshot / (h + p.suffix)
        if not target.exists(): target.write_bytes(data)
        manifest[p.name] = h
    old = sqlite3.connect(f'file:{SOURCE / "legacy6001_v3_2.sqlite3"}?mode=ro', uri=True)
    old.row_factory = sqlite3.Row
    backup = snapshot / 'baseline.sqlite3'
    if not backup.exists():
        dest = sqlite3.connect(backup); old.backup(dest); dest.close()
    manifest['baseline.sqlite3'] = sha(backup.read_bytes())
    db = sqlite3.connect(ROOT / 'derived.sqlite3')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS sources(hash TEXT PRIMARY KEY,path TEXT,raw_json TEXT,ingested_at TEXT);
    CREATE TABLE IF NOT EXISTS observations(source_hash TEXT PRIMARY KEY,legacy_match_id TEXT,
      event_start TEXT,event_end TEXT,observation_time TEXT,time_status TEXT,
      result TEXT,bet REAL,control_source TEXT,actual_players INTEGER,
      balance_before REAL,balance_after_debit REAL,balance_after REAL,page_return REAL,
      net_change REAL,scope TEXT,eligible INTEGER,exclusion TEXT);
    CREATE TABLE IF NOT EXISTS revisions(id TEXT PRIMARY KEY,source_hash TEXT,field TEXT,
      old_value TEXT,new_value TEXT,reason TEXT,evidence TEXT);
    CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,match_id TEXT,seq INTEGER,
      action_id TEXT,kind TEXT,payload TEXT,UNIQUE(match_id,seq));
    ''')
    now = datetime.now(timezone.utc).isoformat()
    receipts = []
    for p in files:
        if not p.name.startswith(('observation_', 'observed_', 'calibration_')): continue
        raw = json.loads(p.read_text()); h = manifest[p.name]
        db.execute('INSERT OR IGNORE INTO sources VALUES(?,?,?,?)', (h,p.name,json.dumps(raw),now))
        linked = []
        for row in old.execute('SELECT m.match_id,a.run_id,a.requested_players,a.bet_display,a.source_hash FROM matches m JOIN match_attempts a ON a.attempt_id=m.attempt_id'):
            if old_digest([p.name,row['run_id'],row['requested_players'],row['bet_display']]) == row['source_hash']:
                linked.append(row['match_id'])
        before, debit, after = (raw.get(k) for k in ('balance_before','balance_after_debit','balance_after'))
        # Correct against the visible same-round sequence in the recorded tool transcript.
        if p.name == 'observation_6001_bet500_autoplay_win_balance_mismatch_20260909_1225.json':
            for field,value in [('balance_before',162920.2),('balance_after_debit',162420.2),('page_net_change',400.0)]:
                db.execute('INSERT OR IGNORE INTO revisions VALUES(?,?,?,?,?,?,?)',
                    (sha((h+field).encode()),h,field,json.dumps(raw.get(field)),json.dumps(value),
                     'Previous record used the preceding losing round balance.',
                     'Conversation: BET500 Play again frame 162420.2; prior loss 162920.2; win 163320.2.'))
            before,debit = 162920.2,162420.2
        net = float(Decimal(str(after))-Decimal(str(before))) if before is not None and after is not None else None
        scope = 'unattributed' if raw.get('record_type') == 'unattributed_settlement_observation' else 'historical_observation'
        control = raw.get('control_source') or 'unknown'
        # Historical summaries do not prove unique, independently sourced game identity.
        exclusion = 'historical_summary_requires_unique_settlement_evidence'
        if scope == 'unattributed': exclusion = 'unattributed_out_of_batch'
        if len(linked)>1: exclusion = 'ambiguous_legacy_match'
        values=(h,linked[0] if len(linked)==1 else None,None,None,None,'event_time_unknown',
                raw.get('result'),raw.get('stake_display'),control,raw.get('actual_players'),
                before,debit,after,raw.get('page_return_display'),net,scope,0,exclusion)
        db.execute('INSERT OR IGNORE INTO observations VALUES('+','.join('?'*18)+')',values)
        receipts.append({'source':p.name,'sha256':h,'legacy_matches':linked,'exclusion':exclusion})
    db.commit()
    result={'status':'partial','source_count':len(receipts),'legacy_matches':old.execute('SELECT COUNT(*) FROM matches').fetchone()[0],
            'legacy_turns':old.execute('SELECT COUNT(*) FROM turns').fetchone()[0],
            'accepted_toward_100':db.execute('SELECT COUNT(*) FROM observations WHERE eligible=1').fetchone()[0],
            'formal_rtp':None,'items':receipts,'manifest':manifest}
    (ROOT/'migration_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('items','manifest')}))
    db.close();old.close()

if __name__ == '__main__': rebuild()

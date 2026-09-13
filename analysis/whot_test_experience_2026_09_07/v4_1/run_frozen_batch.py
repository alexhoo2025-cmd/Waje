"""Serial batch driver. Never modifies strategy, navigates home, or raises BET."""
import argparse,fcntl,hashlib,json,sqlite3,subprocess,sys,uuid
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/'next_strategy_batch.json'
RESTARTABLE={'autoplay_stop','confirmation_stop','turn_transition_unverified',
             'wild_picker_calibration_required','effect_resolution_unverified'}

def is_restartable(reason):
    """Treat known focus/binding wrappers as recoverable execution stops."""
    value=str(reason or '')
    return any(token in value for token in RESTARTABLE) or any(token in value for token in (
        'focus_not_confirmed','focused_window_changed','chrome_not_foreground','binding_changed'))

def verify_frozen(config):
    for name,digest in config['frozen_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('frozen_code_changed:'+name)

def totals():
    with sqlite3.connect(f'file:{ROOT / "derived.sqlite3"}?mode=ro',uri=True) as db:
        return db.execute('SELECT count(*) FROM live_matches').fetchone()[0]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resume-lobby',action='store_true');ap.add_argument('--manifest',default='next_strategy_batch.json');args=ap.parse_args()
    resume_lobby=args.resume_lobby
    lock=(ROOT/'frozen_batch.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    manifest_path=ROOT/args.manifest
    config=json.loads(manifest_path.read_text());verify_frozen(config)
    receipt=ROOT/('batch-run-'+uuid.uuid4().hex[:10]+'.jsonl')
    with receipt.open('x') as out:
        def emit(kind,**data):
            event=dict(kind=kind,batch_id=config['batch_id'],at=datetime.now(timezone.utc).isoformat(),**data)
            out.write(json.dumps(event)+'\n');out.flush()
            print(json.dumps(event),flush=True)
        def save():
            temp=manifest_path.with_suffix('.pending.json')
            with temp.open('w') as f:json.dump(config,f,ensure_ascii=False,indent=2)
            temp.replace(manifest_path)
        emit('batch_resumed',completed=config['completed_matches'],total=totals(),receipt=str(receipt))
        while config['completed_matches']<config['target_completed_matches']:
            verify_frozen(config)
            remaining=min(config['target_completed_matches']-config['completed_matches'],100-totals())
            if remaining<=0:
                config['status']='overall_target_reached';save();emit('overall_target_reached');return
            bet=int(config.get('bet',1000))
            command=[sys.executable,str(ROOT/'resident_calibration.py'),'--execute','--continuous',
                     '--expected-bet',str(bet),'--max-settlements',str(remaining),'--strategy',config['strategy_version'],
                     '--probe-wild','--recover-autoplay','--quiet','--seconds','1800']
            if resume_lobby:
                entry_flag={1:'--start-bet1',1000:'--start-bet1000',2000:'--start-bet2000',5000:'--start-bet5000'}.get(bet)
                if entry_flag is None: raise RuntimeError(f'unsupported_resume_bet:{bet}')
                command.append(entry_flag);resume_lobby=False
            emit('session_start',remaining=remaining,strategy=config['strategy_version'],bet=bet)
            # Exactly one controller process; wait for its authoritative exit.
            run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            messages=[]
            for line in run.stdout.splitlines():
                try:messages.append(json.loads(line))
                except json.JSONDecodeError:pass
            closed=[m for m in messages if m.get('status')=='closed']
            if not closed:
                config['status']='paused_execution';save();emit('session_not_closed',exit_code=run.returncode);return
            source=Path(closed[-1]['log']).resolve()
            if source.parent!=ROOT or not source.name.startswith('native-'):raise RuntimeError('untrusted_log_path')
            events=[json.loads(line) for line in source.read_text().splitlines()]
            if not events or events[-1]['kind']!='closed':raise RuntimeError('log_not_closed')
            imported=subprocess.run([sys.executable,str(ROOT/'record_continuous_session.py'),str(source)],cwd=ROOT,capture_output=True,text=True)
            if imported.returncode:
                config['status']='paused_ingest';save();emit('ingest_failed',source=source.name);return
            with sqlite3.connect(f'file:{ROOT / "derived.sqlite3"}?mode=ro',uri=True) as db:
                ids=[r[0] for r in db.execute("SELECT id FROM live_matches WHERE json_extract(payload,'$.source_file')=?",(source.name,))]
            new=[mid for mid in ids if mid not in config['completed_match_ids']]
            config['completed_match_ids'].extend(new);config['completed_matches']=len(config['completed_match_ids']);save()
            emit('session_recorded',source=source.name,new_completed=len(new),batch_completed=config['completed_matches'],overall_completed=totals())
            reasons=[e.get('reason') for e in events if e['kind']=='stopped']
            if (not new and not reasons) or any(not is_restartable(reason) for reason in reasons):
                config['status']='paused_execution';save();emit('paused_execution',reasons=reasons,no_new_completed=not new);return
        config['status']='awaiting_ten_match_review';save();emit('batch_complete',completed=config['completed_matches'],overall_completed=totals())

if __name__=='__main__':main()

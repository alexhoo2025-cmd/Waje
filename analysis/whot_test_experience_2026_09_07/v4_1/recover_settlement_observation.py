"""Read-only terminal observation after a stopped worker; never enters a room."""
import argparse,hashlib,json,uuid
from datetime import datetime,timezone
from pathlib import Path
from native_session import Session
from resident_calibration import ROOT,observe_settlement

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);args=ap.parse_args()
    raw=args.source.read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
    assert rows[-1]['kind']=='closed','worker_must_be_closed'
    assert any(r['kind']=='entry_submitted' for r in rows),'entry_evidence_required'
    assert not any(r['kind']=='scope_violation' for r in rows),'scope_violation'
    s=Session(False);out=ROOT/('settlement-recovery-'+uuid.uuid4().hex[:10]+'.jsonl')
    try:
        candidates=[]
        for w in s.call('status')['windows']:
            try:b=s.call('inspect',pid=w['pid'],window_id=w['id'])
            except RuntimeError:continue
            if b.get('origin')=='https://test-h5.wajetan.com' and b.get('path')=='/game/6001-whot':candidates.append((w,b))
        assert len(candidates)==1,'ambiguous_window'
        w,b=candidates[0]
        with out.open('x') as f:
            def emit(kind,**kw):
                f.write(json.dumps(dict(kind=kind,at=datetime.now(timezone.utc).isoformat(),**kw))+'\n');f.flush()
            emit('recovery_start',source=args.source.name,source_sha256=hashlib.sha256(raw).hexdigest(),input_enabled=False)
            observe_settlement(s,w,b,emit,seconds=150)
        print(json.dumps({'output':str(out),'input_enabled':False}))
    finally:s.close()

if __name__=='__main__':main()

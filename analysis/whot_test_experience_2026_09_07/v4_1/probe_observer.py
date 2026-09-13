"""Bounded read-only readiness probe. Never enables native input."""
import json,subprocess,selectors,time,uuid,sys
from pathlib import Path
from datetime import datetime,timezone

def main():
    root=Path(__file__).resolve().parent
    p=subprocess.Popen(['/tmp/whot-native-v4'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
    events=[]
    def call(op,**kw):
        request_id=uuid.uuid4().hex;started=time.monotonic_ns()
        p.stdin.write(json.dumps(dict(op=op,request_id=request_id,**kw))+'\n');p.stdin.flush()
        if not sel.select(8):raise RuntimeError('observer_timeout')
        result=json.loads(p.stdout.readline())
        if result.get('request_id')!=request_id:raise RuntimeError('request_mismatch')
        events.append(dict(op=op,elapsed_ms=(time.monotonic_ns()-started)/1e6,status=result.get('status'),reason=result.get('reason')))
        if result.get('status')!='ok':raise RuntimeError(result.get('reason','native_error'))
        return result
    status='partial';reason=None;frames=[]
    try:
        s=call('status');windows=[w for w in s['windows'] if w['bounds']['Height']>300]
        if len(windows)!=1:raise RuntimeError('window_ambiguous')
        w=windows[0];i=call('inspect',pid=w['pid'])
        if i.get('origin')!='https://test-h5.wajetan.com' or i.get('path')!='/game/6001-whot':raise RuntimeError('wrong_route')
        if '--save-settlement-cards' in sys.argv:
            prefix=str(root.parent/'v3_1'/'captures'/('v41-'+uuid.uuid4().hex))
            material=call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=i['content_bounds'],crop=[0,0,1,1],
              allow_background_capture=True,regions={'settlement_cards':[.615,.30,.145,.13]},
              save_prefix=prefix,save_regions=['settlement_cards'])
            frames.append({'material_path':prefix+'-settlement_cards.png','purpose':'visible_own_settlement_cards_only'})
        for _ in range(3):
            f=call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=i['content_bounds'],crop=[0,0,1,1],
              allow_background_capture=True,regions={'hand':[.30,.74,.40,.25],'table':[.56,.35,.11,.28],'turn':[.36,.63,.31,.10]})
            cards=f.get('regions',{}).get('hand',{}).get('cards',[])
            # Retain only calibrated-state evidence, never free OCR or account areas.
            frames.append({'seq':f.get('capture_seq'),'age_ms':f.get('frame_age_ms'),
              'hand_candidates':len(cards),'verified_cards':sum(c.get('confidence',0)>=.98 for c in cards)})
        reason='vision_not_calibrated';status='blocked_observer_readiness'
    except Exception as e:reason=str(e);status='blocked_probe'
    finally:
        p.terminate()
        try:p.wait(timeout=2)
        except subprocess.TimeoutExpired:p.kill();p.wait()
        sel.close()
    report={'at':datetime.now(timezone.utc).isoformat(),'status':status,'reason':reason,'input_enabled':False,'events':events,'frames':frames}
    destination=root/('observer_probe_'+uuid.uuid4().hex[:8]+'.json')
    destination.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));print(destination)
if __name__=='__main__':main()

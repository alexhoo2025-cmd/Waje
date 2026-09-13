"""Click only a currently OCR-verified Play again at the requested existing BET."""
import argparse,json,re,uuid
from datetime import datetime,timezone
from native_session import Session
from resident_calibration import ROOT,text

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--expected-bet',type=int,choices=(1,100,200,500,1000),required=True);a=ap.parse_args()
    s=Session(True)
    try:
        found=[]
        for w in s.call('status')['windows']:
            try:b=s.call('inspect',pid=w['pid'],window_id=w['id'])
            except RuntimeError:continue
            if b.get('origin')=='https://test-h5.wajetan.com' and b.get('path')=='/game/6001-whot':found.append((w,b))
        assert len(found)==1,'ambiguous_window'
        w,b=found[0];s.call('focus_test_window',pid=w['pid'],window_id=w['id']);cb=b['content_bounds']
        # Reuse effect as a freshness-witness region; the OCR label must remain
        # Play again up to the physical click, not merely at discovery time.
        f=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=cb,crop=[0,0,1,1],allow_background_capture=True,
                 regions={'title':[.3,.08,.4,.17],'bet':[.43,.475,.14,.06],'effect':[.53,.77,.23,.13],'again':[.53,.77,.23,.13]})
        r=f['regions'];bet=re.fullmatch(r'BET\s*:\s*(\d+)',text(r['bet']))
        assert bet and int(bet[1])==a.expected_bet,'bet_mismatch'
        assert any(x in text(r['title']) for x in ('VICTORY','LOSE','DEFEAT')),'not_settlement'
        targets=[v for v in r['again'].get('text',[]) if re.fullmatch(r'PLAY\s+AGAIN(?:\s+\d+)?',v['value'].upper().strip())]
        assert len(targets)==1,'play_again_not_verified'
        x,y,width,height=targets[0]['box'];point=[x+width/2,y+height/2]
        receipt={'at':datetime.now(timezone.utc).isoformat(),'kind':'play_again_intent','expected_bet':a.expected_bet,'point':point,'accepted_by_game':None}
        path=ROOT/('play-again-'+uuid.uuid4().hex[:10]+'.jsonl')
        with path.open('x') as out:
            out.write(json.dumps(receipt)+'\n');out.flush()
            ack=s.call('click',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+point[0]*cb[2],cb[1]+point[1]*cb[3]],canvas_screen=cb,
                       expected_origin=b['origin'],expected_path=b['path'],expected_capture_seq=f['capture_seq'])
            out.write(json.dumps({'kind':'play_again_submitted','ack':ack})+'\n')
        print(json.dumps({'log':str(path),'submitted':True,'accepted_by_game':None}))
    finally:s.close()

if __name__=='__main__':main()

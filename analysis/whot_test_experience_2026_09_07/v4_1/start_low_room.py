"""One-shot BET1 lobby action with visible text, scope and fresh-pixel checks."""
import json,re,uuid
from pathlib import Path
from datetime import datetime,timezone
from native_session import Session

def start_in_session(s,w,b):
    cb=b['content_bounds']
    s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
    prefix=str(Path(__file__).resolve().parent.parent/'v3_1'/'captures'/('lobby-'+uuid.uuid4().hex[:12]))
    for index in range(2):
        saved=dict(save_prefix=prefix,save_regions=['amount']) if index==1 else {}
        f=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=cb,crop=[0,0,1,1],allow_background_capture=True,regions={'bet':[.15,.27,.23,.24],'amount':[.245,.345,.045,.085]},**saved)
    labels=[x['value'].upper().strip() for x in f['regions']['bet'].get('text',[])]
    merged=' '.join(labels)
    amount=s.call('analyze',path=prefix+'-amount.png',regions={'amount':[0,0,1,1]})
    amount_labels=[x['value'].strip() for x in amount['regions']['amount'].get('text',[])]
    if not (re.search(r'ASSETS\s*1\s*\+',merged) and amount_labels==['1']):
        raise RuntimeError('bet1_button_not_verified:'+merged)
    s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
    result=s.call('click',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+.264*cb[2],cb[1]+.393*cb[3]],canvas_screen=cb,expected_origin=b['origin'],expected_path=b['path'],expected_capture_seq=f['capture_seq'])
    return {'at':datetime.now(timezone.utc).isoformat(),'operation':'bet1_entry_click','amount_source':prefix+'-amount.png','input_result':result,'accepted_by_game':None}

def main():
    s=Session(True)
    try:
        candidates=[]
        for w in s.call('status')['windows']:
            try:b=s.call('inspect',pid=w['pid'],window_id=w['id'])
            except RuntimeError:continue
            if b.get('origin')=='https://test-h5.wajetan.com' and b.get('path')=='/game/6001-whot' and not b.get('standalone'):candidates.append((w,b))
        if len(candidates)!=1:raise RuntimeError('test_window_not_unique')
        w,b=candidates[0];cb=b['content_bounds']
        if not 1.55<=cb[2]/cb[3]<=1.75:raise RuntimeError('uncalibrated_aspect')
        s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
        print(json.dumps(start_in_session(s,w,b)))
    finally:s.close()

if __name__=='__main__':main()

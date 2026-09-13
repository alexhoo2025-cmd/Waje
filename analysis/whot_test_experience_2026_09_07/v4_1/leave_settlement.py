"""Exit a visibly completed 6001 round; never press Play again/Win more."""
import json,time
from native_session import Session

def main():
    s=Session(True)
    try:
        matches=[]
        for w in s.call('status')['windows']:
            try:b=s.call('inspect',pid=w['pid'],window_id=w['id'])
            except RuntimeError:continue
            if b.get('origin')=='https://test-h5.wajetan.com' and b.get('path')=='/game/6001-whot':matches.append((w,b))
        if len(matches)!=1:raise RuntimeError('test_window_not_unique')
        w,b=matches[0];cb=b['content_bounds'];s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
        f=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=cb,crop=[0,0,1,1],allow_background_capture=True,regions={'effect':[.35,.08,.3,.17]})
        text=' '.join(x['value'] for x in f['regions']['effect']['text']).upper()
        if not any(x in text for x in ('VICTORY','LOSE','DEFEAT')):raise RuntimeError('settlement_not_verified')
        s.call('click',window_id=w['id'],bounds=w['bounds'],canvas_screen=cb,point=[cb[0]+.955*cb[2],cb[1]+.08*cb[3]],expected_origin=b['origin'],expected_path=b['path'],expected_capture_seq=f['capture_seq'])
        end=time.monotonic()+10
        while time.monotonic()<end:
            current=s.call('inspect',pid=w['pid'],window_id=w['id'])
            if current['origin']==b['origin'] and current['path'] in ('','/'):
                print(json.dumps({'status':'home_verified','window_id':w['id']}));return
            time.sleep(.2)
        raise RuntimeError('exit_not_confirmed')
    finally:s.close()

if __name__=='__main__':main()

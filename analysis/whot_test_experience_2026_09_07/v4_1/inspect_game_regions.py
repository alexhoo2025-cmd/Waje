"""Read only, explicitly scoped visible crops of the existing WHOT 6001 window."""
import json,sys,uuid
from native_session import Session
from resident_calibration import ROOT

s=Session()
try:
    matches=[]
    for w in s.call('status')['windows']:
        try:b=s.call('inspect',pid=w['pid'],window_id=w['id'])
        except RuntimeError:continue
        if b.get('origin')=='https://test-h5.wajetan.com' and b.get('path')=='/game/6001-whot':matches.append((w,b))
    assert len(matches)==1
    w,b=matches[0];regions=json.loads(sys.argv[1])
    prefix=str(ROOT.parent/'v3_1'/'captures'/('ui-check-'+uuid.uuid4().hex[:8]))
    r=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=b['content_bounds'],crop=[0,0,1,1],
             allow_background_capture=True,regions=regions,save_prefix=prefix,save_regions=list(regions))
    print(json.dumps({'prefix':prefix,'text':{k:v.get('text') for k,v in r['regions'].items()}}))
finally:s.close()

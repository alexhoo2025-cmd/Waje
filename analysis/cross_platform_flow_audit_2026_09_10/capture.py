import json,subprocess,hashlib
from pathlib import Path
from datetime import datetime
BASE=Path(__file__).resolve().parent
CLI='/Users/robin/.local/node-v24.18.1-darwin-arm64/lib/node_modules/@larksuite/cli/bin/lark-cli'
for label,doc in [('whot_phase1','AMWfd3uA1okFQ8xhn9bllQsyg7e'),('whot_phase2','O8uod8284o4Qv0xFkDBl96qqgQV')]:
    path=BASE/(label+'.json')
    if path.exists():continue
    res=json.loads(subprocess.check_output([CLI,'docs','+fetch','--as','user','--doc',doc,'--detail','full'],text=True))
    assert res.get('ok'),res
    data=res['data']['document'];data['retrieved_at']=datetime.now().astimezone().isoformat(timespec='seconds')
    data['content_sha256']=hashlib.sha256(data['content'].encode()).hexdigest()
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    import re
    paragraphs=re.findall(r'<p[^>]*>(.*?)</p>',data['content'],flags=re.S)
    matching=[re.sub('<[^>]+>','',p) for p in paragraphs if re.search('user_key|participant_key|client_type|session|transfer|跨端|身份|APP和H5|H5使用|端包',p,re.I)]
    print(json.dumps({'source':label,'revision':data['revision_id'],'relevant_paragraphs':matching},ensure_ascii=False))

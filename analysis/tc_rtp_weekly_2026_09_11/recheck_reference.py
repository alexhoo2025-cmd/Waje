#!/usr/bin/env python3
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;URL='https://ksg964l11fam.sg.larksuite.com/wiki/O4wuw0DsxiACgxkf5XAl6RTHgYO?from=from_copylink';expected=json.loads((ROOT/'reference/manifest.json').read_text())
env={**os.environ,'LARKSUITE_CLI_NO_UPDATE_NOTIFIER':'1','LARKSUITE_CLI_NO_SKILLS_NOTIFIER':'1'}
r=subprocess.run(['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc',URL,'--doc-format','xml','--detail','simple','--as','user','--format','json'],capture_output=True,text=True,check=True,env=env)
d=json.loads(r.stdout)['data']['document'];digest=hashlib.sha256(d['content'].encode()).hexdigest();receipt={'checked_at':datetime.now(timezone.utc).isoformat(),'revision_id':d['revision_id'],'content_sha256':digest,'matches_initial_capture':d['revision_id']==expected['revision_id']and digest==expected['content_sha256']}
(ROOT/'reference/recheck.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));assert receipt['matches_initial_capture'],receipt;print(json.dumps(receipt,ensure_ascii=False))

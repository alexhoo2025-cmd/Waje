"""Create the comparison report once and verify it by Lark API readback."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
CLI=Path('/Users/robin/.local/node/bin/lark-cli')
CREATE=BASE/'lark_create_receipt.json'

def call(args: list[str],timeout: int=240) -> dict:
    result=subprocess.run([str(CLI),*args,'--as','user','--format','json'],cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    payload=result.stdout.strip() or result.stderr.strip()
    if result.returncode:raise RuntimeError(payload[:1200])
    return json.loads(payload)

def main() -> int:
    if CREATE.exists():created=json.loads(CREATE.read_text())
    else:
        created=call(['docs','+create','--doc-format','xml','--content','@./draft_c75bb3ad_folder/draft.xml'])
        CREATE.write_text(json.dumps(created,ensure_ascii=False,indent=2)+'\n')
    if not created.get('ok'):raise RuntimeError(json.dumps(created,ensure_ascii=False)[:1200])
    doc=created['data']['document'];doc_id=doc['document_id']
    readback=call(['docs','+fetch','--doc',doc_id,'--detail','with-ids'])
    (BASE/'lark_readback.json').write_text(json.dumps(readback,ensure_ascii=False,indent=2)+'\n')
    content=readback['data']['document']['content']
    checks={
      'title':'Whot旧版埋点与新版一期计划对比分析' in content,
      'summary':'执行摘要' in content and '匹配请求成为新版最重要的数据对象' in content,
      'scope':all(f'{i:02d} {name}' in content for i,name in enumerate(['用户群体','新人引导','进入与加载','对局选择','房间选择','匹配情况','四人局降级'],1)),
      'reuse':'MC' in content and 'GAMESTART' in content and 'BETREWARD / ASSET' in content,
      'new_chain':'WHOT_MATCH_REQUEST' in content and 'WHOT_MATCH_OFFER' in content,
      'boundaries':'旧日志可重建后再比较' in content and '新版二期需求08—15不在本次比较范围' in content,
      'tables':content.count('<table')==4,
      'images':content.count('<img')==1,
    }
    verification={'status':'passed' if all(checks.values()) else 'failed','url':doc.get('url'),'document_id':doc_id,'revision_id':readback['data']['document'].get('revision_id'),'checks':checks,'warnings':created['data'].get('warnings') or []}
    (BASE/'lark_verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(verification,ensure_ascii=False))
    return 0 if verification['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())

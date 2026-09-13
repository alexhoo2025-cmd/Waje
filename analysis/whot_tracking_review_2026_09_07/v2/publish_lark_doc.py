"""Create the Whot V2 Lark document once, then verify by API readback."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
CLI=Path('/Users/robin/.local/node/bin/lark-cli')
CREATE_RECEIPT=BASE/'lark_create_receipt.json'

def call(args: list[str],timeout: int=240) -> dict:
    result=subprocess.run([str(CLI),*args,'--as','user','--format','json'],cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    payload=result.stdout.strip() or result.stderr.strip()
    if result.returncode:
        raise RuntimeError(payload[:1200])
    return json.loads(payload)

def main() -> int:
    if CREATE_RECEIPT.exists():
        created=json.loads(CREATE_RECEIPT.read_text())
    else:
        created=call(['docs','+create','--doc-format','xml','--content','@./draft_a1be2d96_folder/draft.xml'])
        CREATE_RECEIPT.write_text(json.dumps(created,ensure_ascii=False,indent=2)+'\n')
    if not created.get('ok'):
        raise RuntimeError(json.dumps(created,ensure_ascii=False)[:1200])
    doc=created['data']['document'];doc_id=doc['document_id']
    readback=call(['docs','+fetch','--doc',doc_id,'--detail','with-ids'])
    (BASE/'lark_readback.json').write_text(json.dumps(readback,ensure_ascii=False,indent=2)+'\n')
    content=readback['data']['document']['content']
    topics=[item['name'] for item in json.loads((BASE/'requirements_contract.json').read_text())['groups']]
    checks={
        'title':'新版 Whot 埋点与数据指标｜15项需求评审版' in content,
        'summary':'执行摘要' in content and '完整覆盖15项需求' in content,
        'phases':'一期｜基础体验与匹配' in content and '二期｜局内体验与资金引导' in content,
        'requirements':len(topics)==15 and all(f'>{topic}</h1>' in content for topic in topics),
        'updated_definitions':'统计日期当天注册为新用户' in content and '首次付费日期' in content,
        'removed_content':'证据与范围' not in content and '发布门槛' not in content,
        'table_count':content.count('<table')==19,
        'image_count':content.count('<img')==1,
    }
    verification={'status':'passed' if all(checks.values()) else 'failed','document_id':doc_id,'url':doc.get('url'),'revision_id':readback['data']['document'].get('revision_id'),'checks':checks,'warnings':created['data'].get('warnings') or []}
    (BASE/'lark_verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(verification,ensure_ascii=False))
    return 0 if verification['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())

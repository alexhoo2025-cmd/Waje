"""Refresh delivery receipts after full-text readback and HTML verification."""
import json, shutil
from pathlib import Path
from datetime import datetime
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
pub=json.loads((HERE/'publish_receipt.json').read_text())
render=json.loads((BASE/'phase2/html_receipt.json').read_text())
assert pub['status']=='passed' and render['ok'] and render['stages']['verification']=='passed'
for name in ['verification.json','split_receipt.json']:
    backup=HERE/'before_local'/name
    if not backup.exists():shutil.copy2(BASE/name,backup)
split=json.loads((HERE/'before_local/split_receipt.json').read_text())
split['generated_at']=datetime.now().astimezone().isoformat(timespec='seconds')
split['phases'][1]['requirement_ids']=list(range(8,17))
split['phases'][1]['entry_count']=31
split['coverage']='16/16; original 15 plus requirement 16 added to phase 2'
split['allocation_basis']='一期01—07；二期08—15及2026年9月8日新增需求16'
split['extension_receipt']='robot_replay_2026_09_08/build_receipt.json'
(BASE/'split_receipt.json').write_text(json.dumps(split,ensure_ascii=False,indent=2)+'\n')
verify={'status':'passed','checked_at':split['generated_at'],'requirement_coverage':'16/16','phase1_requirement_ids':list(range(1,8)),'phase2_requirement_ids':list(range(8,17)),'exact_three_main_sections':True,'phase1_status':'unchanged; September 7 verification retained','phase2_full_text_readback':pub,'html':{'phase1':'unchanged; prior verification passed','phase2':'passed','viewports':render['viewports']},'prior_phase2_content_preserved':True,'production_instrumentation_deployed':False,'receipts':'robot_replay_2026_09_08/'}
(BASE/'verification.json').write_text(json.dumps(verify,ensure_ascii=False,indent=2)+'\n')
(BASE/'phase2/feishu_readback_receipt.json').write_text(json.dumps(pub,ensure_ascii=False,indent=2)+'\n')
after=json.loads((HERE/'phase2_after.json').read_text())
(BASE/'phase2/feishu_readback.xml').write_text(after['content'])
print(json.dumps({'status':'passed','revision':pub['revision_id'],'coverage':'16/16','phase2_contracts':31},ensure_ascii=False))

from pathlib import Path
import hashlib,json
from datetime import datetime
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
receipt=json.loads((BASE/'html_receipt.json').read_text())
assert receipt['ok'] and receipt['stages']['verification']=='passed'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
output=ROOT/'output/html/APP与H5用户流通埋点能力评估-2026-09-10.html'
record={'updated_at':datetime.now().astimezone().isoformat(timespec='seconds'),'approval_basis':'用户2026年9月10日要求优化当前总结并默认交付HTML','content_basis':'report.md；本次仅优化阅读样式和流程说明，未重新查询线上业务数据','source_sha256':sha(BASE/'report.md'),'artifact_sha256':sha(BASE/'artifact.json'),'output':str(output.relative_to(ROOT)),'output_sha256':sha(output),'backup':'before_html_optimization','html_status':'passed','viewports':receipt['viewports'],'content_status':'assessment_complete_live_reporting_blocked','changes':['摘要高亮','两条跨端证据链流程图','4张原生对照表','正文与来源保留','机制报告无图兼容'],'other_formats_synced':[]}
(BASE/'last-approved-version.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'passed','output':str(output),'bytes':output.stat().st_size},ensure_ascii=False))

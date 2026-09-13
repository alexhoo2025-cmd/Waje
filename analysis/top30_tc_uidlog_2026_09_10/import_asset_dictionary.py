import csv,datetime,hashlib,io,json,re
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
source=P/'asset-change-type-source.json';payload=json.loads(source.read_text())
rows=[]
for raw in csv.reader(io.StringIO(payload['annotated_csv'])):
    if not raw: continue
    m=re.match(r'^\[row=(\d+)\]\s*',raw[0]);row_no=int(m.group(1)) if m else None
    raw[0]=re.sub(r'^\[row=\d+\]\s*','',raw[0]);raw+=['']*(11-len(raw))
    if row_no==1 or not raw[3].strip().isdigit(): continue
    rows.append({'source_row':row_no,'description':raw[0].strip(),'change_value':raw[1].strip(),'technical_field':raw[2].strip(),'ares_code':int(raw[3]),'bill_detail_type':raw[4].strip(),'bill_group':raw[5].strip(),'game_id':raw[6].strip(),'sub_change_type':raw[7].strip(),'h5_status':raw[9].strip(),'app_status':raw[10].strip()})
by_code={}
for row in rows:by_code.setdefault(row['ares_code'],[]).append(row)
duplicates={str(k):v for k,v in by_code.items()if len(v)>1}
used_codes={9000001,9000002,9000211,9000016,9010301,9010302,9010303,9010400,9010403}
assert used_codes.issubset(by_code) and all(len(by_code[c])==1 for c in used_codes)
metadata={'source_url':'https://ksg964l11fam.sg.larksuite.com/wiki/SNqfwcET8ivMd6kUdIUlatXXgMc','spreadsheet_title':'资产变动类型','spreadsheet_token':'TF3ssgqI7hsIH5tJqQtlLA3Igjc','sheet_name':'Sheet1','sheet_id':'eca4f2','revision':1108,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_snapshot_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_rows_scanned':443,'last_nonempty_source_row':284,'dictionary_rows':len(rows),'duplicate_code_count':len(duplicates),'fields':['备注说明','资产变更值','技术字段名','ares 字典值','账单详情Type','账单类型归属','GameId','SubChangeType','H5','APP']}
out={'metadata':metadata,'rows':rows,'duplicates':duplicates,'used_code_mapping':{str(c):by_code[c][0]for c in sorted(used_codes)}}
(P/'asset-change-dictionary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
mapped='\n'.join(f"| {c} | {by_code[c][0]['description']} | {by_code[c][0]['bill_detail_type'] or '未填写'} | {by_code[c][0]['bill_group'] or '未填写'} |"for c in sorted(used_codes))
md=f'''# 资产变动类型字典\n\n- 来源：[飞书电子表格《资产变动类型》]({metadata['source_url']})\n- 来源版本：revision {metadata['revision']}，主表 `Sheet1`\n- 入库时间：{metadata['retrieved_at']}\n- 数据范围：读取第1—443行，最后非空行为第284行；有效字典{len(rows)}条\n- 用途：将BigQuery `change_type`（ares字典值）映射为业务说明、账单明细Type和账单类型归属\n\n## 本次9月10日查询使用的代码\n\n| ares字典值 | 业务说明 | 账单详情Type | 账单类型归属 |\n|---:|---|---|---|\n{mapped}\n\n## 使用边界\n\n- `asset_id`与`change_type`是不同字段。本字典只解释变动类型，不提供5001、5002、5006、5007的资产名称。\n- 字典中的空白、H5／APP状态和重复代码保持源表原值，不自行补齐。\n- 报告中的金额或资产变动仍按各资产ID分别解释，不跨资产相加。\n'''
(ROOT/'knowledge/02-数据/资产变动类型字典-2026-09-11.md').write_text(md)
print(json.dumps({'dictionary_rows':len(rows),'duplicates':len(duplicates),'used_codes':len(used_codes),'revision':metadata['revision']},ensure_ascii=False))

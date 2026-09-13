import datetime,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
book=ROOT/'outputs/019fc549-3241-7d52-90f5-0b39c2e03530/9月10日资产变动汇总_前30.xlsx'
backup=P/'revisions/pre-dictionary/9月10日资产变动汇总_前30.xlsx'
dictionary=json.loads((P/'asset-change-dictionary.json').read_text())
verify=json.loads((P/'output-verification.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert dictionary['metadata']['revision']==1108
assert len(dictionary['rows'])==283
assert '未映射' not in verify['codeTable']
assert 'Cell search matched 0 entries' in verify['errorScan']
receipt={'status':'complete','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':str(book),'output_sha256':sha(book),'backup':str(backup),'backup_sha256':sha(backup),'source':dictionary['metadata'],'dictionary_rows':len(dictionary['rows']),'duplicate_codes_preserved':dictionary['metadata']['duplicate_code_count'],'used_codes_unique_and_mapped':len(dictionary['used_code_mapping']),'workbook':{'sheet_count':6,'chart_count':3,'formula_errors':0,'uid_persisted':False},'changes':['新增资产变动字典工作表','共同变动代码新增业务说明、账单详情Type和账单归属，并用VLOOKUP引用字典','摘要更新Tada下注/返还、提现扣除/手续费及PP代码结论','查询说明增加飞书来源、revision和仍缺少资产ID名称的限制'],'source_revision_rechecked':1108}
(P/'dictionary-integration-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps({'status':'complete','output_sha256':receipt['output_sha256'],'dictionary_rows':receipt['dictionary_rows'],'mapped_codes':receipt['used_codes_unique_and_mapped']}))

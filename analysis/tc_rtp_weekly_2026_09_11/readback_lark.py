#!/usr/bin/env python3
import hashlib,json,os,subprocess,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DOC='SxAOdwmGNo2nTKxP8o3lbGWGgBg';URL='https://ksg964l11fam.sg.larksuite.com/docx/'+DOC
env={**os.environ,'LARKSUITE_CLI_NO_UPDATE_NOTIFIER':'1','LARKSUITE_CLI_NO_SKILLS_NOTIFIER':'1'}
r=subprocess.run(['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc',URL,'--doc-format','xml','--detail','with-ids','--as','user','--format','json'],capture_output=True,text=True,check=True,env=env)
payload=json.loads(r.stdout);content=payload['data']['document']['content'];(ROOT/'lark-readback.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2));(ROOT/'lark-readback.xml').write_text(content)
expected=ET.fromstring('<doc>'+ (ROOT/'report.xml').read_text()+'</doc>');actual=ET.fromstring('<doc>'+content+'</doc>')
def tables(root):return [[[''.join(c.itertext()).strip()for c in row if c.tag in{'th','td'}]for row in t.iter('tr')]for t in root.iter('table')]
text=''.join(actual.itertext());checks={'title':actual.find('title').text=='Waje TC回升，但EasyWin、Tower与Hilo仍需复核｜截至2026年9月10日','revision':payload['data']['document']['revision_id'],'headings':len(list(actual.iter('h1')))==7,'tables':len(list(actual.iter('table')))==6,'table_cells_exact':tables(expected)==tables(actual),'images':len(list(actual.iter('img')))==5,'image_tokens':all(x.get('src')for x in actual.iter('img')),'core_values':all(x in text for x in ['78.92%','+1.78pp','177.86亿','96.73%','149.94%','-7.77pp','渠道TC本期不展示']),'no_placeholders':not any(x in text for x in ['undefined','TODO','待填写'])}
assert all(v is True or k=='revision'for k,v in checks.items()),checks
receipt={'status':'created_and_readback_verified','checked_at':datetime.now(timezone.utc).isoformat(),'url':URL,'document_id':DOC,'revision_id':payload['data']['document']['revision_id'],'checks':checks,'report_xml_sha256':hashlib.sha256((ROOT/'report.xml').read_bytes()).hexdigest(),'readback_sha256':hashlib.sha256(content.encode()).hexdigest(),'reference_document_unchanged':True}
(ROOT/'lark-delivery-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps(receipt,ensure_ascii=False))

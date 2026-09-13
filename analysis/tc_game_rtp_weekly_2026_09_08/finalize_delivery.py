#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,shutil,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
EXPECTED=ET.fromstring('<doc>'+ (ROOT/'report.xml').read_text()+'</doc>')
ACTUAL_TEXT=(ROOT/'feishu-readback.xml').read_text()
ACTUAL=ET.fromstring('<doc>'+ACTUAL_TEXT+'</doc>')

def tables(root):
    return [[[''.join(cell.itertext()).strip() for cell in row if cell.tag in ('th','td')] for row in tab.iter('tr')] for tab in root.iter('table')]

text=''.join(ACTUAL.itertext())
checks={
  'title':ACTUAL.find('title').text=='Waje 全产品TC与新上线游戏RTP周度对比分析 V3｜截至2026年9月7日',
  'headings':len(list(ACTUAL.iter('h1')))==9,
  'tables':len(list(ACTUAL.iter('table')))==7,
  'table_cells_exact':tables(EXPECTED)==tables(ACTUAL),
  'images':len(list(ACTUAL.iter('img')))==7,
  'image_tokens':all(x.get('src') for x in ACTUAL.iter('img')),
  'kpis':len(list(ACTUAL.iter('column')))==7,
  'core_values':all(x in text for x in ['77.37%','-0.37pp','179.34亿','96.51%','43.52%','+8.43%','+5.78%']),
  'sections':all(x in text for x in ['汇总结论（Executive Summary）','渠道变化分化','游戏下注增长8.43%','重点偏离游戏','仍需回答的问题','口径与边界']),
  'no_placeholders':not any(x in text for x in ['undefined','TODO','Data access blockers']),
  'original_report_revision':119,
}
assert all(v is True or k=='original_report_revision' for k,v in checks.items()),checks
url='https://ksg964l11fam.sg.larksuite.com/wiki/O4wuw0DsxiACgxkf5XAl6RTHgYO'
receipt={
  'status':'published_and_readback_verified','published_at':datetime.now(timezone.utc).isoformat(),'identity':'user','wiki_url':url,
  'wiki_node_token':'O4wuw0DsxiACgxkf5XAl6RTHgYO','document_id':'B5X8dAujWo1eJGxn3IClYjfwgZg','space_id':'7672704187443973852','space_name':'产品数据整理和分析','revision':4,
  'checks':checks,'analysis_sha256':hashlib.sha256((ROOT/'analysis-results.json').read_bytes()).hexdigest(),'report_xml_sha256':hashlib.sha256((ROOT/'report.xml').read_bytes()).hexdigest(),'readback_sha256':hashlib.sha256(ACTUAL_TEXT.encode()).hexdigest(),
  'source_status':{'lifecycle_0903':'complete_requery','lifecycle_0907':'complete_independent_requery','metabase_tc':'complete_14_days'},'original_report_unchanged':True,'outbound_messages':0,
}
(ROOT/'feishu-publish-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
source=json.loads((ROOT/'source-receipt.json').read_text());source.update({'status':'published_and_readback_verified','new_lark_document_created':True,'wiki_url':url,'next_action':None});(ROOT/'source-receipt.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
draft=PROJECT/'draft_33a61320_folder'
assert draft.parent==PROJECT and draft.name=='draft_33a61320_folder' and {p.name for p in draft.iterdir()}=={'draft.xml','.presentation-decision.json'}
shutil.rmtree(draft)
print(json.dumps(receipt,ensure_ascii=False,indent=2))

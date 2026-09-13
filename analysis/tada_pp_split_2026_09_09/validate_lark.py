from pathlib import Path
import json,re,hashlib,csv,collections,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent
def norm(s):return re.sub(r'[\s\u200b\u200c\u200d\ufeff]+','',s or '')
def xml(s):return ET.fromstring('<document>'+s+'</document>')
for slug in ['macro','detail']:
 d=P/slug;expected=json.loads((d/'lark-expected.json').read_text());created=json.loads((d/'lark-create.json').read_text());readback=json.loads((d/'lark-readback.json').read_text());root=xml(readback['content']);source=xml((d/'lark-source.xml').read_text())
 assert not created.get('warnings'),created.get('warnings')
 assert norm(''.join(root.find('.//title').itertext()))==norm(expected['title'])
 assert len(root.findall('.//h1'))==expected['h1_count']
 assert len(root.findall('.//img'))==len(expected['images'])
 assert len(root.findall('.//table'))==len(expected['tables'])
 assert len(root.findall('.//source'))==len(expected['attachments'])
 actual=collections.Counter(norm(''.join(p.itertext())) for p in root.iter('p'))
 planned=collections.Counter(norm(p) for p in expected['paragraph_texts'])
 missing={p:n-actual[p] for p,n in planned.items() if actual[p]<n};assert not missing,missing
 total_cells=0;color_map={}
 for source_table,target_table in zip(source.iter('table'),root.iter('table')):
  a=[n for n in source_table.iter() if n.tag in ['td','th']];b=[n for n in target_table.iter() if n.tag in ['td','th']];assert len(a)==len(b)
  for left,right in zip(a,b):
   assert norm(''.join(left.itertext()))==norm(''.join(right.itertext()))
   total_cells+=1
   if left.get('background-color'):
    assert right.get('background-color'),'missing color'
    color_map.setdefault(left.get('background-color'),set()).add(right.get('background-color'))
   if left.find('.//b') is not None:assert right.find('.//b') is not None,'lost bold'
 assert all(len(values)==1 for values in color_map.values())
 assert len({next(iter(values)) for values in color_map.values()})==len(color_map)
 for asset in expected['images']:
  assert hashlib.sha256((P.parents[1]/asset['path']).read_bytes()).hexdigest()==asset['sha256']
 for att in expected['attachments']:
  path=d/att['name'];assert hashlib.sha256(path.read_bytes()).hexdigest()==att['sha256']
  with path.open(encoding='utf-8-sig',newline='') as f:assert len(list(csv.DictReader(f)))==att['rows']
 result={'status':'full_readback_verified','document_id':readback['document_id'],'url':created['document']['url'],'revision':readback['revision_id'],'h1':expected['h1_count'],'charts':len(expected['images']),'tables':len(expected['tables']),'attachments':len(expected['attachments']),'paragraphs_verified':sum(planned.values()),'table_cells_verified':total_cells,'color_map':{k:list(v) for k,v in color_map.items()},'html_artifact_sha256':expected['artifact_sha256'],'source_xml_sha256':hashlib.sha256((d/'lark-source.xml').read_bytes()).hexdigest(),'readback_sha256':hashlib.sha256(readback['content'].encode()).hexdigest(),'external_messages_sent':False}
 (d/'lark-delivery-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))

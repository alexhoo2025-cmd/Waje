"""Convert the two validated canonical reports into native Lark documents."""
from pathlib import Path
import json,re,html,csv,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
DRAFTS={'macro':'draft_a58c3d8b_folder/draft.xml','detail':'draft_c398d8a0_folder/draft.xml'}
ORIGINAL='https://ksg964l11fam.sg.larksuite.com/docx/MUmUdKO7ko3hKIxY822lBXJQggg'
def esc(s):return html.escape(str(s),quote=True)
def inline(s):
 out=[]
 for part in re.split(r'(\*\*.*?\*\*|\[[^\]]+\]\([^)]*\))',str(s)):
  if part.startswith('**') and part.endswith('**'):out.append('<b>'+esc(part[2:-2])+'</b>')
  elif re.fullmatch(r'\[[^\]]+\]\([^)]*\)',part):
   m=re.match(r'\[([^\]]+)\]\(([^)]*)\)',part);out.append('<a href="'+esc(m[2])+'">'+esc(m[1])+'</a>')
  else:out.append(esc(part))
 return ''.join(out)
def cell_color(block,row,col):
 joined=' '.join(row)
 if col==0 and ('Tada' in row[0] or 'PP' in row[0]):return 'light-blue' if 'Tada' in row[0] else 'light-orange'
 if block=='table-new_30d':return 'light-blue'
 if block=='table-old_over_30d':return 'light-purple'
 if block in ['ret-exact','depth-metrics']:
  if '新用户' in joined:return 'light-blue'
  if '老用户' in joined:return 'light-purple'
  return 'light-gray'
 if block in ['macro-all','game-counts','game-profiles']:return 'light-blue' if 'Tada' in joined else 'light-orange' if 'PP' in joined else None
 return None
def table_xml(chunk,block):
 lines=chunk.splitlines();rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in lines];headers=rows[0];values=rows[2:];n=len(headers)
 assert values and all(len(r)==n for r in values)
 if block=='game-profiles': widths=[80,190]+[110]*(n-2)
 else:widths=[max(85,int(1000/n))]*n
 out='<table><colgroup>'+''.join(f'<col width="{v}"/>' for v in widths)+'</colgroup><thead><tr>'+''.join('<th background-color="light-gray"><p><b>'+inline(h)+'</b></p></th>' for h in headers)+'</tr></thead><tbody>'
 for r in values:
  out+='<tr>'
  for i,v in enumerate(r):
   color='light-yellow' if '**' in v else cell_color(block,r,i)
   out+='<td vertical-align="middle"'+(' background-color="'+color+'"' if color else '')+'><p>'+inline(v)+'</p></td>'
  out+='</tr>'
 return out+'</tbody></table>',{'block':block,'headers':headers,'rows':[[x.replace('**','') for x in r] for r in values]}
def markdown(body,block,expected):
 out=[]
 for chunk in re.split(r'\n\s*\n',body.strip()):
  if re.match(r'^#{1,6} ',chunk):
   marks,title=chunk.split(' ',1);level=max(1,len(marks)-1);title=re.sub(r'^\d+｜','',title)
   out.append(f'<h{level} seq="auto">{inline(title)}</h{level}>')
  elif chunk.startswith('|'):
   xml,rows=table_xml(chunk,block);expected.append(rows);out.append(xml)
  elif re.match(r'^\d+\. ',chunk):out.append('<ol>'+''.join('<li>'+inline(re.sub(r'^\d+\. ','',line))+'</li>' for line in chunk.splitlines())+'</ol>')
  elif chunk.startswith('- '):out.append('<ul>'+''.join('<li>'+inline(line[2:])+'</li>' for line in chunk.splitlines())+'</ul>')
  else:out.append('<p>'+inline(chunk.replace('\n',' '))+'</p>')
 return '\n'.join(out)
def main():
 for slug,draft in DRAFTS.items():
  a=json.loads((P/slug/'artifact.json').read_text());m=a['manifest'];receipt=json.loads((P/slug/'delivery-receipt.json').read_text())
  assert receipt['ok'] and receipt['stages']['verification']=='passed'
  assert hashlib.sha256((P/slug/'artifact.json').read_bytes()).hexdigest()==receipt['report_quality']['input_sha256']
  expected=[];images=[];attachments=[];out=['<title>'+esc(m['title'])+'</title>']
  for b in m['blocks']:
   if b['id']=='title':continue
   if b['type']=='markdown':
    body=b['body']
    if b['id']=='summary':
     body=re.sub(r'^## 执行摘要\s*','',body);out.append('<h1 seq="auto">执行摘要</h1><callout background-color="light-blue" border-color="blue">'+markdown(body,b['id'],expected)+'</callout>')
    else:
     if b['id']=='game-details':body=body.replace('下表提供已展示的游戏×渠道明细，可排序、翻页和查阅。','文末附件提供已展示的游戏×渠道明细，可下载筛选与查阅。')
     if b['id']=='actions':body=body.replace('原报告与原飞书保留，本篇为独立拆分稿。','原综合报告保留，本篇为独立拆分稿。')
     out.append(markdown(body,b['id'],expected))
   elif b['type']=='chart':
    c=next(c for c in m['charts'] if c['id']==b['chartId']);img=P/'qa'/f'{slug}-{b["id"]}.png';svg=img.with_suffix('.svg');assert img.exists()
    wh=re.search(r'<svg[^>]*width="([\d.]+)" height="([\d.]+)"',svg.read_text());assert wh
    images.append({'block':b['id'],'title':c['title'],'path':str(img.relative_to(ROOT)),'sha256':hashlib.sha256(img.read_bytes()).hexdigest()})
    out.extend(['<p><b>'+esc(c['title'])+'</b></p>','<p>'+esc(c['subtitle'])+'</p>',f'<img path="@./{esc(str(img.relative_to(ROOT)))}" width="{wh[1]}" height="{wh[2]}" caption="{esc(c["title"])}"/>'])
   elif b['type']=='table':
    # The only native table is the full 1,081-row game table; keep it as an exact CSV attachment.
    t=next(t for t in m['tables'] if t['id']==b['tableId']);rows=a['snapshot']['datasets'][t['dataset']];assert t['id']=='all-games' and len(rows)==1081
    attachment=P/'detail'/'完整游戏明细-1081行.csv'
    with attachment.open('w',encoding='utf-8-sig',newline='') as f:
     writer=csv.DictWriter(f,fieldnames=[c['field'] for c in t['columns']]);writer.writeheader();writer.writerows(rows)
    attachments.append({'name':attachment.name,'rows':len(rows),'sha256':hashlib.sha256(attachment.read_bytes()).hexdigest()})
    out.append('<p><b>完整游戏明细附件：1,081条游戏×渠道记录</b></p><p>字段与HTML完整明细表一致，保留游戏ID、下注人数、下注额、人均下注、人均局次、下注活跃天数和结算RTP，便于下载筛选。</p><source path="@./'+esc(str(attachment.relative_to(ROOT)))+'" name="'+esc(attachment.name)+'"/>')
  out.append('<p>数据来源：Waje起源BigQuery游戏结算、用户与回访的已核验聚合；统计窗口及口径见正文。原综合报告保留：<a href="'+ORIGINAL+'">Tada与PP：APP/H5下注与回访对比</a>。</p>')
  xml='\n\n'.join(out)+'\n';ET.fromstring('<document>'+xml+'</document>')
  target=ROOT/draft;assert not target.exists(),'initial draft already exists';target.write_text(xml)
  (P/slug/'lark-expected.json').write_text(json.dumps({'title':m['title'],'draft':draft,'artifact_sha256':hashlib.sha256((P/slug/'artifact.json').read_bytes()).hexdigest(),'tables':expected,'images':images,'attachments':attachments,'h1_count':xml.count('<h1 '),'paragraph_texts':[ ''.join(el.itertext()) for el in ET.fromstring('<document>'+xml+'</document>').iter('p')]},ensure_ascii=False,indent=2))
  print(json.dumps({'slug':slug,'draft':draft,'tables':len(expected),'images':len(images),'attachments':len(attachments),'h1_count':xml.count('<h1 ')},ensure_ascii=False))
if __name__=='__main__':main()

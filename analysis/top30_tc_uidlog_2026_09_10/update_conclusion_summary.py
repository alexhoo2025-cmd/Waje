import os,tempfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
P=Path(__file__).resolve().parent
TARGET=P.parents[1]/'outputs/019fc549-3241-7d52-90f5-0b39c2e03530/9月10日资产变动汇总_前30.xlsx'
BASE=P/'revisions/pre-conclusion-summary/9月10日资产变动汇总_前30.xlsx'
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main';E.register_namespace('',NS);q=lambda x:f'{{{NS}}}{x}'
updates={
'A16':'结论摘要：TC差值与9月10日资产来源',
'A17':'1. TC差值规模：源Excel筛选期内，前30名累计提现49,619,515.32、累计充值22,913,598.00，TC差值26,705,917.32；提现金额为充值的2.17倍。',
'A18':'2. 差值集中度较高：头部1名贡献20.2%，前5名贡献51.0%，前10名贡献67.2%；Top30平均TC差值890,197.24，中位数518,969.94。',
'A19':'3. 9月10日资产日志：前30名全部匹配，共98,031条事件；现金（5002）占80.4%，游戏币（5001）占16.2%，资产活动主要集中在这两类。',
'A20':'4. 游戏事件是主要来源：Tada下注9010301共60,376条，占当日事件61.6%；Tada chip/cash返还9010302、9010303共13,360条。事件数不能直接换算RTP或输赢。',
'A21':'5. 提现链路需重点核对：现金（5002）的提现扣除9000002与提现手续费9000211均为380条；手续费变动量约为提现扣除的1.02%。',
'A22':'6. 核心判断：该人群同时具备较高TC差值和高频游戏结算行为。现有证据支持重点复核提现及Tada下注/返还链路，但不能用9月10日单日日志对整个筛选期TC差值作因果归因。'
}
with zipfile.ZipFile(BASE) as src:
 entries={i.filename:(i,src.read(i.filename))for i in src.infolist()}
 root=E.fromstring(entries['xl/worksheets/sheet1.xml'][1])
 for ref,value in updates.items():
  cell=root.find(f".//{q('c')}[@r='{ref}']");assert cell is not None,ref
  for child in list(cell):cell.remove(child)
  cell.set('t','inlineStr');node=E.SubElement(cell,q('is'));text=E.SubElement(node,q('t'));text.text=value
 for row in root.findall(f'.//{q("row")}'):
  if 17<=int(row.get('r'))<=22:row.set('ht','34');row.set('customHeight','1')
 changed=E.tostring(root,encoding='utf-8',xml_declaration=True)
 fd,tmp=tempfile.mkstemp(prefix='conclusion-summary-',suffix='.xlsx',dir=TARGET.parent);os.close(fd)
 try:
  with zipfile.ZipFile(tmp,'w')as dst:
   for name,(info,data)in entries.items():dst.writestr(info,changed if name=='xl/worksheets/sheet1.xml'else data)
  with zipfile.ZipFile(tmp)as check:
   assert check.testzip()is None
   wb=E.fromstring(check.read('xl/workbook.xml'));assert len(list(wb.iter(q('sheet'))))==6
   s1=E.fromstring(check.read('xl/worksheets/sheet1.xml'));assert s1.find(f".//{q('c')}[@r='H5']")is None and s1.find(f".//{q('c')}[@r='H6']")is None
  os.replace(tmp,TARGET)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
with zipfile.ZipFile(TARGET)as out:
 assert all(out.read(n)==d for n,(i,d)in entries.items()if n!='xl/worksheets/sheet1.xml')
print({'status':'complete','updated':list(updates),'preserved_entries':len(entries)-1,'sheets':6})

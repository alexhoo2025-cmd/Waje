import os,re,shutil,tempfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as E

P=Path(__file__).resolve().parent
BASE=P/'revisions/pre-asset-labels/9月10日资产变动汇总_前30.xlsx'
TARGET=P.parents[1]/'outputs/019fc549-3241-7d52-90f5-0b39c2e03530/9月10日资产变动汇总_前30.xlsx'
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
E.register_namespace('',NS)
qn=lambda x:f'{{{NS}}}{x}'
labels={'5001':'5001｜游戏币（Chip）','5002':'5002｜现金（Cash）','5006':'5006｜Waje游戏币（WajeChip）','5007':'5007｜Waje现金（WajeCash）'}
short_labels={'5001':'5001 游戏币','5002':'5002 现金','5006':'5006 Waje游戏币','5007':'5007 Waje现金'}

with zipfile.ZipFile(BASE) as src:
    entries={i.filename:(i,src.read(i.filename)) for i in src.infolist()}
    sst=E.fromstring(entries['xl/sharedStrings.xml'][1])
    strings=[''.join(si.itertext()) for si in sst]
    def text(cell):
        if cell is None:return None
        if cell.get('t')=='s':
            v=cell.find(qn('v'));return strings[int(v.text)] if v is not None else None
        if cell.get('t')=='inlineStr':
            node=cell.find(qn('is'));return ''.join(node.itertext()) if node is not None else None
        v=cell.find(qn('v'));return v.text if v is not None else None
    def set_text(root,ref,value):
        cell=root.find(f".//{qn('c')}[@r='{ref}']")
        if cell is None:raise AssertionError(f'missing cell {ref}')
        for child in list(cell):cell.remove(child)
        cell.set('t','inlineStr');node=E.SubElement(cell,qn('is'));t=E.SubElement(node,qn('t'));t.text=value
    def remove_cell(root,ref):
        cell=root.find(f".//{qn('c')}[@r='{ref}']");assert cell is not None
        for row in root.findall(f'.//{qn("row")}'):
            if cell in list(row):row.remove(cell);return
        raise AssertionError(ref)
    def replace_id_cells(root,refs,mapping=labels):
        for ref in refs:
            cell=root.find(f".//{qn('c')}[@r='{ref}']");old=text(cell)
            assert old in mapping,(ref,old);set_text(root,ref,mapping[old])
    def set_first_col_width(root,width):
        cols=root.find(qn('cols'));assert cols is not None
        for col in cols.findall(qn('col')):
            if int(col.get('min'))<=1<=int(col.get('max')):
                col.set('width',str(width));col.set('customWidth','1');return
        raise AssertionError('column A definition missing')

    modified={}
    s1=E.fromstring(entries['xl/worksheets/sheet1.xml'][1])
    remove_cell(s1,'H5');remove_cell(s1,'H6')
    set_text(s1,'A10','资产ID／中文业务说明')
    replace_id_cells(s1,['A11','A12','A13','A14'])
    replace_id_cells(s1,['J10','J11','J12','J13','J17','J18','J19','J20'],short_labels)
    set_first_col_width(s1,27)
    set_text(s1,'A18','2. 现金（5002）占80.4%事件，游戏币（5001）占16.2%；另有60条事件来自不足10名用户的低覆盖资产，已合并抑制。')
    set_text(s1,'A21','5. 现金（5002）中，提现扣除9000002与提现手续费9000211均为380条；手续费变动量约为提现扣除的1.02%。')
    set_text(s1,'A22','6. PP下注9010400与PP cash返还9010403已映射。资产中文业务说明与原始ID同时展示，便于日志和字典对账。')
    modified['xl/worksheets/sheet1.xml']=E.tostring(s1,encoding='utf-8',xml_declaration=True)

    s2=E.fromstring(entries['xl/worksheets/sheet2.xml'][1]);set_text(s2,'A5','资产ID／中文业务说明')
    replace_id_cells(s2,[f'A{r}' for r in range(6,22)])
    set_first_col_width(s2,27)
    modified['xl/worksheets/sheet2.xml']=E.tostring(s2,encoding='utf-8',xml_declaration=True)

    s3=E.fromstring(entries['xl/worksheets/sheet3.xml'][1]);set_text(s3,'A5','资产ID／中文业务说明')
    replace_id_cells(s3,[f'A{r}' for r in range(6,23)])
    set_first_col_width(s3,27)
    modified['xl/worksheets/sheet3.xml']=E.tostring(s3,encoding='utf-8',xml_declaration=True)

    s5=E.fromstring(entries['xl/worksheets/sheet5.xml'][1])
    set_text(s5,'B18','变动类型已按飞书字典revision 1108映射；资产ID增加中文业务说明并保留原始编号。')
    set_text(s5,'A25','资产ID业务说明')
    set_text(s5,'B25','5001=游戏币（Chip）；5002=现金（Cash）；5006=Waje游戏币（WajeChip）；5007=Waje现金（WajeCash）')
    modified['xl/worksheets/sheet5.xml']=E.tostring(s5,encoding='utf-8',xml_declaration=True)

    fd,tmp=tempfile.mkstemp(prefix='asset-summary-',suffix='.xlsx',dir=TARGET.parent);os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w') as dst:
            for name,(info,data) in entries.items():dst.writestr(info,modified.get(name,data))
        with zipfile.ZipFile(tmp) as check:
            bad=check.testzip();assert bad is None,bad
            wb=E.fromstring(check.read('xl/workbook.xml'));sheet_names=[x.get('name') for x in wb.iter(qn('sheet'))]
            assert sheet_names==['摘要','时段明细','共同变动代码','聚合数据','查询说明','资产变动字典'],sheet_names
            out1=E.fromstring(check.read('xl/worksheets/sheet1.xml'))
            assert out1.find(f".//{qn('c')}[@r='H5']") is None and out1.find(f".//{qn('c')}[@r='H6']") is None
        os.replace(tmp,TARGET)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

unchanged=[name for name,(info,data) in entries.items()if name not in modified]
assert all(entries[n][1]==zipfile.ZipFile(TARGET).read(n) for n in unchanged)
print({'status':'complete','modified_entries':sorted(modified),'unchanged_entries':len(unchanged),'sheets':6,'removed':['摘要!H5','摘要!H6']})

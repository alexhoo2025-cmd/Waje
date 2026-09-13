from pathlib import Path
import json,ast,io,contextlib
try:
 import nbformat
except ImportError:
 class V4:
  @staticmethod
  def new_markdown_cell(source):return {'cell_type':'markdown','metadata':{},'source':source}
  @staticmethod
  def new_code_cell(source):return {'cell_type':'code','metadata':{},'source':source,'outputs':[],'execution_count':None}
  @staticmethod
  def new_notebook():return Notebook()
 class Notebook(dict):
  def __init__(self):super().__init__(nbformat=4,nbformat_minor=4,metadata={},cells=[])
  def __getattr__(self,key):return self[key]
  def __setattr__(self,key,val):self[key]=val
 class NB:
  v4=V4
  @staticmethod
  def validate(n):assert n['nbformat']==4 and all(c['cell_type'] in ['code','markdown'] for c in n['cells'])
  @staticmethod
  def write(n,p):p.write_text(json.dumps(n,ensure_ascii=False,indent=2))
 nbformat=NB
P=Path(__file__).resolve().parent
n=nbformat.v4.new_notebook()
n.metadata['kernelspec']={'name':'python3','display_name':'Python 3','language':'python'}
n.cells=[
 nbformat.v4.new_markdown_cell('# 坦桑调研复算记录\n\n## 结论\n最低存款中位数100 TZS，最低提现中位数1,000 TZS；12/17家提现门槛更高。此处复算原材料，不代表实时测试。'),
 nbformat.v4.new_markdown_cell('## 范围与方法\n输入：Research TZ _ Bet.xlsx（12表）与坦桑行业调研数据.xlsx（13表）。两份同源，固定原始19品牌；支付子表17家。金额TZS，未识别时长不填零。extract.py保留原值与单元格，analyze.py生成规范记录。外部官方事实与日期见external-evidence.json。'),
 nbformat.v4.new_code_cell("from pathlib import Path\nimport json, statistics, sqlite3\nbase=Path.cwd()\nif not (base/'normalized.json').exists(): base=base/'analysis/tanzania_gambling_research_2026_09_08'\ndata=json.loads((base/'normalized.json').read_text())\nlen(data['brands']),len(data['payment'])"),
 nbformat.v4.new_markdown_cell('## 数据与结果\n先复算支付门槛，随后用独立SQL核对人数和范围。'),
 nbformat.v4.new_code_cell("p=data['payment']\nresult={'最低存款中位数':statistics.median(r['min_deposit'] for r in p),'最低提现中位数':statistics.median(r['min_withdraw'] for r in p),'提现门槛更高':sum(r['min_withdraw']>r['min_deposit'] for r in p),'品牌分母':len(p)}\nassert result=={'最低存款中位数':100,'最低提现中位数':1000,'提现门槛更高':12,'品牌分母':17}\nresult"),
 nbformat.v4.new_code_cell("con=sqlite3.connect(':memory:')\ncon.execute('CREATE TABLE payments(brand TEXT, deposit REAL, withdraw REAL)')\ncon.executemany('INSERT INTO payments VALUES (?,?,?)',[(r['brand'],r['min_deposit'],r['min_withdraw']) for r in p])\ncheck=con.execute('SELECT COUNT(*), SUM(withdraw>deposit), MIN(deposit), MAX(withdraw) FROM payments').fetchone()\nassert check==(17,12,100,4000)\ncheck"),
 nbformat.v4.new_code_cell("assert round((7959.40/6413.94-1)*100,1)==24.1\nassert round(24628003/62793986*100,1)==39.2\nassert sum(r['deposit_seconds'] is None for r in p)==2\nf=json.loads((base/'formula_validation.json').read_text())\nassert len(f)==265 and all(r['cache_match'] for r in f)\nx=json.loads((base/'cross_version_reconciliation.json').read_text())\nassert x['compared_fields']==378 and len(x['differences'])==1\n{'公式复算':len(f),'同源共同字段':x['compared_fields'],'差异':x['differences']}"),
 nbformat.v4.new_markdown_cell('## 使用建议\n原材料适合制定产品走查和验证清单。当前限额与活动应看具体官方条款；税收、收入、投注额、订阅数与人数保持分开。HTML和飞书共享artifact.json，图表保留原数据，未用模型评分排序。')]
env={};seq=0
for c in n.cells:
 if c['cell_type']!='code':continue
 seq+=1;tree=ast.parse(c['source']);last=tree.body.pop() if isinstance(tree.body[-1],ast.Expr) else None
 stream=io.StringIO()
 with contextlib.redirect_stdout(stream):
  exec(compile(tree,'notebook-cell','exec'),env)
  val=eval(compile(ast.Expression(last.value),'notebook-result','eval'),env) if last else None
 c['execution_count']=seq;c['outputs']=[]
 if stream.getvalue():c['outputs'].append({'output_type':'stream','name':'stdout','text':stream.getvalue()})
 if val is not None:c['outputs'].append({'output_type':'execute_result','execution_count':seq,'data':{'text/plain':repr(val)},'metadata':{}})
n.metadata['execution']={'method':'Sequential Python AST execution','status':'passed','note':'环境未提供Jupyter/nbformat；代码单元已按顺序在Python执行并通过断言，未启动Jupyter内核。'}
nbformat.validate(n);nbformat.write(n,P/'复算记录.ipynb')
print(P/'复算记录.ipynb')

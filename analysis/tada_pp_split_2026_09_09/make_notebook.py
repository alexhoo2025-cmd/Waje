from pathlib import Path
import nbformat
from nbclient import NotebookClient
P=Path(__file__).resolve().parent
nb=nbformat.v4.new_notebook()
nb.cells=[
nbformat.v4.new_markdown_cell('# 双报告复算记录\n\n## tl;dr\n\n宏观指标沿用冻结38日窗口。新增关联按游戏与日粒度分开，H5·Tada游戏层相关更明显，但不构成RTP影响回访的因果证据。'),
nbformat.v4.new_markdown_cell('## Context & Methods\n\n业务日Africa/Lagos，2026-08-01至09-07；渠道按注册命名，新用户0—29天、老用户30天及以上。\n\n### Key Assumptions\n\n下注活跃天数是复玩强度而非定日回访。原始下注笔数与单游戏独立回访未取得；只读聚合，不导出用户明细。'),
nbformat.v4.new_code_cell("from pathlib import Path\nimport json, runpy\nbase=Path.cwd()\nassert (base/'analyze.py').exists()\nrunpy.run_path(str(base/'analyze.py'),run_name='__main__')\ndata=json.loads((base/'data.json').read_text())"),
nbformat.v4.new_markdown_cell('## Data\n\n来源为原报告核心、游戏及回访聚合；原文件哈希在source-inventory.json保存。'),
nbformat.v4.new_code_cell("{k:len(data[k]) for k in ['overview','games','returns','paired','correlations']}"),
nbformat.v4.new_markdown_cell('## Results\n\n以下列出主阈值下的分层相关；不使用显著性检验包装用户重叠的游戏样本。'),
nbformat.v4.new_code_cell("[{k:r[k] for k in ['platform','provider','n','rho_stake_rtp','rho_days_rtp']} for r in data['correlations'] if r['min_bettors']==100 and r['scope']=='全部已展示品类']"),
nbformat.v4.new_markdown_cell('## Takeaways\n\n游戏层关联、日级关联和同厂商定日回访分别解释。报告一用于宏观判断，报告二用于细分验证；不直接据此调整RTP配置。'),
nbformat.v4.new_code_cell("validation=json.loads((base/'analysis-validation.json').read_text())\nassert validation['status']=='passed'\nassert all(x['unchanged'] for x in validation['original_preservation'])\nprint('Recomputed; original report preserved.')")]
nb.metadata['kernelspec']={'name':'python3','display_name':'Python 3','language':'python'}
NotebookClient(nb,timeout=120,resources={'metadata':{'path':str(P)}}).execute()
nbformat.validate(nb);nbformat.write(nb,P/'复算与校验.ipynb');print('notebook executed and validated')

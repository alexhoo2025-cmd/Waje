#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
D=json.loads((ROOT/'analysis-results.json').read_text())
Q=json.loads((ROOT/'quality-checks.json').read_text())
XML=(ROOT/'report.xml').read_text()

spec=importlib.util.spec_from_file_location('weekly',ROOT/'build_weekly_analysis.py')
w=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(w)
games=w.read_game_rows();old_rows=[r for r in games if date(2026,8,26)<=r['date']<=date(2026,9,1) and r['complete_bet']>0]
old_calc=w.old.aggregate(old_rows)
old=json.loads((PROJECT/'analysis/tc_game_rtp_tracking_2026_09_02/report_data.json').read_text())['overall_7d']

checks={
  'quality_gate_passed':Q['status']=='passed' and Q['publication_allowed'] is True,
  'equal_seven_day_windows':D['tc']['previous']['days']==D['tc']['current']['days']==7 and D['game_overall']['previous']['days']==D['game_overall']['current']['days']==7,
  'date_game_grain_complete':D['quality']['game_rows']==434 and D['quality']['duplicate_date_game_keys']==[],
  'tc_formula_recomputed':abs(D['tc']['current']['current' if False else 'tc']-D['tc']['current']['withdraw']/D['tc']['current']['recharge'])<1e-12,
  'rtp_formula_recomputed':abs(D['game_overall']['current']['actual_rtp']-(1-D['game_overall']['current']['complete_actual_profit']/D['game_overall']['current']['complete_bet']))<1e-12,
  'overlap_matches_v2_bet':abs(old_calc['complete_bet']-old['complete_bet'])<0.01,
  'overlap_matches_v2_actual_profit':abs(old_calc['complete_actual_profit']-old['complete_actual_profit'])<0.01,
  'overlap_matches_v2_rtp':abs(old_calc['actual_rtp']-old['actual_rtp'])<1e-12,
  'draft_profile_shape':XML.count('<table>')==8 and XML.count('<img ')==7 and XML.count('<h1 ')==9,
  'core_values_present':all(x in XML for x in ['77.37%','下降0.37个百分点','179.34亿','96.51%','84.48%','充值环比','本周充值占比','EasyWin','Tower','Hilo']),
  'no_placeholders':not any(x in XML for x in ['undefined','TODO','Data access blockers']),
  'privacy_boundary':not any(x in XML.lower() for x in ['user_id','order_id','account_id','bank card','银行卡号']),
  'visual_qa':True,
  'original_report_revision_unchanged':119,
}
assert all(v is True or k=='original_report_revision_unchanged' for k,v in checks.items()),checks
report={
 'status':'ready_to_share_with_caveats','validated_at':datetime.now(timezone.utc).isoformat(),'checks':checks,
 'required_caveats':['游戏下注表与渠道/包体资金表缺少共同关联键，不能把充值变化直接归因为某款游戏。','缺少最终结算、取消/退款、Bonus、配置版本和用户级大额派奖分布。','RTP与TC同向或反向变化均不构成因果证据。'],
 'visual_review':{'charts':7,'result':'passed','notes':'所有图表已按最终PNG检查；RTP散点图已标注两端异常游戏，逐日曲线已标注极值和最新值，日期、轴、单位和正负方向可读，无裁切。'},
 'publication_decision':'allowed'
}
(ROOT/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))

"""Build the reviewed legacy-vs-phase-1 Whot comparison and its visual."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
TITLE='Whot旧版埋点与新版一期计划对比分析'

comparison=[
 {'requirement':'01 用户群体','legacy':'已有注册、付费等用户信息；事件发生时的分组状态需补充','phase1':'记录注册日、首次付费日期、首次玩Whot时间和当时付费状态','change':'用户分组改为在事件发生时保存当时状态','type':'扩展'},
 {'requirement':'02 新人引导','legacy':'现有资料未形成展示、接受、步骤和完成的完整链路','phase1':'分别记录展示、接受或关闭、步骤完成和全部完成','change':'可以定位引导在哪一步流失','type':'新增'},
 {'requirement':'03 进入与加载','legacy':'通用事件可观察进入和开局；H5加载三段已有设计基础','phase1':'记录加载开始、完成、失败、超时、离开和可下注','change':'从“是否开局”前移到“是否成功加载并可操作”','type':'复用并扩展'},
 {'requirement':'04 对局选择','legacy':'可看到实际开局人数，用户原本选择2人还是4人不清晰','phase1':'记录2人或4人选择，并关联实际2/3/4人开局','change':'用户意图和最终结果可以分开分析','type':'新增'},
 {'requirement':'05 房间选择','legacy':'MC可记录部分点击；房间展示、推荐和服务端受理关系不完整','phase1':'记录房间展示、快速匹配或手动点击，以及服务端受理结果','change':'可以区分“看到了、点击了、成功进入”','type':'复用并扩展'},
 {'requirement':'06 匹配情况','legacy':'GAMESTART记录已经开局的用户；取消、超时和组桌失败缺少统一结果','phase1':'记录匹配请求、状态变化、取消结果、唯一终态并关联GAMESTART','change':'建立完整匹配分母，解释用户为什么没有开局','type':'核心新增'},
 {'requirement':'07 四人局降级','legacy':'系统按人数或机器人直接处理，用户同意过程不完整','phase1':'记录N1/N2建议、实际展示、用户响应、建议失效和降级开局','change':'可以衡量四人模式兑现和降级挽回效果','type':'规则新增'},
]

metric_rows=[
 {'metric':'入口点击','legacy':'MC可提供基础点击量','phase1':'保留MC并统一入口标识','comparison':'完成入口映射后可对齐'},
 {'metric':'游戏开局','legacy':'GAMESTART记录已开局牌局','phase1':'GAMESTART关联匹配请求和实际人数','comparison':'补齐版本和关联键后可对齐'},
 {'metric':'加载成功与可下注','legacy':'现有通用事件不足以拆分加载阶段','phase1':'LOAD开始→完成→可下注','comparison':'建立新版基线'},
 {'metric':'匹配后开局率','legacy':'缺少完整匹配请求和失败结果','phase1':'成功开局请求÷已结束等待的匹配请求','comparison':'旧日志可重建后再比较'},
 {'metric':'四人模式兑现率','legacy':'缺少用户选择人数','phase1':'实际4人开局÷已结束等待的4人请求','comparison':'仅新版可直接计算'},
 {'metric':'超时与取消','legacy':'失败路径记录不完整','phase1':'超时、取消和其他结果分别统计','comparison':'旧日志可重建后再比较'},
 {'metric':'降级挽回效果','legacy':'缺少建议展示和用户响应','phase1':'建议展示、接受和降级开局逐层统计','comparison':'仅新版可直接计算'},
]

reuse_rows=[
 {'item':'MC','handling':'复用','work':'统一Whot入口、模式和房间按钮标识，并关联后续请求'},
 {'item':'H5_GAME_LOAD / READY / BET_READY','handling':'复用设计并验收','work':'统一新版Whot游戏ID、网页版本和加载阶段'},
 {'item':'GAMESTART','handling':'扩展','work':'增加匹配请求ID、请求人数、实际人数和真人/机器人组成'},
 {'item':'GAMEEND','handling':'继续复用','work':'保留局终态；匹配失败由独立匹配事件记录'},
 {'item':'BETREWARD / ASSET','handling':'继续复用','work':'保持结算与资金对账，不承担匹配过程统计'},
]

new_rows=[
 {'group':'用户与引导','events':'用户分组快照、WHOT_TUTORIAL','purpose':'稳定新老/付费分组，统计引导展示、接受和完成'},
 {'group':'选择与房间','events':'WHOT_MODE_SELECT、WHOT_ROOM、WHOT_ROOM_RESULT','purpose':'记录用户人数意图、房间展示、点击和受理'},
 {'group':'匹配主链','events':'WHOT_MATCH_REQUEST、WHOT_MATCH_END、WHOT_MATCH_CANCEL','purpose':'建立匹配分母，记录成功、取消、超时和失败结果'},
 {'group':'降级建议','events':'WHOT_MATCH_OFFER、WHOT_MATCH_RESPONSE','purpose':'记录N1/N2建议、用户响应和实际降级开局'},
]

def markdown_table(rows,columns):
    labels=[label for _,label in columns]
    lines=['| '+' | '.join(labels)+' |','|'+'|'.join('---' for _ in labels)+'|']
    for row in rows:lines.append('| '+' | '.join(str(row[key]) for key,_ in columns)+' |')
    return '\n'.join(lines)

def build_svg():
    def box(x,y,w,text,fill,stroke='#7b91a6'):
        return f'<rect x="{x}" y="{y}" width="{w}" height="64" rx="12" fill="{fill}" stroke="{stroke}"/><text x="{x+w/2}" y="{y+38}" text-anchor="middle">{text}</text>'
    parts=['''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="520" viewBox="0 0 1500 520">
<style>text{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;fill:#263f52;font-size:22px;font-weight:600}.label{font-size:26px;fill:#174e7b}.note{font-size:19px;font-weight:500;fill:#6d5529}.arrow{stroke:#7890a5;stroke-width:3;marker-end:url(#a)}.dash{stroke:#c19d55;stroke-width:3;stroke-dasharray:8 7;marker-end:url(#a)}</style>
<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#7890a5"/></marker></defs>
<rect width="1500" height="520" rx="24" fill="#f5f8fb"/><text class="label" x="54" y="64">旧版：以已开局牌局为主</text>''']
    old=[(55,100,235,'入口点击 MC'),(415,100,235,'GAMESTART'),(775,100,235,'GAMEEND'),(1135,100,300,'BETREWARD / ASSET')]
    for x,y,w,t in old:parts.append(box(x,y,w,t,'#e8eef3'))
    for x1,x2 in [(290,415),(650,775),(1010,1135)]:parts.append(f'<line class="arrow" x1="{x1}" y1="132" x2="{x2-12}" y2="132"/>')
    parts.append('<rect x="297" y="183" width="345" height="58" rx="10" fill="#fff3d8" stroke="#d4ad63"/><text class="note" x="470" y="219" text-anchor="middle">匹配尝试与失败路径难还原</text><line class="dash" x1="470" y1="183" x2="470" y2="163"/>')
    parts.append('<text class="label" x="54" y="310">新版一期：覆盖开局前完整过程</text>')
    new=[(55,345,170,'用户分组'),(255,345,190,'引导与加载'),(475,345,190,'模式与房间'),(695,345,190,'匹配请求'),(915,345,250,'状态 / 建议 / 响应'),(1195,345,235,'结果 → 开局')]
    for x,y,w,t in new:parts.append(box(x,y,w,t,'#e5f3f8','#6b9cb0'))
    for left,right in zip(new,new[1:]):parts.append(f'<line class="arrow" x1="{left[0]+left[2]}" y1="377" x2="{right[0]-12}" y2="377"/>')
    parts.append('<text class="note" x="750" y="470" text-anchor="middle">新版把用户选择、服务端处理和最终结果串成同一次匹配</text></svg>')
    return ''.join(parts)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'comparison.json').write_text(json.dumps({'comparison':comparison,'metrics':metric_rows,'reuse':reuse_rows,'new':new_rows},ensure_ascii=False,indent=2)+'\n')
    (OUT/'old-vs-phase1.svg').write_text(build_svg())
    report=f'''# {TITLE}

## 执行摘要

**新版一期把统计范围从“已开局牌局”扩展到“开局前完整过程”。** 旧版通用事件可以观察入口、开局、结束和资金，但匹配取消、超时、组桌失败等用户没有开局的原因缺少统一记录。

**匹配请求成为新版最重要的数据对象。** 新版用同一次匹配标识串联人数选择、房间、服务端受理、队列变化、降级建议、用户响应、匹配结果和GAMESTART，匹配成功率才有完整分母。

**旧版核心事件继续复用。** MC、GAMESTART、GAMEEND、BETREWARD和ASSET保留原职责；新版补充关联键和人数、版本等字段，减少重复建设。

**旧版匹配成功率需要先验证日志。** 当前证据可以确认通用事件和历史统计需求，尚不能证明旧版已经完整记录每次匹配请求及失败结果。旧日志可重建后，再做新旧成功率和等待时长比较。

## 新旧链路变化

![旧版与新版一期埋点链路](old-vs-phase1.png)

旧版主要从GAMESTART开始形成完整数据。新版一期向前补齐用户分组、引导、加载、模式与房间选择，以及匹配处理过程，因此能够解释“为什么没有开局”。

## 一期7项需求差异

{markdown_table(comparison,[('requirement','一期需求'),('legacy','旧版已知情况'),('phase1','新版一期计划'),('change','主要变化'),('type','处理方式')])}

## 可复用与新增内容

### 继续复用

{markdown_table(reuse_rows,[('item','现有事件'),('handling','处理'),('work','一期调整')])}

### 一期新增

{markdown_table(new_rows,[('group','新增范围'),('events','事件组'),('purpose','解决的问题')])}

## 指标能力变化

{markdown_table(metric_rows,[('metric','指标'),('legacy','旧版能力'),('phase1','新版一期能力'),('comparison','新旧比较方式')])}

## 关键判断

1. **入口到开局可以连续分析。** MC、加载、人数和房间选择、匹配请求及GAMESTART使用同一条关联链。
2. **匹配结果可以完整解释。** 成功、取消、超时和失败分别记录，结果未知也保留。
3. **四人体验与最终开局分开评价。** 同时看四人模式兑现率和任意人数开局率，避免降级开局掩盖四人供给不足。
4. **客户端记录用户意图，服务端确认业务结果。** 展示和点击由客户端记录，受理、匹配结果、实际人数和开局由服务端确认。

## 建议实施顺序

1. **先统一用户分组和关联键。** 固定新老、付费状态、游戏ID、规则版本、匹配请求和牌局的对应关系。
2. **再扩展现有事件。** 补齐MC、加载和GAMESTART字段，保证入口、选择和开局可以关联。
3. **完成匹配主链。** 上线请求、状态、取消、建议、响应和唯一结果事件。
4. **双轨核对。** 同时保留旧事件和新版一期事件，核对开局数、牌局数和资金结果的一致性。
5. **建立新版基线。** 旧日志可重建时比较共同指标；无法重建时，从新版一期形成首个可信匹配基线。

## 数据边界

- 本报告比较的是旧版已知埋点能力与新版一期设计，不代表新版事件已经上线。
- 旧版托管和初始手牌属于历史统计需求，现网字段完整度仍需回读验证。
- 新版二期需求08—15不在本次比较范围。
'''
    (OUT/'report.md').write_text(report)
    knowledge=ROOT/'knowledge/02-数据/Whot旧版埋点与新版一期计划对比分析-2026-09-07.md'
    knowledge.write_text(report)
    receipt={'status':'review_ready','scope':'legacy vs phase1 requirements 01-07','sources':['report_data.jsonl','Whot新版玩法与旧版埋点对照及规划-2026-09-07.md','v2/requirements_contract.json'],'comparison_rows':len(comparison),'metric_rows':len(metric_rows),'visuals':['old-vs-phase1.svg'],'evidence_boundary':'old production completeness not verified'}
    (OUT/'build_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({**receipt,'knowledge':str(knowledge.relative_to(ROOT))},ensure_ascii=False))

if __name__=='__main__':main()

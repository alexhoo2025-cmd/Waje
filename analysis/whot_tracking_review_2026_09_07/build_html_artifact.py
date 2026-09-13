#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
RUN_AT = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rows() -> dict[str, list[dict]]:
    status = [{
        "p0_new_events": 8,
        "p1_new_events": 3,
        "reuse_or_extend_events": 8,
        "primary_metrics": 3,
        "open_decisions": 10,
        "first_load_mb": 1.5,
        "full_flow_mb": 2.5,
    }]
    event_stage_counts = [
        {"stage": "入口与准备", "event_count": 4, "order": 1, "scope": "MC + H5 LOAD/READY/BET_READY"},
        {"stage": "匹配", "event_count": 6, "order": 2, "scope": "REQUEST/STATE/OFFER/RESPONSE/CANCEL/END"},
        {"stage": "开局", "event_count": 1, "order": 3, "scope": "GAMESTART"},
        {"stage": "玩法与恢复", "event_count": 5, "order": 4, "scope": "ACTION/LAST_CARD/TIE_BREAK/RECONNECT/TRACKER"},
        {"stage": "结束与资金", "event_count": 3, "order": 5, "scope": "GAMEEND/BETREWARD/ASSET"},
    ]
    old_new = [
        {"area": "人数意图", "legacy": "系统决定 4/3/2 人", "new": "用户选择 2 或 4 人", "measurement": "requested_match_mode 必须独立记录"},
        {"area": "低峰开局", "legacy": "系统按阈值降到当前人数或机器人", "new": "N1/N2 建议并按真人共同同意降级", "measurement": "offer、响应集合、实际人数"},
        {"area": "付费分池", "legacy": "当前资料没有可比口径", "new": "付费只配付费，非付费只配非付费", "measurement": "payer_pool 分层"},
        {"area": "取消", "legacy": "客户端可退出匹配", "new": "取消与建桌按服务端先后裁决", "measurement": "取消请求和取消结果分开"},
        {"area": "Last Card", "legacy": "没有该规则", "new": "宣告、抓罚、罚抽 2、失效后重宣告", "measurement": "独立状态机"},
        {"area": "牌堆耗尽", "legacy": "记录耗尽与积分", "new": "最低分唯一或多轮同分决胜", "measurement": "决胜阶段和轮次"},
        {"area": "记牌器", "legacy": "已有功能", "new": "当局购买，下一局生效", "measurement": "购买局与生效局关联"},
        {"area": "H5体验", "legacy": "横版", "new": "竖版轻量化、弱网与低端机", "measurement": "资源字节与 LOAD→BET_READY"},
    ]
    p0_events = [
        {"event": "WHOT_MATCH_REQUEST", "trigger": "服务端受理真人匹配请求", "business_use": "匹配率主分母", "minimum_keys": "match_attempt_id, requested_match_mode"},
        {"event": "WHOT_MATCH_STATE", "trigger": "队列人员或状态发生变化", "business_use": "还原人数变化和重新判断", "minimum_keys": "match_attempt_id, queue_epoch, state"},
        {"event": "WHOT_MATCH_OFFER", "trigger": "生成 N1/N2/尝试双人建议", "business_use": "建议曝光和低峰依赖", "minimum_keys": "offer_id, offer_stage, target_count"},
        {"event": "WHOT_MATCH_RESPONSE", "trigger": "服务端确认同意/拒绝/等待/无响应", "business_use": "建议同意率和降级路径", "minimum_keys": "offer_id, response, result"},
        {"event": "WHOT_MATCH_CANCEL_RESULT", "trigger": "取消请求获得服务端结果", "business_use": "取消与建桌竞争", "minimum_keys": "client_action_id, cancel_result"},
        {"event": "WHOT_MATCH_END", "trigger": "一次 attempt 达到唯一终态", "business_use": "开局/取消/超时/失败", "minimum_keys": "match_attempt_id, terminal_reason"},
        {"event": "WHOT_LAST_CARD", "trigger": "宣告和抓罚状态改变", "business_use": "宣告、抓罚和罚抽质量", "minimum_keys": "game_round_id, state, actor_type"},
        {"event": "WHOT_TIE_BREAK", "trigger": "牌堆耗尽和决胜阶段改变", "business_use": "同分决胜完整性", "minimum_keys": "tie_break_id, round_no, state"},
    ]
    other_events = [
        {"priority": "复用", "event": "MC", "use": "入口、2/4 人选择、房间、Quick Match、Rules"},
        {"priority": "复用设计", "event": "H5_GAME_LOAD", "use": "加载阶段、资源字节、缓存与错误"},
        {"priority": "复用设计", "event": "H5_GAME_READY", "use": "真实画面和配置 ready"},
        {"priority": "复用设计", "event": "H5_BET_READY", "use": "余额、币种、限额、连接和控件 ready"},
        {"priority": "扩展", "event": "GAMESTART", "use": "关联 match_attempt_id、实际人数和席位组成"},
        {"priority": "P1新增", "event": "WHOT_ACTION", "use": "服务端接受的出牌/摸牌/选图案/恢复动作"},
        {"priority": "P1新增", "event": "WHOT_RECONNECT_RESULT", "use": "快照恢复、耗时和重复动作抑制"},
        {"priority": "P1新增", "event": "WHOT_TRACKER_RESULT", "use": "购买局、计划生效局和实际生效局"},
        {"priority": "扩展", "event": "GAMEEND", "use": "唯一局终态、结束原因、点数和人机组成"},
        {"priority": "复用", "event": "BETREWARD", "use": "最终结算、币种和金额方向"},
        {"priority": "复用", "event": "ASSET", "use": "账本幂等和余额对账"},
    ]
    key_contract = [
        {"key": "root_match_id", "job": "串联 Quick Match/Play Again 的匹配旅程", "rule": "一次明确发起产生；重试不换根键"},
        {"key": "match_attempt_id", "job": "一次服务端受理的排队尝试", "rule": "主分析单位；重新入队新建"},
        {"key": "queue_epoch", "job": "人员稳定的一段队列", "rule": "加入/离开/取消/断线重算时递增"},
        {"key": "offer_id / offer_stage", "job": "一次降级建议", "rule": "N1/N2 独立，不继承响应"},
        {"key": "client_action_id", "job": "客户端动作幂等", "rule": "取消、同意、宣告和抓罚使用"},
        {"key": "game_round_id", "job": "实际牌局", "rule": "GAMESTART 到 ASSET 全链一致"},
        {"key": "server_seq", "job": "状态顺序", "rule": "同一匹配/牌局单调递增"},
        {"key": "event_uid / event_version", "job": "事件幂等和 schema", "rule": "同一事实重试复用 UID"},
    ]
    core_metrics = [
        {"metric": "4 人原模式兑现率", "numerator": "请求 4 人并实际开 4 人的 attempts", "denominator": "成熟的服务端受理 4 人 attempts", "decision": "用户是否得到所选模式"},
        {"metric": "任意人数开局率", "numerator": "实际开 2/3/4 人的 attempts", "denominator": "全部成熟受理 attempts", "decision": "最终是否玩上"},
        {"metric": "降级挽回率", "numerator": "接受建议并实际开 2/3 人的 attempts", "denominator": "收到建议的成熟 attempts", "decision": "建议是否挽回开局"},
        {"metric": "超时率", "numerator": "terminal=timeout attempts", "denominator": "全部成熟受理 attempts", "decision": "匹配失败规模"},
        {"metric": "取消成功率", "numerator": "cancel_result=cancelled", "denominator": "有取消请求 attempts", "decision": "取消体验"},
        {"metric": "取消竞争失败率", "numerator": "建桌先完成、取消未生效", "denominator": "有取消请求 attempts", "decision": "被拉回牌局的风险"},
        {"metric": "匹配等待时长", "numerator": "match end - server accepted", "denominator": "P50/P90/P95", "decision": "真实等待体验"},
        {"metric": "机器人辅助开局率", "numerator": "开局且 robot_count>0", "denominator": "全部成熟受理 attempts", "decision": "系统对手依赖"},
    ]
    comparison_rules = [
        {"rule": "同分析单位", "requirement": "使用服务端受理 match_attempt_id", "failure_if_missing": "旧版匹配率 blocked"},
        {"rule": "同构成", "requirement": "固定付费池、房间、小时、端、包和版本权重", "failure_if_missing": "用户结构差异冒充版本效果"},
        {"rule": "共享池干扰", "requirement": "按房间×时间块或分阶段放量", "failure_if_missing": "新旧版本互相改变真人供给"},
        {"rule": "同时间读法", "requirement": "展示 P50/P90/P95 和共同 5/10/15 秒开局率", "failure_if_missing": "15 秒和 45 秒配置不可比"},
        {"rule": "同终态", "requirement": "取消、超时、风险无桌、建桌失败、未知分别保留", "failure_if_missing": "空结果被混成失败或成功"},
    ]
    gameplay = [
        {"topic": "Last Card", "measure": "pending、宣告、漏宣告、抓罚机会/成功、罚抽、失效", "guardrail": "多对手并发只允许一次成功"},
        {"topic": "机器人公平性", "measure": "机器人宣告/抓罚率、真人被机器人抓罚率", "guardrail": "按 bot policy version 汇总"},
        {"topic": "牌堆耗尽", "measure": "耗尽率、最低分唯一率、同分率", "guardrail": "结束原因由服务端确认"},
        {"topic": "同分决胜", "measure": "决胜率、轮次分布、重复同分、恢复失败", "guardrail": "每轮 tie_break_id + round_no"},
        {"topic": "托管", "measure": "进入/结束/恢复率、胜率、托管动作数", "guardrail": "事件级汇总替代日总数"},
        {"topic": "重连", "measure": "成功率、恢复耗时P95、状态完整率、重复抑制", "guardrail": "以后端快照为准"},
        {"topic": "记牌器", "measure": "购买成功、购买局→生效局、打开率", "guardrail": "定义下一局"},
        {"topic": "H5轻量化", "measure": "首局/全流程字节、LOAD→BET_READY、弱网失败", "guardrail": "1.5MB / 2.5MB 产品门槛"},
        {"topic": "局与资金", "measure": "完局、时长、实际人数、RTP、平台盈利", "guardrail": "GAMESTART→ASSET 对账"},
    ]
    implementation = [
        {"priority": "P0-1", "action": "确认游戏映射、匹配状态机、终态枚举和结算公式", "owner": "策划+服务端+数据", "evidence": "签字版字段与状态机"},
        {"priority": "P0-2", "action": "实现 MATCH REQUEST/STATE/OFFER/RESPONSE/CANCEL/END", "owner": "服务端", "evidence": "确定性用例和入库样本"},
        {"priority": "P0-3", "action": "扩展 GAMESTART/GAMEEND 并打通 BETREWARD/ASSET", "owner": "服务端+数据", "evidence": "局和资金对账"},
        {"priority": "P0-4", "action": "实现 Last Card/Tie Break 状态事件", "owner": "服务端+客户端", "evidence": "并发抓罚、决胜和重连用例"},
        {"priority": "P1-1", "action": "接入 H5 LOAD/READY/BET_READY 和资源性能", "owner": "H5+数据", "evidence": "弱网/低端机报告"},
        {"priority": "P1-2", "action": "接入托管、重连和记牌器事件", "owner": "游戏端+服务端", "evidence": "状态恢复与权益用例"},
        {"priority": "上线前", "action": "回放、双端同服对账、查询预演和灰度", "owner": "测试+数据+策划", "evidence": "质量门槛全部通过"},
    ]
    open_questions = [
        {"id": 1, "question": "H5 9006、APP/服务端 6001 与 play_id 的正式映射是什么？", "blocks": "跨端和新旧归因"},
        {"id": 2, "question": "4 人队列已有 2/3 名真人时是否允许机器人补位？", "blocks": "4人模式兑现与超时"},
        {"id": 3, "question": "队列只有本人时，跨 2 人真人与机器人候选谁优先？", "blocks": "机器人辅助率"},
        {"id": 4, "question": "payer_pool 在哪个时点判定，机器人如何进入分池？", "blocks": "付费/非付费匹配"},
        {"id": 5, "question": "X0/X1/X2、N1/N2、Y 的配置版本怎样记录？", "blocks": "等待和建议分析"},
        {"id": 6, "question": "Last Card 的 3 秒与按对手回合机会采用哪套状态机？", "blocks": "宣告/抓罚指标"},
        {"id": 7, "question": "记牌器购买后的“下一局”如何跨换房和断线定义？", "blocks": "权益生效"},
        {"id": 8, "question": "赢家金额按玩家人数还是对手人数计算？", "blocks": "结算/RTP/资产"},
        {"id": 9, "question": "机器人策略哪些字段进入受控审计，策略版本如何标识？", "blocks": "公平性和RTP"},
        {"id": 10, "question": "旧版是否存在可重建的 request/terminal 服务端日志？", "blocks": "新旧匹配率比较"},
    ]
    return {
        "status": status,
        "event_stage_counts": event_stage_counts,
        "old_new": old_new,
        "p0_events": p0_events,
        "other_events": other_events,
        "key_contract": key_contract,
        "core_metrics": core_metrics,
        "comparison_rules": comparison_rules,
        "gameplay": gameplay,
        "implementation": implementation,
        "open_questions": open_questions,
    }


def main() -> None:
    datasets = rows()
    report_data = []
    for dataset, values in datasets.items():
        for row in values:
            report_data.append({"dataset": dataset, **row})
    (ANALYSIS / "report_data.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in report_data) + "\n", encoding="utf-8")

    data_source = {
        "id": "src_report_data",
        "label": "Whot 埋点评审结构化数据",
        "path": "analysis/whot_tracking_review_2026_09_07/report_data.jsonl",
        "query": {
            "engine": "duckdb",
            "language": "sql",
            "sql": "SELECT * FROM read_json_auto('analysis/whot_tracking_review_2026_09_07/report_data.jsonl', format='newline_delimited', union_by_name=true);",
            "description": "从已复核的新版玩法、旧版埋点资料和事件/指标合同生成报告表格。",
            "executed_at": RUN_AT,
            "tables_used": ["analysis/whot_tracking_review_2026_09_07/report_data.jsonl"],
            "filters": ["设计评审截至2026-09-07", "不包含生产用户或订单明细"],
            "metric_definitions": ["P0事件数按event_contract中add_p0计数", "匹配主分母为成熟的服务端受理真人match_attempt_id"],
        },
    }
    sources = [
        data_source,
        {"id": "src_new_prd", "label": "Whot游戏H5竖版轻量化及app同步新增规则需求", "href": "https://ksg964l11fam.sg.larksuite.com/wiki/WjLww2oliipOPzkJMHil0yvbglc", "description": "2026-09-07回读revision 5641。"},
        {"id": "src_robot", "label": "Whot 6001 真金博彩机器人策略", "href": "https://ksg964l11fam.sg.larksuite.com/wiki/Sijzw1c40idjfRk2GMNlZbV5g2f", "description": "2026-09-07回读revision 69；上线状态待验收。"},
        {"id": "src_archive", "label": "Whot新版玩法与旧版埋点对照及规划", "path": "knowledge/02-数据/Whot新版玩法与旧版埋点对照及规划-2026-09-07.md", "description": "本地完整评审稿和来源边界。"},
    ]

    cards = [
        {"id": "card_p0", "dataset": "status", "sourceId": "src_report_data", "metrics": [{"label": "P0新增事件", "field": "p0_new_events", "format": "number", "unit": "个"}], "description": "匹配6个 + Last Card + Tie Break。"},
        {"id": "card_reuse", "dataset": "status", "sourceId": "src_report_data", "metrics": [{"label": "复用/扩展事件", "field": "reuse_or_extend_events", "format": "number", "unit": "个"}], "description": "保留跨游戏生命周期与H5 ready链路。"},
        {"id": "card_p1", "dataset": "status", "sourceId": "src_report_data", "metrics": [{"label": "P1新增事件", "field": "p1_new_events", "format": "number", "unit": "个"}], "description": "玩法动作、重连、记牌器。"},
        {"id": "card_metrics", "dataset": "status", "sourceId": "src_report_data", "metrics": [{"label": "核心决策指标", "field": "primary_metrics", "format": "number", "unit": "个"}], "description": "4人兑现、任意开局、等待P95。"},
        {"id": "card_questions", "dataset": "status", "sourceId": "src_report_data", "metrics": [{"label": "待确认边界", "field": "open_decisions", "format": "number", "unit": "项"}], "description": "必须在事件创建前形成签字口径。"},
        {"id": "card_resource", "dataset": "status", "sourceId": "src_report_data", "metrics": [{"label": "H5完整流程资源", "field": "full_flow_mb", "format": "number", "unit": "MB"}, {"label": "首局首次下载", "field": "first_load_mb", "format": "number", "unit": "MB"}], "description": "产品需求中的资源上限。"},
    ]
    charts = [{
        "id": "chart_event_scope",
        "title": "事件合同按生命周期阶段分布",
        "subtitle": "19个复用、扩展和新增事件；匹配阶段是本轮最大缺口。",
        "type": "bar",
        "dataset": "event_stage_counts",
        "sourceId": "src_report_data",
        "encodings": {
            "x": {"field": "stage", "type": "ordinal", "label": "阶段"},
            "y": {"field": "event_count", "type": "quantitative", "label": "事件数", "format": "number"},
            "tooltip": [{"field": "scope", "type": "nominal", "label": "范围"}],
        },
        "xAxisTitle": "生命周期阶段",
        "yAxisTitle": "事件数",
        "showDescription": True,
    }]
    tables = [
        {"id": "table_old_new", "title": "新旧玩法与测量要求", "subtitle": "按用户意图、匹配、玩法和体验逐项对照。", "dataset": "old_new", "sourceId": "src_report_data", "columns": [{"field": "area", "label": "环节", "type": "text"}, {"field": "legacy", "label": "旧版", "type": "text"}, {"field": "new", "label": "新版", "type": "text"}, {"field": "measurement", "label": "埋点要求", "type": "text"}]},
        {"id": "table_p0", "title": "P0 新增事件", "subtitle": "事件创建前先确认状态机和唯一键。", "dataset": "p0_events", "sourceId": "src_report_data", "columns": [{"field": "event", "label": "事件", "type": "text"}, {"field": "trigger", "label": "触发时机", "type": "text"}, {"field": "business_use", "label": "分析用途", "type": "text"}, {"field": "minimum_keys", "label": "最小关键字段", "type": "text"}]},
        {"id": "table_other_events", "title": "复用、扩展与 P1 事件", "subtitle": "跨游戏通用链路继续保留，玩法和恢复能力单独补充。", "dataset": "other_events", "sourceId": "src_report_data", "columns": [{"field": "priority", "label": "处理", "type": "text"}, {"field": "event", "label": "事件", "type": "text"}, {"field": "use", "label": "用途", "type": "text"}]},
        {"id": "table_keys", "title": "匹配与牌局关联键", "subtitle": "每个键只承担一个层级，重试和状态变化不混用。", "dataset": "key_contract", "sourceId": "src_report_data", "columns": [{"field": "key", "label": "关联键", "type": "text"}, {"field": "job", "label": "用途", "type": "text"}, {"field": "rule", "label": "生成与更新规则", "type": "text"}]},
        {"id": "table_metrics", "title": "核心匹配指标", "subtitle": "分母统一为成熟的服务端受理真人匹配尝试。", "dataset": "core_metrics", "sourceId": "src_report_data", "columns": [{"field": "metric", "label": "指标", "type": "text"}, {"field": "numerator", "label": "分子", "type": "text"}, {"field": "denominator", "label": "分母/统计", "type": "text"}, {"field": "decision", "label": "回答的问题", "type": "text"}]},
        {"id": "table_comparison", "title": "新旧比较质量门", "subtitle": "不满足任一项时，相应版本效果结论降级或阻断。", "dataset": "comparison_rules", "sourceId": "src_report_data", "columns": [{"field": "rule", "label": "检查", "type": "text"}, {"field": "requirement", "label": "要求", "type": "text"}, {"field": "failure_if_missing", "label": "缺失时的风险", "type": "text"}]},
        {"id": "table_gameplay", "title": "新版玩法专项指标", "subtitle": "每项都以服务端确认状态或完整资金链为准。", "dataset": "gameplay", "sourceId": "src_report_data", "columns": [{"field": "topic", "label": "专题", "type": "text"}, {"field": "measure", "label": "指标", "type": "text"}, {"field": "guardrail", "label": "质量护栏", "type": "text"}]},
        {"id": "table_implementation", "title": "实施顺序与验收证据", "subtitle": "先定状态机和口径，再创建事件与上线灰度。", "dataset": "implementation", "sourceId": "src_report_data", "columns": [{"field": "priority", "label": "顺序", "type": "text"}, {"field": "action", "label": "动作", "type": "text"}, {"field": "owner", "label": "建议负责人", "type": "text"}, {"field": "evidence", "label": "验收证据", "type": "text"}]},
        {"id": "table_questions", "title": "待策划与研发确认", "subtitle": "这些问题会直接改变事件定义、分母或结算结果。", "dataset": "open_questions", "sourceId": "src_report_data", "columns": [{"field": "id", "label": "#", "type": "number", "format": "number"}, {"field": "question", "label": "问题", "type": "text"}, {"field": "blocks", "label": "影响", "type": "text"}]},
    ]
    blocks = [
        {"id": "title", "type": "markdown", "body": "# Whot 新版埋点方案｜评审版"},
        {"id": "summary", "type": "markdown", "body": "## Executive Summary\n\n**旧版事件能解释已开局的牌局，解释不了为什么没开局。** 新版首先要把一次匹配尝试完整记录下来，从用户选择2/4人、服务端受理、队列变化、N1/N2建议，到取消、超时、失败或开局。\n\n**四人局同时看“原模式兑现”和“最终玩上”。** 4人原模式兑现率回答用户是否真的获得四人局；任意人数开局率回答降级后是否玩上；降级挽回率说明建议机制救回了多少尝试。三者不能互相替代。\n\n**匹配、Last Card和同分决胜是P0。** 匹配链需要6个服务端状态事件，Last Card和Tie Break各需要独立状态机；托管、重连、记牌器和H5性能放在P1。\n\n**新旧比较先过可比性门槛。** 如果旧版服务日志不能重建失败和取消尝试，旧版匹配成功率无法客观计算。共享匹配池还要求按房间和时间分批发布，并固定付费池、端、房间和小时构成。"},
        {"id": "scope_cards", "type": "metric-strip", "cardIds": ["card_p0", "card_reuse", "card_p1", "card_metrics", "card_questions", "card_resource"]},
        {"id": "gap_story", "type": "markdown", "body": "## 新版第一数据对象是一条匹配尝试\n\n旧版已有通用局事件、托管统计和初始手牌需求，但匹配失败不会产生GAMESTART或GAMEEND。新版自选2/4人、付费状态分池、N1/N2同意降级和取消竞争，让“尝试但未开局”成为最关键的分析对象。\n\n**决策含义：**先完成服务端匹配事实，再扩展玩法事件；否则上线后只能看到开了多少局，仍无法回答四人局为什么失败。"},
        {"id": "old_new_table", "type": "table", "tableId": "table_old_new"},
        {"id": "event_scope_story", "type": "markdown", "body": "## 匹配阶段是本轮最大的新增工作量\n\n19个事件中，匹配阶段需要6个P0服务端事件，覆盖请求、队列、建议、响应、取消结果和唯一终态。入口和局生命周期优先复用现有事件，避免同一行为出现两套分母。\n\n**图中数量表示事件合同范围，不表示业务重要性或当前上报量。**"},
        {"id": "event_scope_chart", "type": "chart", "chartId": "chart_event_scope"},
        {"id": "p0_story", "type": "markdown", "body": "## P0先打通匹配、Last Card与同分决胜\n\n匹配事件全部由服务端确认，客户端点击只用于解释用户意图。Last Card和同分决胜采用状态事件，支持多人并发、重连和唯一结果校验。"},
        {"id": "p0_table", "type": "table", "tableId": "table_p0"},
        {"id": "other_events_story", "type": "markdown", "body": "## 通用事件继续复用，恢复与权益单独补充\n\nGAMESTART、GAMEEND、BETREWARD和ASSET继续承担跨游戏开局、终局和资金对账。H5的LOAD/READY/BET_READY沿用既有设计。托管动作、重连结果和记牌器生效进入P1。"},
        {"id": "other_events_table", "type": "table", "tableId": "table_other_events"},
        {"id": "keys_story", "type": "markdown", "body": "## 关联键把用户旅程、匹配尝试和牌局分开\n\n`root_match_id`描述连续匹配旅程，`match_attempt_id`描述一次排队，`queue_epoch`描述一次稳定队列，`game_round_id`只在真正开局后产生。这样既能去重，也能保留多次建议、取消竞争和重连顺序。"},
        {"id": "keys_table", "type": "table", "tableId": "table_keys"},
        {"id": "metric_story", "type": "markdown", "body": "## 同时看四人兑现、任意开局和等待体验\n\n主分母是达到成熟截止时间的服务端受理真人匹配尝试。机器人参与、用户取消、超时和建桌失败保留为结果维度；配置生成的虚拟在线人数不进入任何分子或分母。\n\n**产品判断：**如果任意开局率提高而4人兑现率下降，说明降级机制提高了可玩性，但四人体验供给仍不足。"},
        {"id": "metrics_table", "type": "table", "tableId": "table_metrics"},
        {"id": "comparison_story", "type": "markdown", "body": "## 新旧版本只有在同一分析单位下才可比较\n\n旧版等待约15秒，新版4人最长45秒，因此直接比较平均时长会误导。报告应同时展示原始P50/P90/P95、共同的5/10/15秒开局率和各自超时率。共享池发布还会互相改变真人供给，优先按房间×时间块或分阶段放量。"},
        {"id": "comparison_table", "type": "table", "tableId": "table_comparison"},
        {"id": "gameplay_story", "type": "markdown", "body": "## 新玩法需要可恢复的状态事件\n\nLast Card、同分决胜、托管和记牌器都可能跨多个回合或发生重连。服务端必须记录状态、顺序和唯一结果；局结束时只保留汇总，避免把所有过程塞进GAMEEND。"},
        {"id": "gameplay_table", "type": "table", "tableId": "table_gameplay"},
        {"id": "next_steps", "type": "markdown", "body": "## Recommended next steps\n\n1. **先签字口径。** 确认6001/9006/play_id映射、4人机器人边界、Last Card状态机、记牌器下一局和正式结算公式。\n2. **服务端先实现匹配事实。** 完成6个匹配事件及唯一关联键，再扩展GAMESTART/GAMEEND。\n3. **完成玩法与资金回归。** 覆盖多人并发抓罚、多轮决胜、断线恢复和GAMESTART→ASSET对账。\n4. **灰度后再比较。** 固定房间、时段、付费池和端构成；旧版attempt不可重建时，从新版建立首个可信基线。"},
        {"id": "implementation_table", "type": "table", "tableId": "table_implementation"},
        {"id": "questions_story", "type": "markdown", "body": "## Further Questions\n\n下面10项会直接改变事件字段、指标分母或结算结果，需要策划、服务端和数据团队在创建事件前确认。"},
        {"id": "questions_table", "type": "table", "tableId": "table_questions"},
        {"id": "caveats", "type": "markdown", "body": "## Caveats and Assumptions\n\n- 新版埋点尚未上线，本文中的事件名和字段是评审方案。\n- 旧版资料包含历史迁移文档，不能证明所有字段当前仍完整上报。\n- 本次没有执行生产查询；旧版匹配attempt可重建性仍待服务端核验。\n- 机器人策略文档是候选策略来源，是否进入新版及生效版本待确认。\n- 当前最关键的规则冲突是Last Card时序、记牌器生效和结算公式，未确认前不得发布对应经营指标。"},
    ]
    artifact = {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "Whot 新版埋点方案｜评审版",
            "description": "旧版埋点复用、新版匹配与玩法状态、指标分母、新旧比较及发布验收。",
            "generatedAt": RUN_AT,
            "sources": sources,
            "cards": cards,
            "charts": charts,
            "tables": tables,
            "blocks": blocks,
        },
        "snapshot": {"version": 1, "generatedAt": RUN_AT, "status": "ready", "datasets": datasets},
        "sources": sources,
    }
    (ANALYSIS / "artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS / "chart_map.json").write_text(json.dumps({
        "status": "ready",
        "charts": [{"section": "匹配阶段是本轮最大的新增工作量", "question": "事件合同主要新增在哪个生命周期阶段", "family": "comparison", "type": "bar", "dataset": "event_stage_counts", "fields": ["stage", "event_count", "scope"], "takeaway": "匹配阶段新增6个P0服务端事件", "palette": "single blue with text labels"}],
        "omissions": ["没有业务结果趋势图，因为新版尚未上线且本次证据是设计合同。"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ready", "artifact": str(ANALYSIS / "artifact.json"), "datasets": {k: len(v) for k, v in datasets.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()

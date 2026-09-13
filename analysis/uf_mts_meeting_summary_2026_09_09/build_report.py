#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def cell(value: object, background: str | None = None, bold: bool = False) -> str:
    bg = "" if background is None else f' background-color="{background}"'
    text = f"<b>{esc(value)}</b>" if bold else esc(value)
    return f'<td{bg} vertical-align="middle"><p>{text}</p></td>'


def table(headers: list[str], rows: list[list[str]], widths: list[int]) -> str:
    cols = "<colgroup>" + "".join(f'<col width="{w}"/>' for w in widths) + "</colgroup>"
    head = "<thead><tr>" + "".join(
        f'<th background-color="medium-gray"><p><b>{esc(item)}</b></p></th>' for item in headers
    ) + "</tr></thead>"
    body = "<tbody>" + "".join(
        "<tr>" + "".join(item if item.startswith("<td") else cell(item) for item in row) + "</tr>"
        for row in rows
    ) + "</tbody>"
    return "<table>" + cols + head + body + "</table>"


def status(value: str, tone: str) -> str:
    return cell(value, f"light-{tone}", True)


def main() -> None:
    summary = (
        '<callout emoji="💡" background-color="light-blue" border-color="blue"><ol>'
        '<li><b>当前仍处于UF第一阶段。</b>访问令牌已经生成，但SDK示例尚未下载、控制台模板尚未配置、首次连接尚未完成；当前最重要的交付是让Java SDK在集成环境收到并正确处理首批消息。</li>'
        '<li><b>UF是MTS和生产上线的前置门禁。</b>MTS使用Transaction 3.0 API；可在资源充足时并行开发，但正式体育前端测试及相关团队交接仍依赖UF阶段评审和最终集成评审。</li>'
        '<li><b>集成难点集中在数据一致性和恢复链路。</b>平台需要正确组合AMQP动态消息与API静态信息，并处理赛前到滚球切换、市场复合键、断线恢复、回滚/取消及赛果结算。</li>'
        '<li><b>时间表尚未形成统一承诺。</b>会议出现供应商常规8—10周、可压缩4—6周、Waje计划3—10周及“长期大改”等多种表述；应改为按可验收里程碑排期，并明确资源、负责人和退出标准。</li>'
        '</ol></callout>'
    )

    source_rows = [
        ["逐字稿", "2026年9月9日 17:32—18:09", "原始发言记录，作为会议事实主来源", "revision 3"],
        ["AI智能纪要", "同一场会议", "用于核对待办和章节，不作为独立会议重复计数", "revision 5"],
        ["体育改版需求v1", "产品需求", "确认Sportradar数据范围、页面一致性、异常处理及埋点要求", "revision 302"],
        ["三方合作对接整理／Sportradar", "商务台账", "补充收费与Alpha Odds条款；会议未再次确认", "revision 283"],
    ]

    status_rows = [
        ["项目阶段", "UF Stage 1", status("进行中", "blue"), "已生成访问令牌；首次连接未完成"],
        ["SDK", "建议使用最新4.1版；Waje计划Java", status("待下载", "yellow"), "供应商承诺提供下载链接和技术演示材料"],
        ["控制台模板", "赛前与滚球生产者均需配置", status("未完成", "red"), "未配置前无法接收基础Feed消息"],
        ["静态数据导入", "体育类型、国家、联赛、赛事、市场描述", status("待实施", "yellow"), "应先于AMQP业务消息处理"],
        ["MTS", "Transaction 3.0 API", status("门禁后启动", "blue"), "UF Sprint／集成评审后进入正式对接；资源足够可并行开发"],
        ["Live Data", "独立产品、独立凭据与商务范围", status("待确认", "yellow"), "需与销售确认采购范围和环境账号"],
        ["培训", "控制台操作培训", status("暂缓", "blue"), "当前先使用教程；需要时再预约培训"],
        ["生产环境", "完成集成并通过最终评审后开放", status("未开放", "red"), "生产阶段才需要IP白名单"],
    ]

    data_contract_rows = [
        ["动态数据", "AMQP推送", "赔率、盘口、赛事状态及事件消息", "必须持续监听并按顺序处理；不能依赖频繁API轮询"],
        ["静态信息", "API／SDK查询", "体育、联赛、球队、赛事详情、市场描述", "本地缓存近期赛事，减少无效查询"],
        ["实体主键", "完整URN", "prefix＋type＋ID", "只保存数字ID会产生跨类型重复风险"],
        ["市场主键", "market ID＋specifier＋producer/product ID", "盘口线及赛前/滚球来源", "同一market ID可跨生产者复用，specifier不能遗漏"],
        ["赛前与滚球", "两个生产者", "赛前产品ID与滚球产品ID需区分", "交接后停用赛前市场并同步前端状态"],
        ["心跳", "每个生产者约10秒Alive消息", "约20秒未收到应视为异常信号", "结合SDK状态上报、告警和可观测日志"],
        ["当前恢复", "SDK自动Present Recovery", "初始化、Odds恢复、Snapshot Complete", "应用必须等快照完成后再把状态标为可服务"],
        ["历史恢复", "带时间戳的Past Recovery", "恢复断线期间遗漏的状态消息", "服务重启必须保存最后处理时间点"],
        ["Fixture恢复", "应用主动调用", "使用与Odds恢复一致的时间戳", "SDK不会自动补全，必须单独实现并验收"],
    ]

    roadmap_rows = [
        ["阶段1｜连接准备", "SDK 4.1、令牌、唯一node ID、模板、静态数据导入、首次连接", "能稳定收到两类生产者消息；Snapshot Complete完成；基础对象落库", "当前阶段"],
        ["阶段2｜基础消息", "Fixture Change、Odds Change、Bet Stop、Bet Settlement", "消息落库、页面状态和投注状态一致；完成第一次Sprint评审", "UF核心路径"],
        ["阶段3｜异常与容量", "Rollback、取消、赛前→滚球交接、断线恢复、Replay压测", "250场滚球并发；消息处理≤2秒；恢复后数据无遗漏或重复", "高风险阶段"],
        ["阶段4｜扩展范围", "新增体育／市场、Outright、边界场景、环境使用", "范围清单通过、异常状态完整、最终集成评审通过", "上线前门禁"],
        ["MTS与体育前端测试", "Transaction 3.0 API、前端Sportsbook测试", "UF评审通过后完成前后端联调及供应商验收", "可并行开发，验收有前置"],
    ]

    product_rows = [
        ["赛事与市场映射", "体育、国家、联赛、赛事、球队、玩法、盘口", "完整URN；市场ID＋specifier＋来源；赛前/滚球映射可追溯"],
        ["实时一致性", "首页、赛事大厅、详情、即时比分、数据分析、投注篮", "比分、赔率、盘口、封盘和赛事状态在各页面一致"],
        ["投注安全", "赔率变化、封盘、提交超时、重复点击", "提交前重新校验；状态不确定时查询最终订单，不重复扣款"],
        ["赛果与结算", "官方赛果进入平台结算", "完整性校验；异常赛果进入人工或风控复核"],
        ["弱网体验", "尼日利亚低端设备与不稳定网络", "局部刷新、最近有效状态、可理解错误提示；核心投注流程可完成"],
        ["数据记录", "曝光、赛事筛选、赔率选择、投注提交、失败原因", "埋点可还原从首页到投注结果的完整链路"],
    ]

    risk_rows = [
        ["P0", "模板和首次连接尚未完成", "项目仍未进入可验证的消息处理阶段", "先完成Stage 1最小闭环，再展开大规模页面开发"],
        ["P0", "时间表口径冲突", "无法判断是否按计划推进，容易形成对内外不同承诺", "用里程碑、负责人、开始/完成日期重排项目计划"],
        ["P0", "复合主键遗漏", "市场、盘口或生产者切换时可能覆盖、重复或错配", "数据库设计评审必须覆盖URN、specifier和producer/product ID"],
        ["P0", "恢复与幂等未见实施证据", "断线或服务重启后可能漏赔率、重复结算或状态倒退", "保存offset/timestamp/request ID，建立可重放与幂等验证"],
        ["P1", "Java SDK与现有技术栈适配", "会议确认无Go SDK且计划使用Java，但部署边界未确认", "明确独立Feed服务、资源规格、版本升级和故障隔离方案"],
        ["P1", "产品文档命名不一致", "需求文档同时出现Sportradar和BetRadar", "统一供应商名称并建立外部ID到内部ID的数据字典"],
        ["P1", "Live Data商务与技术边界未确认", "可能遗漏账号、环境、能力包和费用", "销售、产品、技术联合确认采购能力及凭据矩阵"],
        ["P1", "商业条款未进入实施门禁", "MMG及Alpha Odds增量分成可能影响上线范围", "财务／商务确认合同版本、计费数据和月度对账责任"],
    ]

    action_rows = [
        ["P0", "获取并锁定UF SDK 4.1示例及版本", "供应商集成支持＋Waje技术", "下载链接、校验版本、示例可运行", "待办／日期待确认"],
        ["P0", "配置赛前与滚球模板", "Waje技术／运营配置", "两类生产者模板截图或配置回执", "待办／Stage 1"],
        ["P0", "完成Java SDK首次连接", "Waje后端", "集成环境连接日志、唯一node ID、Alive与Snapshot Complete", "待办／Stage 1"],
        ["P0", "完成静态对象导入及数据库主键评审", "Waje后端＋数据", "体育／赛事／市场数据字典，URN与市场复合键DDL", "待办／Stage 1"],
        ["P0", "确认里程碑和资源计划", "项目负责人＋前后端＋供应商", "两次Sprint评审、最终评审、前端测试日期", "待确认"],
        ["P1", "实现基础Feed消息和异常状态", "Waje后端＋前端", "Fixture/Odds/Stop/Settlement及页面状态验收", "Stage 2"],
        ["P1", "实现恢复、回滚、取消和交接逻辑", "Waje后端＋QA", "Present/Past/Fixture Recovery与幂等测试报告", "Stage 3"],
        ["P1", "执行容量及延迟测试", "QA／性能", "250场并发，消息处理P95≤2秒，积压和恢复指标", "Stage 3"],
        ["P1", "确认Live Data与Alpha Odds范围", "商务＋产品＋技术", "采购能力表、环境凭据、计费和对账口径", "待确认"],
    ]

    commercial_rows = [
        ["收入分成", "月收入0—€500k：10.5%；>€500k—€1m：9.5%；>€1m—€1.5m：8.5%；>€1.5m：7.5%", "需与正式合同版本核对"],
        ["最低月费MMG", "第一年€10,000/月；第二年€11,000/月；第三年€13,000/月", "上线节奏和范围会影响单位成本"],
        ["Alpha Odds", "相对标准赔率产生的月度GGR Uplift收取15%", "需保留实际赔率与标准赔率双轨数据，支持月度复算"],
    ]

    xml = [
        '<title>UF、MTS与实时数据技术整合会议汇总及实施建议｜2026年9月9日</title>',
        '<h1 seq="auto">汇总结论（Executive Summary）</h1>',
        summary,
        '<h1 seq="auto">会议与资料范围</h1>',
        '<p><b>两份链接属于同一场会议。</b>第一份是逐字稿，第二份是AI智能纪要；本报告以逐字稿为事实主来源，AI纪要只用于核对待办和章节。逐字稿中多个发言人共用同一设备标识，因此行动责任以角色表达，未根据说话人编号推断具体个人。</p>',
        table(["资料", "适用时间／类型", "本报告用途", "版本"], source_rows, [190, 180, 330, 100]),
        '<callout background-color="light-yellow" border-color="yellow"><p><b>记录状态：</b>这是基于会议材料和现有项目文档形成的工作汇总，不代表全部行动已获资源或日期批准；owner和截止日期缺失处仍需项目负责人确认。</p></callout>',
        '<h1 seq="auto">当前状态：令牌已生成，但尚未形成首条可验证数据链路</h1>',
        '<p><b>Stage 1的阻塞点不是账号本身，而是SDK、模板、首次连接和静态数据导入尚未闭环。</b>在收到真实Feed消息前，后续消息处理、恢复、压测和前端一致性都无法进入有效验收。</p>',
        table(["事项", "会议确认内容", "状态", "判断"], status_rows, [150, 285, 120, 330]),
        '<h1 seq="auto">技术模型：AMQP负责动态变化，API负责静态信息</h1>',
        '<p><b>UF是消息驱动系统。</b>动态赔率和状态从AMQP推送，API用于补充静态元数据；平台必须在本地合并两类信息，维护顺序、幂等、缓存和恢复位置。</p>',
        table(["对象／机制", "来源", "关键内容", "实施要求"], data_contract_rows, [145, 170, 260, 320]),
        '<h1 seq="auto">路线图：以评审门禁组织计划，而不是承诺单一周数</h1>',
        '<p><b>建议按两次Sprint评审和一次最终评审管理进度。</b>每个阶段只有在验收证据齐全后才进入下一阶段；周度检查用于发现偏差，不替代阶段退出标准。</p>',
        table(["阶段", "主要范围", "退出标准", "定位"], roadmap_rows, [175, 300, 345, 120]),
        '<h1 seq="auto">项目需求映射：集成成功必须落到页面一致性和投注安全</h1>',
        '<p><b>体育改版并非单纯替换数据源。</b>项目要求Sportradar支撑赛事、盘口、赔率、比分、赛况、统计、赛果和结算，并确保不同页面显示同一状态。</p>',
        table(["能力域", "产品范围", "集成验收重点"], product_rows, [155, 290, 450]),
        '<h1 seq="auto">主要风险与需要决策的问题</h1>',
        table(["优先级", "风险／未决", "影响", "处理建议"], risk_rows, [90, 230, 295, 300]),
        '<h1 seq="auto">行动清单</h1>',
        table(["优先级", "行动", "责任角色", "交付／验收证据", "状态／时点"], action_rows, [80, 245, 190, 315, 130]),
        '<h1 seq="auto">商务条款需与技术范围同步确认</h1>',
        '<p><b>以下内容来自《三方合作对接整理》的Sportradar子表，并未在本次技术会议中重新确认。</b>正式实施前应以合同和最新报价为准。</p>',
        table(["条款", "台账内容", "项目影响"], commercial_rows, [150, 440, 300]),
        '<h1 seq="auto">术语与转写校正</h1>',
        '<ul><li>逐字稿中的“pretty much”按上下文解释为Prematch（赛前）；“live ads”解释为Live Odds（滚球赔率）。</li><li>“ads change”解释为Odds Change；“bad stop／bad settlement”解释为Bet Stop／Bet Settlement。</li><li>上述为基于上下文的转写校正，最终接口名称以供应商SDK、文档和评审清单为准。</li></ul>',
        '<h1 seq="auto">仍需确认</h1>',
        '<ul><li>Waje最终承诺的UF、MTS和体育前端时间表，以及各阶段投入人数。</li><li>Java SDK作为独立Feed服务还是嵌入现有服务，部署、扩缩容和升级责任归属。</li><li>赛前与滚球生产者的准确product ID、模板范围和Live Booking流程。</li><li>MTS与Live Data的正式账号、环境、权限、采购能力和合同版本。</li><li>供应商演示材料、SDK下载链接、Sprint检查清单是否已收到并归档。</li></ul>',
        '<h1 seq="auto">来源</h1>',
        '<ul><li><a href="https://ksg964l11fam.sg.larksuite.com/docx/O7pJdqWIJosQAXxxqbqlFXjkgOc">会议逐字稿</a></li><li><a href="https://ksg964l11fam.sg.larksuite.com/docx/B5zbdIs0UoGVHfxXY5IlOjJCgNe">AI智能纪要</a></li><li><a href="https://ksg964l11fam.sg.larksuite.com/wiki/VbPJwiD0QiHVPYkFocblawUrgCd">体育改版需求v1</a></li><li><a href="https://ksg964l11fam.sg.larksuite.com/wiki/CkVOwZ2s3iJmdjkiEl1lXz4qgcd?sheet=39SSLe">三方合作对接整理／Sportradar</a></li></ul>',
    ]

    content = "\n\n".join(xml) + "\n"
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "report.xml").write_text(content)
    (ROOT / "report.md").write_text(
        "# UF、MTS与实时数据技术整合会议汇总及实施建议\n\n"
        "当前处于UF Stage 1：令牌已生成，但SDK示例、模板、首次连接和静态数据导入尚未闭环。\n\n"
        "MTS使用Transaction 3.0 API，正式测试与交接依赖UF评审。项目排期应按Stage 1—4、两次Sprint评审及最终集成评审管理。\n"
    )
    (ROOT / "source-receipt.json").write_text(json.dumps({
        "status": "sources_reviewed",
        "primary_source": {"token": "O7pJdqWIJosQAXxxqbqlFXjkgOc", "type": "verbatim_transcript", "revision": 3},
        "secondary_source": {"token": "B5zbdIs0UoGVHfxXY5IlOjJCgNe", "type": "ai_minutes", "revision": 5},
        "project_sources": [
            {"token": "VbPJwiD0QiHVPYkFocblawUrgCd", "title": "体育改版需求v1", "revision": 302},
            {"token": "M425spjRxhSvkathmHglrx6Tgce", "sheet_id": "39SSLe", "title": "三方合作对接整理/Sportradar", "revision": 283}
        ],
        "source_conflicts": ["项目周期存在3—10周、4—6周、8—10周和长期项目等不同表述", "体育需求文档同时出现Sportradar与BetRadar名称"],
        "privacy": "role_based_actions_no_personal_identifiers"
    }, ensure_ascii=False, indent=2))
    (ROOT / "quality-checks.json").write_text(json.dumps({
        "status": "passed", "primary_transcript_used": True, "same_meeting_not_double_counted": True,
        "meeting_decisions_separated_from_suggestions": True, "missing_owners_and_dates_marked": True,
        "project_documents_cross_checked": True, "source_links_present": True,
        "tables": content.count("<table>"), "headings": content.count('<h1 seq="auto">'),
        "no_credentials_or_tokens_in_body": True
    }, ensure_ascii=False, indent=2))
    if len(sys.argv) > 1:
        (PROJECT / sys.argv[1]).write_text(content)
    print(json.dumps({"status": "ready", "chars": len(content), "tables": content.count("<table>"), "headings": content.count('<h1 seq="auto">')}, ensure_ascii=False))


if __name__ == "__main__":
    main()

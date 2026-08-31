#!/usr/bin/env python3
"""Build the Lark Docx XML draft from the safe H5/Ares inventory."""

from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "analysis/h5_origin_tracking_inventory_2026_08_28/inventory.json"
DRAFT = ROOT / "draft_3e2ca1b6_folder/draft.xml"


def x(value):
    return escape("" if value is None else str(value), quote=True)


def p(value):
    return f"<p>{x(value)}</p>"


def table(headers, rows):
    head = "<thead><tr>" + "".join(f"<th>{p(v)}</th>" for v in headers) + "</tr></thead>"
    body = "<tbody>" + "".join(
        "<tr>" + "".join(f"<td>{p(v)}</td>" for v in row) + "</tr>" for row in rows
    ) + "</tbody>"
    return f"<table>{head}{body}</table>"


def link(label, url):
    return f'<a type="url-preview" href="{x(url)}">{x(label)}</a>'


def main():
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    pages = inv["h5_pages"]
    meta = inv["meta_events"]
    fields = inv["h5_relevant_event_properties"]
    quality = inv["quality_rows"]
    virtual = inv["h5_relevant_virtual_events"]
    qsum = inv["quality_summary"]

    meta_rows = [
        [m["relevance"], m["event_name"], m["display_name"], m["yesterday_ingested_count"], m["description"] or "—"]
        for m in meta
    ]
    page_rows = [
        [r["page_name"], r["page_id"], r["system_type"], r["module_event_count"], r["updated_at"]]
        for r in pages
    ]
    field_rows = [
        [f["group"], f["name"], f["display_name"], f["type"], f["property_type"], f["dimension_table"], f["description"]]
        for f in fields
    ]
    quality_rows = [
        [r["event_name"], r["source"], f'{r["received_count"]:,}', f'{r["ingested_count"]:,}',
         f'{r["abnormal_count"]:,}', r["abnormal_rate"]]
        for r in quality
    ]
    virtual_rows = [[r["id"], r["identifier"], r["name"], "目录已见；规则待核"] for r in virtual]
    core_rows = [
        [r["page_id"], r["page_name"], " / ".join(r["historical_function_event_ids"]),
         "已见", r["evidence_state"], r["note"]]
        for r in inv["h5_core_mapping"]
    ]
    perf_rows = [
        [r["logical_event"], r["trigger"], r["dedupe_key"], "待创建", r["priority"]]
        for r in inv["h5_performance_events"]
    ]

    xml = []
    add = xml.append
    add("<title>Waje H5 起源埋点上报全量盘点（团队阅读版）</title>")
    add('<h1 seq="auto">结论先行</h1>')
    add('<callout emoji="✅" background-color="light-green" border-color="green">' +
        p("本次以历史 Markdown、Lark H5 埋点工作表 revision 93 和 Ares Waje Special 当前只读页面为主证据。已核对 34 个元事件、74 个 H5 页面、111 个事件属性和最近 7 天质量聚合。H5 当前可做页面访问及部分业务事实分析，但性能事件、H5 来源拆分、模块明细和真实功能 event_id 仍未闭环。") +
        "</callout>")
    add('<grid><column width-ratio="0.25">' + p("34\n元事件") + '</column><column width-ratio="0.25">' + p("74\nH5 页面") + '</column><column width-ratio="0.25">' + p("178\n配置模块/事件") + '</column><column width-ratio="0.25">' + p("6.1284%\nGAMEEND 异常率") + '</column></grid>')
    add('<callout emoji="⚠️" background-color="light-red" border-color="red">' +
        p("P0 口径纠偏：Ares 元事件列表中的 2855092、2184105、1589607、2199814 位于“昨日入库量”列，元事件详情也未将其展示为事件 ID。历史文档将其记作实际 event_id 的做法不能继续沿用；研发必须从功能埋点详情或导出取得真实 event_id。") +
        "</callout>")
    add('<h2 seq="auto">范围与证据状态</h2>')
    add(table(["项目", "结论"], [
        ["产品空间", "Ares 当前选择器为 Waje Special。"],
        ["终端范围", "H5、安卓H5；历史方案另覆盖 PWA、APP WebView，但当前上报分层未独立证实。"],
        ["主证据", "Ares 元事件、页面、模块、功能参数、事件属性、用户属性、数据质量、埋点测试。"],
        ["辅助证据", "Lark H5 埋点表 revision 93；历史知识库文档；GA4/BigQuery 仅作辅助。"],
        ["隐私", "不保存凭据、请求正文、用户明细、完整设备指纹、owner 展示名或测试页载荷。"],
    ]))
    add(table(["状态", "含义", "使用规则"], [
        ["historical_design", "历史需求/方案中定义", "只还原设计，不代表当前上线"],
        ["ares_config_observed", "Ares 当前页面可见配置", "只证明配置存在"],
        ["ares_ingestion_observed", "质量页有接收/入库聚合", "需确认端和业务语义"],
        ["h5_source_observed", "质量表来源含 js", "证明 H5/JS 线索，不等于具体页面调用"],
        ["actual_validation_pending", "明细、来源拆分或关联键未回读", "不得写成已配置/已上报"],
        ["platform_no_rows", "平台返回空表/暂无数据", "不等于不存在配置"],
    ]))

    add('<h1 seq="auto">H5 埋点证据链</h1>')
    add("""<whiteboard type="mermaid">flowchart LR
A[历史需求与Lark采集表] --> B[Ares页面/模块/功能配置]
B --> C[H5 SDK getReqData]
C --> D[Ares元事件接收/入库]
D --> E[数据质量与埋点测试]
E --> F[聚合报表/看板]
G[服务端注册/订单/下注/结算/资产事实] --> F
D -.来源/端/版本拆分待补.-> F</whiteboard>""")
    add(p("业务层级：页面 PV/PD → 模块 MV/MC → 功能事件 → 服务端事实。页面或客户端事件只能证明行为过程；注册成功、订单支付、下注、结算、资产到账和提现终态必须以服务端事实为准。"))

    add('<h1 seq="auto">Ares 现网对象</h1>')
    add('<h2 seq="auto">元事件清单（34 个）</h2>')
    add(p("下表“昨日入库量”沿用 Ares 当前列表字段原义；它不是事件 ID，也不是最近 7 天质量窗口的接收量。"))
    add(table(["分组", "事件", "展示名", "昨日入库量", "说明"], meta_rows))
    add('<h2 seq="auto">H5 页面清单（74 个）</h2>')
    add(table(["页面名", "page_id", "端类型", "模块数/事件数", "最后更新时间"], page_rows))
    add(p("页面列表的模块数/事件数是配置统计，不是实时上报量；owner 展示名不进入本团队文档。"))
    add('<h2 seq="auto">模块与功能明细</h2>')
    add(table(["对象", "当前状态", "解释"], [
        ["模块列表", "暂无数据", "不能据此判定没有模块；需核查接口、产品上下文和权限。"],
        ["功能埋点参数", "暂无数据", "不能据此判定没有功能参数；历史采集表仍保留登记。"],
        ["页面管理日志", "H5 首页可见新增与二次修改", "只证明配置变化，不证明线上上报。"],
    ]))

    add('<h1 seq="auto">历史采集表与现网对照</h1>')
    add(p("Lark H5 页面采集表 revision=93，工作表为说明、页面埋点方式、通用参数、自定义参数。"))
    add(table(["page_id", "页面", "历史登记功能事件", "当前页面", "证据状态", "备注"], core_rows))
    add('<h2 seq="auto">H5 性能逻辑事件</h2>')
    add(table(["逻辑编码", "触发时机", "关联键", "实际 event_id", "优先级"], perf_rows))
    add(p("10 个事件在历史需求表中有定义，但本次 Ares 现场未观察到对应逻辑编码或实际 ID，属于 historical_design，不纳入当前性能看板。"))

    add('<h1 seq="auto">事件属性与分析能力</h1>')
    add(p("Ares 事件属性目录当前去重观察到 111 个字段；以下是与 H5 页面、游戏、资产和 DOM 结构直接相关的 31 个安全字段。身份标识、广告标识、网络硬件标识和原始崩溃载荷类字段不展开，也不保存其值。"))
    add(table(["分组", "字段", "展示名", "类型", "属性类型", "维度表", "平台说明"], field_rows))
    add('<h2 seq="auto">可支持与不可支持</h2>')
    add(table(["分析层面", "当前能力", "边界"], [
        ["H5 页面访问", "PV + page_id + 页面配置", "H5 来源在质量表中与其他端混合，需补分母。"],
        ["页面停留", "PD + event_duration", "单位/来源可作为候选，H5 单独上报尚未核验。"],
        ["模块曝光/点击", "MV/MC + 元素字段", "模块明细页为空，H5 来源未单独证实。"],
        ["注册/登录", "REGISTER/LOGIN + 页面", "服务端事实有量，步骤/会话关联不足。"],
        ["游戏入口到开局", "MV/MC → GAMESTART", "缺 session、entry、game_load 关联。"],
        ["游戏局级事实", "GAMESTART/GAMEEND/BETREWARD/ASSET", "GAMEEND 异常 P0；金额和链路需对账。"],
        ["充值/提现", "商城/TX 页面 + ORDER/WITHDRAW/AUDIT", "页面行为不等于订单/提现终态。"],
        ["H5 性能", "历史方案设计", "10 个性能事件未落地，自动 Web 量接近 0。"],
        ["版本/包/渠道", "页面端类型 + 历史设计字段", "实际 H5/PWA/WebView/版本/包拆分待补。"],
    ]))

    add('<h1 seq="auto">实际上报与质量状态</h1>')
    add(table(["对象", "Ares 配置", "上报证据", "H5 拆分", "当前结论"], [
        ["PV", "元事件和 H5 页面可见", "质量表来源包含 js", "部分", "页面访问候选可用，端/版本需补"],
        ["PD", "元事件和 H5 页面可见", "当前可见来源未含 js", "未证", "停留候选，H5 单独上报待证"],
        ["MV", "元事件和 H5 页面可见", "当前可见来源未含 js", "未证", "配置存在，调用待证"],
        ["MC", "元事件和 H5 页面可见", "当前可见来源未含 js", "未证", "入口转化待证"],
        ["PAGELOAD", "元事件可见", "昨日入库量 0", "否", "不能支持性能结论"],
        ["AUTOPV/AUTOPD", "元事件可见", "昨日入库量 1；AUTOPV质量为1接收/0入库", "极弱", "只作异常线索"],
        ["AUTOMC/AUTOWEBSTAY", "元事件可见", "昨日入库量 0", "否", "不能支持 Web 点击/停留"],
        ["GAMESTART/GAMEEND", "服务端元事件可见", "质量窗口有 server 接收；GAMEEND异常较高", "不足", "游戏事实候选，H5入口关联待补"],
        ["ORDER/WITHDRAW/AUDIT/ASSET", "服务端元事件可见", "质量窗口有接收/入库", "不足", "服务端结果事实，不等同 H5行为"],
        ["10个H5性能事件", "历史需求设计", "未观察到实际 Ares ID", "否", "未落地"],
    ]))

    add('<h1 seq="auto">最近 7 天数据质量</h1>')
    add(p("质量窗口：2026-08-21 至 2026-08-27；产品：Waje Special。"))
    add(table(["指标", "数值"], [
        ["接收条数", f'{qsum["received_count"]:,}'],
        ["入库条数", f'{qsum["ingested_count"]:,}'],
        ["异常属性条数", f'{qsum["abnormal_count"]:,}'],
        ["抛弃条数", f'{qsum["dropped_count"]:,}'],
        ["错误率", qsum["error_rate"]],
    ]))
    add(table(["事件", "上报源", "接收", "入库", "异常", "异常率"], quality_rows))
    add('<callout emoji="🚨" background-color="light-red" border-color="red">' +
        p("GAMEEND：112,564,153 条接收、105,665,781 条入库、6,898,372 条异常，按异常/接收计算约 6.1284%。在异常字段、版本和来源未拆清前，不得直接用于完局、RTP、人机或收益结论。") +
        "</callout>")

    add('<h1 seq="auto">虚拟事件与 H5 分析入口</h1>')
    add(table(["ID", "事件标识", "展示名", "状态"], virtual_rows))
    add(p("当前 Ares 虚拟事件目录共 41 个；上表仅列页面、生命周期、交易和游戏常用目录，组合条件尚未逐一核验。"))

    add('<h1 seq="auto">P0/P1/P2 整改与验收</h1>')
    add('<grid><column width-ratio="0.33">' + p("P0 可信度\n纠正 ID 误标；修复 GAMEEND；拆分 H5 来源；服务端事实为准。") + '</column><column width-ratio="0.33">' + p("P1 可诊断性\n创建 10 个性能事件；补 session/page_visit/game_load/request；修复空结果链路。") + '</column><column width-ratio="0.34">' + p("P2 可维护\n清理 0/0 历史页；发版核验；建立版本/包/渠道质量看板。") + '</column></grid>')
    add('<h2 seq="auto">研发验收</h2>')
    add('<ul><li>Ares 产品空间确认是 Waje Special。</li><li>每个 H5 页面保留 page_id；功能事件取得真实 event_id；逻辑编码、实际 ID、昨日入库量分列。</li><li>H5 PV/PD/MV/MC 可按 session/page_visit 去重，并可区分 H5/PWA/WebView/版本/包/渠道。</li><li>游戏加载 → ready → 可下注可按关联键连接；真实注册、订单、下注、结算、资产和提现结果以服务端事实确认。</li><li>必填字段完整率 ≥99.5%，核心入库率 ≥99%，GAMEEND 异常率 &lt;1%，链路关联率 ≥98%。</li><li>性能分位数仅使用 measurement_state=complete；未知/不支持不得以 0 伪造。</li></ul>')

    add('<h1 seq="auto">后续刷新流程</h1>')
    add("""<whiteboard type="mermaid">flowchart LR
A[历史Markdown与Lark采集表] --> B[Ares现网对象]
B --> C[数据质量/测试聚合]
C --> D[按对象、实际ID、revision/hash去重]
D --> E[新增/修改/下线/无样本/阻塞]
E --> F[更新MD与飞书]
F --> G[刷新知识图谱与回执]</whiteboard>""")
    add(p("建议每周或每次发版执行。固定保存观察日期、质量窗口、产品空间、对象数量、H5 页面/0-0 页面、核心事件接收/入库/异常/来源、实际功能 ID 回读状态和待人工确认项。"))

    add('<h1 seq="auto">来源</h1>')
    add("<p>" + "<br/>".join([
        link("Ares 元事件管理", "https://datagrowth.trackares.com/tracking-web/burying/eventPoint/tupleEvent"),
        link("Ares 页面列表", "https://datagrowth.trackares.com/tracking-web/burying/buryingPoint/pageManagement"),
        link("Ares 模块列表", "https://datagrowth.trackares.com/tracking-web/burying/buryingPoint/moduleList"),
        link("Ares 埋点参数", "https://datagrowth.trackares.com/tracking-web/burying/buryingPoint/paramList"),
        link("Ares 事件属性", "https://datagrowth.trackares.com/tracking-web/burying/buryingPoint/param"),
        link("Ares 用户属性", "https://datagrowth.trackares.com/tracking-web/burying/buryingPoint/paramUser"),
        link("Ares 数据质量", "https://datagrowth.trackares.com/tracking-web/burying/buryingPoint/dataQuality"),
        link("Ares 埋点测试", "https://datagrowth.trackares.com/tracking-web/burying/buryingPoint/trajectoryDetail"),
        link("H5历史埋点采集表", "https://ksg964l11fam.sg.larksuite.com/sheets/YBwksyRY2hRHiwtThD8l86EzgXe?sheet=Sw06fl") + "（revision 93）",
    ]) + "</p>")
    add('<callout emoji="ℹ️" background-color="light-yellow" border-color="orange">' +
        p("交付状态：partial_actual_ares_with_historical_baseline。Ares 元事件、页面、虚拟事件、事件属性和质量页已只读盘点；模块/功能明细、H5来源拆分、真实功能 event_id 和性能事件落地状态待补证。") +
        "</callout>")

    DRAFT.write_text("".join(xml), encoding="utf-8")
    print(DRAFT)


if __name__ == "__main__":
    main()


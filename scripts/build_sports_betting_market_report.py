#!/usr/bin/env python3
"""Build the Waje sports betting and prediction-market research report."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DATE = "2026-08-18"
OUT_DIR = ROOT / "data/outputs/competitor" / REPORT_DATE
DATA_PATH = OUT_DIR / "sports-betting-prediction-markets-analysis.json"
SOURCE_PATH = OUT_DIR / "source-registry.json"
MARKDOWN_PATH = ROOT / "knowledge/03-竞品/专题" / f"{REPORT_DATE}-全球体育真金博彩与预测市场产品商业化分析.md"
HTML_PATH = ROOT / "knowledge/03-竞品/专题" / f"{REPORT_DATE}-全球体育真金博彩与预测市场产品商业化分析.html"
PREVIEW_PATH = ROOT / "output/html/Waje-global-sports-betting-prediction-markets-analysis.html"


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_map(sources: dict) -> dict[str, dict]:
    return {item["id"]: item for item in sources["sources"]}


def source_tag(source_ids: list[str], sources: dict) -> str:
    lookup = source_map(sources)
    return " ".join(f"[S{list(lookup).index(source_id) + 1}]" for source_id in source_ids if source_id in lookup)


def money(value: object, unit: str, currency: str) -> str:
    if value is None:
        return "未披露"
    if unit == "million":
        return f"{currency} {float(value):,.1f}m".replace(".0m", "m")
    return f"{value} {unit}"


def operator_rows(data: dict, sources: dict) -> list[list[str]]:
    source_ids = {
        "fanduel_flutter": ["flutter_2024_10k"],
        "bet365": ["bet365_2024_accounts"],
        "draftkings": ["draftkings_2024_10k", "draftkings_2024_results"],
        "betmgm": ["betmgm_2024_update"],
        "betway_supergroup": ["supergroup_2024_10k"],
    }
    rows = []
    for item in data["operators"]:
        metrics = item["metrics"]
        if item["id"] == "fanduel_flutter":
            revenue = money(metrics["us_segment_revenue"], metrics["us_segment_revenue_unit"], "USD") + "（US段）"
            activity = f"{metrics['us_sportsbook_amps']}m US Sportsbook AMPs"
            handle = money(metrics["us_sportsbook_stakes"], metrics["us_sportsbook_stakes_unit"], "USD")
            margin = f"{metrics['us_sportsbook_net_revenue_margin']}% NRM"
        elif item["id"] == "bet365":
            revenue = money(metrics["group_turnover"], metrics["group_turnover_unit"], "GBP")
            activity = "未披露可比 MUP"
            handle = "未披露"
            margin = f"运营利润 {money(metrics['operating_profit'], metrics['operating_profit_unit'], 'GBP')}"
        elif item["id"] == "draftkings":
            revenue = money(metrics["revenue"], metrics["revenue_unit"], "USD")
            activity = f"{metrics['q4_mups']}m Q4 MUP"
            handle = money(metrics["sportsbook_handle"], metrics["sportsbook_handle_unit"], "USD")
            margin = f"{metrics['sportsbook_net_revenue_margin']}% NRM"
        elif item["id"] == "betmgm":
            revenue = money(metrics["net_revenue"], metrics["net_revenue_unit"], "USD")
            activity = f"{metrics['average_monthly_actives']}m AMA"
            handle = money(metrics["sportsbook_handle"], metrics["sportsbook_handle_unit"], "USD")
            margin = f"在线体育 GGR {metrics['online_sports_ggr_share']}%"
        else:
            revenue = money(metrics["betway_revenue"], metrics["betway_revenue_unit"], "USD") + "（Betway）"
            activity = f"{metrics['betway_average_monthly_active_customers']}m Betway MAAC"
            handle = "未披露可比值"
            margin = f"体育 margin {metrics['sports_betting_margin']}%"
        rows.append([item["brand"], item["parent"], item["geography"], revenue, handle, activity, margin, source_tag(source_ids[item["id"]], sources)])
    return rows


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(out)


def build_markdown(data: dict, sources: dict) -> str:
    op_rows = operator_rows(data, sources)
    capability_rows = [[row["capability"], row["fanduel_flutter"], row["bet365"], row["draftkings"], row["betmgm"], row["betway_supergroup"], row["polymarket"], row["kalshi"]] for row in data["product_capability_matrix"]]
    persona_rows = [[item["name"], item["need"], item["product_signal"], item["commercial_role"]] for item in data["user_personas"]]
    principle_rows = [[item["priority"], item["principle"], item["why"], item["adoption"], item["guardrail"]] for item in data["waje_principles"]]
    source_lines = []
    for index, item in enumerate(sources["sources"], 1):
        source_lines.append(f"| S{index} | {item['entity']} | [{item['title']}]({item['url']}) | {item['period']} | {item['source_type']} | {item['evidence_grade']} |")

    sections = [
        "---",
        "type: research-analysis",
        "domain: competitor",
        "status: generated",
        f"updated: {REPORT_DATE}",
        "tags: [sports-betting, prediction-markets, product, monetization, waje, nigeria, west-africa]",
        "---",
        "",
        "# 全球体育真金博彩与预测市场产品商业化分析",
        "",
        "> 研究截止：2026-08-18｜目标读者：Waje 产品、商业化、运营与数据团队｜落地视角：尼日利亚/西非",
        "",
        "## 执行摘要",
        "",
        "本报告不把‘最大’简化为一个收入排名，而是选择公开规模、市场覆盖和数据可验证性同时较强的五个体育真金博彩品牌/集团组合：FanDuel（Flutter）、bet365、DraftKings、BetMGM、Betway（Super Group）。报告将集团层数据、品牌/地区层数据和产品层数据拆开，所有数字保留期间、币种和口径。",
        "",
        "最值得 Waje 借鉴的不是某个大额奖金或某个炫技功能，而是成熟平台把‘赛事内容 → 理解赔率 → 投注单 → 实时反馈 → 结算/再次进入’做成连续体验，并用定价、数据、CRM、支付和风险控制共同支撑商业化。",
        "",
        "Polymarket 与 Kalshi 提供了另一种思路：用户交易的是可转让的事件合约，价格表达群体对结果的隐含概率，平台依靠撮合、手续费、流动性和结算规则形成网络效应。它们可以启发 Waje 的概率表达、市场信息和社交观察层，但不能被当成绕过当地博彩牌照、KYC 或责任博彩要求的替代方案。",
        "",
        "### 结论先行",
        "",
        "- **应该采用**：明确的体育入口、简单首注、实时赛事中心、可理解的赔率/概率表达、可靠结算与提现、分层 CRM、服务端事实指标和责任博彩护栏。",
        "- **谨慎采用**：大规模首注补贴、复杂 Parlay、过度实时刺激、社交排行榜、预测市场式 P2P 交易和跨市场复制。",
        "- **不应直接复制**：美国联邦预测市场的监管定位、加密货币结算、成熟市场的营销预算强度、没有本地牌照/支付/风控基础时的全球化扩张。",
        "",
        "## 研究口径与证据等级",
        "",
        "| 等级 | 含义 | 使用方式 |",
        "|---|---|---|",
        "| A | 年报、SEC/IR、公司正式财务或官方规则 | 可作为经营事实，但仍保留集团/品牌边界 |",
        "| A- | 官方产品页、帮助中心、规则文档或公司披露的产品事实 | 用于功能与机制判断 |",
        "| B | 公司自报平台指标、内部研究或第三方对官方文件的整理 | 需注明“公司自报/内部证据/估算” |",
        "| C | 行业推断、媒体估算、不可完整复核的第三方信息 | 只用于方向性背景，不作为核心结论 |",
        "",
        "数据比较原则：Handle/投注额不是收入；GGR/NGR 不是用户充值；交易量不是预测市场收入；集团收入不能当作单一品牌收入；不同期间、币种和监管市场不做未经调整的排名。",
        "",
        "## 全球 Top 5 横向矩阵",
        "",
        md_table(["品牌/平台", "母集团", "主要市场", "公开收入代理", "Sports Handle", "活跃用户代理", "利润/效率代理", "来源"], op_rows),
        "",
        "### 五家平台的产品商业化画像",
        "",
        "### FanDuel / Flutter：规模、定价与内容飞轮",
        "",
        "Flutter 2024 年集团收入为 USD 14.048bn、平均月度玩家 13.9m；其美国段收入为 USD 5.798bn，Sportsbook 金额 staked 为 USD 50.876bn，Sportsbook AMPs 3.1m，Sportsbook NRM 7.9%。这些数字说明 FanDuel 的优势并非单一赔率页面，而是规模化定价、品牌/联盟内容、跨品类交叉销售和高强度数据营销共同作用。集团 2024 年销售与市场费用为 USD 3.205bn，不能直接归因于 FanDuel，但能反映成熟平台的获客和品牌投入强度。",
        "",
        "产品启发：把赛事观看、赔率理解、投注和责任工具放在同一场景；商业化上应优先追求可持续 NGR 和留存，而不是只追求 Handle。",
        "",
        "### bet365：全球深度、功能密度与私有化运营",
        "",
        "bet365 的 53 周公司账目显示，2024-03-31 期间集团 Turnover 为 GBP 3.720bn，其中 Sports and Football Club gaming turnover 为 GBP 3.696bn，Operating Profit 为 GBP 365.7m。它没有像上市公司那样披露可比 MUP 或 Sports Handle，因此不能与 FanDuel/DraftKings 的用户和 Handle 直接排位。",
        "",
        "产品页显示其将 In-Play、Live Streaming、Match Live、Bet Builder 与 Cash Out 组合在同一体育消费场景；这是一种‘功能密度服务于高频场景’的策略，而不是把所有功能堆在首屏。",
        "",
        "### DraftKings：数据化获客、跨品类与结构性 Hold",
        "",
        "DraftKings 2024 年收入 USD 4.768bn，Sportsbook Handle USD 48.1bn；2024 Q4 平均 MUP 4.8m，ARPMUP USD 97，Sportsbook NRM 6.0%。公司披露 FY2024 新增客户 3.5m，并强调结构性 Sportsbook hold 提升、促销再投资占 GGR 的比例下降约 200bp。",
        "",
        "其商业化重点是把 Sportsbook、iGaming、DFS、彩票和广告/赞助接成一个 Super App，并用 CAC、ARPMUP、MUP、Hold 和交叉销售共同管理用户价值。Waje 应学习其指标体系，而不是照搬其高竞争市场的促销力度。",
        "",
        "### BetMGM：iGaming 现金流支撑 Sportsbook 重建",
        "",
        "BetMGM 2024 年总净收入 USD 2.102bn，其中 Online Sports USD 554m，Sports Handle USD 13.075bn，平均月活 946k，Online Sports GGR share 8%，EBITDA 为 -USD 244m。公司将 2024 定义为投资和重建期，同时披露 MLB Same Game Parlay bets per active 增长 41%。",
        "",
        "这说明体育业务的短期收入和利润会受到赛事结果、促销和产品重建影响；如果有更高毛利或更稳定频次的相邻品类，跨品类经营可以平滑波动，但必须用真实增量和责任博彩指标管理。",
        "",
        "### Betway / Super Group：非美国市场规模与区域运营",
        "",
        "Super Group 2024 年集团收入 USD 1.835bn，Betway segment revenue USD 1.106bn，Sports Betting revenue USD 363m，Betway 平均月活客户 4.4m，Sports Betting margin 12.7%。公司披露的区域结构显示 Africa and Middle East 是重要增长来源，这使 Betway 比纯美国样本更适合 Waje 做西非运营参照，但集团收入包含 Spin 在线赌场，不能当作 Betway Sportsbook 收入。",
        "",
        "产品启发：区域化支付、体育内容、语言和营销渠道的组合可能比全局统一产品更重要；但跨地区扩张必须以牌照、支付和风险控制能力为前置条件。",
        "",
        "## 产品能力对比",
        "",
        md_table(["能力", "FanDuel", "bet365", "DraftKings", "BetMGM", "Betway", "Polymarket", "Kalshi"], capability_rows),
        "",
        "传统 Sportsbook 的核心是‘平台定价 + 用户下注 + 事件结算’，平台承担赔率、风险和流动性管理；预测市场的核心是‘用户报价/成交 + 事件合约结算’，平台更像交易所和规则/清算系统。两者在 UI 上都可以展示概率、价格变化、热门市场和即时反馈，但底层责任不同。",
        "",
        "## 商业化模型对比",
        "",
        "### 传统体育真金博彩",
        "",
        "1. 收入基础是 Sportsbook 的净博彩收入、赔率边际和长期 Hold；部分平台通过 iGaming、DFS、彩票、媒体、广告和赞助做交叉销售。",
        "2. 获客依靠联盟/球队/媒体合作、赛事内容、Affiliate、付费广告、促销和 CRM；成熟平台开始从‘大额补贴换注册’转向 CAC、留存、ARPMUP、结构性 Hold 和净促销成本。",
        "3. 运营优势来自赔率定价、实时数据、风控、赛事覆盖、支付可靠性和客服；单一功能很容易被复制，系统稳定性和用户信任更难复制。",
        "4. 主要风险是客户友好赛事结果导致短期收入波动、奖金和促销侵蚀、欺诈/套利、支付失败、合规成本和责任博彩风险。",
        "",
        "### Polymarket：协议化撮合与流动性激励",
        "",
        "Polymarket 当前帮助中心披露 Sports 市场对 Taker 收取 5% fee rate、Maker fee 为 0、Maker rebate 为 15%；费用用于 Maker Rebates，而不是传统意义上的庄家赔率收入。Polymarket 文档说明使用 UMA Optimistic Oracle，任何人可提出结果，之后进入挑战期，市场规则定义来源、结束时间和边界情况。",
        "",
        "这套机制的商业化关键不是‘押中后平台赚多少’，而是市场深度、订单撮合、交易频次、手续费和流动性激励。它能提供概率与市场情绪，但也把规则清晰度、争议解决和流动性质量变成核心产品。",
        "",
        "### Kalshi：受监管事件合约交易所与体育入口",
        "",
        "Kalshi 官方 Institutional 页面自报 8,000+ live markets、800+ institutional clients、USD 500bn+ annualized volume 和 1bn+ annual trades；这些属于公司自报平台指标，不等于审计收入，也不能与传统 Sportsbook Handle 直接比较。官方帮助中心将其定位为由官方来源和市场规则确定结算的事件合约平台，并提供体育 Combos。",
        "",
        "Kalshi 的商业化增长来自合规交易所身份、机构和零售入口、体育市场扩展、媒体/球队合作以及新市场供给；对 Waje 最有价值的启发是把‘事件、概率、规则、结算时间’做得可读，而不是复制其美国联邦监管路径。",
        "",
        "### 传统博彩与预测市场的迁移边界",
        "",
        md_table(["能力层", "Sportsbook 做法", "预测市场做法", "Waje 可借鉴", "不可直接复制"], [
            ["定价", "庄家赔率与隐含边际", "订单簿价格与隐含概率", "概率解释、价格变动、市场共识", "未经许可的 P2P 交易或金融化定位"],
            ["流动性", "平台承担风险与报价", "Maker/Taker 撮合与激励", "热门市场排序、深度/可成交性提示", "把用户资金风险转为平台无法管理的交易对手风险"],
            ["退出", "Cash Out 由平台报价", "用户在订单簿上卖出/平仓", "明确退出价值、暂停和延迟状态", "承诺任何时点都可退出或保证盈利"],
            ["结算", "官方赛事数据 + 规则 + 运营系统", "预言机/官方来源 + 市场规则", "规则摘要、来源、结算倒计时和争议说明", "绕过当地监管和责任博彩"],
            ["增长", "媒体、联盟、促销、CRM、Affiliate", "市场供给、流动性、内容和网络效应", "围绕赛事内容构建自然回访与社交分享", "用高频刺激和无上限补贴掩盖留存问题"]
        ]),
        "",
        "## 市场与用户画像",
        "",
        md_table(["用户类型", "核心需要", "产品信号", "商业角色"], persona_rows),
        "",
        "### 全球成熟市场与尼日利亚/西非的差异",
        "",
        "- 成熟市场的差异化来自赔率、实时数据、媒体版权、产品体验和用户价值管理；Waje 还必须先解决入口认知、支付/提现信任、结算透明度、语言和本地客服。",
        "- 美国样本的高额促销、联盟赞助和全国媒体合作不能直接作为 Waje 的单位经济目标；应先算清合格用户可触达规模、首注成功、净收入、奖励成本和 7 日回访。",
        "- 预测市场的‘概率产品’可以帮助降低理解门槛，但真实资金产品必须服从当地牌照、KYC、年龄/地区限制、负责任博彩、自我排除和营销审查。",
        "- Waje 内部研究显示，目标样本中存在体育入口发现和理解问题，且首注前流失是比复杂玩法更上游的瓶颈；该研究应作为实验假设，不应外推为全量用户事实。",
        "",
        "## Waje 产品启发与商业化原则",
        "",
        md_table(["优先级", "原则", "为什么", "建议采用", "护栏"], principle_rows),
        "",
        "### 设计原则的落地解释",
        "",
        "1. **先做清晰入口，再做复杂玩法。** 将 `Sports` 的语义改为用户能理解的体育下注/赛事入口，配合简短解释和可测量的曝光→点击→赛事→投注单→服务端首注成功漏斗。",
        "2. **首注体验采用‘简单市场 + 透明赔率 + 可恢复投注单’。** 默认展示少量易理解市场，解释赔率与潜在回报，保存投注单状态，避免第一次进入就暴露长尾盘口。",
        "3. **实时体验优先建设可靠状态恢复。** 实时比分、市场暂停、赔率更新、Cash Out 可用性和结算状态必须被用户看懂；不把实时刺激设计成追损工具。",
        "4. **把预测市场启发放在信息层。** 可尝试市场隐含概率、热门选择、价格变化、规则摘要、结算来源和社交分享；真正的交易所、加密结算和 P2P 机制不在本报告建议范围内。",
        "5. **把支付与提现当作核心产品。** 展示余额、下注成功、派彩、提现预计时间、费用、失败原因和客服升级路径；所有核心状态以服务端和账务事实为准。",
        "6. **激励按用户意图分层。** 新手用教育和小额、可审计的低风险激励；成熟用户用内容、个性化和服务；风险/脆弱用户不是商业化目标，必须获得限额、自我排除和冷静期保护。",
        "",
        "## 指标建议",
        "",
        "### 北极星与漏斗",
        "",
        md_table(["指标组", "建议指标", "计算/口径", "为什么重要"], [
            ["价值", "合格体育用户 7 日净贡献", "服务端首注/复投产生的 NGR - 奖励成本 - 支付/客服可归因成本", "防止用 Handle 或注册量掩盖补贴和风险"],
            ["发现", "体育入口触达率、点击率、正确理解率", "合格用户中曝光、点击和能正确解释入口的比例", "验证最上游瓶颈"],
            ["激活", "首注服务端成功率", "服务端 accepted bet 用户 ÷ 合格目标用户", "区分真实投注与点击/提交"],
            ["体验", "赛事详情→投注单→首注成功漏斗", "按 event、market、版本和实验分层", "找到具体体验断点"],
            ["复访", "7 日体育回访率、再次下注率", "首注 cohort 中 7 日内的查看/投注行为", "判断激活是否形成习惯"],
            ["效率", "CAC、促销再投资率、ARPU/ARPMUP", "按渠道、用户层、产品和市场分开", "对齐成熟平台的单位经济"],
            ["护栏", "拒单率、提现 P90、投诉率、奖励滥用率、风险提示/自我排除采用率", "服务端、账务、客服和责任博彩事实表", "保证增长不以信任和安全为代价"]
        ]),
        "",
        "### Waje 首期实验边界",
        "",
        "- 入口命名/图标实验：先看理解率和点击率，再看首注成功率。",
        "- 简单市场/短教程实验：用首注服务端成功和 7 日回访作为主指标，不用教程播放量作成功标准。",
        "- 低成本激励实验：必须有对照组、资格校验、奖励账本、反作弊和净收入口径。",
        "- 市场信息层实验：可展示概率、热门市场和价格变化，但必须保留规则、来源、结算、风险和监管说明。",
        "",
        "## 证据限制与待验证问题",
        "",
        "- bet365 是私有集团，公开账目不提供与上市同口径的 MUP、Handle 和市场份额，因此功能深度强、商业数据可比性弱。",
        "- Flutter 的集团收入/营销费用包含多个品牌和地区；FanDuel 的美国段数据是品牌代理，不应写成全球 FanDuel 单一财务报表。",
        "- BetMGM 的收入同时包含 iGaming、Online Sports 和其他业务；Betway/Super Group 的集团收入同时包含 Spin，已在矩阵中拆开。",
        "- Polymarket 与 Kalshi 的公开指标很大一部分是平台自报的交易量、市场数或机构客户数；报告不把它们视为审计收入，也不与传统 GGR/Handle 混算。",
        "- 尼日利亚/西非的牌照、税务、支付、年龄/KYC、责任博彩和体育数据合作条件需要法务、合规和本地业务进一步核实；本报告不是法律意见。",
        "",
        "## 来源注册表",
        "",
        md_table(["ID", "实体", "来源", "期间", "来源类型", "等级"], source_lines),
        "",
        "## 研究工件",
        "",
        "- 结构化指标：[sports-betting-prediction-markets-analysis.json](../../../data/outputs/competitor/2026-08-18/sports-betting-prediction-markets-analysis.json)",
        "- 来源注册表：[source-registry.json](../../../data/outputs/competitor/2026-08-18/source-registry.json)",
        "- 预览 HTML：[Waje-global-sports-betting-prediction-markets-analysis.html](../../../output/html/Waje-global-sports-betting-prediction-markets-analysis.html)",
        "",
    ]
    return "\n".join(sections) + "\n"


def svg_bar_chart(data: dict) -> str:
    bars = [
        ("FanDuel/Flutter US", 5798, "USD 5.798bn", "#1d7a5a"),
        ("DraftKings", 4768, "USD 4.768bn", "#2d8ec4"),
        ("bet365", 3719.9, "GBP 3.720bn", "#d38a2a"),
        ("BetMGM", 2102, "USD 2.102bn", "#b84848"),
        ("Betway segment", 1106, "USD 1.106bn", "#7256a8"),
    ]
    max_value = max(value for _, value, _, _ in bars)
    rects = []
    for index, (label, value, text, color) in enumerate(bars):
        y = 32 + index * 42
        width = 470 * value / max_value
        rects.append(f'<text x="0" y="{y + 15}" class="chart-label">{esc(label)}</text><rect x="170" y="{y}" width="{width:.1f}" height="22" rx="5" fill="{color}"></rect><text x="{180 + width:.1f}" y="{y + 15}" class="chart-value">{esc(text)}</text>')
    return f'<div class="viz-panel"><h3>公开收入代理：期间与币种不可混算</h3><svg class="bar-chart" viewBox="0 0 760 250" role="img" aria-label="Top五家平台公开收入代理横向比较">{"".join(rects)}</svg><p class="viz-note">FanDuel 使用 Flutter 美国段，Betway 使用 Betway segment；bet365 为 GBP，其他为 USD。</p></div>'


def capability_heatmap(data: dict) -> str:
    labels = [("very strong", "强"), ("strong", "有"), ("available by market", "按市场"), ("selected sports markets", "选定市场"), ("focused event contracts", "事件合约"), ("Combos", "Combos"), ("trade out on order book", "订单簿退出"), ("peer order book", "订单簿"), ("not sportsbook-style", "非 Sportsbook"), ("core", "核心"), ("jurisdiction dependent", "按辖区")]
    lookup = dict(labels)
    head = "".join(f"<th>{esc(label)}</th>" for label in ["能力", "FanDuel", "bet365", "DraftKings", "BetMGM", "Betway", "Polymarket", "Kalshi"])
    rows = []
    for item in data["product_capability_matrix"]:
        cells = [f"<th scope=\"row\">{esc(item['capability'])}</th>"]
        for key in ["fanduel_flutter", "bet365", "draftkings", "betmgm", "betway_supergroup", "polymarket", "kalshi"]:
            raw = item[key]
            text = lookup.get(raw, raw)
            cells.append(f"<td class=\"heat heat-{re.sub(r'[^a-z]+', '-', raw.lower()).strip('-')}\" title=\"{esc(raw)}\">{esc(text)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="viz-panel"><h3>产品能力热力图</h3><div class="table-scroll"><table class="heatmap"><thead><tr>' + head + "</tr></thead><tbody>" + "".join(rows) + '</tbody></table></div><p class="viz-note">“强/核心”代表公开资料中明确出现或业务模型的核心能力；“按市场/选定市场”表示并非所有赛事或辖区可用。</p></div>'


def value_chain_svg() -> str:
    nodes = [("内容", "赛事、数据、直播", 35, 45), ("决策", "赔率/概率、规则、推荐", 230, 45), ("成交", "Bet Slip / Order Book", 425, 45), ("结果", "结算、Cash Out、退出", 620, 45)]
    parts = []
    for index, (title, subtitle, x, y) in enumerate(nodes):
        if index < len(nodes) - 1:
            parts.append(f'<path d="M {x + 150} 90 L {x + 185} 90" stroke="#2d8ec4" stroke-width="3" marker-end="url(#arrow)"></path>')
        parts.append(f'<rect x="{x}" y="{y}" width="150" height="90" rx="12" fill="#e9f6f0" stroke="#b8dec9"></rect><text x="{x + 75}" y="78" text-anchor="middle" class="chain-title">{esc(title)}</text><text x="{x + 75}" y="108" text-anchor="middle" class="chain-subtitle">{esc(subtitle)}</text>')
    return '<div class="viz-panel"><h3>两种产品的共同价值链</h3><svg class="chain-chart" viewBox="0 0 805 190" role="img" aria-label="内容到决策到成交再到结果的产品价值链"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#2d8ec4"></path></marker></defs>' + "".join(parts) + '<text x="35" y="166" class="chain-foot">Sportsbook：平台报价与承担风险</text><text x="425" y="166" class="chain-foot">Prediction market：用户撮合与规则/结算</text></svg></div>'


def persona_grid(data: dict) -> str:
    cells = []
    for item in data["user_personas"]:
        cells.append(f'<div class="persona"><strong>{esc(item["name"])}</strong><span>{esc(item["need"])}</span><small>{esc(item["commercial_role"])}</small></div>')
    return '<div class="viz-panel"><h3>用户需求不是一个漏斗</h3><div class="persona-grid">' + "".join(cells) + '</div></div>'


def priority_svg(data: dict) -> str:
    positions = [("P0", 70, 52), ("P1", 290, 95), ("P1", 520, 80), ("P2", 220, 185), ("P2", 560, 190)]
    labels = [item["principle"] for item in data["waje_principles"][:5]]
    circles = []
    for (priority, x, y), label in zip(positions, labels):
        color = "#b84848" if priority == "P0" else "#d38a2a" if priority == "P1" else "#2d8ec4"
        circles.append(f'<circle cx="{x}" cy="{y}" r="24" fill="{color}"></circle><text x="{x}" y="{y + 5}" text-anchor="middle" fill="#fff" class="priority-label">{priority}</text><text x="{x + 34}" y="{y + 5}" class="priority-text">{esc(label)}</text>')
    return '<div class="viz-panel"><h3>Waje 采纳优先级：先信任与理解，再复杂化与社交</h3><svg class="priority-chart" viewBox="0 0 790 260" role="img" aria-label="Waje产品原则优先级图"><line x1="40" y1="225" x2="750" y2="225" stroke="#9fb9aa"></line><line x1="40" y1="225" x2="40" y2="30" stroke="#9fb9aa"></line><text x="45" y="248" class="axis-caption">实现复杂度 →</text><text x="16" y="40" class="axis-caption" transform="rotate(-90 16 40)">用户价值与信任 ↑</text>' + "".join(circles) + '</svg></div>'


def chart_css() -> str:
    return """
:root{--ink:#1b2822;--muted:#617269;--canvas:#eef5ef;--paper:#fff;--line:#d7e4da;--green:#0b7544;--mint:#e6f5eb;--blue:#2d8ec4;--amber:#d38a2a;--red:#b84848;--purple:#7256a8;--shadow:0 18px 50px rgba(26,70,43,.12)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--canvas);color:var(--ink);font:16px/1.72 -apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Microsoft YaHei",Arial,sans-serif}.top{background:linear-gradient(125deg,#0b7544,#153c4a 70%,#a1d76d);color:#fff;padding:56px max(24px,calc((100% - 1220px)/2)) 48px}.eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;opacity:.78}.top h1{max-width:900px;font-size:clamp(36px,5.5vw,68px);line-height:1.08;letter-spacing:-.055em;margin:16px 0}.top p{max-width:820px;font-size:18px;opacity:.91}.meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}.meta span{padding:5px 10px;border:1px solid rgba(255,255,255,.32);border-radius:999px;font-size:12px}.layout{width:min(1220px,calc(100% - 40px));margin:auto;display:grid;grid-template-columns:220px minmax(0,1fr);gap:30px;padding:32px 0 80px}.toc{position:sticky;top:18px;height:max-content;padding:16px 0}.toc strong{font-size:11px;letter-spacing:.12em;color:var(--muted);text-transform:uppercase}.toc a{display:block;padding:6px 10px;border-left:2px solid transparent;color:var(--muted);font-size:13px;text-decoration:none}.toc a:hover{border-left-color:var(--green);background:var(--mint);color:var(--green)}.report{background:var(--paper);border:1px solid var(--line);border-radius:24px;padding:clamp(26px,5vw,64px);box-shadow:var(--shadow)}.report h1{font-size:clamp(32px,4.6vw,58px);line-height:1.1;letter-spacing:-.055em;margin:0 0 28px}.report h2{font-size:30px;line-height:1.18;margin:58px 0 18px;padding-top:12px;letter-spacing:-.035em}.report h3{font-size:21px;line-height:1.3;margin:32px 0 12px}.report p{max-width:920px;margin:0 0 16px}.report blockquote{margin:22px 0;padding:15px 18px;border-left:5px solid var(--green);border-radius:0 14px 14px 0;background:var(--mint);color:#2d5a40}.report ul,.report ol{padding-left:26px}.report li{margin:6px 0}.table-wrap,.table-scroll{overflow:auto;margin:20px 0 28px;border:1px solid var(--line);border-radius:14px}.report table{width:100%;min-width:700px;border-collapse:collapse;font-size:13px}.report th,.report td{padding:12px 13px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}.report th{background:#eff7f0;color:#24583b;white-space:nowrap}.report tr:last-child td{border-bottom:0}.report a{color:var(--green);text-underline-offset:3px}.report code{padding:2px 6px;background:#eef4ef;border-radius:5px;color:#0b5730}.viz-panel{margin:28px 0;padding:20px;border:1px solid var(--line);border-radius:18px;background:linear-gradient(145deg,#fbfefb,#f3f9f4)}.viz-panel h3{margin:0 0 14px;color:#24583b}.viz-note{font-size:12px!important;color:var(--muted);margin:10px 0 0!important}.bar-chart,.chain-chart,.priority-chart{display:block;width:100%;height:auto}.chart-label,.chart-value,.chain-title,.chain-subtitle,.chain-foot,.priority-label,.priority-text,.axis-caption{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif}.chart-label{font-size:13px;fill:#2c4435}.chart-value{font-size:12px;fill:#40594a}.chain-title{font-size:15px;fill:#174d33;font-weight:600}.chain-subtitle{font-size:11px;fill:#567060}.chain-foot{font-size:12px;fill:#516b5b}.priority-label{font-size:12px;font-weight:700}.priority-text{font-size:13px;fill:#314e3d}.axis-caption{font-size:11px;fill:#617269}.heatmap{min-width:890px!important}.heatmap td,.heatmap th{font-size:12px;text-align:center}.heatmap th:first-child{min-width:185px;text-align:left}.heat{font-weight:600}.heat-very-strong,.heat-core{background:#bde8ca;color:#164f31}.heat-strong{background:#d8f0dc;color:#245d38}.heat-available-by-market,.heat-jurisdiction-dependent,.heat-combos{background:#fff0c9;color:#80530c}.heat-selected-sports-markets,.heat-focused-event-contracts,.heat-trade-out-on-order-book,.heat-peer-order-book{background:#dcecf7;color:#205276}.heat-not-sportsbook-style{background:#f7e2e2;color:#7a3232}.persona-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.persona{padding:15px;border:1px solid var(--line);border-radius:12px;background:#fff;display:grid;gap:6px}.persona strong{color:var(--green)}.persona span{font-size:13px}.persona small{color:var(--muted);font-size:11px}.footer{width:min(1220px,calc(100% - 40px));margin:0 auto 40px;border-top:1px solid var(--line);padding-top:14px;color:var(--muted);font-size:12px}@media(max-width:900px){.layout{display:block;width:min(100% - 24px,1220px);padding-top:16px}.toc{position:relative;top:auto;margin-bottom:16px;padding:12px;border:1px solid var(--line);border-radius:14px;background:rgba(255,255,255,.65)}.toc a{display:inline-block;border:0;padding:4px 7px}.report{padding:26px 20px;border-radius:17px}.persona-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.top{padding:36px 18px}.top h1{font-size:38px}.top p{font-size:16px}.layout{width:calc(100% - 16px)}.report{padding:22px 15px}.persona-grid{grid-template-columns:1fr}.viz-panel{padding:14px}.bar-chart{min-width:650px}.bar-chart{overflow:visible}.report h2{font-size:27px}}
 .report>h1:first-child{display:none}
"""


def build_html(markdown: str, data: dict, sources: dict) -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    from render_analysis_report_html import render_body, split_front_matter

    metadata, body = split_front_matter(markdown)
    rendered_body, toc = render_body(body)
    injections = {
        "全球 Top 5 横向矩阵": svg_bar_chart(data),
        "产品能力对比": capability_heatmap(data),
        "商业化模型对比": value_chain_svg(),
        "市场与用户画像": persona_grid(data),
        "Waje 产品启发与商业化原则": priority_svg(data),
    }
    for title, chart in injections.items():
        pattern = re.compile(r'(<h2 id="[^"]+">' + re.escape(title) + r"</h2>)")
        rendered_body = pattern.sub(chart + r"\1", rendered_body, count=1)
    toc_markup = "".join(f'<a href="#{anchor}">{esc(label)}</a>' for level, anchor, label in toc if level <= 2)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="全球体育真金博彩与预测市场产品商业化分析，面向 Waje 尼日利亚/西非体育产品。"><title>全球体育真金博彩与预测市场产品商业化分析｜Waje</title><style>{chart_css()}</style></head>
<body><header class="top"><div class="eyebrow">WAJE PRODUCT &amp; COMMERCIAL INTELLIGENCE</div><h1>全球体育真金博彩与预测市场产品商业化分析</h1><p>Top 5 sportsbook 与 Polymarket / Kalshi 的产品、商业化、运营和用户机制对照，转译为 Waje 尼日利亚/西非场景的产品原则。</p><div class="meta"><span>截至 {REPORT_DATE}</span><span>公开证据优先</span><span>离线可读</span><span>产品原则版</span></div></header><div class="layout"><aside class="toc"><strong>报告导航</strong>{toc_markup}</aside><main class="report">{rendered_body}</main></div><footer class="footer">Waje Research · 公开来源研究，不构成投资或法律意见 · 结构化数据与来源注册表随报告保存</footer></body></html>"""


def main() -> None:
    data = load_json(DATA_PATH)
    sources = load_json(SOURCE_PATH)
    markdown = build_markdown(data, sources)
    MARKDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_PATH.write_text(markdown, encoding="utf-8")
    html_doc = build_html(markdown, data, sources)
    HTML_PATH.write_text(html_doc, encoding="utf-8")
    PREVIEW_PATH.write_text(html_doc, encoding="utf-8")
    artifact = {
        "schema_version": 1,
        "report_id": data["report_id"],
        "report_date": REPORT_DATE,
        "status": "ok",
        "markdown": str(MARKDOWN_PATH.relative_to(ROOT)),
        "html": str(HTML_PATH.relative_to(ROOT)),
        "preview_html": str(PREVIEW_PATH.relative_to(ROOT)),
        "data": str(DATA_PATH.relative_to(ROOT)),
        "source_registry": str(SOURCE_PATH.relative_to(ROOT)),
        "operator_count": len(data["operators"]),
        "prediction_market_count": len(data["prediction_markets"]),
        "html_bytes": len(html_doc.encode("utf-8")),
        "required_markers": ["全球 Top 5 横向矩阵", "Polymarket", "Kalshi", "Waje 产品启发与商业化原则", "来源注册表"],
        "validation": {"passed": all(marker in html_doc for marker in ["全球 Top 5 横向矩阵", "Polymarket", "Kalshi", "Waje 产品启发与商业化原则", "来源注册表"])},
    }
    (OUT_DIR / "report-artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

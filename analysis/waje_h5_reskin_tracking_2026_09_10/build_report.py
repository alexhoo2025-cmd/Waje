from __future__ import annotations

import csv
import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DRAFT = Path("/Users/robin/Documents/wajetan_analyst/draft_f67219c4_folder/draft.xml")


def txt(value: object) -> str:
    return escape(str(value), quote=True)


def p(value: object) -> str:
    return f"<p>{txt(value)}</p>"


def table(headers: list[str], rows: list[list[object]]) -> str:
    head = "".join(f"<th background-color=\"light-gray\"><p><b>{txt(v)}</b></p></th>" for v in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td vertical-align=\"top\"><p>{txt(v)}</p></td>" for v in row) + "</tr>")
    return "<table><thead><tr>" + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table>"


def bullets(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{txt(v)}</li>" for v in items) + "</ul>"


def callout(text: str, color: str = "light-blue", emoji: str = "💡") -> str:
    return f"<callout emoji=\"{emoji}\" background-color=\"{color}\" border-color=\"blue\"><p>{txt(text)}</p></callout>"


common_fields = [
    ["event_name", "STRING", "是", "逻辑事件名；与Ares元事件类型组合使用"],
    ["event_version", "STRING", "是", "本方案首版v1；字段含义变化必须升版"],
    ["event_uid", "STRING", "是", "事件幂等键；重试必须复用"],
    ["event_time_client", "TIMESTAMP", "条件", "客户端发生时间；原始UTC"],
    ["event_time_server / received_at", "TIMESTAMP", "是", "服务端事实时间／接收时间；原始UTC"],
    ["session_id", "STRING", "是", "浏览器H5会话；匿名转登录时保持连续"],
    ["page_visit_id", "STRING", "页面必填", "每次SPA路由访问唯一"],
    ["trace_id", "STRING", "关键链路必填", "跨推荐、游戏、账号和资金链路"],
    ["uuid / user_id", "STRING", "条件", "匿名身份／登录身份；不得互相替代"],
    ["surface_type", "ENUM", "是", "本期固定h5_browser"],
    ["web_version / release_id / ui_version", "STRING", "是", "代码版、发布批次、old/new换皮版本"],
    ["channel / country / locale", "STRING", "是", "渠道、ISO国家码、语言"],
    ["theme_mode", "ENUM", "页面条件", "dark/light/system/unknown"],
    ["page_id / route_key", "STRING", "页面必填", "Ares实际页面ID／稳定逻辑路由"],
    ["module_id / element_id / position", "STRING/INT", "模块条件", "模块、元素和展示位置"],
    ["action_type / entry_source", "ENUM", "行为条件", "动作及入口来源"],
    ["network_level / device_level", "ENUM", "条件", "网络和设备等级；不可读填unknown"],
    ["config_version", "STRING", "配置条件", "页面、推荐、活动等运行配置版本"],
]

page_mapping = [
    ["首页", "n9pixal64m", "复用候选", "Ares确认语义与线上状态后复用"],
    ["登录页", "x8asb2sqh7", "复用候选", "手机号/邮箱Tab改造仍属同一登录任务"],
    ["充值页", "ijkbaricdx", "复用候选", "原商城页；需确认新底部Tab入口不改变页面定义"],
    ["提现页", "vue16bnq1d", "复用候选", "保留页面身份，新增底部Tab来源字段"],
    ["注册合并页", "旧：2w52yelknv / odnbn5xq12 / hhlzz0fs3h", "新建page_id", "旧三步映射为predecessor_page_id；步骤改用flow_step"],
    ["找回密码合并页", "旧：cpd4pyx737 / p0pkkreu3l", "新建page_id", "旧页面只作迁移映射"],
    ["搜索页", "待回读", "确认或新建", "若无同语义有效ID则创建"],
    ["我的页", "待回读", "确认或新建", "若无同语义有效ID则创建"],
    ["分类/Show All二级页", "待回读", "确认或新建", "统一route_key，分类作为参数"],
]

events = [
    ["会话与页面", "H5_SESSION_START / H5_SESSION_END", "自定义H5", "会话开始、结束", "session_id, entry_source, close_reason, duration", "待确认/创建"],
    ["会话与页面", "PAGE_VIEW / PAGE_LEAVE", "PV / PD", "页面进入、退出", "page_id, page_visit_id, route_key, duration", "复用元事件"],
    ["底部导航", "BOTTOM_NAV_EXPOSURE / CLICK", "MV / MC", "五个Tab曝光、默认游戏Tab、切换", "tab_key, position, is_default, from_page, to_page", "待创建/确认"],
    ["首页头部", "HOME_HEADER_ACTION", "MV / MC", "登录注册、资产、消息、每日礼包", "element_key, login_state, action_type", "待创建/确认"],
    ["Banner", "HOME_BANNER_EXPOSURE / CLICK", "MV / MC", "Banner曝光、滑动位置、整图点击", "banner_id, position, campaign_id, exposure_rule", "待创建/确认"],
    ["Daily Chip", "DAILY_CHIP_EXPOSURE / CLICK", "MV / MC", "资格入口曝光与点击", "activity_id, eligible, claim_state, position", "待创建/确认"],
    ["Daily Chip", "DAILY_CHIP_CLAIM_RESULT", "服务端事实", "领取请求终态及奖励到账", "request_id, activity_id, result, reward_id, asset_type", "待服务端确认"],
    ["游戏分类", "GAME_CATEGORY_EXPOSURE / CLICK", "MV / MC", "分类Tab曝光、选择和左右浏览", "category_key, position, previous_category, action_type", "待创建/确认"],
    ["游戏分类", "GAME_LIST_SHOW_ALL", "MC", "Show All／For You All Games", "category_key, game_count, entry_source", "待创建/确认"],
    ["游戏卡", "GAME_CARD_EXPOSURE / CLICK", "MV / MC", "卡片曝光、点击和打开来源", "game_id, provider_id, category_key, position, list_id", "待创建/确认"],
    ["For You", "FOR_YOU_REQUEST", "客户端/桥接", "推荐请求", "recommend_request_id, request_type, requested_slot_count", "复用现有方案"],
    ["For You", "FOR_YOU_RESPONSE / RESULT_ITEM", "服务端", "返回状态及逐位置结果", "batch_id, returned_count, position, game_id, strategy_version", "复用现有方案"],
    ["For You", "FOR_YOU_EXPOSURE / CLICK", "MV / MC", "推荐卡曝光和点击", "exposure_id, batch_id, position, game_id, visible_ms", "复用现有方案"],
    ["For You", "FOR_YOU_GAME_OPEN", "客户端/桥接", "游戏打开终态", "game_id, position, open_status, load_duration_ms", "复用现有方案"],
    ["搜索", "SEARCH_OPEN / CLOSE", "PV/PD或MC", "进入、关闭搜索模块", "page_visit_id, entry_source, duration", "待创建/确认"],
    ["搜索", "SEARCH_EXECUTE / RESULT", "MC/自定义", "达到阈值后自动搜索及结果", "search_id, query_length, query_source, result_count, latency_ms", "待创建/确认"],
    ["搜索", "SEARCH_TERM_CLICK", "MC", "历史词／配置推荐词点击", "search_id, term_source, configured_term_id, history_rank", "待创建/确认"],
    ["搜索", "SEARCH_CLEAR / RESULT_CLICK", "MC", "清空输入、选择游戏", "search_id, result_count, game_id, result_rank", "待创建/确认"],
    ["我的页", "PROFILE_MODULE_EXPOSURE / ACTION", "MV / MC", "资料、余额、我的游戏、交易记录、下载、客服等", "module_key, element_key, action_type, login_state", "待创建/确认"],
    ["主题", "THEME_SWITCH_RESULT", "MC/自定义", "主题切换及本地保存结果", "theme_before, theme_after, save_result, trigger_page", "待创建/确认"],
    ["账号", "AUTH_METHOD_SELECT", "MC", "手机号／邮箱Tab选择", "flow_id, flow_type, auth_method", "待创建/确认"],
    ["账号", "OTP_REQUEST / VERIFY_RESULT", "客户端+服务端", "短信/邮件/语音OTP请求和校验", "flow_id, otp_channel, result, error_code, latency_ms", "待创建/确认"],
    ["账号", "VOICE_OTP_EXPOSURE / CLICK", "MV / MC", "语音OTP兜底出现和使用", "flow_id, wait_seconds_config, auth_method", "待创建/确认"],
    ["账号", "REGISTER_SUBMIT / LOGIN_SUBMIT / RESET_SUBMIT", "MC", "客户端提交行为", "flow_id, flow_step, auth_method, validation_result", "待创建/确认"],
    ["账号", "REGISTER / LOGIN", "服务端事实", "注册、登录最终成功", "flow_id, user_id, result, server_result_code", "复用服务端元事件"],
    ["资金", "DEPOSIT / WITHDRAW_PAGE_ACTION", "PV/PD/MV/MC", "充值、提现页面入口和操作", "page_visit_id, entry_source, action_type, amount_band", "待创建/确认"],
    ["资金", "ORDER / WITHDRAW / AUDIT / ASSET", "服务端事实", "支付、提现和资产终态", "request/order/withdraw/ledger id, status, amount", "复用服务端元事件"],
    ["稳定性", "H5_NAVIGATION_PERF / CORE_REQUEST", "自定义H5", "关键就绪与白名单请求性能", "page_visit_id, critical_ready_ms, request_kind, status_class", "复用H5方案"],
    ["稳定性", "H5_CLIENT_ERROR / NETWORK_CHANGE / RECOVERY_RESULT", "自定义H5", "错误、切网和恢复", "error_fingerprint, stage, recovery_id, result", "复用H5方案"],
]

metrics = [
    ["首页到开局转化率", "发生可归因有效GAMESTART的首页访问用户/有效首页访问用户", "PV + GAMESTART", "用户/日", "国家、渠道、版本、新老用户", "GAMESTART为服务端事实"],
    ["注册完成率", "服务端REGISTER成功flow_id/注册流程开始flow_id", "客户端流程 + REGISTER", "流程/日", "国家、渠道、auth_method、版本", "同一flow_id；失败不补成功"],
    ["For You点击后开局率", "点击后30分钟内有效GAMESTART用户/点击用户", "FOR_YOU_CLICK + GAMESTART", "用户/日", "position、game、版本、策略", "request/batch/position透传"],
    ["模块CTR", "有效点击数/有效曝光数", "MV + MC", "元素/日", "页面、模块、位置、版本", "曝光规则沿用Ares并记录版本"],
    ["游戏打开率", "游戏打开成功数/游戏卡有效点击数", "GAME_CARD_CLICK + GAME_OPEN", "游戏/日", "分类、供应商、位置、版本", "打开成功不等于开局"],
    ["分类流量占比", "分类下有效游戏点击数/全部分类有效游戏点击数", "MC", "分类/日", "国家、渠道、版本", "分类互斥口径按展示归属"],
    ["Show All使用率", "Show All点击用户/对应模块曝光用户", "MV + MC", "模块/日", "分类、版本", "For You单独拆分"],
    ["搜索使用率", "发起有效搜索session/首页有效session", "SEARCH_EXECUTE + PV", "会话/日", "国家、渠道、版本", "达到运行配置阈值才算有效"],
    ["搜索有结果率", "result_count大于0的search_id/有效search_id", "SEARCH_RESULT", "搜索/日", "query_source、版本", "不保存原始搜索词"],
    ["搜索到游戏打开率", "搜索结果游戏打开成功search_id/有效search_id", "SEARCH_RESULT + GAME_OPEN", "搜索/日", "来源、结果排名、版本", "按search_id关联"],
    ["Daily Chip领取成功率", "服务端领取成功request_id/eligible入口曝光用户", "MV + CLAIM_RESULT", "用户/日", "活动、国家、版本", "服务端奖励到账控制成功"],
    ["主题切换率", "主题切换成功用户/我的页有效访问用户", "THEME_SWITCH_RESULT + PV", "用户/日", "before/after、国家、版本", "save_result=success"],
    ["主题保持率", "后续有效会话仍应用所选主题用户/切换成功用户", "THEME_SWITCH_RESULT + SESSION_START", "用户/7日", "主题、国家、版本", "仅成熟7日样本"],
    ["登录成功率", "服务端LOGIN成功flow_id/登录提交flow_id", "LOGIN_SUBMIT + LOGIN", "流程/日", "auth_method、国家、版本", "服务端结果控制成功"],
    ["OTP校验成功率", "VERIFY成功flow_id/VERIFY尝试flow_id", "OTP_VERIFY_RESULT", "流程/日", "channel、flow_type、版本", "不采集OTP值"],
    ["Voice OTP兜底使用率", "语音OTP点击flow_id/语音入口曝光flow_id", "VOICE_OTP MV/MC", "流程/日", "国家、版本", "等待秒数按配置版本拆分"],
    ["充值支付成功率", "支付成功order_id/由H5充值页创建order_id", "页面链路 + ORDER", "订单/日", "国家、渠道、版本", "金额及成功只取服务端"],
    ["提现申请/审核率", "申请或审核终态withdraw_id/提现页提交withdraw_id", "页面链路 + WITHDRAW/AUDIT", "申请/日", "国家、渠道、版本", "申请与审核分别展示"],
    ["关键就绪P50/P95", "critical_ready_ms分位数", "H5_NAVIGATION_PERF", "页面访问/日", "route、网络、设备、版本", "仅measurement complete样本"],
    ["核心请求失败率", "非success请求/request总数", "H5_CORE_REQUEST", "请求/日", "kind、页面、网络、版本", "HTTP成功不等于业务成功"],
    ["错误与恢复率", "去重错误数/有效会话；恢复成功/recovery尝试", "ERROR + RECOVERY", "会话/日", "stage、error_type、版本", "无SESSION_END不推断崩溃"],
]

test_cases = [
    ["底部导航", "五Tab曝光；默认游戏；逐Tab点击；返回切换", "PV/PD与MV/MC顺序正确，from/to page可还原"],
    ["Banner", "首屏、滑动后、重复露出、点击", "曝光去重符合规则；假按钮不产生独立CTA"],
    ["Daily Chip", "可领取、不可领取、成功、失败、重复请求", "客户端与服务端request_id一致；奖励到账可对账"],
    ["For You", "正常、空结果、兜底、换一批、卡片点击、开局", "请求到GAMESTART链路可按batch/position还原"],
    ["分类与卡片", "分类选择、横滑、Show All、卡片点击和打开失败", "category/list/position完整"],
    ["搜索", "少于阈值、达到阈值、无结果、有结果、历史/推荐词、清空", "不上传原文；search_id完整关联"],
    ["账号", "匿名、手机号/邮箱、OTP、Voice OTP、注册、登录、找回密码", "flow_id贯通；服务端事实控制成功"],
    ["我的页/主题", "全部入口、深浅切换、刷新和新会话", "本地保存结果和后续主题一致"],
    ["资金", "充值创建/支付失败/成功；提现提交/审核终态", "页面行为不替代服务端终态；金额可反算"],
    ["稳定性", "慢网、离线、超时、白屏、重试、恢复", "错误指纹脱敏；recovery连接origin_id"],
    ["版本", "old/new及多个release并存", "ui_version、web_version、release_id均可筛选"],
    ["跨国日界", "NG/TZ当地午夜边界", "UTC原始时间分别派生正确业务日"],
]

source_rows = [
    ["WAJE H5 换皮需求", "主需求与策划案", "revision 1751", "https://ksg964l11fam.sg.larksuite.com/wiki/KI1yweIdui1Kewkj7PqlBnFlgjb"],
    ["For You 游戏推荐｜数据指标与埋点设计", "推荐链路与字段", "revision 10", "https://ksg964l11fam.sg.larksuite.com/wiki/QOl7wpeUMipmrBkIO8nlAet7gcf"],
    ["Waje H5 补充埋点｜事件定义", "H5公共字段与性能事件", "revision 12", "https://ksg964l11fam.sg.larksuite.com/wiki/SZPqwhPIuiVBiqkD9QhlXKWUgvh"],
    ["Waje H5 起源埋点上报全量盘点", "当前Ares能力和旧page_id", "revision 16", "https://ksg964l11fam.sg.larksuite.com/wiki/No3IwQh3VinaeskuWvulM4eFgFf"],
    ["H5 核心数据指标与一期看板规划方案", "核心指标与服务端事实边界", "revision 84", "https://ksg964l11fam.sg.larksuite.com/wiki/RqqWwPGgviUzZdkcbz3lNmJhgVd"],
]


parts = [
    "<title>WAJE H5换皮数据指标与埋点设计 V1｜浏览器H5</title>",
    '<p><span text-color="gray">适用范围：浏览器H5｜市场：尼日利亚、坦桑尼亚｜文档日期：2026-09-10｜需求状态：待审核／未排期</span></p>',
    '<h1 seq="auto">结论与实施边界</h1>',
    callout("本方案将H5换皮从视觉改版转化为可度量的流量分发、注册转化、游戏开局、资金入口和体验质量链路。客户端行为只解释入口与体验；注册、登录、游戏、订单、提现和资产成功必须由服务端事实确认。"),
    callout("本期只覆盖浏览器H5，surface_type固定为h5_browser；不覆盖PWA和APP WebView。原需求的埋点章节保持不变，本文件作为独立实施与验收依据。", "light-yellow", "⚠️"),
    bullets([
        "三项主指标：首页访问到有效GAMESTART转化率、注册完成率、For You点击后开局率。",
        "换皮效果按ui_version、web_version和release_id做前后14个完整业务日比较，不采用A/B实验。",
        "所有实际Ares page_id、module_id和event_id须创建或回读确认；逻辑名称不得冒充实际ID。",
        "不采集手机号、邮箱、密码、OTP、完整搜索词、完整URL、请求体、支付明细或原始错误堆栈。",
    ]),
    '<h1 seq="auto">需求拆解与测量目标</h1>',
    table(["需求域", "主要变化", "要回答的问题", "证据链"], [
        ["首页导航", "五个底部Tab；默认游戏", "流量是否更快到达游戏、充值和提现", "PV/PD + 导航MV/MC"],
        ["首页内容", "Banner、Daily Chip、分类模块和Show All重排", "各模块获得多少曝光、点击和后续开局", "模块曝光→点击→游戏打开/奖励终态"],
        ["For You", "默认置顶并增加二级All Games", "推荐是否填充、曝光、点击并真正进入游戏", "请求→返回→曝光→点击→GAMESTART"],
        ["搜索", "实时模糊搜索、历史词、推荐词和猜你喜欢", "用户是否搜到并打开目标游戏", "search_id→结果→游戏打开"],
        ["我的页", "资产、我的游戏、下载、主题、语言、客服重排", "入口是否被使用，主题是否保存", "模块曝光/点击→业务页/保存结果"],
        ["登录注册", "手机号/邮箱Tab；注册与找回密码步骤合并；Voice OTP", "步骤流失在哪里，最终注册/登录是否成功", "flow_id→OTP→提交→服务端REGISTER/LOGIN"],
        ["充值/提现", "由二级页面提升为底部独立Tab", "入口变化是否带来真实支付/提现变化", "页面行为→ORDER/WITHDRAW/AUDIT"],
        ["深浅色", "本地保存主题", "有多少用户切换，后续会话是否保持", "切换结果→下次SESSION_START"],
    ]),
    '<h1 seq="auto">数据链路与事实来源</h1>',
    p("统一链路：H5_SESSION_START → 页面PV/模块MV → MC操作 → 推荐、账号、游戏或资金请求 → 服务端终态 → ASSET／账本。页面行为只能证明用户看见或操作，不能替代业务成功。"),
    table(["业务对象", "客户端事实", "最终事实源", "关联键"], [
        ["推荐", "请求、曝光、点击、打开", "推荐服务返回；游戏服务GAMESTART", "recommend_request_id / batch_id / position / trace_id"],
        ["注册登录", "Tab、OTP、提交和错误阶段", "REGISTER / LOGIN", "flow_id / trace_id / user_id"],
        ["游戏", "卡片点击、打开状态", "GAMESTART / GAMEEND / BETREWARD", "game_id / session_id / trace_id / round_id"],
        ["充值", "入口、页面和提交", "ORDER支付成功 / ASSET", "request_id / order_id / trace_id"],
        ["提现", "入口、页面和提交", "WITHDRAW / AUDIT", "request_id / withdraw_id / trace_id"],
        ["Daily Chip", "资格曝光和点击", "领取结果 / 奖励账本", "activity_id / request_id / reward_id"],
    ]),
    '<h1 seq="auto">公共字段契约</h1>',
    table(["字段", "类型", "必填", "说明"], common_fields),
    '<h1 seq="auto">页面ID迁移与Ares登记</h1>',
    callout("以下仅为复用候选和迁移规则。实施人员必须在Waje Special空间回读当前状态，取得真实ID后填入登记表；未确认时状态保持actual_validation_pending。", "light-orange", "🔎"),
    table(["页面", "现有/旧ID", "处理", "规则"], page_mapping),
    '<h1 seq="auto">功能事件矩阵</h1>',
    table(["模块", "逻辑事件", "元事件/来源", "触发", "关键字段", "ID状态"], events),
    '<h1 seq="auto">核心指标字典</h1>',
    callout("主指标只保留三项，其余指标用于解释变化。所有比率必须显示分子、分母、统计周期、数据更新时间和口径版本；未成熟或链路不完整不得补0。"),
    table(["指标", "定义/算法", "来源", "粒度", "主要维度", "成熟/边界"], metrics),
    '<h1 seq="auto">版本前后效果评估</h1>',
    table(["项目", "规则"], [
        ["基线", "上线前14个完整当地业务日"],
        ["观察期", "上线后D1–D14；排除发布日D0；D1–D7先出快速读数"],
        ["时间", "原始UTC；NG按Africa/Lagos、TZ按Africa/Dar_es_Salaam派生business_date"],
        ["版本", "ui_version、web_version和release_id共同识别old/new及发布批次"],
        ["变化", "比率给前值、后值、百分点变化及相对变化；数量/金额给绝对差及环比"],
        ["分层", "国家、渠道、登录状态、新老用户、页面/模块、主题、网络和设备等级"],
        ["干扰", "记录活动、投放、游戏上下架、支付/OTP策略及配置变化"],
        ["结论边界", "未随机分流，只描述版本上线前后相关变化，不写成换皮导致"],
    ]),
    '<h1 seq="auto">隐私与数据治理</h1>',
    table(["类别", "允许", "禁止"], [
        ["身份", "uuid、内部user_id、session_id", "手机号、邮箱、姓名、OTP"],
        ["搜索", "长度、来源、结果数、配置词ID、选中game_id", "完整搜索词和输入内容"],
        ["页面来源", "entry_source、规范化referrer_host_key", "完整URL、查询串、user-info URL"],
        ["错误", "白名单error_code、脱敏fingerprint、阶段", "原始堆栈、请求体、响应正文"],
        ["资金", "聚合金额、订单/提现内部业务键、终态", "账号、支付工具或订单明细输出"],
        ["交付", "聚合看板和质量回执", "用户、设备、订单、资金逐条明细"],
    ]),
    '<h1 seq="auto">联调测试与验收</h1>',
    table(["测试域", "场景", "验收结果"], test_cases),
    '<h2 seq="auto">数据质量门禁</h2>',
    table(["门禁", "标准", "失败处理"], [
        ["必填字段完整率", "≥99.5%", "按事件、版本和渠道定位；低于门禁不发布正式分析"],
        ["核心事件入库率", "≥99%", "检查客户端调用、桥接、接收与入库阶段"],
        ["核心链路关联率", "≥98%", "隔离无关联链路，核对业务键与时钟"],
        ["幂等", "重试复用event_uid；服务端业务键不重复", "重复事件去重并定位重试策略"],
        ["服务端对账", "REGISTER/LOGIN/ORDER/WITHDRAW/AUDIT/GAME/ASSET一致", "客户端成功提示不得覆盖服务端失败或未知"],
        ["缺失值", "unknown/N/A/immature按规则保留", "不得用0代替未采集、未成熟或不支持"],
    ]),
    '<h1 seq="auto">实施清单与交付状态</h1>',
    table(["阶段", "动作", "交付物", "通过条件"], [
        ["口径冻结", "产品/数据确认页面、模块、版本和业务状态", "需求→事件→指标追踪矩阵", "无未定义核心状态"],
        ["Ares登记", "回读旧ID并创建缺失page/module/event及事件属性", "实际ID映射表", "无逻辑ID冒充实际ID"],
        ["客户端实现", "浏览器H5接入公共字段、PV/PD/MV/MC和H5事件", "开发自测回执", "全部必测场景有事件轨迹"],
        ["服务端联调", "推荐、账号、游戏、活动和资金事实关联", "链路回执与对账", "关键业务键可贯通"],
        ["测试验收", "NG/TZ、old/new、匿名/登录、成功/失败/重试", "验收矩阵", "质量门禁全部通过"],
        ["上线审计", "24小时数据审计；D1–D7快报；D1–D14正式对比", "审计及版本报告", "结论标明干扰和非因果边界"],
    ]),
    '<h2 seq="auto">当前未关闭项</h2>',
    bullets([
        "原换皮需求仍为待审核／未排期；本文不代表已批准、已开发或已上线。",
        "搜索页、我的页及合并后的注册/找回密码页实际page_id待Ares确认或创建。",
        "页面/模块实际event_id、For You线上策略版本及服务端物理表待实施时回填。",
        "换皮发布日期和release_id待研发排期冻结后补充。",
    ]),
    '<h1 seq="auto">资料来源</h1>',
    table(["资料", "用途", "版本", "链接"], source_rows),
]

xml = "\n".join(parts) + "\n"
ROOT.mkdir(parents=True, exist_ok=True)
DRAFT.parent.mkdir(parents=True, exist_ok=True)
ROOT.joinpath("report.xml").write_text(xml, encoding="utf-8")
DRAFT.write_text(xml, encoding="utf-8")

with ROOT.joinpath("event-field-matrix.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["模块", "逻辑事件", "元事件/来源", "触发", "关键字段", "ID状态"])
    writer.writerows(events)

with ROOT.joinpath("metric-dictionary.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["指标", "定义/算法", "来源", "粒度", "主要维度", "成熟/边界"])
    writer.writerows(metrics)

ROOT.joinpath("source-receipt.json").write_text(json.dumps({
    "generated_at": "2026-09-10",
    "source_requirement": {"title": "WAJE H5 换皮需求", "revision": 1751, "url": source_rows[0][3]},
    "supporting_sources": [
        {"title": row[0], "revision": row[2], "url": row[3]} for row in source_rows[1:]
    ],
    "scope": "h5_browser_only",
    "comparison": "14_complete_local_business_days_before_vs_D1_D14_after; D0 excluded",
    "timezones": {"raw": "UTC", "NG": "Africa/Lagos", "TZ": "Africa/Dar_es_Salaam"},
    "privacy": "aggregate_only; no raw user, device, order, payment or search-input detail in delivery",
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({
    "draft": str(DRAFT),
    "local_xml": str(ROOT / "report.xml"),
    "event_rows": len(events),
    "metric_rows": len(metrics),
    "xml_chars": len(xml),
}, ensure_ascii=False))

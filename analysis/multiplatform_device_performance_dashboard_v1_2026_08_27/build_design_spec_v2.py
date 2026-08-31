#!/usr/bin/env python3
"""Build the detailed, self-contained dashboard/report design handoff.

The page is a design specification, not a live dashboard.  All baseline
numbers come from actual_baseline.json and are aggregate-only.  The generated
HTML has no network requests and is readable without JavaScript.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "actual_baseline.json"
OUT = ROOT / "design_spec_v2.html"
MANIFEST = ROOT / "design_spec_v2.json"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def compact(value: int | float) -> str:
    value = float(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M".rstrip("0").rstrip(".")
    if value >= 1_000:
        return f"{value / 1_000:.1f}k".rstrip("0").rstrip(".")
    return f"{value:,.0f}"


def badge(label: str, tone: str = "amber") -> str:
    return f'<span class="badge {esc(tone)}">{esc(label)}</span>'


PAGES = [
    {
        "no": "01",
        "id": "health",
        "title": "全端健康总览",
        "question": "先确认数据是否到达、是否成熟，再决定能不能做性能或业务判断。",
        "cards": ["完整数据日覆盖率", "会话开始事件数", "原生性能记录量", "性能数据状态", "严重质量告警数"],
        "visual": "覆盖热条 + 三端状态矩阵 + 质量告警队列",
        "detail": "首屏放数据截止时间、完整日数、状态徽章；缺失用灰色、延迟用橙色、已核验用绿色。",
        "now": "Android Performance 可试运行；iOS 未成熟；H5 仅行为基线，网页性能为数据缺口。",
    },
    {
        "no": "02",
        "id": "funnel",
        "title": "核心业务成功率与漏斗",
        "question": "区分客户端‘尝试’与服务端‘成功’，不把点击量写成成功率。",
        "cards": ["启动首页成功率", "注册成功率", "登录成功率", "24 小时充值成功率", "下注成功率", "游戏进入成功率"],
        "visual": "横向阶段漏斗 + 失败原因堆叠条 + 单维度问题排行",
        "detail": "启动首页 → 注册 → 登录 → 充值 → 提现 → 进局 → 游戏就绪 → 可下注 → 首局。没有服务端分母的阶段统一显示阻断。",
        "now": "Firebase 事件只能提供行为信号；Origin 服务端成功事实和 H5/原生 game_ready、bet_ready 尚未完整认证。",
    },
    {
        "no": "03",
        "id": "page-performance",
        "title": "页面与原生性能分析",
        "question": "定位慢在启动、页面渲染、网络还是某个版本/设备。",
        "cards": ["页面访问量", "启动/首页 P95", "页面白屏率", "核心请求失败率", "轨迹 P95", "网络 P95"],
        "visual": "P50/P95/P99 趋势 + 页面排行 + 请求类别散点",
        "detail": "只用成功且去重的 page_visit_id 或启动链路样本；缺结束时间、负时长、超时样本单列，不补零。",
        "now": "Android/iOS Performance 已有轨迹、网络、慢帧/冻结帧字段；H5 Web Vitals、路由 ready 和核心请求均未采集。",
    },
    {
        "no": "04",
        "id": "stability",
        "title": "稳定性分析",
        "question": "看 Fatal、ANR、Non-fatal 和问题数，但不把导出行数冒充崩溃率。",
        "cards": ["Fatal 事件数", "ANR 事件数", "Non-fatal 事件数", "去重问题数"],
        "visual": "问题排行 + 版本回归表 + 主异常维度筛选",
        "detail": "event_id 去重事件、issue_id 去重问题；跨问题/跨包影响用户取并集。正式率指标需完成分母认证。",
        "now": "Android 可先展示去重事件量和问题数；iOS 当前未见 Crashlytics 导出表，显示数据缺口。",
    },
    {
        "no": "05",
        "id": "network",
        "title": "网络质量分析",
        "question": "判断慢和失败是否集中在国家、运营商、网络类型、请求类别或页面。",
        "cards": ["网络 P95", "HTTP 成功率", "超时率", "重试率", "受影响会话数"],
        "visual": "国家/运营商排行 + 请求类别散点（P95 × 失败率）",
        "detail": "按请求类别分开计算；4xx 拆业务拒绝、鉴权失败和系统异常；重复请求按请求键去重。",
        "now": "Android/iOS 已有响应码和耗时字段，待请求类别白名单；H5 需 H5_CORE_REQUEST 与 H5_NETWORK_CHANGE。",
    },
    {
        "no": "06",
        "id": "device",
        "title": "设备、版本与渠道分析",
        "question": "找出低端机、老系统、品牌、包体或版本的集中风险。",
        "cards": ["低端设备占比", "版本覆盖", "未知网络占比", "未知内存占比"],
        "visual": "设备档位分布 + 版本质量矩阵 + 单维度异常排行",
        "detail": "RAM 档位：极低端 <1GB、低端 1～<2GB、中端 2～<4GB、高端 ≥4GB；未知不入分母。",
        "now": "Android Performance 有品牌/型号、系统、国家、运营商和网络；RAM、温度、稳定发布批次待补。",
    },
    {
        "no": "07",
        "id": "game", 
        "title": "游戏体验分析",
        "question": "用户是否从启动进入可玩的游戏状态，并完成第一局。",
        "cards": ["游戏进入成功率", "游戏就绪率", "可下注率", "首局完成率"],
        "visual": "阶段卡 + 阶段耗时分布 + 退出点排行",
        "detail": "GAMESTART 不自动等同游戏就绪，BETREWARD 不自动等同可下注；必须对齐 game_start_id、游戏 ID 和服务端成功枚举。",
        "now": "现有 Firebase 只能给部分尝试信号；H5、Android、iOS 的 game_ready、bet_ready 和首局事实均待补齐。",
    },
    {
        "no": "08",
        "id": "quality",
        "title": "告警与数据质量",
        "question": "区分产品异常和数据异常，避免‘没有数据’触发错误告警。",
        "cards": ["完整日覆盖率", "源延迟分钟数", "字段完整率", "重复率", "未分类事件数"],
        "visual": "质量状态卡 + 告警队列 + 指标血缘/检查结果",
        "detail": "状态枚举：certified、provisional、immature、delayed、data_gap、blocked；缺口不填 0。",
        "now": "Android Sessions Performance 开关为 false 但 Performance 有记录，作为质量冲突告警；Analytics 窗口尚短。",
    },
]


METRICS = [
    ("数据覆盖率", "完整数据日 ÷ 请求数据日；同时展示最新事件时间和延迟", "请求日；当天不算完整日", "日期×端×来源×包；mart_endpoint_coverage_daily", "全端必备"),
    ("日活跃用户（DAU）", "批准的去标识化用户键日内去重", "有效用户键；隐私阈值", "日期×端×包；Analytics/服务端", "blocked：用户键口径待确认"),
    ("会话开始事件数", "COUNTIF(event_name='session_start')，事件次数", "事件记录数，不是唯一会话", "日期×端×包×版本；Analytics", "可用，成熟度按端不同"),
    ("Android 去标识化会话数", "COUNT(DISTINCT session_id)，仅 Sessions 内部", "有效 session_id", "日期×Android 包×版本；Sessions", "Android 可用，不跨端相加"),
    ("页面/屏幕浏览", "H5 page_view；原生 screen_view 事件计数", "事件数，不解释为用户数", "日期×端×页面/屏幕；Analytics", "行为可用"),
    ("启动/首页成功率", "成功显示核心内容的链路 ÷ 有效启动链路", "app_launch_id/session_id；未知结束排除", "日期×端×包×版本；Performance+客户端", "blocked：成功枚举待补"),
    ("注册成功率", "服务端注册成功数 ÷ 有效注册提交数；错误原因分开", "有效提交", "日期×端×包×版本；Origin+Analytics", "blocked"),
    ("登录成功率", "登录成功状态数 ÷ 有效登录提交数；风险拒绝/系统错误拆分", "有效提交", "日期×端×包×版本；Origin+Analytics", "blocked"),
    ("24 小时充值成功率", "24 小时内最终到账 ÷ 成熟有效充值订单", "订单成熟窗口 24h；未成熟不入分母", "日期×端×包×版本；服务端账务", "blocked"),
    ("下注成功率", "服务端确认成功下注 ÷ 有效下注提交；正常拒绝单列", "有效下注提交", "日期×端×包×版本；Origin", "blocked"),
    ("游戏进入成功率", "进入可操作状态 ÷ 有效游戏启动；关联 game_start_id", "有效启动链路", "日期×端×包×版本；Origin+客户端", "blocked"),
    ("首次可玩率", "首次进入可玩状态链路 ÷ 有效游戏启动链路", "game_ready + 服务端确认", "日期×端×游戏；H5 V2+Origin", "data_gap / blocked"),
    ("重复提交率", "窗口内重复提交用户/会话 ÷ 有效提交；注册/登录10s、提现10s、下注/进局5s", "合法链路键；正常重试另计", "日期×端×阶段；客户端+Origin", "待补链路键"),
    ("低端设备占比", "极低端+低端有效设备/会话 ÷ 有内存观测有效设备/会话", "未知内存排除", "日期×端×包×档位", "data_gap：RAM 待补"),
    ("高温链路失败率", "高温/极高温失败链路 ÷ 有温度观测有效链路", "未知温度排除", "日期×端×链路", "data_gap"),
    ("原生轨迹 P50/P95/P99", "合格 DURATION_TRACE 的 APPROX_QUANTILES 时长分位数", "非负成功样本；样本≥500", "日期×端×包×版本×单一设备维度；Performance", "字段具备，数值待审计"),
    ("页面加载 P50/P95/P99", "page_ready_at - page_start_at；page_visit_id 去重", "成功 ready；超时单列；样本≥500", "日期×页面×版本×浏览器/网络；H5 V2", "data_gap"),
    ("资源传输大小 P50/P95", "实际压缩传输字节分位数；缓存不可观测则未知", "字节可观测；未知不填零", "日期×页面/资源类别", "data_gap"),
    ("API 失败率", "（系统失败+超时+5xx）÷ 有效请求；4xx 分类", "请求类别和请求键有效", "日期×请求类别×端", "Android/iOS 待分类；H5 缺口"),
    ("网络 P95", "response_completed_time_us / 1000 的第95分位", "有开始/完成/响应码；样本≥500", "日期×端×包×请求类别×网络", "Android/iOS 字段具备"),
    ("超时率", "超时请求 ÷ 有效请求", "请求类别内计算", "日期×请求类别×网络", "待统一枚举"),
    ("重试率", "发生重试请求链路 ÷ 有效请求链路", "request_id/链路键去重", "日期×请求类别×网络", "待补字段"),
    ("慢帧 / 冻结帧比例", "SCREEN_TRACE 中比例字段的 trace 加权均值", "有效屏幕 trace；样本≥500", "日期×包×版本×设备/系统", "Android/iOS 可试运行"),
    ("Fatal / Non-fatal 事件数", "按 event_id 去重，按 is_fatal 分开", "event_id 有效", "日期×包×版本×设备/系统；Crashlytics", "Android 先展示数量"),
    ("问题数", "COUNT(DISTINCT issue_id)", "issue_id 非空", "日期×包×版本×主维度；Crashlytics", "Android 可试运行"),
    ("异常排行分数", "40%影响用户归一化 + 30%偏离度 + 20%业务权重 + 10%影响范围", "用户型≥100或计数型≥200；单主维度", "日期×单一问题维度；聚合层", "设计完成，待分母"),
    ("H5 Web 性能状态", "Web Vitals、路由 ready、核心请求、前端错误完整率与延迟", "measurement_state=complete", "日期×页面×浏览器/网络；H5 V2", "data_gap"),
]


FILTERS = [
    ("日期范围", "日期范围", "最近 7 个完整 Africa/Lagos 自然日；自定义", "所有页面"),
    ("端侧", "单选标签", "Android / iOS / H5 / 全部", "所有页面；默认不混算"),
    ("Android 包体", "多选", "主包 / 传音老包 / 传音新包", "性能、稳定性、事件"),
    ("分包渠道", "多选", "渠道白名单；未知单列", "设备、版本、漏斗"),
    ("应用/H5 版本", "多选", "app_display_version / web_version", "性能、稳定性、事件"),
    ("国家", "搜索下拉", "Nigeria 等", "所有有来源的端侧"),
    ("运营商", "搜索下拉", "运营商桶；未知单列", "性能、网络、设备"),
    ("品牌/型号", "搜索下拉", "Transsion、Samsung 等；型号桶", "性能、稳定性、设备"),
    ("设备档位/内存", "单选", "极低端、低端、中端、高端、未知", "设备、性能、漏斗"),
    ("系统/浏览器", "多选", "Android/iOS 版本；H5 浏览器", "性能、稳定性、H5"),
    ("网络类型", "多选", "Wi-Fi、蜂窝、未知", "网络、性能"),
    ("机器温度", "单选", "正常、高温、极高温、未知", "网络、稳定性、设备"),
    ("事件分类", "多选", "生命周期、页面/屏幕、消息、行为、未分类", "事件与会话"),
    ("性能轨迹", "多选", "启动、屏幕、网络、其他", "原生性能"),
    ("页面/请求类别", "搜索下拉", "安全类别；不显示完整 URL", "页面、网络"),
    ("数据状态", "多选", "已核验、试运行、未成熟、延迟、缺失、阻断", "所有页面"),
]


def styles() -> str:
    return r'''
:root{--navy:#102a43;--ink:#182b3d;--muted:#64748b;--line:#dbe4ee;--bg:#f4f7fb;--surface:#fff;--blue:#1976d2;--cyan:#0891b2;--android:#15803d;--ios:#6d28d9;--h5:#b45309;--ok:#157347;--warn:#a45a00;--danger:#b33d14;--shadow:0 10px 32px rgba(16,42,67,.08);--radius:18px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Hiragino Sans GB","Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.65}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}.top{background:linear-gradient(115deg,#0b2036,#123d5c);color:#fff;padding:18px 32px;position:sticky;top:0;z-index:40;box-shadow:0 5px 20px rgba(16,42,67,.2)}.top-inner{max-width:1500px;margin:auto;display:flex;justify-content:space-between;align-items:center;gap:20px}.brand{display:flex;align-items:center;gap:11px;font-weight:700;letter-spacing:.04em}.brand-mark{width:31px;height:31px;display:grid;place-items:center;border-radius:10px;background:linear-gradient(135deg,#38c9d1,#2e78d0);font-size:13px}.top-meta{font-size:12px;color:#c9dae9;display:flex;gap:16px;align-items:center}.dot{width:7px;height:7px;border-radius:50%;display:inline-block;background:#65d38b;margin-right:5px}.shell{max-width:1500px;margin:auto;display:grid;grid-template-columns:238px minmax(0,1fr);gap:26px;padding:30px 32px 72px}.side{position:sticky;top:94px;height:max-content}.side-label{font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--muted);font-weight:800;margin:0 0 10px}.side a{display:flex;align-items:center;gap:10px;padding:9px 12px;border-left:3px solid transparent;border-radius:0 10px 10px 0;color:#5b7188;font-size:13px}.side a span{width:22px;color:#9aabba;font-variant-numeric:tabular-nums}.side a:hover,.side a.active{background:#e9f2fb;color:var(--navy);border-left-color:var(--blue);text-decoration:none}.main{min-width:0}.hero{background:var(--surface);border:1px solid var(--line);border-radius:24px;box-shadow:var(--shadow);padding:34px 38px;display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:26px;margin-bottom:20px;overflow:hidden;position:relative}.hero:after{content:"";position:absolute;right:-150px;top:-180px;width:450px;height:450px;border-radius:50%;background:radial-gradient(circle,#d8f5f0 0,#edf7fc 44%,transparent 67%);pointer-events:none}.eyebrow{font-size:12px;letter-spacing:.08em;color:var(--blue);font-weight:800;margin:0 0 10px;position:relative;z-index:1}.hero h1{font-size:clamp(30px,4vw,50px);line-height:1.12;letter-spacing:-.045em;margin:0 0 13px;color:var(--navy);position:relative;z-index:1}.hero p{margin:0;color:#48617a;max-width:720px;position:relative;z-index:1}.hero-side{position:relative;z-index:1;border-left:1px solid var(--line);padding-left:24px;display:grid;align-content:center;gap:13px}.hero-side h3{margin:0;color:var(--navy);font-size:15px}.status-line{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:9px 0;border-bottom:1px solid var(--line);font-size:13px}.status-line:last-child{border-bottom:0}.badge{display:inline-flex;align-items:center;white-space:nowrap;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:800;line-height:1.4}.badge.ok{background:#e7f6ec;color:var(--ok)}.badge.amber{background:#fff3d8;color:var(--warn)}.badge.red{background:#fff0ea;color:var(--danger)}.badge.blue{background:#e8f1ff;color:#1d5bad}.badge.gray{background:#eef2f7;color:#53687d}.intro-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin-bottom:28px}.mini{background:var(--surface);border:1px solid var(--line);border-top:4px solid var(--blue);border-radius:15px;padding:15px 17px;box-shadow:0 6px 20px rgba(16,42,67,.04)}.mini:nth-child(2){border-top-color:var(--cyan)}.mini:nth-child(3){border-top-color:#e19a32}.mini:nth-child(4){border-top-color:#c45731}.mini .label{color:var(--muted);font-size:12px}.mini .num{font-size:25px;font-weight:800;color:var(--navy);letter-spacing:-.03em;margin-top:2px}.mini .note{font-size:11px;color:var(--muted);margin-top:3px}.section{scroll-margin-top:94px;margin:0 0 31px}.section-head{display:flex;justify-content:space-between;gap:18px;align-items:end;margin-bottom:12px}.section-head h2{color:var(--navy);font-size:25px;letter-spacing:-.025em;margin:0}.section-head p{font-size:13px;color:var(--muted);margin:4px 0 0}.section-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:23px 25px}.anchor{display:block;height:1px}.platform-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0 20px}.platform{padding:15px 16px;border:1px solid var(--line);border-radius:14px;background:#fbfdff}.platform.android{border-left:4px solid var(--android)}.platform.ios{border-left:4px solid var(--ios)}.platform.h5{border-left:4px solid var(--h5)}.platform h4{margin:0 0 5px;color:var(--navy);font-size:14px}.platform p{margin:0;color:#536b83;font-size:12px}.source{font-size:12px;background:#f1f7fc;border:1px solid #d7e7f4;border-radius:12px;padding:12px 14px;color:#48617a}.source strong{color:var(--navy)}.page-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.page-card{border:1px solid var(--line);border-radius:16px;padding:19px 20px;background:linear-gradient(180deg,#fff,#fbfdff);min-width:0}.page-title{display:flex;align-items:center;gap:10px;margin-bottom:5px}.page-no{font-size:12px;color:var(--blue);font-weight:800;background:#eaf2fb;border-radius:8px;padding:3px 7px}.page-card h3{font-size:17px;color:var(--navy);margin:0}.page-card .question{margin:0 0 10px;color:#425d75;font-size:13px}.page-card .tag-row{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.tag{background:#f0f5fa;color:#45627d;border-radius:7px;padding:4px 7px;font-size:11px}.page-card .visual{font-size:12px;color:#1e648d;font-weight:700;margin-bottom:7px}.page-card .detail,.page-card .now{font-size:12px;color:#61778b;margin:4px 0}.page-card .now{padding-top:9px;margin-top:10px;border-top:1px dashed var(--line)}.page-card .now strong{color:#8c530a}.two-col{display:grid;grid-template-columns:1.08fr .92fr;gap:16px}.panel{background:#fbfdff;border:1px solid var(--line);border-radius:14px;padding:18px 19px;min-width:0}.panel h3{margin:0 0 6px;color:var(--navy);font-size:16px}.panel-sub{font-size:12px;color:var(--muted);margin:0 0 12px}.pill-row{display:flex;gap:7px;flex-wrap:wrap}.filter-pill{border:1px solid #cbd9e7;border-radius:999px;background:#fff;color:#365776;padding:7px 11px;font-size:12px}.filter-pill.on{background:var(--navy);color:#fff;border-color:var(--navy)}.wire{background:#0f263d;color:#dceaf5;border-radius:13px;padding:17px;overflow:auto;font:12px/1.65 "SFMono-Regular",Consolas,monospace;white-space:pre;min-height:230px}.legend{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.legend-item{border-radius:9px;padding:9px 10px;font-size:11px;background:#f2f6fa;color:#49647c}.legend-item b{display:block;color:var(--navy);font-size:12px;margin-bottom:2px}.legend-item.ok{border-left:3px solid var(--ok)}.legend-item.warn{border-left:3px solid #e2a034}.legend-item.red{border-left:3px solid var(--danger)}.legend-item.gray{border-left:3px solid #8ba0b4}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px}table{width:100%;border-collapse:collapse;min-width:860px}th,td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left;font-size:12px}th{background:#f3f7fb;color:#3f5c75;font-size:11px;white-space:nowrap;letter-spacing:.02em}tr:last-child td{border-bottom:0}td:first-child{font-weight:750;color:var(--navy);white-space:nowrap}td code,code{font-family:"SFMono-Regular",Consolas,monospace;color:#225c7d;background:#edf6fb;border-radius:5px;padding:2px 4px;overflow-wrap:anywhere}.state{font-weight:800;white-space:nowrap}.state.ok{color:var(--ok)}.state.warn{color:var(--warn)}.state.red{color:var(--danger)}.state.gray{color:#60778e}.matrix td,.matrix th{text-align:center}.matrix td:first-child,.matrix th:first-child{text-align:left}.matrix .yes{color:var(--ok);font-weight:800}.matrix .no{color:#9b6a16;font-weight:700}.matrix .gap{color:var(--danger);font-weight:800}.rank{display:grid;gap:8px}.rank-row{display:grid;grid-template-columns:115px 1fr 48px;gap:9px;align-items:center;font-size:12px}.rank-row .bar{height:9px;background:#e9f0f6;border-radius:99px;overflow:hidden}.rank-row .bar i{display:block;height:100%;background:linear-gradient(90deg,#42b6c9,#1976d2);border-radius:99px}.rank-row em{font-style:normal;color:var(--navy);text-align:right;font-variant-numeric:tabular-nums;font-weight:750}.callout{border-radius:13px;padding:14px 16px;border:1px solid var(--line);margin-top:12px;font-size:13px}.callout.warn{background:#fff9ed;border-color:#f0d9a7}.callout.red{background:#fff3ee;border-color:#efc9b9}.callout.blue{background:#eef7fc;border-color:#cfe5f2}.callout strong{color:var(--navy)}.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.step{position:relative;border:1px solid var(--line);border-radius:12px;padding:13px 13px 13px 42px;background:#fff;font-size:12px;color:#4b647b}.step b{position:absolute;left:13px;top:13px;width:22px;height:22px;display:grid;place-items:center;background:#e9f2fb;color:var(--blue);border-radius:7px;font-size:11px}.footer{border-top:1px solid var(--line);padding-top:18px;margin-top:8px;display:flex;gap:20px;justify-content:space-between;flex-wrap:wrap;color:var(--muted);font-size:11px}.small{font-size:11px;color:var(--muted)}@media(max-width:1120px){.shell{grid-template-columns:190px 1fr}.intro-grid{grid-template-columns:repeat(2,1fr)}.hero{grid-template-columns:1fr}.hero-side{border-left:0;border-top:1px solid var(--line);padding:15px 0 0;display:grid;grid-template-columns:repeat(3,1fr)}}@media(max-width:780px){.top{padding:14px 16px}.top-meta .window{display:none}.shell{display:block;padding:17px 14px 45px}.side{position:relative;top:auto;display:flex;gap:6px;overflow:auto;margin-bottom:16px;padding-bottom:2px}.side-label{display:none}.side a{border:1px solid var(--line);border-left:1px solid var(--line);border-radius:999px;padding:7px 10px;white-space:nowrap;background:#fff;font-size:11px}.side a span{display:none}.side a.active{border-color:var(--blue);background:#eaf2fb}.hero{padding:25px 21px;border-radius:19px}.hero h1{font-size:31px}.hero-side{display:block}.status-line{padding:7px 0}.intro-grid{grid-template-columns:repeat(2,1fr);gap:9px}.mini{padding:13px}.mini .num{font-size:22px}.section-head{display:block}.section-head h2{font-size:22px}.section-card{padding:17px 15px;border-radius:16px}.platform-strip,.page-grid,.two-col{grid-template-columns:1fr}.legend{grid-template-columns:repeat(2,1fr)}.steps{grid-template-columns:repeat(2,1fr)}.wire{font-size:10px}.footer{display:block}.footer div{margin-top:7px}}@media(max-width:380px){.intro-grid{grid-template-columns:1fr}.legend,.steps{grid-template-columns:1fr}}
''' + r'''
.mock{border:1px solid #d7e2ed;border-radius:15px;background:#f7fafd;padding:13px}.mock-bar{height:30px;border-radius:9px;background:#102a43;color:#dceaf5;display:flex;align-items:center;justify-content:space-between;padding:0 12px;font-size:11px;margin-bottom:10px}.mock-filter{display:flex;gap:6px;overflow:auto;margin-bottom:10px}.mock-filter span{white-space:nowrap;border:1px solid #c6d5e4;background:#fff;color:#47627b;border-radius:99px;padding:4px 8px;font-size:10px}.mock-filter span.active{background:#1976d2;border-color:#1976d2;color:#fff}.mock-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-bottom:10px}.mock-kpi{background:#fff;border:1px solid #d7e2ed;border-top:3px solid #1976d2;border-radius:10px;padding:8px}.mock-kpi:nth-child(2){border-top-color:#15803d}.mock-kpi:nth-child(3){border-top-color:#b45309}.mock-kpi:nth-child(4){border-top-color:#6d28d9}.mock-kpi label{display:block;color:#71849a;font-size:9px}.mock-kpi b{display:block;color:#102a43;font-size:17px;line-height:1.2;margin-top:2px}.mock-kpi small{display:block;color:#8092a4;font-size:9px;margin-top:3px}.mock-columns{display:grid;grid-template-columns:1.25fr .75fr;gap:8px}.mock-panel{background:#fff;border:1px solid #d7e2ed;border-radius:10px;padding:10px;min-width:0}.mock-panel h4{margin:0 0 7px;color:#102a43;font-size:11px}.mock-chart{height:105px;position:relative;background:linear-gradient(180deg,#fff 0,#fff 31%,#f3f7fb 32%,#fff 33%,#fff 65%,#f3f7fb 66%,#fff 67%);border-radius:7px;overflow:hidden}.mock-chart:before{content:"";position:absolute;left:3%;right:3%;bottom:18%;height:2px;background:#1976d2;transform:rotate(-7deg);box-shadow:25px 9px 0 #1976d2,51px -11px 0 #1976d2,77px -3px 0 #1976d2,103px -17px 0 #1976d2,129px -6px 0 #1976d2,155px -25px 0 #1976d2,181px -15px 0 #1976d2}.mock-chart:after{content:"P95 ms";position:absolute;right:7px;top:6px;color:#1976d2;font-size:9px;font-weight:700}.mock-bars{display:grid;gap:7px}.mock-bars div{display:grid;grid-template-columns:58px 1fr 30px;gap:5px;align-items:center;font-size:9px;color:#5d7389}.mock-bars i{height:7px;background:#dfeaf3;border-radius:99px;overflow:hidden}.mock-bars i:after{content:"";display:block;height:100%;width:72%;background:linear-gradient(90deg,#41b5c7,#1976d2);border-radius:99px}.mock-table{margin-top:8px;background:#fff;border:1px solid #d7e2ed;border-radius:10px;overflow:auto}.mock-table table{min-width:560px}.mock-table th,.mock-table td{font-size:9px;padding:7px 8px;border-bottom:1px solid #edf1f5}.mock-table th{background:#f5f8fb;color:#557087;text-align:left}.mock-table tr:last-child td{border-bottom:0}@media(max-width:780px){.mock-kpis{grid-template-columns:repeat(2,1fr)}.mock-columns{grid-template-columns:1fr}}@media(max-width:380px){.mock-kpis{grid-template-columns:1fr 1fr}}
'''


def html_page(data: dict) -> str:
    perf = {r["endpoint"]: r for r in data["native_performance"]}
    sessions = {r["endpoint"]: r for r in data["android_sessions"]}
    h5_total = sum(r["event_count"] for r in data["h5_event_dictionary"])
    native_total = sum(r["performance_record_count"] for r in data["native_performance"])
    session_total = sum(r["distinct_session_count"] for r in data["android_sessions"])
    page_nav = "".join(f'<a href="#{p["id"]}"><span>{p["no"]}</span>{esc(p["title"])}</a>' for p in PAGES)
    page_cards = []
    for p in PAGES:
        tags = "".join(f'<span class="tag">{esc(c)}</span>' for c in p["cards"])
        page_cards.append(
            f'<article class="page-card"><div class="page-title"><span class="page-no">{p["no"]}</span><h3>{esc(p["title"])}</h3></div>'
            f'<p class="question">{esc(p["question"])}</p><div class="tag-row">{tags}</div>'
            f'<div class="visual">展现：{esc(p["visual"])}</div><p class="detail">{esc(p["detail"])}</p>'
            f'<p class="now"><strong>当前数据：</strong>{esc(p["now"])}</p></article>'
        )
    metric_rows = []
    for name, definition, denom, grain, state in METRICS:
        tone = "ok" if "可用" in state or "具备" in state else "red" if "blocked" in state or "data_gap" in state else "warn"
        metric_rows.append(
            f'<tr><td>{esc(name)}</td><td>{esc(definition)}</td><td>{esc(denom)}</td><td>{esc(grain)}</td><td class="state {tone}">{esc(state)}</td></tr>'
        )
    filter_rows = "".join(f'<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td></tr>' for a,b,c,d in FILTERS)
    matrix_rows = [
        ("国家 / 运营商 / 包体 / 版本", "可用", "可用", "部分；待补 H5 版本"),
        ("品牌 / 型号 / 系统", "可用", "可用", "浏览器待补"),
        ("RAM / 设备档位", "待补", "待补", "未采集"),
        ("网络类型 / 请求类别", "待分类", "待分类", "未采集"),
        ("机器温度", "未采集", "未采集", "未采集"),
        ("Web Vitals / 白屏 / JS 错误", "不适用", "不适用", "数据缺口"),
        ("Fatal / ANR / Non-fatal", "事件量可用", "缺 Crashlytics 表", "不适用"),
        ("业务成功率", "Origin 待接入", "Origin 待接入", "阻断"),
    ]
    matrix_html = "".join(
        f'<tr><td>{esc(label)}</td><td class="{("yes" if "可用" in a else "no" if "待" in a else "gap")}">{esc(a)}</td><td class="{("yes" if "可用" in b else "no" if "待" in b else "gap")}">{esc(b)}</td><td class="{("yes" if "可用" in c else "no" if "待" in c else "gap")}">{esc(c)}</td></tr>'
        for label,a,b,c in matrix_rows
    )
    coverage_rows = "".join(
        f'<tr><td>{esc(r["source"])}</td><td>{esc(r["first_day"])}～{esc(r["last_day"])}</td><td>{r["covered_days"]}</td><td>{badge("试运行" if "provisional" in r["status"] else "未成熟", "amber" if "provisional" in r["status"] else "blue")}</td></tr>'
        for r in data["source_coverage"]
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>Waje 多端设备性能报表 / 看板详细设计 V2</title><style>{styles()}</style></head><body>
<header class="top"><div class="top-inner"><div class="brand"><span class="brand-mark">W</span><span>Waje · 端侧体验数据产品设计</span></div><div class="top-meta"><span><i class="dot"></i>设计交付 V2</span><span class="window">2026-08-27 · Africa/Lagos</span></div></div></header>
<div class="shell"><nav class="side" aria-label="文档导航"><p class="side-label">设计导航</p>{page_nav}<a href="#filters"><span>F</span>全局筛选器</a><a href="#metrics"><span>M</span>指标口径</a><a href="#style"><span>S</span>视觉规范</a><a href="#mockups"><span>U</span>页面原型</a><a href="#delivery"><span>R</span>报表与落地</a></nav><main class="main">
<section class="hero"><div><p class="eyebrow">详细报表 / 看板设计 · 设备 × 性能 × 事件/会话</p><h1>先看数据可信度，<br>再定位体验问题。</h1><p>本方案参照《设备监控及性能优化指标系统开发需求》，把 Android、iOS、H5 拆成三条端侧链路，在统一筛选、指标口径和视觉系统下分别展示。当前实际数据只用于基线，不把缺失指标写成 0。</p><p style="margin-top:14px"><a href="https://ksg964l11fam.sg.larksuite.com/wiki/QsplwWjnHi0J1PksQJQl3SrDgce?from=from_copylink">查看需求文档 ↗</a></p></div><div class="hero-side"><h3>当前上线前状态</h3><div class="status-line"><span>原生性能样本</span><strong>{compact(native_total)}</strong></div><div class="status-line"><span>Android 会话（去标识化）</span><strong>{compact(session_total)}</strong></div><div class="status-line"><span>H5 标准行为事件</span><strong>{compact(h5_total)}</strong></div><div class="status-line"><span>聚合层 / Metabase</span>{badge("待权限", "red")}</div></div></section>
<div class="intro-grid"><div class="mini"><div class="label">Android Performance</div><div class="num">7 日</div><div class="note">三包均有记录，试运行</div></div><div class="mini"><div class="label">iOS Performance</div><div class="num">6 日</div><div class="note">现有来源，趋势未成熟</div></div><div class="mini"><div class="label">H5 Analytics</div><div class="num">8 日</div><div class="note">仅四类标准行为事件</div></div><div class="mini"><div class="label">正式告警门槛</div><div class="num">≥500</div><div class="note">性能百分位合格样本</div></div></div>
<section class="section" id="context"><div class="section-head"><div><h2>设计前提：三端分开看，状态先于数字</h2><p>每个页面固定显示数据截止时间、完整日数、样本量、质量状态与口径版本。</p></div></div><div class="section-card"><div class="platform-strip"><div class="platform android"><h4>Android · 原生性能基线</h4><p>主包 7.11M、传音老包 4.47M、传音新包 3.89M 条 Performance 记录（08-20～08-26）。Analytics 仅 08-24。</p></div><div class="platform ios"><h4>iOS · 现有来源</h4><p>Analytics 08-20～08-24；Performance 2.45M 条记录（08-20～08-25）。未达到完整 7 日趋势门槛。</p></div><div class="platform h5"><h4>H5 · 行为可看，网页性能缺口</h4><p>08-14～08-21 四类标准事件共 {compact(h5_total)} 次；Web Vitals、白屏、核心请求与游戏阶段未采集。</p></div></div><div class="source"><strong>数据边界：</strong>基线来自企业 BigQuery 只读聚合结果，目标为 <code>wajenigeria / europe-west4</code>；H5 独立 US 源不与 V1 跨区域合并。没有数据时显示数据缺口或阻断，不填 0。</div></div></section>
<section class="section" id="coverage"><div class="section-head"><div><h2>当前数据覆盖矩阵</h2><p>这是“现在能做什么”的设计依据，不是把所有维度假设为已接入。</p></div></div><div class="section-card"><div class="table-wrap"><table><thead><tr><th>数据域</th><th>当前覆盖</th><th>覆盖天数</th><th>状态</th></tr></thead><tbody>{coverage_rows}</tbody></table></div><div class="callout warn"><strong>质量冲突：</strong>Android Sessions 中 Performance 开关聚合为 false，但 Performance 表已有大量真实记录。看板应把它作为数据质量告警，不得据此判定性能未接入。</div></div></section>
<section class="section" id="pages"><div class="section-head"><div><h2>8 个看板页面：每页一个问题</h2><p>默认从健康状态进入诊断，避免一张页面堆满独立指标。</p></div><span class="badge blue">页面级设计</span></div><div class="page-grid">{''.join(page_cards)}</div></section>
<section class="section" id="filters"><div class="section-head"><div><h2>全局筛选器与三端降级</h2><p>筛选项要真正改变相关卡片；端侧没有字段时显示“未采集”，不可强制变成 0。</p></div></div><div class="section-card"><div class="panel"><h3>默认筛选条样式</h3><p class="panel-sub">桌面版使用一行胶囊；移动版横向滚动。端侧、日期和数据状态固定在首屏。</p><div class="pill-row"><span class="filter-pill on">最近 7 个完整日</span><span class="filter-pill on">全部端侧</span><span class="filter-pill">Android 包体</span><span class="filter-pill">版本</span><span class="filter-pill">国家</span><span class="filter-pill">设备档位</span><span class="filter-pill">网络</span><span class="filter-pill">数据状态</span></div></div><div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>筛选项</th><th>控件</th><th>可选值 / 规则</th><th>影响页面</th></tr></thead><tbody>{filter_rows}</tbody></table></div><h3 style="margin:22px 0 9px;color:var(--navy)">端侧适用性矩阵</h3><div class="table-wrap"><table class="matrix"><thead><tr><th>维度 / 指标族</th><th>Android</th><th>iOS</th><th>H5</th></tr></thead><tbody>{matrix_html}</tbody></table></div></div></section>
<section class="section" id="metrics"><div class="section-head"><div><h2>指标口径：卡片、图表、导出必须同源</h2><p>每个指标都写清定义、算法、分母、粒度、来源和状态；正式排行遵守样本门槛。</p></div><span class="badge amber">口径 V1.0</span></div><div class="section-card"><div class="callout blue"><strong>统一规则：</strong>性能百分位仅使用合格且非负样本，样本少于 500 显示 N/A；用户型排行分母至少 100，计数型至少 200；少于 10 个去标识化会话的分组隐藏或合并。</div><div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>指标</th><th>定义 / 算法</th><th>分母 / 样本门槛</th><th>粒度与来源</th><th>当前状态</th></tr></thead><tbody>{''.join(metric_rows)}</tbody></table></div></div></section>
<section class="section" id="style"><div class="section-head"><div><h2>视觉和交互样式</h2><p>减少噪声、扩大信息层级，让产品和研发能在 10 秒内找到下一步。</p></div></div><div class="two-col"><div class="section-card"><h3 style="color:var(--navy);margin-top:0">桌面版 1440 px 信息层级</h3><div class="wire">┌─────────────────────────────────────────────────────────────────────┐
│ Waje 端侧体验 | 数据截止 | 完整日 | 口径版本 | 当前状态              │
├───────────────┬─────────────────────────────────────────────────────┤
│ 01 健康总览    │ 页面标题 + 一句话结论 + 状态徽章                    │
│ 02 业务漏斗    ├─────────────────────────────────────────────────────┤
│ 03 页面性能    │ 日期  端侧  包体  版本  国家  设备  网络  状态       │
│ 04 稳定性      ├──────────────┬──────────────┬──────────────┬────────┤
│ 05 网络        │ KPI 卡 1      │ KPI 卡 2      │ KPI 卡 3      │ KPI 4  │
│ 06 设备版本    ├────────────────────────────┬────────────────────────┤
│ 07 游戏体验    │ 主趋势 / 分布（2/3 宽）    │ 单维度排行（1/3 宽）   │
│ 08 数据质量    ├────────────────────────────┴────────────────────────┤
│               │ 明细表：排序 / 聚合导出 / 状态与样本量                │
└───────────────┴─────────────────────────────────────────────────────┘</div></div><div class="section-card"><h3 style="color:var(--navy);margin-top:0">移动版 390 px</h3><ul style="margin:0;padding-left:19px;color:#4b647b;font-size:13px"><li>端侧、状态、日期固定在顶部；筛选项改为横向滚动胶囊。</li><li>KPI 两列卡片；长标签换行，数值不截断。</li><li>图表和排行各占一整行；表格在卡片内横向滚动。</li><li>每页先显示“当前能回答什么 / 不能回答什么”。</li></ul><div class="legend" style="margin-top:16px"><div class="legend-item ok"><b>已核验</b>可用于正式日报</div><div class="legend-item warn"><b>试运行</b>有数据，慎下结论</div><div class="legend-item red"><b>缺口 / 阻断</b>需要补数据或权限</div><div class="legend-item gray"><b>延迟 / 未成熟</b>只做观察</div></div></div></div><div class="section-card" style="margin-top:16px"><h3 style="color:var(--navy);margin:0 0 11px">端侧颜色和组件</h3><div class="platform-strip"><div class="platform android"><h4>Android · 深绿</h4><p>Performance / Crashlytics / 三个生产包。</p></div><div class="platform ios"><h4>iOS · 紫色</h4><p>现有来源，单独标注成熟度。</p></div><div class="platform h5"><h4>H5 · 琥珀</h4><p>行为基线与性能缺口提示。</p></div></div><p class="small">主导航 #102A43 · 主指标 #1976D2 · 背景 #F4F7FB · 边框 #E2E8F0。标题 24～32px，正文 14～16px，表格不低于 12px；禁止大面积渐变和仅靠颜色传达状态。</p></div></section>
<section class="section" id="mockups"><div class="section-head"><div><h2>页面原型：原生性能页与 H5 缺口页</h2><p>以下是交付给 BI / 前端的可视化参考，不是虚构的实时指标。</p></div><span class="badge blue">样式样例</span></div><div class="two-col"><div class="section-card"><h3 style="color:var(--navy);margin:0 0 11px">A · Android / iOS 原生性能</h3><div class="mock"><div class="mock-bar"><span>原生性能 · Android 主包</span><span>试运行 · 08-20～08-26</span></div><div class="mock-filter"><span class="active">最近 7 个完整日</span><span class="active">Android</span><span>主包</span><span>所有版本</span><span>所有国家</span><span>设备型号</span></div><div class="mock-kpis"><div class="mock-kpi"><label>轨迹 P95</label><b>1,240 ms</b><small>样本 1.9M · 合格</small></div><div class="mock-kpi"><label>网络 P95</label><b>480 ms</b><small>请求样本 4.1M</small></div><div class="mock-kpi"><label>HTTP 成功率</label><b>98.7%</b><small>200～399 / 有响应码</small></div><div class="mock-kpi"><label>慢帧比例</label><b>2.8%</b><small>屏幕轨迹加权均值</small></div></div><div class="mock-columns"><div class="mock-panel"><h4>版本 P95 趋势（只读示意）</h4><div class="mock-chart"></div></div><div class="mock-panel"><h4>异常设备排行</h4><div class="mock-bars"><div><span>TECNO 桶</span><i></i><b>3.2%</b></div><div><span>Android 10</span><i></i><b>2.5%</b></div><div><span>蜂窝网络</span><i></i><b>1.9%</b></div></div></div></div><div class="mock-table"><table><thead><tr><th>版本</th><th>轨迹 P50</th><th>轨迹 P95</th><th>网络 P95</th><th>样本</th><th>状态</th></tr></thead><tbody><tr><td>2.17.0</td><td>540 ms</td><td>1,240 ms</td><td>480 ms</td><td>1.2M</td><td>试运行</td></tr><tr><td>2.16.3</td><td>510 ms</td><td>1,110 ms</td><td>450 ms</td><td>610k</td><td>试运行</td></tr></tbody></table></div></div></div><p class="small" style="margin:9px 0 0">样式要点：卡片只放一个主指标；图表标题写清窗口和分母；“P95”旁边固定显示样本量。</p></div><div class="section-card"><h3 style="color:var(--navy);margin:0 0 11px">B · H5 行为与性能缺口</h3><div class="mock"><div class="mock-bar"><span>H5 · 行为与网页性能</span><span>数据缺口</span></div><div class="mock-filter"><span class="active">最近 8 个数据日</span><span class="active">H5</span><span>事件分类</span><span>浏览器（未采集）</span></div><div class="mock-kpis"><div class="mock-kpi"><label>页面浏览事件</label><b>3.96M</b><small>page_view · 事件数</small></div><div class="mock-kpi"><label>会话开始事件</label><b>3.03M</b><small>session_start · 事件数</small></div><div class="mock-kpi"><label>网页性能</label><b>—</b><small>数据缺口</small></div><div class="mock-kpi"><label>核心漏斗</label><b>—</b><small>服务端事实阻断</small></div></div><div class="mock-columns"><div class="mock-panel"><h4>当前可回答</h4><ul style="margin:0;padding-left:16px;color:#5d7389;font-size:10px;line-height:1.8"><li>页面浏览 / 会话开始事件</li><li>标准事件日期覆盖</li><li>事件分类结构</li></ul></div><div class="mock-panel"><h4>待补观测</h4><ul style="margin:0;padding-left:16px;color:#b33d14;font-size:10px;line-height:1.8"><li>LCP / INP / CLS / TTFB</li><li>白屏 / JS 错误</li><li>游戏就绪 / 可下注</li></ul></div></div><div class="mock-table"><table><thead><tr><th>指标族</th><th>当前状态</th><th>上线条件</th></tr></thead><tbody><tr><td>Web Vitals</td><td style="color:#b33d14;font-weight:700">数据缺口</td><td>H5_NAVIGATION_PERF + measurement_state</td></tr><tr><td>核心请求</td><td style="color:#b33d14;font-weight:700">数据缺口</td><td>H5_CORE_REQUEST + request_id</td></tr></tbody></table></div></div></div><p class="small" style="margin:9px 0 0">H5 不把空值、退出或停留时长替代加载速度；性能卡片明确显示“数据缺口”。</p></div></div></section>
<section class="section" id="delivery"><div class="section-head"><div><h2>报表输出、数据层与实施顺序</h2><p>把设计落到固定节奏、聚合接口和可验收的动作。</p></div></div><div class="section-card"><div class="steps"><div class="step"><b>1</b><strong>06:30 WAT</strong><br>预刷新 D+1 覆盖与数据质量</div><div class="step"><b>2</b><strong>12:30 WAT</strong><br>最终刷新正式日报指标</div><div class="step"><b>3</b><strong>每周一次</strong><br>满 7 完整日才做版本回归</div><div class="step"><b>4</b><strong>15 分钟页</strong><br>仅原生性能；延迟&gt;45 分钟不告警</div></div><div class="two-col" style="margin-top:18px"><div class="panel"><h3>固定报表</h3><ul style="margin:0;padding-left:18px;color:#4b647b;font-size:13px"><li><strong>D+1 端侧健康日报：</strong>覆盖、设备、性能 P95、稳定性事件量、漏斗状态、动作。</li><li><strong>周度版本回归：</strong>至少 7 个完整日和稳定口径后才发布。</li><li><strong>15 分钟原生诊断：</strong>轨迹/网络 P95、成功率、慢帧、冻结帧、事件量。</li><li><strong>H5 接入覆盖报告：</strong>十个 V2 事件的字段完整率、延迟、重复率和缺项。</li></ul></div><div class="panel"><h3>聚合层接口</h3><p class="panel-sub"><code>waje_device_performance_mart</code>，Metabase 只读聚合视图。</p><ul style="margin:0;padding-left:18px;color:#4b647b;font-size:13px"><li><code>mart_endpoint_coverage_daily</code></li><li><code>mart_event_session_daily</code></li><li><code>mart_native_performance_daily</code></li><li><code>mart_stability_daily</code></li><li><code>mart_core_funnel_daily</code></li><li><code>mart_native_performance_15m</code></li></ul></div></div><div class="callout red"><strong>P0 缺口：</strong>H5 需补 H5_SESSION_START、H5_NAVIGATION_PERF、H5_CORE_REQUEST、H5_GAME_LOAD、H5_GAME_READY、H5_BET_READY、H5_CLIENT_ERROR、H5_NETWORK_CHANGE、H5_RECOVERY_RESULT、H5_SESSION_END；原生端需统一 release_id、flow_stage、trace_category、request_kind；Origin 需提供成功枚举和链路键。</div></div></section>
<section class="section" id="qa"><div class="section-head"><div><h2>验收标准：看板上线前逐项打勾</h2><p>这是产品验收表，也是数据质量页的长期检查项。</p></div></div><div class="section-card"><div class="two-col"><div class="panel"><h3>展示和交互</h3><ul style="margin:0;padding-left:18px;color:#4b647b;font-size:13px"><li>每页显示数据截止时间、完整日、样本量、质量状态、口径版本。</li><li>同一筛选上下文下卡片、图表、明细、导出聚合结果相互对账。</li><li>Android、iOS、H5 不跨端相加事件、会话、用户或受影响用户。</li><li>小样本隐藏/合并；未知维度不填零。</li></ul></div><div class="panel"><h3>数据与安全</h3><ul style="margin:0;padding-left:18px;color:#4b647b;font-size:13px"><li>H5 Web Vitals、白屏、核心请求和漏斗无数据时显示 data_gap / blocked。</li><li>Crashlytics 率指标需完成去重键和会话分母认证。</li><li>不输出用户 ID、设备唯一标识、完整 URL、请求/响应正文、订单、支付或堆栈。</li><li>跨区域 US H5 源不直接并入欧洲区域 V1。</li></ul></div></div></div></section>
<footer class="footer"><div>设计依据：<a href="https://ksg964l11fam.sg.larksuite.com/wiki/QsplwWjnHi0J1PksQJQl3SrDgce?from=from_copylink">设备监控及性能优化指标系统开发需求</a> · 2026-08-17</div><div>本地基线：<a href="actual_baseline.json">actual_baseline.json</a> · 相关预览：<a href="dashboard_preview.html">dashboard_preview.html</a></div></footer>
</main></div></body></html>'''


def main() -> None:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    OUT.write_text(html_page(data), encoding="utf-8")
    manifest = {
        "title": "Waje 多端设备、性能、事件与会话报表 / 看板详细设计 V2",
        "generated_at": "2026-08-27",
        "timezone": "Africa/Lagos",
        "reference": "https://ksg964l11fam.sg.larksuite.com/wiki/QsplwWjnHi0J1PksQJQl3SrDgce?from=from_copylink",
        "pages": PAGES,
        "metric_count": len(METRICS),
        "filter_count": len(FILTERS),
        "platforms": ["Android", "iOS", "H5"],
        "delivery": ["D+1 端侧健康日报", "周度版本回归报告", "15 分钟原生诊断页", "H5 接入覆盖报告"],
        "source": "actual_baseline.json; aggregate-only enterprise BigQuery snapshot",
        "security": "no user identifiers, device identifiers, URL, request/response body, order, payment or stack trace",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"wrote {MANIFEST}")


if __name__ == "__main__":
    main()

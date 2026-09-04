from html import escape
from pathlib import Path

OUT = Path(__file__).parent / "wireframes"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 970
BLUE = "#1D6FE8"
NAVY = "#15324B"
TEXT = "#263548"
MUTED = "#6B7785"
GRID = "#DDE5ED"
BG = "#F5F8FB"
GREEN = "#16A36A"
AMBER = "#D88900"
RED = "#D94A4A"
PURPLE = "#7D5BE1"


def rect(x, y, w, h, fill="#FFFFFF", stroke=GRID, r=10, sw=1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def text(x, y, value, size=22, fill=TEXT, weight=400, anchor="start"):
    return f'<text x="{x}" y="{y}" font-family="Arial, Noto Sans SC, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(str(value))}</text>'


def multiline(x, y, lines, size=18, fill=TEXT, weight=400, leading=25):
    items = []
    for index, line in enumerate(lines):
        items.append(text(x, y + index * leading, line, size, fill, weight))
    return "".join(items)


def chip(x, y, label, color, width=None):
    width = width or max(74, 16 + len(label) * 14)
    return rect(x, y, width, 27, fill="#FFFFFF", stroke=color, r=14) + text(x + width / 2, y + 19, label, 13, color, 600, "middle")


def header(active):
    tabs = ["设备健康总览", "核心业务与游戏", "页面与网络体验", "稳定性与异常", "设备版本与渠道"]
    parts = [rect(0, 0, W, H, BG, BG, 0), rect(0, 0, W, 72, "#FFFFFF", "#FFFFFF", 0)]
    parts.append(text(36, 45, "Waje · 设备监控（五页版报表示例）", 27, NAVY, 700))
    x = 520
    for tab in tabs:
        selected = tab == active
        parts.append(text(x, 44, tab, 17, BLUE if selected else MUTED, 700 if selected else 400))
        if selected:
            parts.append(f'<rect x="{x - 6}" y="62" width="{len(tab) * 17 + 12}" height="4" rx="2" fill="{BLUE}"/>')
        x += len(tab) * 18 + 42
    return "".join(parts)


def filter_strip(extra=""):
    filters = ["业务日期：最近 7 个完整日", "终端：全部", "包体：全部", "版本：全部", "分包渠道：全部", "国家：Nigeria"]
    parts = [rect(24, 92, 1552, 78, "#FFFFFF", "#E6EDF3", 12)]
    x = 44
    widths = [260, 180, 190, 180, 230, 180]
    for label, width in zip(filters, widths):
        parts.append(rect(x, 111, width, 40, "#F9FBFD", "#D8E2EC", 6))
        parts.append(text(x + 14, 137, label, 14, TEXT, 500))
        x += width + 13
    if extra:
        parts.append(text(42, 194, extra, 14, MUTED, 400))
    return "".join(parts)


def cards(items, y=215):
    parts = []
    card_w, card_h, gap = 246, 148, 14
    for i, item in enumerate(items):
        x = 24 + i * (card_w + gap)
        color = {"ok": GREEN, "warn": AMBER, "blocked": RED, "info": BLUE, "gap": PURPLE}.get(item.get("status"), BLUE)
        parts.append(rect(x, y, card_w, card_h, "#FFFFFF", "#DFE8F0", 12))
        parts.append(text(x + 16, y + 28, item["title"], 15, TEXT, 600))
        parts.append(text(x + 16, y + 79, item["value"], item.get("size", 33), color if item.get("status") in ("blocked", "gap") else NAVY, 700))
        parts.append(chip(x + 16, y + 103, item.get("tag", "聚合可用"), color))
        if item.get("note"):
            parts.append(text(x + 16, y + 137, item["note"], 12, MUTED, 400))
    return "".join(parts)


def table(x, y, widths, headers, rows, title=None, row_h=38):
    total = sum(widths)
    parts = []
    if title:
        parts.append(text(x, y - 14, title, 18, NAVY, 700))
    parts.append(rect(x, y, total, row_h * (len(rows) + 1), "#FFFFFF", GRID, 8))
    parts.append(f'<rect x="{x}" y="{y}" width="{total}" height="{row_h}" rx="8" fill="#EDF3F8"/>')
    cx = x
    for j, (h, width) in enumerate(zip(headers, widths)):
        parts.append(text(cx + 10, y + 25, h, 13, TEXT, 700))
        if j:
            parts.append(f'<line x1="{cx}" y1="{y}" x2="{cx}" y2="{y + row_h * (len(rows) + 1)}" stroke="{GRID}"/>')
        cx += width
    for i, row in enumerate(rows):
        yy = y + row_h * (i + 1)
        parts.append(f'<line x1="{x}" y1="{yy}" x2="{x + total}" y2="{yy}" stroke="{GRID}"/>')
        cx = x
        for value, width in zip(row, widths):
            fill = RED if str(value).startswith("blocked") or str(value).startswith("data_gap") else (AMBER if str(value).startswith("待核") else TEXT)
            parts.append(text(cx + 10, yy + 25, value, 13, fill, 500))
            cx += width
    return "".join(parts)


def svg_doc(title, active, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect width="{W}" height="{H}" fill="{BG}"/>
{header(active)}
{filter_strip()}
{body}
<text x="24" y="946" font-family="Arial, Noto Sans SC, sans-serif" font-size="12" fill="{MUTED}">示例数据来源：起源当前可见页面与 2026-08-27 Firebase 聚合快照；红色状态为未上报/不可计算，不能补零。</text>
</svg>'''


def health():
    c = cards([
        {"title":"日活用户（现有起源）", "value":"249,171", "tag":"业务规模", "status":"info", "note":"口径与截止时间待认证"},
        {"title":"传音老包 P0 启动 Fatal", "value":"6,584", "tag":"事件量", "status":"blocked", "note":"BuildConfigHelper"},
        {"title":"P0 首秒异常占比", "value":"98%", "tag":"启动风险", "status":"blocked", "note":"同一 Fatal Issue"},
        {"title":"主包网络 P95", "value":"2,114ms", "tag":"网络体验", "status":"warn", "note":"HTTP 网络层"},
        {"title":"主包 HTTP 成功率", "value":"99.95%", "tag":"请求质量", "status":"ok", "note":"不是业务成功率"},
        {"title":"H5 性能监控", "value":"盲区", "tag":"无 RUM", "status":"gap", "note":"无法定位加载/白屏"},
    ])
    matrix = table(24, 410, [220, 250, 220, 220, 250, 360],
                   ["端/包体", "Analytics", "Performance", "Crashlytics", "当前状态", "页面允许展示"],
                   [
                       ["Android 主包", "1 日事件快照", "7.11M 记录", "Issue 聚合可读", "provisional", "P95/网络/Issue"],
                       ["传音老包", "1 日事件快照", "4.47M 记录", "Issue 聚合可读", "provisional", "P95/网络/Issue"],
                       ["传音新包", "1 日事件快照", "3.89M 记录", "Issue 聚合可读", "provisional", "P95/网络/Issue"],
                       ["iOS", "5 日", "2.45M 记录", "未作趋势认证", "immature", "只显示覆盖/样本"],
                       ["H5", "4 类行为事件", "无 RUM", "无 Web 错误", "data_gap", "访问/会话基线"],
                   ], title="数据覆盖与可信度（仅作辅助状态，不作为首屏产品 KPI）")
    return c + matrix


def funnel():
    c = cards([
        {"title":"登录最终成功率", "value":"blocked", "tag":"缺服务端终态", "status":"blocked", "note":"需 trace_id"},
        {"title":"游戏进入成功率", "value":"blocked", "tag":"缺游戏回调", "status":"blocked", "note":"需 game_load_id"},
        {"title":"游戏可玩率", "value":"blocked", "tag":"缺 bet_ready", "status":"blocked", "note":"需 H5_BET_READY"},
        {"title":"首注成功率", "value":"blocked", "tag":"缺最终状态", "status":"blocked", "note":"服务端结算为准"},
        {"title":"首局结算成功率", "value":"blocked", "tag":"缺最终状态", "status":"blocked", "note":"不得用客户端尝试"},
        {"title":"现有充值成功率", "value":"64.41%", "tag":"待核旧口径", "status":"warn", "note":"不能命名最终到账"},
    ])
    parts=[c, text(24, 405, "业务链路漏斗（当前为接入验收示例，不虚构数值）",18,NAVY,700)]
    labels=["访问", "登录", "点击游戏", "游戏加载", "可下注", "首注", "首局结算", "充值到账"]
    x=36
    for i,label in enumerate(labels):
        fill="#FFF4F4" if i>0 else "#EAF3FF"
        stroke=RED if i>0 else BLUE
        parts.append(rect(x, 438, 166, 94, fill, stroke, 12, 2))
        parts.append(text(x+83, 473,label,16,TEXT,700,"middle"))
        parts.append(text(x+83,505,"已接入" if i==0 else "blocked",14,BLUE if i==0 else RED,600,"middle"))
        if i<7:
            parts.append(f'<path d="M {x+166} 485 L {x+184} 485" stroke="#AAB7C4" stroke-width="3"/>')
            parts.append(f'<polygon points="{x+184},485 {x+176},480 {x+176},490" fill="#AAB7C4"/>')
        x+=193
    details=table(24, 600,[165,165,175,175,175,200,200,230],
                  ["游戏/厂家", "点击会话", "game_ready", "bet_ready", "首注成功", "P95 加载", "失败阶段", "数据状态"],
                  [["全部游戏", "未认证", "未上报", "未上报", "未认证", "未上报", "无法定位", "blocked：待事件+服务端"]],
                  title="游戏体验明细表（开发完成后按游戏 / 厂家 / 版本 / 配置版本分组）")
    return "".join(parts)+details


def performance():
    c = cards([
        {"title":"主包 trace P95", "value":"714,709ms", "tag":"全 trace 聚合", "status":"warn", "note":"不是首页/启动"},
        {"title":"新传音 trace P95", "value":"409,642ms", "tag":"全 trace 聚合", "status":"warn", "note":"不是首页/启动"},
        {"title":"老传音 trace P95", "value":"439,041ms", "tag":"全 trace 聚合", "status":"warn", "note":"不是首页/启动"},
        {"title":"网络请求 P95", "value":"2,114ms", "tag":"主包", "status":"ok", "note":"HTTP 网络层"},
        {"title":"HTTP 成功率", "value":"99.95%", "tag":"主包", "status":"ok", "note":"非业务成功率"},
        {"title":"H5 Web Vitals", "value":"data_gap", "tag":"未上报", "status":"gap", "note":"FCP/LCP/INP/CLS"},
    ])
    parts=[c, text(24, 405,"包体原生 trace P95 对比（只展示当前已验收的窗口聚合）",18,NAVY,700)]
    data=[("Android 主包",714709,BLUE),("传音新包",409642,GREEN),("传音老包",439041,AMBER)]
    maxv=max(v for _,v,_ in data)
    x=84
    for lab,val,color in data:
        h=220*val/maxv
        parts.append(f'<rect x="{x}" y="{660-h}" width="180" height="{h}" rx="8" fill="{color}"/>')
        parts.append(text(x+90,685,lab,14,TEXT,600,"middle"))
        parts.append(text(x+90,640-h,str(f"{val:,}ms"),13,NAVY,700,"middle"))
        x+=260
    parts.append(text(28,725,"正式日趋势：需按 metric_date_lagos × app_package × app_version 从有效原始 trace 重算 P95；当前快照不允许伪造折线。",14,RED,600))
    tbl=table(24,765,[180,190,150,150,150,160,170,185,190],
              ["页面/trace", "集中维度", "记录量", "P50", "P95", "P99", "网络 P95", "HTTP 成功率", "状态"],
              [["原生 trace", "主包", "7.11M", "21,977ms", "714,709ms", "2,180,637ms", "2,114ms", "99.9469%", "provisional"],
               ["H5 页面/路由", "全部", "page_view 可用", "N/A", "N/A", "N/A", "N/A", "N/A", "data_gap"]],
              title="页面 / trace 体验明细表")
    return "".join(parts)+tbl


def stability():
    c = cards([
        {"title":"传音老包 P0 Fatal", "value":"6,584", "tag":"事件量", "status":"blocked", "note":"BuildConfigHelper"},
        {"title":"单 Issue 影响用户", "value":"1,997", "tag":"单问题范围", "status":"warn", "note":"不可跨 issue 相加"},
        {"title":"首秒发生比例", "value":"98%", "tag":"启动早期", "status":"blocked", "note":"需研发优先处理"},
        {"title":"主包 Top Non-fatal", "value":"160,984", "tag":"事件量", "status":"warn", "note":"不是崩溃率"},
        {"title":"崩溃率", "value":"待核", "tag":"缺认证分母", "status":"blocked", "note":"现有 0.02% 不复用"},
        {"title":"白屏/内存异常", "value":"data_gap", "tag":"未上报", "status":"gap", "note":"H5 未接入"},
    ])
    rows=[
        ["P0", "传音老包", "BuildConfigHelper 初始化空指针", "Fatal", "6,584", "1,997", "2.17.0", "98% 首秒", "研发"],
        ["P1", "Android 主包", "高量 JS Non-fatal", "Non-fatal", "160,984", "32,643", "2.13—2.17", "待设备下钻", "客户端"],
        ["blocked", "H5", "白屏/JS/内存", "—", "N/A", "N/A", "—", "未上报", "H5 前端"],
    ]
    tbl=table(24,410,[90,150,300,130,120,140,150,190,160],
              ["等级", "端/包", "异常", "类型", "事件量", "影响范围", "版本", "集中信号", "责任"],rows,
              title="稳定性问题与异常告警示例")
    return c+tbl


def dimensions():
    c = cards([
        {"title":"主包 MTN 记录量", "value":"4.45M", "tag":"运营商维度", "status":"ok", "note":"窗口聚合"},
        {"title":"主包 MTN trace P95", "value":"733,116ms", "tag":"运营商维度", "status":"warn", "note":"全 trace"},
        {"title":"主包 MTN 网络 P95", "value":"1,876ms", "tag":"运营商维度", "status":"ok", "note":"HTTP 网络层"},
        {"title":"主包 MTN HTTP 成功率", "value":"99.9%", "tag":"运营商维度", "status":"ok", "note":"非业务成功率"},
        {"title":"低端机 / 内存档位", "value":"未采集", "tag":"字典缺损", "status":"gap", "note":"不能计算占比"},
        {"title":"H5 浏览器/设备档位", "value":"未采集", "tag":"待 H5 RUM", "status":"gap", "note":"不能做排行"},
    ])
    parts=[c, text(24,405,"单一维度 Top N：当前选择“运营商”，切换到设备 / OS / 网络 / 渠道时必须重算整表",18,NAVY,700)]
    rows=[
        ["运营商", "MTN", "Android 主包", "4.45M", "733,116ms", "1,876ms", "99.9%", "eligible"],
        ["运营商", "Airtel/ZAIN/Econet", "Android 主包", "1.46M", "669,964ms", "2,478ms", "99.9%", "eligible"],
        ["运营商", "Glo Mobile", "Android 主包", "1.12M", "691,190ms", "2,346ms", "100.0%", "eligible"],
        ["设备档位", "unknown", "全部", "N/A", "N/A", "N/A", "N/A", "data_gap"],
    ]
    tbl=table(24,438,[150,250,210,160,180,170,170,180],
              ["排行维度", "对象", "端/包", "记录量", "trace P95", "网络 P95", "HTTP 成功率", "状态"],rows,
              title="设备、版本、网络、渠道定位明细表")
    return "".join(parts)+tbl


pages = {
    "01-设备健康总览.svg": ("设备健康总览", "设备健康总览", health()),
    "02-核心业务与游戏.svg": ("核心业务与游戏", "核心业务与游戏", funnel()),
    "03-页面与网络体验.svg": ("页面与网络体验", "页面与网络体验", performance()),
    "04-稳定性与异常.svg": ("稳定性与异常", "稳定性与异常", stability()),
    "05-设备版本与渠道.svg": ("设备版本与渠道", "设备版本与渠道", dimensions()),
}

for filename, (title, active, body) in pages.items():
    (OUT / filename).write_text(svg_doc(title, active, body), encoding="utf-8")

print("\n".join(str(OUT / name) for name in pages))

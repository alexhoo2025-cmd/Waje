from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

FONT_PATHS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def font(size: int, bold: bool = False):
    for path in FONT_PATHS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size, index=1 if bold else 0)
            except Exception:
                return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


INK = "#16233A"
MUTED = "#5D6B82"
BLUE = "#2F6BFF"
BLUE_LIGHT = "#EAF1FF"
TEAL = "#0A9B8E"
TEAL_LIGHT = "#E6F7F5"
ORANGE = "#E88935"
ORANGE_LIGHT = "#FFF1E4"
PURPLE = "#7456C8"
PURPLE_LIGHT = "#F1EDFF"
GREY = "#F4F6F9"
LINE = "#CCD5E3"
RED = "#C84A4A"


def canvas(width: int, height: int, title: str, subtitle: str):
    im = Image.new("RGB", (width, height), "#FFFFFF")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((48, 38, width - 48, 150), radius=24, fill="#F7F9FC")
    d.text((78, 60), title, font=font(42, True), fill=INK)
    d.text((80, 112), subtitle, font=font(22), fill=MUTED)
    return im, d


def box(d, xy, title, lines=(), fill=GREY, outline=LINE, title_color=INK, width=3, radius=22):
    x1, y1, x2, y2 = xy
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    d.text((x1 + 24, y1 + 18), title, font=font(28, True), fill=title_color)
    y = y1 + 62
    for line in lines:
        d.text((x1 + 24, y), line, font=font(20), fill=MUTED)
        y += 32


def arrow(d, start, end, color=BLUE, width=5, dashed=False):
    x1, y1 = start
    x2, y2 = end
    if dashed:
        steps = 20
        for i in range(0, steps, 2):
            a = i / steps
            b = min((i + 1) / steps, 1)
            d.line((x1 + (x2 - x1) * a, y1 + (y2 - y1) * a,
                    x1 + (x2 - x1) * b, y1 + (y2 - y1) * b), fill=color, width=width)
    else:
        d.line((x1, y1, x2, y2), fill=color, width=width)
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 18
    pts = [
        (x2, y2),
        (x2 - size * math.cos(angle - 0.55), y2 - size * math.sin(angle - 0.55)),
        (x2 - size * math.cos(angle + 0.55), y2 - size * math.sin(angle + 0.55)),
    ]
    d.polygon(pts, fill=color)


def current_architecture():
    im, d = canvas(1800, 1060, "当前数据平台架构", "数据存储集中，但指标、筛选、权限和分析流程分散")

    sources = [
        ("游戏/用户/埋点", BLUE_LIGHT, BLUE),
        ("投放/媒体/成本", ORANGE_LIGHT, ORANGE),
        ("订单/收入/TX/结算", TEAL_LIGHT, TEAL),
    ]
    for i, (name, fill, stroke) in enumerate(sources):
        y = 205 + i * 150
        box(d, (70, y, 390, y + 105), name, fill=fill, outline=stroke, title_color=stroke)
        arrow(d, (390, y + 52), (535, 430), color=stroke, width=4)

    box(d, (535, 325, 905, 535), "Google Cloud", ("游戏、投放和收入数据", "统一存储环境"), fill="#EEF4FF", outline=BLUE, title_color=BLUE)
    box(d, (1035, 210, 1355, 345), "Impala", ("旧引擎",), fill=GREY, outline="#8290A6")
    box(d, (1035, 405, 1355, 555), "BigQuery", ("迁移中", "预计8月底，排期待确认"), fill=TEAL_LIGHT, outline=TEAL, title_color=TEAL)
    arrow(d, (905, 385), (1035, 278), color="#8290A6")
    arrow(d, (905, 475), (1035, 475), color=TEAL)

    apps = [
        ("起源", "产品/用户/行为/报表", BLUE_LIGHT, BLUE),
        ("ARES", "投放/归因/ROI/策略", ORANGE_LIGHT, ORANGE),
        ("BI", "经营/财务/结算/分发", PURPLE_LIGHT, PURPLE),
        ("Metabase", "受控访问/风险隔离", GREY, "#6E7C90"),
    ]
    for i, (name, desc, fill, stroke) in enumerate(apps):
        y = 175 + i * 165
        box(d, (1450, y, 1730, y + 118), name, (desc,), fill=fill, outline=stroke, title_color=stroke)
        source_y = 278 if i == 0 else 480
        arrow(d, (1355, source_y), (1450, y + 58), color=stroke, width=4)

    box(d, (535, 700, 905, 900), "GM / AdminLTE", ("用户维护、客服、运营排障", "Lifecycle Pool 临时报表"), fill="#FFF7E8", outline="#C9922B", title_color="#9A6A12")
    arrow(d, (390, 505), (535, 785), color="#C9922B", width=4)
    arrow(d, (905, 785), (1450, 627), color=RED, width=4, dashed=True)
    d.text((1010, 745), "逐日导出 / 人工拼接", font=font(22, True), fill=RED)

    d.rounded_rectangle((70, 942, 1730, 1012), radius=18, fill="#FFF2F2", outline="#F0C5C5", width=2)
    d.text((95, 962), "主要断点：跨平台筛选不继承｜同名指标多口径｜No Data状态不清｜GM分析与操作混杂", font=font(23, True), fill=RED)
    im.save(OUT / "current_architecture.png", quality=95)


def target_architecture():
    im, d = canvas(1800, 1160, "目标数据平台架构", "一个可信数据底座、一个认证指标体系、五类任务工作台")

    layers = [
        ("数据源", "游戏/埋点｜投放成本｜订单收入｜TX结算｜GM操作", "#F7F9FC", "#6E7C90"),
        ("BigQuery 原始层", "原始留存｜接收时间｜审计｜错误隔离", BLUE_LIGHT, BLUE),
        ("标准事实层", "用户｜会话｜事件｜局｜订单｜投放｜生命周期｜结算", TEAL_LIGHT, TEAL),
        ("共享维度层", "产品｜游戏｜玩法｜版本｜设备｜渠道｜媒体｜账号", ORANGE_LIGHT, ORANGE),
        ("认证指标语义层", "公式｜口径版本｜成熟条件｜完整日｜质量状态", PURPLE_LIGHT, PURPLE),
    ]
    x1, x2 = 270, 1530
    y = 195
    for i, (title, desc, fill, stroke) in enumerate(layers):
        box(d, (x1, y, x2, y + 112), title, (desc,), fill=fill, outline=stroke, title_color=stroke)
        if i < len(layers) - 1:
            arrow(d, (900, y + 112), (900, y + 146), color=stroke, width=4)
        y += 150

    app_y = 930
    apps = [
        ("起源", "产品分析", BLUE_LIGHT, BLUE),
        ("ARES", "投放执行", ORANGE_LIGHT, ORANGE),
        ("BI", "经营分发", PURPLE_LIGHT, PURPLE),
        ("GM", "操作排障", "#FFF7E8", "#9A6A12"),
        ("Metabase", "受控访问/风险隔离", GREY, "#6E7C90"),
    ]
    start_x = 95
    gap = 18
    width = 310
    for i, (name, desc, fill, stroke) in enumerate(apps):
        x = start_x + i * (width + gap)
        box(d, (x, app_y, x + width, app_y + 120), name, (desc,), fill=fill, outline=stroke, title_color=stroke)
        arrow(d, (900, 907), (x + width / 2, app_y), color=stroke, width=3)

    d.rounded_rectangle((60, 175, 230, 900), radius=24, fill="#F3F6FA", outline=LINE, width=2)
    d.text((95, 260), "质量", font=font(30, True), fill=INK)
    d.text((88, 315), "血缘", font=font(30, True), fill=INK)
    d.text((88, 370), "调度", font=font(30, True), fill=INK)
    d.text((105, 425), "SLA", font=font(30, True), fill=INK)
    d.line((145, 485, 145, 810), fill=LINE, width=4)
    d.text((93, 830), "横向治理", font=font(22, True), fill=MUTED)

    d.rounded_rectangle((1570, 175, 1740, 900), radius=24, fill="#F3F6FA", outline=LINE, width=2)
    d.text((1590, 260), "权限", font=font(30, True), fill=INK)
    d.text((1590, 315), "脱敏", font=font(30, True), fill=INK)
    d.text((1590, 370), "导出", font=font(30, True), fill=INK)
    d.text((1590, 425), "审计", font=font(30, True), fill=INK)
    d.line((1655, 485, 1655, 810), fill=LINE, width=4)
    d.text((1600, 830), "安全边界", font=font(22, True), fill=MUTED)

    d.text((90, 1090), "Gemini：仅在认证数据集、权限穿透、脱敏和审计通过后接入", font=font(24, True), fill=PURPLE)
    im.save(OUT / "target_architecture.png", quality=95)


def information_architecture():
    im, d = canvas(1800, 1060, "目标报表与工作台结构", "按业务任务组织入口，而不是继续按历史报表名称堆叠")
    box(d, (650, 185, 1150, 300), "Waje 数据工作台", ("统一身份、统一筛选、统一数据状态",), fill="#EEF4FF", outline=BLUE, title_color=BLUE)

    groups = [
        ("BI 经营管理", ["经营健康", "收入利润", "TX结算", "订阅推送"], PURPLE_LIGHT, PURPLE),
        ("起源 产品分析", ["产品健康", "新手生命周期", "游戏与RTP", "付费与资产", "H5/低端机", "故障与质量"], BLUE_LIGHT, BLUE),
        ("ARES 增长投放", ["成本归因", "渠道质量", "ROI回收", "策略执行"], ORANGE_LIGHT, ORANGE),
        ("GM 运营客服", ["用户明细", "运营配置", "客服排障", "操作审计"], "#FFF7E8", "#9A6A12"),
        ("Metabase", ["受控访问/风险隔离", "受限业务数据", "敏捷分析", "专题看板"], GREY, "#6E7C90"),
    ]
    positions = [(60, 410), (400, 410), (800, 410), (1140, 410), (1480, 410)]
    widths = [300, 360, 300, 300, 260]
    for (title, items, fill, stroke), (x, y), w in zip(groups, positions, widths):
        h = 135 + len(items) * 58
        d.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=fill, outline=stroke, width=3)
        d.text((x + 22, y + 22), title, font=font(27, True), fill=stroke)
        yy = y + 78
        for item in items:
            d.rounded_rectangle((x + 20, yy, x + w - 20, yy + 42), radius=12, fill="#FFFFFF", outline="#DDE3EC", width=1)
            d.text((x + 34, yy + 8), item, font=font(20), fill=INK)
            yy += 56
        arrow(d, (900, 300), (x + w / 2, y), color=stroke, width=3)

    d.rounded_rectangle((90, 955, 1710, 1012), radius=16, fill="#F7F9FC", outline=LINE, width=2)
    d.text((125, 970), "统一筛选：日期｜产品｜游戏｜生命周期｜H5/APP｜版本｜媒体/渠道｜数据状态", font=font(23, True), fill=INK)
    im.save(OUT / "report_information_architecture.png", quality=95)


def horizontal_bar_chart(filename: str, title: str, subtitle: str, rows, maximum: int):
    """Render a print-safe chart used by the static HTML/PDF fallback."""
    chart_height = max(500, 330 + 78 * len(rows))
    im, d = canvas(1600, chart_height, title, subtitle)
    chart_left = 410
    chart_right = 1480
    top = 205
    row_gap = 92
    palette = [BLUE, TEAL, PURPLE, ORANGE, "#5E769A"]

    for tick in range(0, maximum + 1, max(1, maximum // 5)):
        x = chart_left + (chart_right - chart_left) * tick / maximum
        d.line((x, top - 12, x, top + row_gap * len(rows) - 20), fill="#E3E8F0", width=2)
        d.text((x - 10, top + row_gap * len(rows) - 4), str(tick), font=font(18), fill=MUTED)

    for idx, (label, value, note) in enumerate(rows):
        y = top + idx * row_gap
        d.text((90, y + 10), label, font=font(24, True), fill=INK)
        bar_w = (chart_right - chart_left) * value / maximum
        color = palette[idx % len(palette)]
        d.rounded_rectangle((chart_left, y, chart_left + bar_w, y + 48), radius=16, fill=color)
        d.text((chart_left + bar_w + 18, y + 7), str(value), font=font(25, True), fill=color)
        if note:
            d.text((90, y + 48), note, font=font(17), fill=MUTED)

    d.text((90, chart_height - 42), "单位：项｜目录清点快照：2026-08-03", font=font(18), fill=MUTED)
    im.save(OUT / filename, quality=95)


def static_charts():
    horizontal_bar_chart(
        "report_groups_bar.png",
        "起源报表集市各组条目数",
        "70项目录记录分散在5个报表组，经营分析与游戏分析各占27.1%",
        [
            ("经营分析", 19, "BQ前缀9项"),
            ("玩法数值", 10, "BQ前缀5项"),
            ("游戏分析", 19, "BQ前缀9项"),
            ("增长分析", 10, "BQ前缀5项"),
            ("经济体系", 12, "BQ前缀6项"),
        ],
        20,
    )
    horizontal_bar_chart(
        "version_structure_bar.png",
        "起源报表版本结构",
        "BQ前缀34项、非BQ 36项；名称前缀仅说明版本结构，不等于一一重复",
        [
            ("BQ前缀", 34, "占目录48.6%"),
            ("非BQ", 36, "占目录51.4%"),
        ],
        40,
    )


if __name__ == "__main__":
    current_architecture()
    target_architecture()
    information_architecture()
    static_charts()
    print(OUT)

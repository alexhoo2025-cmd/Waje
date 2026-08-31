from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"
BLUE, NAVY, ORANGE, SLATE, DARK, GRID, WHITE = "#2563EB", "#0F3D66", "#EA580C", "#64748B", "#1E293B", "#E2E8F0", "#FFFFFF"
LIGHT_YELLOW = "#FEF3C7"


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT, size, index=0)
    except OSError:
        return ImageFont.load_default()


def label(draw, position, value, size=20, color=DARK, bold=False, anchor=None):
    draw.text(position, value, font=font(size, bold), fill=color, anchor=anchor)


def save(image, name):
    image.save(OUT / name, "PNG", optimize=True)


def line_plot(draw, box, labels, values, color, baseline=None, shade_from=None):
    x0, y0, x1, y1 = box
    min_y, max_y = 70, 85
    if shade_from is not None:
        step = (x1 - x0) / max(1, len(labels) - 1)
        draw.rectangle((x0 + step * shade_from - step / 2, y0, x1, y1), fill=LIGHT_YELLOW)
    for tick in range(min_y, max_y + 1, 3):
        y = y1 - (tick - min_y) / (max_y - min_y) * (y1 - y0)
        draw.line((x0, y, x1, y), fill=GRID, width=2)
        label(draw, (x0 - 12, y), f"{tick}%", 13, SLATE, anchor="rm")
    if baseline is not None:
        y = y1 - (baseline - min_y) / (max_y - min_y) * (y1 - y0)
        draw.line((x0, y, x1, y), fill=SLATE, width=2)
        label(draw, (x0 + 8, y - 7), f"基线 {baseline:.2f}%", 13, SLATE)
    points = []
    for i, value in enumerate(values):
        x = x0 + (x1 - x0) * i / max(1, len(values) - 1)
        y = y1 - (value - min_y) / (max_y - min_y) * (y1 - y0)
        points.append((x, y))
        label(draw, (x, y1 + 23), labels[i], 13, SLATE, anchor="mt")
    draw.line(points, fill=color, width=5, joint="curve")
    for x, y in points:
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=WHITE, outline=color, width=4)


# Chart 1: full day vs same window
img = Image.new("RGB", (2200, 900), WHITE)
draw = ImageDraw.Draw(img)
label(draw, (90, 55), "全产品TC：完整日与同窗口", 34, DARK, True)
label(draw, (90, 105), "完整日用于经营判断；同窗口用于将8月28日部分日与历史可比时段对齐", 19, SLATE)
full_labels = ["8/19", "8/20", "8/21", "8/22", "8/23", "8/24", "8/25", "8/26", "8/27"]
full_values = [78.43, 77.76, 79.02, 79.96, 79.18, 77.57, 75.27, 79.48, 79.50]
win_labels = ["8/19", "8/20", "8/21", "8/22", "8/23", "8/24", "8/25", "8/26", "8/27", "8/28"]
win_values = [79.43, 78.53, 79.33, 80.98, 78.11, 72.75, 74.48, 81.72, 81.46, 82.95]
label(draw, (110, 185), "全产品完整日TC", 25, DARK, True)
line_plot(draw, (150, 250, 1040, 700), full_labels, full_values, NAVY, baseline=78.17)
label(draw, (1210, 185), "全产品同窗口TC（00:00—11:59）", 25, DARK, True)
line_plot(draw, (1250, 250, 2140, 700), win_labels, win_values, BLUE, baseline=77.66, shade_from=7)
label(draw, (150, 790), "结论：8月26—27日完整日TC接近基线；近3日上午窗口持续高于历史同窗口。", 20, DARK, True)
save(img, "01_全产品TC_完整日与同窗口.png")


# Chart 2: contribution drivers
img = Image.new("RGB", (2200, 860), WHITE)
draw = ImageDraw.Draw(img)
label(draw, (90, 55), "近3日同窗口TC的主要渠道贡献", 34, DARK, True)
label(draw, (90, 105), "超额提现 = 当前提现 − 当前充值 × 渠道自身历史同窗口TC；用于贡献排序，不代表真实损失", 19, SLATE)
groups = {
    "8月26日": [("Android", 5.215), ("iOS", 2.454), ("Wajebet H5", 0.846), ("H5", -0.060)],
    "8月27日": [("iOS", 3.864), ("H5", 1.878), ("Android", 1.152)],
    "8月28日（部分日）": [("Android", 5.246), ("iOS", 2.194), ("H5", 0.515)],
}
for index, (day, rows) in enumerate(groups.items()):
    x0, x1, y0, y1 = 110 + index * 700, 670 + index * 700, 260, 700
    label(draw, ((x0 + x1) / 2, 185), day, 24, DARK, True, anchor="mm")
    for tick in [0, 2, 4]:
        x = x0 + (x1 - x0) * tick / 5.6
        draw.line((x, y0, x, y1), fill=GRID, width=2)
        label(draw, (x, y1 + 23), f"{tick}M", 13, SLATE, anchor="mt")
    for row_index, (name, value) in enumerate(rows):
        y, start = y0 + row_index * 90 + 20, x0 + 145
        label(draw, (x0, y + 19), name, 17, DARK)
        width = abs(value) / 5.6 * (x1 - start)
        if value >= 0:
            draw.rounded_rectangle((start, y, start + width, y + 38), radius=8, fill=BLUE)
            label(draw, (start + width + 10, y + 19), f"+{value:.2f}M", 15, DARK, anchor="lm")
        else:
            draw.rounded_rectangle((start - width, y, start, y + 38), radius=8, fill=SLATE)
            label(draw, (start - width - 10, y + 19), f"{value:.2f}M", 15, DARK, anchor="rm")
label(draw, (110, 790), "结论：贡献端每天切换。H5只在8月27日为第二贡献端，不能解释近3日全产品共同上行。", 20, DARK, True)
save(img, "02_近3日TC主要渠道贡献.png")


# Chart 3: Hilo/Plinko scale and return rate
img = Image.new("RGB", (2200, 900), WHITE)
draw = ImageDraw.Draw(img)
label(draw, (90, 55), "PAWAJEH5轻量化游戏：结算规模与回报", 34, DARK, True)
label(draw, (90, 105), "仅覆盖Hilo与Plinko，窗口为每日00:00—11:59；结算金额不能直接等同于提现金额", 19, SLATE)
days = ["8/26", "8/27", "8/28"]
hilo_pay, plinko_pay = [47.01013, 12.86354, 73.00430], [159.42431, 134.85598, 131.46906]
hilo_rate, plinko_rate = [275.75, 168.99, 206.90], [89.21, 93.11, 95.87]
label(draw, (110, 185), "结算派奖（千）", 25, DARK, True)
x0, y0, x1, y1 = 150, 250, 1040, 700
for tick in [0, 50, 100, 150, 200]:
    y = y1 - tick / 200 * (y1 - y0)
    draw.line((x0, y, x1, y), fill=GRID, width=2)
    label(draw, (x0 - 12, y), str(tick), 13, SLATE, anchor="rm")
for i, day in enumerate(days):
    center = x0 + 150 + i * 250
    h1, h2 = hilo_pay[i] / 200 * (y1 - y0), plinko_pay[i] / 200 * (y1 - y0)
    draw.rounded_rectangle((center - 55, y1 - h1, center - 8, y1), radius=7, fill=ORANGE)
    draw.rounded_rectangle((center + 8, y1 - h2, center + 55, y1), radius=7, fill=BLUE)
    label(draw, (center, y1 + 23), day, 14, SLATE, anchor="mt")
label(draw, (790, 745), "Hilo", 15, ORANGE, True)
label(draw, (890, 745), "Plinko", 15, BLUE, True)

label(draw, (1210, 185), "结算派奖 / 下注（%）", 25, DARK, True)
x0, y0, x1, y1 = 1250, 250, 2140, 700
for tick in [0, 100, 200, 300]:
    y = y1 - tick / 320 * (y1 - y0)
    draw.line((x0, y, x1, y), fill=GRID, width=2)
    label(draw, (x0 - 12, y), f"{tick}%", 13, SLATE, anchor="rm")
for values, color in [(hilo_rate, ORANGE), (plinko_rate, BLUE)]:
    points = []
    for i, value in enumerate(values):
        x = x0 + 100 + i * 320
        y = y1 - value / 320 * (y1 - y0)
        points.append((x, y))
        label(draw, (x, y1 + 23), days[i], 14, SLATE, anchor="mt")
    draw.line(points, fill=color, width=5)
    for x, y in points:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=WHITE, outline=color, width=4)
label(draw, (1800, 745), "Hilo", 15, ORANGE, True)
label(draw, (1910, 745), "Plinko", 15, BLUE, True)
label(draw, (110, 790), "结论：Hilo有小样本高回报信号；Plinko约89%—96%。两者金额均不足以解释全产品渠道贡献。", 20, DARK, True)
save(img, "03_轻量化游戏结算规模与回报.png")

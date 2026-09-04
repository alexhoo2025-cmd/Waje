"""Reader-facing scope and language rules for this H5/APP report."""
import re

EXCLUDED = re.compile(r"phoenix|phenix|firebase|h5phx", re.I)


def chinese(text):
    replacements = [
        ("Executive Summary", "执行摘要"),
        ("Recommended next steps", "后续行动"),
        ("Further Questions", "待核实事项"),
        ("Caveats and Assumptions", "数据边界与口径"),
        ("注册 cohort", "注册批次"),
        ("首访 cohort", "首访批次"),
        ("cohort 用户", "同批用户"),
        ("cohort", "注册批次"),
        ("session 事件", "会话事件"),
        ("N/A", "暂不可用"),
        ("Web 首包", "网页首包"),
    ]
    for before, after in replacements:
        text = text.replace(before, after)
    text = re.sub(r"(?<=\d)pp\b", " 个百分点", text)
    return re.sub(r"\b(\d+(?:\.\d+)?)k\b", lambda m: f"{float(m[1]) / 10:g}万", text)


def finalize_topic(manifest, snapshot, lifecycle):
    """Remove out-of-scope material from the delivered payload, not archives."""
    for collection in ("sources", "cards", "charts", "tables"):
        manifest[collection] = [
            item for item in manifest.get(collection, [])
            if not EXCLUDED.search(" ".join(str(item.get(k, "")) for k in ("id", "sourceId", "dataset", "title", "label")))
        ]
    card_ids = {card["id"] for card in manifest["cards"]}
    table_ids = {table["id"] for table in manifest["tables"]}
    chart_ids = {chart["id"] for chart in manifest["charts"]}
    blocks = []
    for item in manifest["blocks"]:
        if EXCLUDED.search(item["id"]):
            continue
        if item.get("type") == "table" and item["tableId"] not in table_ids:
            continue
        if item.get("type") == "chart" and item["chartId"] not in chart_ids:
            continue
        if item.get("type") == "metric-strip":
            item["cardIds"] = [key for key in item["cardIds"] if key in card_ids]
        if "body" in item:
            paragraphs = []
            for paragraph in item["body"].split("\n\n"):
                if not EXCLUDED.search(paragraph):
                    paragraphs.append(paragraph)
                elif paragraph.startswith(("- ", "1. ")):
                    paragraphs.append("\n".join(line for line in paragraph.splitlines() if not EXCLUDED.search(line)))
            item["body"] = chinese("\n\n".join(part for part in paragraphs if part.strip()))
        blocks.append(item)
    manifest["blocks"] = blocks
    manifest["description"] = "H5 自然新增为重点、APP 为对照的留存、LTV 与付费价值专题分析。"
    manifest["accessIssues"] = [chinese(x) for x in manifest.get("accessIssues", []) if not EXCLUDED.search(x)]
    snapshot["datasets"] = {key: rows for key, rows in snapshot["datasets"].items() if not EXCLUDED.search(key)}
    for row in snapshot["datasets"].get("headline", []):
        for key in list(row):
            if EXCLUDED.search(key):
                del row[key]

    july = next(row for row in lifecycle if row["cohort_month"] == "2026-07")
    august = next(row for row in lifecycle if row["cohort_month"] == "2026-08")
    lines = []
    for day in (14, 30):
        before, after = july[f"ltv_{day}"], august[f"ltv_{day}"]
        lines.append(f"第{day}日 LTV：{before:.2f} → {after:.2f}，减少 **{before-after:.2f}（{(after/before-1)*100:.1f}%）**")
    ltv_text = "**H5 生命周期价值继续下移。** " + "；".join(lines) + "。"
    for block in blocks:
        if block["id"] == "summary":
            paragraphs = [p for p in block["body"].split("\n\n") if "H5 生命周期价值继续下移" not in p]
            block["body"] = "\n\n".join(paragraphs + [ltv_text])
        elif block["id"] == "ltv-payment-story":
            block["body"] = "## 03｜生命周期价值下降幅度\n\n" + "\n\n".join(lines) + "。\n\n**解读：** 以上降幅按各生命周期已达到观察日的注册批次计算，长期指标的有效批次范围不同。"
            block["sourceId"] = "h5-lifecycle-source"

    # Localize display strings only. Keep SQL, identifiers, paths and numbers exact.
    def display_fields(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"body", "title", "subtitle", "description", "label", "emptyState"} and isinstance(item, str):
                    value[key] = chinese(item)
                elif key not in {"query", "sources"}:
                    display_fields(item)
        elif isinstance(value, list):
            for item in value:
                display_fields(item)
    display_fields(manifest)
    for source in manifest["sources"]:
        source["label"] = chinese(source["label"])
        query = source.get("query", {})
        for key in ("description",):
            if key in query:
                query[key] = chinese(query[key])
        for key in ("filters", "metric_definitions"):
            if key in query:
                query[key] = [chinese(x) for x in query[key]]

    # Consistent Chinese section headings and one analytical question per section.
    headings = {
        "priority": "01｜优先行动",
        "retention-story": "02｜自然新增留存表现",
        "ltv-payment-story": "03｜生命周期价值变化",
        "platform-story": "05｜多平台留存对照",
        "stage-story": "06｜付费用户结构",
        "caveats": "数据范围与统计口径",
    }
    for block in manifest["blocks"]:
        if block["id"] in headings:
            body = block["body"].split("\n", 1)
            block["body"] = "## " + headings[block["id"]] + ("\n" + body[1] if len(body) > 1 else "")

    payments = snapshot["datasets"]["h5_payment_monthly"]
    jul_pay = next(row for row in payments if row["cohort_month"] == "2026-07")
    aug_pay = next(row for row in payments if row["cohort_month"] == "2026-08")
    payment_story = {
        "id": "payment-story",
        "type": "markdown",
        "sourceId": "h5-payment-cohort",
        "body": "## 04｜付费转化与人均支付\n\n"
            f"第14日付费率：**{jul_pay['day_14_payment_rate']*100:.2f}% → {aug_pay['day_14_payment_rate']*100:.2f}%**，"
            f"下降 **{(jul_pay['day_14_payment_rate']-aug_pay['day_14_payment_rate'])*100:.2f} 个百分点**。"
            f"同期第14日 ARPU 从 {jul_pay['day_14_arpu']:,.2f} 增至 {aug_pay['day_14_arpu']:,.2f}。\n\n"
            "**解读：** 付费覆盖下降、人均支付上升，需同时检查首充完成率和付费金额结构。",
    }
    lifecycle_table = next(block for block in manifest["blocks"] if block["id"] == "h5-lifecycle-table")
    ordered = []
    for block in manifest["blocks"]:
        if block["id"] == "h5-lifecycle-table":
            continue
        if block["id"] == "payment-chart":
            ordered.extend([lifecycle_table, payment_story])
        ordered.append(block)
    manifest["blocks"] = ordered

    # Give headline cards their comparison context; all values already exist in the snapshot.
    headline = snapshot["datasets"]["headline"][0]
    retention = snapshot["datasets"]["h5_retention_monthly"]
    jul_ret = next(row for row in retention if row["cohort_month"] == "2026-07")
    headline.update({
        "july_day14_retention": jul_ret["day_14_retention"],
        "july_day14_payment": jul_pay["day_14_payment_rate"],
        "july_ltv14": july["ltv_14"],
    })
    contexts = {"h5-aug-d14-retention": ("july_day14_retention", "percent"),
                "h5-aug-d14-payment": ("july_day14_payment", "percent"),
                "h5-aug-ltv14": ("july_ltv14", "number")}
    for card in manifest["cards"]:
        if card["id"] in contexts:
            field, fmt = contexts[card["id"]]
            card["metrics"] = card["metrics"][:1] + [{"label": "7月对照", "field": field, "format": fmt}]

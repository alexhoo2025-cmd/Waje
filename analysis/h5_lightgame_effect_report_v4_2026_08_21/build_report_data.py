#!/usr/bin/env python3
"""Build the retention-and-activity-only payload for H5 lightweight-game report V4."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "analysis/h5_pwa_lightgame_effect_v2_2026_08_19/analysis.json"
GA4_SOURCE = ROOT / "data/outputs/ga4-h5-readiness/2026-08-20/ga4-h5-readiness.json"
OUTPUT = Path(__file__).resolve().parent / "report_data.json"


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def pp(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:+.1f}pp"


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    ga4 = json.loads(GA4_SOURCE.read_text(encoding="utf-8"))
    channels = []
    for item in source["channel_summary"]:
        channels.append(
            {
                "group": item["group"],
                "surface": item["surface"],
                "channel": item["channel"],
                "new_users": int(item["new_users"]),
                "d1": item["d1"],
                "d3": item["d3"],
                "d7": item["d7"],
                "d15": item["d15"],
                "d30": item["d30"],
                "d1_cohorts": item["d1_cohorts"],
                "d3_cohorts": item["d3_cohorts"],
                "d7_cohorts": item["d7_cohorts"],
                "d15_cohorts": item["d15_cohorts"],
                "d30_cohorts": item["d30_cohorts"],
            }
        )

    pre_post = []
    for item in source["lightgame_pre_post"]:
        group_rows = [row for row in source["daily_rows"] if row["group"] == item["group"]]
        before_d15_rows = [
            row
            for row in group_rows
            if "2026-06-16" <= row["date"] <= "2026-07-13" and row.get("d15") is not None
        ]
        after_d15_rows = [
            row
            for row in group_rows
            if "2026-07-14" <= row["date"] <= "2026-08-04" and row.get("d15") is not None
        ]
        def weighted_d15(rows: list[dict]) -> float | None:
            numerator = sum(float(row["d15"]) * float(row["new_users"]) for row in rows)
            denominator = sum(float(row["new_users"]) for row in rows)
            return numerator / denominator if denominator else None
        before_d15 = weighted_d15(before_d15_rows)
        after_d15 = weighted_d15(after_d15_rows)
        pre_post.append(
            {
                "group": item["group"],
                "before_window": item["before_window"],
                "after_window": item["after_window"],
                "before_new_users": int(item["before_new_users"]),
                "after_new_users": int(item["after_new_users"]),
                "new_users_change": item["new_users_change"],
                "before_d1": item["before_d1"],
                "after_d1": item["after_d1"],
                "d1_delta": item["d1_delta"],
                "before_d3": item["before_d3"],
                "after_d3": item["after_d3"],
                "d3_delta": item["d3_delta"],
                "before_d7": item["before_d7"],
                "after_d7": item["after_d7"],
                "d7_delta": item["d7_delta"],
                "before_d15": before_d15,
                "after_d15": after_d15,
                "d15_delta": (after_d15 - before_d15) if before_d15 is not None and after_d15 is not None else None,
                "before_d15_cohorts": len(before_d15_rows),
                "after_d15_cohorts": len(after_d15_rows),
                "before_d15_users": int(sum(float(row["new_users"]) for row in before_d15_rows)),
                "after_d15_users": int(sum(float(row["new_users"]) for row in after_d15_rows)),
            }
        )

    def ga4_row(report_name: str, dimension: str, value: str) -> dict | None:
        for row in ga4["reports"][report_name]["rows"]:
            if row["dimensions"].get(dimension) == value:
                return row
        return None

    def metrics(row: dict | None) -> dict:
        return {} if row is None else {key: int(value) for key, value in row["metrics"].items()}

    limbo = metrics(ga4_row("pages_28d", "pagePath", "/game/9008"))
    color_dice = metrics(ga4_row("pages_28d", "pagePath", "/game/9003"))
    ga4_activity = {
        "window": "2026-07-23—2026-08-19",
        "timezone": ga4["timezone"],
        "host": metrics(ga4_row("hosts_28d", "hostName", "www.wajegame.com")),
        "games": [
            {
                "name": "Limbo 9008",
                "page_path": "/game/9008",
                **limbo,
                "views_per_active_user": limbo["screenPageViews"] / limbo["activeUsers"],
            },
            {
                "name": "Color Dice 9003",
                "page_path": "/game/9003",
                **color_dice,
                "views_per_active_user": color_dice["screenPageViews"] / color_dice["activeUsers"],
            },
        ],
        "device": {
            "mobile": metrics(ga4_row("tech_deviceCategory_28d", "deviceCategory", "mobile")),
            "android": metrics(ga4_row("tech_operatingSystem_28d", "operatingSystem", "Android")),
            "ios": metrics(ga4_row("tech_operatingSystem_28d", "operatingSystem", "iOS")),
        },
        "browsers": [
            {"browser": name, **metrics(ga4_row("tech_browser_28d", "browser", name))}
            for name in ["Chrome", "Safari", "Samsung Internet", "Opera", "Phoenix Browser"]
        ],
        "boundary": "GA4页面活跃用户和浏览量不等于游戏开始、首局完成、结算或局数。",
    }

    phases = []
    for item in source["phase_overview"]:
        phases.append(
            {
                "phase": item["phase"],
                "window": item["window"],
                "new_users": int(item["new_users"]),
                "d1": item["d1"],
                "d3": item["d3"],
                "d7": item["d7"],
                "d3_delta_baseline": item["d3_delta_baseline"],
                "d7_delta_baseline": item["d7_delta_baseline"],
                "d7_status": item["d7_status"],
                "best_channel": item["best_channel"],
            }
        )

    report = {
        "title": "Waje H5轻量化游戏上线后留存与活跃度效果分析 V4（阶段性）",
        "window": source["window"],
        "as_of": source["as_of"],
        "metric_definitions": {
            "new_users": "当天注册用户数。",
            "retention": "同日注册用户在第N天仍活跃的比例；仅统计已经达到对应观察天数的注册用户。",
            "decay": "阶段衰减率 = 1 - 后一观察点留存 ÷ 前一观察点留存；数值越高代表该阶段流失越快。",
            "game_activity_status": "当前缺少通过H5筛选验证的游戏参与、局数和首局数据，因此这些结果不以数值呈现。",
        },
        "channels": channels,
        "pre_post": pre_post,
        "phases": phases,
        "phase_channels": [
            {
                "phase": row["phase"],
                "window": row["window"],
                "overall_d3": row["overall_d3"],
                "overall_d7": row["overall_d7"],
                "h5_natural_d3": row["h5_natural_d3"],
                "h5_facebook_d3": row["h5_facebook_d3"],
                "h5_google_d3": row["h5_google_d3"],
                "pwa_natural_d3": row["pwa_natural_d3"],
                "h5_natural_d7": row["h5_natural_d7"],
                "h5_facebook_d7": row["h5_facebook_d7"],
                "h5_google_d7": row["h5_google_d7"],
                "pwa_natural_d7": row["pwa_natural_d7"],
                "d7_status": row["d7_status"],
            }
            for row in source["phase_channel_matrix"]
        ],
        "matched_retention_curve": source["matched_retention_curve"],
        "matched_retention_decay": source["matched_retention_decay"],
        "ga4_activity": ga4_activity,
        "event_nodes": [
            "Limbo 9008：2026-07-14上线，07-15下线，07-16恢复",
            "Keno：2026-07-23上线，与H5 2.1.14和KYC变更同日",
            "Color Dice 9003：2026-07-29上线",
            "Hilo、Plinko：2026-08-21上线，长期留存尚未达到观察条件",
        ],
        "quality_status": {
            "h5_game_filter": "blocked：wajeh5ga + googleadwords_int筛选结果未通过H5结果行验证。",
            "device_monitor": "blocked：设备监控报app_id字段歧义，所有页面No Data。",
            "event_chain": "provisional：已有入口点击/模块点击、游戏开始、游戏结束、结算；缺可玩、版本和标准游戏关联字段。",
            "ga4": "provisional：可用于页面、来源、设备和会话结构；首个BigQuery日表尚未出现。",
        },
        "facebook_account_ban": source["facebook_account_ban"],
        "visuals": [
            "62日新增趋势与投放事件.png",
            "62日窗口留存对比.png",
            "上线前后D1-D15留存变化.png",
            "四渠道同批注册用户D1-D30留存曲线.png",
            "四渠道分阶段留存衰减率.png",
            "轻量化更新节点D3留存折线.png",
            "GA4轻量化游戏页面活跃快照.png",
        ],
        "formatters": {"pct": "0.0%", "pp": "+0.0pp"},
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "channels": len(channels), "phases": len(phases)}))


if __name__ == "__main__":
    main()

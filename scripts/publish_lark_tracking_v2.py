#!/usr/bin/env python3
"""Publish and verify the native Lark Sheets data behind the Waje V2 document.

Authentication is delegated to the official ``lark-cli``. App secrets, user
tokens and cookies are never accepted by this script and never written to the
project. Run without ``--execute`` for a side-effect-free dry run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/lark_publish_v2.json"


def resolve_cli() -> Path:
    explicit = os.environ.get("LARK_CLI_BIN", "").strip()
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"LARK_CLI_BIN does not exist: {candidate}")
    found = shutil.which("lark-cli")
    if found:
        return Path(found)
    candidates = sorted(Path.home().glob(".local/node-*/bin/lark-cli"), reverse=True)
    if candidates:
        return candidates[0]
    raise FileNotFoundError("lark-cli not found; run: npx -y @larksuite/cli@latest install")


def run_cli(cli: Path, args: list[str], *, cwd: Path, timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        [str(cli), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode != 0:
        raise RuntimeError(f"lark-cli exit={completed.returncode}: {output[:1200]}")
    if not output:
        return {}
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"lark-cli returned non-JSON output: {output[:1200]}") from exc


def build_tables() -> tuple[dict[str, Any], dict[str, Any]]:
    source = "Waje 全链路数据需求与埋点设计（团队阅读版 V2）"
    window = "2026-08-04 至 2026-08-10"
    sheets = {
        "sheets": [
            {
                "name": "overview_kpi",
                "columns": ["metric_id", "display_name", "value", "display_value", "window", "status", "source"],
                "data": [
                    ["existing_meta_events", "现有元事件", 34, "34 个", "当前平台盘点", "已确认", source],
                    ["gameend_abnormal_rate", "GAMEEND 当前异常率", 0.0624, "6.24%", window, "P0", source],
                    ["trusted_layers", "数据可信链路", 3, "3 层", "目标架构", "设计目标", source],
                    ["dashboard_topics", "核心看板主题", 6, "6 类", "目标架构", "设计目标", source],
                ],
                "dtypes": {
                    "metric_id": "string",
                    "display_name": "string",
                    "value": "float64",
                    "display_value": "string",
                    "window": "string",
                    "status": "string",
                    "source": "string"
                },
                "header": True,
                "mode": "overwrite",
                "allow_overwrite": True,
            },
            {
                "name": "event_quality",
                "columns": ["event_name", "received_count", "abnormal_count", "abnormal_rate", "severity", "window"],
                "data": [
                    ["GAMEEND", 112635044, 7030603, 0.0624, "P0", window],
                    ["PV 页面进入", None, None, 0.0072, "观察", window],
                    ["MV 模块曝光", None, None, 0.0005, "低异常", window],
                    ["ASSET 资产流水", None, None, 0.0000004, "低异常", window],
                ],
                "dtypes": {
                    "event_name": "string",
                    "received_count": "Float64",
                    "abnormal_count": "Float64",
                    "abnormal_rate": "float64",
                    "severity": "string",
                    "window": "string"
                },
                "formats": {
                    "received_count": "#,##0",
                    "abnormal_count": "#,##0",
                    "abnormal_rate": "0.00000%"
                },
                "header": True,
                "mode": "overwrite",
                "allow_overwrite": True,
            },
            {
                "name": "quality_gate",
                "columns": ["gate_name", "target_value", "operator", "current_value", "status", "owner", "说明"],
                "data": [
                    ["核心事件入库率", 0.99, ">=", None, "待接入", "待研发确认", "低于 99% 为 P1"],
                    ["GAMEEND 异常率", 0.01, "<=", 0.0624, "P0", "待研发确认", "超过 1% 预警，超过 3% 为 P1；当前阻断决策"],
                    ["金融金额对账差异", 0.001, "<=", None, "待接入", "待研发确认", "超过 0.1% 为 P0"],
                    ["局链路可关联率", 0.99, ">=", None, "待接入", "待研发确认", "GAMESTART → GAMEEND → BETREWARD → ASSET"],
                    ["新版本核心事件量变化", -0.30, ">=", None, "待接入", "待研发确认", "较基线下降超过 30% 为 P1"],
                ],
                "dtypes": {
                    "gate_name": "string",
                    "target_value": "float64",
                    "operator": "string",
                    "current_value": "Float64",
                    "status": "string",
                    "owner": "string",
                    "说明": "string"
                },
                "formats": {
                    "target_value": "0.00%",
                    "current_value": "0.00%"
                },
                "header": True,
                "mode": "overwrite",
                "allow_overwrite": True,
            },
        ]
    }
    border = {"style": "solid", "weight": "thin", "color": "#D9E5DE"}
    styles = {
        "styles": [
            {
                "name": "overview_kpi",
                "freeze": {"rows": 1, "cols": 0},
                "cell_styles": [
                    {"range": "A1:G1", "background_color": "#087345", "font_color": "#FFFFFF", "font_weight": "bold", "horizontal_alignment": "center", "vertical_alignment": "middle", "border": border},
                    {"range": "A2:G5", "font_color": "#17352D", "vertical_alignment": "middle", "word_wrap": "auto-wrap", "border": border},
                    {"range": "A2:G2", "background_color": "#E8F6EE"},
                    {"range": "A3:G3", "background_color": "#FFF0EE"},
                    {"range": "A4:G4", "background_color": "#EDF4FB"},
                    {"range": "A5:G5", "background_color": "#FFF6DF"},
                    {"range": "C2:C5", "horizontal_alignment": "right"},
                ],
                "row_sizes": [{"range": "1:1", "size": 32}, {"range": "2:5", "size": 42}],
                "col_sizes": [{"range": "A:B", "size": 180}, {"range": "C:D", "size": 110}, {"range": "E:E", "size": 190}, {"range": "F:F", "size": 110}, {"range": "G:G", "size": 300}],
            },
            {
                "name": "event_quality",
                "freeze": {"rows": 1, "cols": 0},
                "cell_styles": [
                    {"range": "A1:F1", "background_color": "#087345", "font_color": "#FFFFFF", "font_weight": "bold", "horizontal_alignment": "center", "vertical_alignment": "middle", "border": border},
                    {"range": "A2:F5", "font_color": "#17352D", "vertical_alignment": "middle", "word_wrap": "auto-wrap", "border": border},
                    {"range": "A2:F2", "background_color": "#FFF0EE"},
                    {"range": "A3:F3", "background_color": "#FFF6DF"},
                    {"range": "A4:F5", "background_color": "#E8F6EE"},
                    {"range": "B2:D5", "horizontal_alignment": "right"},
                ],
                "row_sizes": [{"range": "1:1", "size": 32}, {"range": "2:5", "size": 38}],
                "col_sizes": [{"range": "A:A", "size": 180}, {"range": "B:D", "size": 125}, {"range": "E:E", "size": 100}, {"range": "F:F", "size": 190}],
            },
            {
                "name": "quality_gate",
                "freeze": {"rows": 1, "cols": 0},
                "cell_styles": [
                    {"range": "A1:G1", "background_color": "#087345", "font_color": "#FFFFFF", "font_weight": "bold", "horizontal_alignment": "center", "vertical_alignment": "middle", "border": border},
                    {"range": "A2:G6", "font_color": "#17352D", "vertical_alignment": "middle", "word_wrap": "auto-wrap", "border": border},
                    {"range": "A2:G2", "background_color": "#E8F6EE"},
                    {"range": "A3:G3", "background_color": "#FFF0EE"},
                    {"range": "A4:G6", "background_color": "#FFF6DF"},
                    {"range": "B2:D6", "horizontal_alignment": "right"},
                ],
                "row_sizes": [{"range": "1:1", "size": 32}, {"range": "2:6", "size": 46}],
                "col_sizes": [{"range": "A:A", "size": 190}, {"range": "B:D", "size": 110}, {"range": "E:E", "size": 100}, {"range": "F:F", "size": 130}, {"range": "G:G", "size": 310}],
            },
        ]
    }
    return sheets, styles


def build_chart(config: dict[str, Any]) -> dict[str, Any]:
    chart = config["chart"]
    sheet_name = chart["sheet_name"]
    return {
        "position": chart["position"],
        "size": chart["size"],
        "snapshot": {
            "title": {"text": chart["title"]},
            "plotArea": {"plot": {"type": "bar"}},
            "data": {
                "refs": [{"value": f"'{sheet_name}'!{chart['data_range']}"}],
                "dim1": {"serie": {"index": 1}},
                "dim2": {"series": [{"index": 4}]},
            },
        },
    }


def validate_local_payloads(sheets: dict[str, Any], styles: dict[str, Any], chart: dict[str, Any]) -> dict[str, Any]:
    sheet_items = sheets.get("sheets", [])
    style_items = styles.get("styles", [])
    sheet_names = [item.get("name") for item in sheet_items]
    style_names = [item.get("name") for item in style_items]
    if sheet_names != style_names:
        raise RuntimeError(f"sheet/style name mismatch: {sheet_names} != {style_names}")
    if sheet_names != ["overview_kpi", "event_quality", "quality_gate"]:
        raise RuntimeError(f"unexpected sheet order: {sheet_names}")
    for item in sheet_items:
        width = len(item.get("columns", []))
        if width == 0 or any(len(row) != width for row in item.get("data", [])):
            raise RuntimeError(f"invalid table width: {item.get('name')}")
    refs = chart.get("snapshot", {}).get("data", {}).get("refs", [])
    series = chart.get("snapshot", {}).get("data", {}).get("dim2", {}).get("series", [])
    if not refs or not series:
        raise RuntimeError("chart payload is missing refs or value series")
    return {
        "sheet_names": sheet_names,
        "row_counts": {item["name"]: len(item["data"]) for item in sheet_items},
        "chart_type": chart["snapshot"]["plotArea"]["plot"]["type"],
        "chart_ref": refs[0]["value"],
    }


def envelope_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else {}


def verify_tables(payload: dict[str, Any]) -> dict[str, Any]:
    expected_rows = {"overview_kpi": 4, "event_quality": 4, "quality_gate": 5}
    found = {}
    for sheet in envelope_data(payload).get("sheets", []):
        if not isinstance(sheet, dict):
            continue
        name = str(sheet.get("name", ""))
        if name in expected_rows:
            found[name] = {
                "columns": len(sheet.get("columns", [])),
                "rows": len(sheet.get("data", [])),
                "range": sheet.get("range", ""),
                "truncated": bool(sheet.get("truncated", False)),
            }
    missing = sorted(set(expected_rows) - set(found))
    bad_rows = {name: meta for name, meta in found.items() if meta["rows"] != expected_rows[name] or meta["truncated"]}
    if missing or bad_rows:
        raise RuntimeError(f"table readback failed: missing={missing}, bad_rows={bad_rows}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Perform remote writes. Default is dry-run.")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cli = resolve_cli()
    sheets, styles = build_tables()
    chart = build_chart(config)
    audit: dict[str, Any] = {
        "schema_version": 1,
        "run_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "execute" if args.execute else "dry-run",
        "document_url": config["document_url"],
        "workbook_url": config["workbook_url"],
        "status": "started",
        "credentials_persisted_by_script": False,
    }
    with tempfile.TemporaryDirectory(prefix="waje-lark-v2-") as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "sheets.json").write_text(json.dumps(sheets, ensure_ascii=False), encoding="utf-8")
        (tmpdir / "styles.json").write_text(json.dumps(styles, ensure_ascii=False), encoding="utf-8")
        (tmpdir / "chart.json").write_text(json.dumps(chart, ensure_ascii=False), encoding="utf-8")
        local_validation = validate_local_payloads(sheets, styles, chart)
        audit["local_validation"] = local_validation
        if args.execute:
            run_cli(cli, ["config", "show"], cwd=tmpdir)
            audit["before"] = envelope_data(run_cli(cli, ["sheets", "+workbook-info", "--url", config["workbook_url"], "--as", config["identity"], "--format", "json"], cwd=tmpdir))
            put_args = [
                "sheets", "+table-put", "--url", config["workbook_url"],
                "--sheets", "@sheets.json", "--styles", "@styles.json",
                "--as", config["identity"], "--format", "json",
            ]
            audit["table_write"] = envelope_data(run_cli(cli, put_args, cwd=tmpdir))
            readback = run_cli(cli, ["sheets", "+table-get", "--url", config["workbook_url"], "--as", config["identity"], "--format", "json"], cwd=tmpdir)
            audit["table_readback"] = verify_tables(readback)
            chart_list = run_cli(cli, ["sheets", "+chart-list", "--url", config["workbook_url"], "--sheet-name", config["chart"]["sheet_name"], "--as", config["identity"], "--format", "json"], cwd=tmpdir)
            existing = json.dumps(envelope_data(chart_list), ensure_ascii=False)
            if config["chart"]["title"] not in existing:
                audit["chart_write"] = envelope_data(run_cli(cli, ["sheets", "+chart-create", "--url", config["workbook_url"], "--sheet-name", config["chart"]["sheet_name"], "--properties", "@chart.json", "--as", config["identity"], "--format", "json"], cwd=tmpdir))
            else:
                audit["chart_write"] = {"status": "skipped_existing_title"}
            verified_charts = run_cli(cli, ["sheets", "+chart-list", "--url", config["workbook_url"], "--sheet-name", config["chart"]["sheet_name"], "--as", config["identity"], "--format", "json"], cwd=tmpdir)
            if config["chart"]["title"] not in json.dumps(envelope_data(verified_charts), ensure_ascii=False):
                raise RuntimeError("chart readback failed: expected chart title not found")
            audit["chart_readback"] = {"title": config["chart"]["title"], "verified": True}
            audit["after"] = envelope_data(run_cli(cli, ["sheets", "+workbook-info", "--url", config["workbook_url"], "--as", config["identity"], "--format", "json"], cwd=tmpdir))
        else:
            audit["table_write"] = {"status": "prepared_not_sent"}
            audit["chart_dry_run"] = {
                "status": "prepared_not_sent",
                "official_template": envelope_data(run_cli(cli, ["sheets", "+chart-create", "--print-example", "bar"], cwd=tmpdir)),
            }
    audit["status"] = "verified" if args.execute else "dry_run_ok"
    out_dir = ROOT / "data/outputs/lark-publish" / dt.date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "waje-tracking-v2.json"
    out_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Lark V2 publish {audit['status']}; audit={out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

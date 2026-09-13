"""Build a local, aggregate-only audit of live calibration attempts.

The audit intentionally reads only the redacted JSONL produced by
``calibrate_live.py`` and the hand-authored settlement evidence. It never
stores account identifiers, screenshots, cookies, network responses or card
faces beyond the aggregate counts needed to assess controller quality.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import Counter

from lab import ROOT, encoded, now


def read_jsonl(path: Path):
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            yield line_no, json.loads(line)
        except json.JSONDecodeError:
            yield line_no, {"type": "invalid_json"}


def audit(root: Path) -> dict:
    attempts = []
    for log in sorted((root / "calibration_runs").glob("*/observations.jsonl")):
        rows = [row for _, row in read_jsonl(log)]
        events = Counter(row.get("type", "unknown") for row in rows)
        frames = [row.get("frame", {}) for row in rows if row.get("type") == "frame"]
        actions = [row for row in rows if row.get("type") == "action_submitted"]
        distinct = rows[-1].get("distinct_observation_records") if rows else None
        stop = next((row for row in reversed(rows) if row.get("type") == "stop"), {})
        attempts.append(
            {
                "run": log.parent.name,
                "source": str(log.relative_to(root)),
                "frame_count": len(frames),
                "distinct_observation_records": distinct,
                "actions_submitted": len(actions),
                "action_state_changes": events.get("action_state_changed", 0),
                "unresolved_evidence": events.get("unresolved_card_evidence", 0),
                "manual_resume_taps": events.get("manual_resume_tap", 0),
                "dau1_lobby_clicks": events.get("dau1_lobby_click", 0),
                "settlement_observed": events.get("settlement_observed", 0),
                "stop_reason": stop.get("reason"),
                "action_reasons": Counter(
                    row.get("action", {}).get("reason", "unknown")
                    for row in actions
                    if isinstance(row.get("action"), dict)
                ),
            }
        )
    for item in attempts:
        item["action_reasons"] = dict(item["action_reasons"])

    settlements = []
    for path in sorted(root.glob("calibration_settlement_*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        # Keep only aggregate settlement fields and status labels.
        settlements.append(
            {
                "source": str(path.relative_to(root)),
                "game": raw.get("game"),
                "stake": raw.get("stake"),
                "result": raw.get("result"),
                "result_label_observed": raw.get("result_label_observed"),
                "player_points": raw.get("player_points"),
                "opponent_points": raw.get("opponent_points"),
                "player_display_reward": raw.get("player_display_reward"),
                "player_display_delta": raw.get("player_display_delta"),
                "balance_after_display": raw.get("balance_after_display"),
                "quality": raw.get("quality"),
                "end_reason": raw.get("end_reason"),
            }
        )

    total_actions = sum(item["actions_submitted"] for item in attempts)
    total_frames = sum(item["frame_count"] for item in attempts)
    return {
        "generated_at": now(),
        "scope": "test-h5.wajew.com / WHOT 6001 / calibration_only",
        "status": "provisional",
        "attempt_count": len(attempts),
        "total_frames": total_frames,
        "total_actions_submitted": total_actions,
        "attempts": attempts,
        "settlements": settlements,
        "quality_gate": {
            "formal_samples_added": 0,
            "rules_certified": False,
            "vision_certified": False,
            "no_autoplay_certified": False,
            "rtp_status": "settlement_semantics_unverified",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", type=Path, default=ROOT / "calibration_audit.json")
    parser.add_argument("--md", type=Path, default=ROOT / "calibration_audit.md")
    args = parser.parse_args()
    payload = audit(args.root)
    args.json.write_text(encoded(payload) + "\n", encoding="utf-8")
    lines = [
        "# WHOT 6001 校准尝试审计",
        "",
        f"- 状态：`{payload['status']}`；尝试：{payload['attempt_count']}；帧：{payload['total_frames']}；提交动作：{payload['total_actions_submitted']}",
        "- 正式样本：0；规则/视觉/无托管认证：均未通过；RTP：settlement_semantics_unverified",
        "",
        "| 尝试 | 帧 | 动作 | 动作状态变化 | Lobby DAU1 点击 | 结算 | 停止原因 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in payload["attempts"]:
        lines.append(
            f"| {item['run']} | {item['frame_count']} | {item['actions_submitted']} | {item['action_state_changes']} | {item['dau1_lobby_clicks']} | {item['settlement_observed']} | {item['stop_reason'] or '—'} |"
        )
    lines += ["", "所有结果仅为校准/机器人观察证据，不用于策略胜率或正式 RTP。"]
    args.md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(args.json), "md": str(args.md), "attempts": payload["attempt_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

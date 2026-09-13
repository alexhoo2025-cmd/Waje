"""Import a redacted 6001 calibration/observation record.

Observations intentionally remain unqualified because they do not contain the
continuous turn/ack evidence required by the formal experiment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from legacy6001 import Store


def ingest(db: Path, run_id: str, source: Path) -> dict[str, object]:
    raw = json.loads(source.read_text(encoding="utf-8"))
    autoplay = bool(raw.get("autoplay_observed", False))
    manual_intervention = bool(raw.get("manual_intervention", False))
    control_source = raw.get("control_source")
    if not control_source:
        if autoplay and manual_intervention:
            control_source = "mixed_auto_play"
        elif autoplay:
            control_source = "autoplay"
        elif int(raw.get("action_count", 0) or 0) > 0:
            control_source = "manual"
        else:
            control_source = "uncontrolled_observation"
    store = Store(db)
    attempt = store.add_attempt(
        run_id,
        requested_players=int(raw.get("requested_players", 2)),
        bet=float(raw.get("stake_display", 1)),
        room_label=str(raw.get("room_label", "legacy_observation")),
        source=source.name,
        requested_at=raw.get("observed_at"),
        actual_players=raw.get("actual_players"),
        terminal_reason=raw.get("end_reason"),
        quality_status=str(raw.get("quality_status", "observation")),
    )
    match = store.add_match(
        attempt,
        strategy_arm=str(raw.get("strategy_arm", "first_legal_play")),
        game_build=str(raw.get("game_build", "unknown")),
        source=source.name,
        started_at=raw.get("observed_at"),
        control_source=str(control_source),
    )
    result = store.settle(
        match,
        result=str(raw.get("result", "unknown")),
        end_reason=raw.get("end_reason"),
        player_points=raw.get("player_points"),
        opponent_points=raw.get("opponent_points"),
        player_cards=raw.get("player_cards"),
        opponent_cards=raw.get("opponent_cards"),
        autoplay_observed=autoplay,
        manual_intervention=manual_intervention,
        page_stake=raw.get("stake_display"),
        page_return=raw.get("page_return_display"),
        page_net_change=raw.get("page_net_change"),
        balance_before=raw.get("balance_before"),
        balance_after=raw.get("balance_after"),
        ledger_semantics_status="unverified",
        return_assumption="page_value_unverified",
        control_source=str(control_source),
        source=source.name,
        coverage_verified=False,
    )
    store.close()
    return {"attempt_id": attempt, "match_id": match, "qualified": result["qualified"],
            "exclusion_reason": result["exclusion_reason"], "source": source.name}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("--db", type=Path, default=Path(__file__).with_name("legacy6001_v3_2.sqlite3"))
    p.add_argument("--run-id", required=True)
    a = p.parse_args()
    print(json.dumps(ingest(a.db, a.run_id, a.source), ensure_ascii=False))


if __name__ == "__main__":
    main()

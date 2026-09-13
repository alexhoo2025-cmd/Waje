#!/usr/bin/env python3
"""Local, aggregate-only WHOT sample database and transparent strategy baseline.

This module deliberately stores no account identifiers, cookies, tokens, hidden
cards, or raw browser payloads.  It ingests settlement/turn summaries from the
test site and exposes a deterministic visible-board policy for fast human-like
decisions.  Bot/auto-play observations are kept separate from human-controlled
outcome metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "whot_samples.sqlite3"
DEFAULT_RECEIPTS = ROOT / "runs"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS matches (
  match_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  round_no INTEGER NOT NULL,
  observed_at TEXT NOT NULL,
  environment TEXT NOT NULL DEFAULT 'test_h5',
  game_id TEXT NOT NULL DEFAULT '6001',
  room_stake_displayed_units REAL,
  opponent_alias TEXT,
  player_mode TEXT NOT NULL CHECK (player_mode IN ('human_controlled','bot_auto_play_observation','unknown')),
  strategy_arm TEXT,
  result TEXT CHECK (result IN ('win','loss','draw','unknown')),
  player_settlement_displayed_units REAL,
  opponent_settlement_displayed_units REAL,
  player_points INTEGER,
  opponent_points INTEGER,
  balance_after_displayed_units REAL,
  settlement_visible INTEGER NOT NULL DEFAULT 0,
  quality_status TEXT NOT NULL DEFAULT 'observed_only',
  evidence_note TEXT,
  UNIQUE(run_id, round_no, player_mode)
);

CREATE TABLE IF NOT EXISTS turns (
  turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
  match_id INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
  turn_no INTEGER NOT NULL,
  actor_type TEXT NOT NULL CHECK (actor_type IN ('human','bot','auto_play','unknown')),
  strategy_arm TEXT,
  table_rank INTEGER,
  table_shape TEXT,
  hand_count_before INTEGER,
  legal_card_count INTEGER,
  chosen_rank INTEGER,
  chosen_shape TEXT,
  action TEXT NOT NULL CHECK (action IN ('play','draw','declare_last_card','pass','unknown')),
  decision_ms INTEGER,
  timeout_flag INTEGER NOT NULL DEFAULT 0,
  special_effect TEXT,
  visible_opponent_card_count INTEGER,
  note TEXT,
  UNIQUE(match_id, turn_no, actor_type)
);

CREATE TABLE IF NOT EXISTS policy_versions (
  policy_version TEXT PRIMARY KEY,
  description TEXT NOT NULL,
  created_at TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS strategy_metrics (
  policy_version TEXT NOT NULL,
  strategy_arm TEXT NOT NULL,
  sample_count INTEGER NOT NULL,
  win_count INTEGER NOT NULL,
  loss_count INTEGER NOT NULL,
  win_rate REAL,
  timeout_rate REAL,
  mean_decision_ms REAL,
  mean_settlement REAL,
  lower_bound_95 REAL,
  score REAL,
  computed_at TEXT NOT NULL,
  PRIMARY KEY(policy_version, strategy_arm)
);

CREATE INDEX IF NOT EXISTS idx_matches_mode_result ON matches(player_mode, result);
CREATE INDEX IF NOT EXISTS idx_matches_strategy ON matches(strategy_arm, result);
CREATE INDEX IF NOT EXISTS idx_turns_actor ON turns(actor_type, action);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    con.execute(
        "INSERT OR IGNORE INTO policy_versions(policy_version, description, created_at, is_active) "
        "VALUES (?, ?, ?, 1)",
        ("visible-board-v1", "公开牌面规则过滤 + 高点牌优先 + 5秒动作门槛", utc_now()),
    )
    return con


def alias(value: str | None) -> str | None:
    if not value:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"robot_{digest}"


def num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value: Any) -> int | None:
    value = num(value)
    return None if value is None else int(value)


def insert_match(con: sqlite3.Connection, row: dict[str, Any]) -> int:
    fields = {
        "run_id": row.get("run_id", "manual-observation"),
        "round_no": int(row.get("round_no", 0)),
        "observed_at": row.get("observed_at", utc_now()),
        "environment": row.get("environment", "test_h5"),
        "game_id": str(row.get("game_id", "6001")),
        "room_stake_displayed_units": num(row.get("room_stake_displayed_units")),
        "opponent_alias": alias(row.get("opponent_alias")) if row.get("opponent_alias") else None,
        "player_mode": row.get("player_mode", "human_controlled"),
        "strategy_arm": row.get("strategy_arm", "reduce_high_point_cards"),
        "result": row.get("result", "unknown"),
        "player_settlement_displayed_units": num(row.get("player_settlement_displayed_units")),
        "opponent_settlement_displayed_units": num(row.get("opponent_settlement_displayed_units")),
        "player_points": integer(row.get("player_points")),
        "opponent_points": integer(row.get("opponent_points")),
        "balance_after_displayed_units": num(row.get("balance_after_displayed_units")),
        "settlement_visible": int(bool(row.get("settlement_visible", False))),
        "quality_status": row.get("quality_status", "observed_only"),
        "evidence_note": row.get("evidence_note"),
    }
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    values = list(fields.values())
    con.execute(
        f"INSERT OR IGNORE INTO matches ({columns}) VALUES ({placeholders})", values
    )
    found = con.execute(
        "SELECT match_id FROM matches WHERE run_id=? AND round_no=? AND player_mode=?",
        (fields["run_id"], fields["round_no"], fields["player_mode"]),
    ).fetchone()
    assert found is not None
    return int(found[0])


def ingest_receipt(con: sqlite3.Connection, receipt_path: Path) -> int:
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    run_id = data.get("run_id", receipt_path.parent.name)
    if not isinstance(data.get("rounds"), list):
        # Preflight/blocked receipts may use a diagnostic object or strings
        # under ``rounds``; they contain no match-level observations.
        return 0
    mode = "human_controlled" if data.get("player_mode") == "normal_human_simulation" else "unknown"
    if "quick-strategy" in run_id:
        mode = "human_controlled"
    strategy = data.get("strategy") or (data.get("next_phase_plan") or {}).get("arms", ["baseline"])[0]
    count = 0
    for round_row in data.get("rounds", []):
        settlement = round_row.get("settlement_displayed_units")
        insert_match(
            con,
            {
                "run_id": run_id,
                "round_no": round_row.get("round_no", count + 1),
                "player_mode": mode,
                "strategy_arm": strategy,
                "result": round_row.get("result", "unknown"),
                "player_settlement_displayed_units": settlement,
                "opponent_settlement_displayed_units": round_row.get("opponent_settlement_displayed_units"),
                "player_points": round_row.get("player_points_at_settlement"),
                "opponent_points": round_row.get("opponent_points_at_settlement"),
                "room_stake_displayed_units": round_row.get("stake_displayed_units"),
                "settlement_visible": settlement is not None,
                "quality_status": "observed_only",
                "evidence_note": round_row.get("evidence"),
            },
        )
        count += 1
    return count


def ingest_receipts(con: sqlite3.Connection, receipts_dir: Path) -> int:
    total = 0
    for path in sorted(receipts_dir.glob("*/run_receipt.json")):
        total += ingest_receipt(con, path)
    con.commit()
    return total


def ingest_jsonl(con: sqlite3.Connection, jsonl_path: Path) -> int:
    """Ingest manually curated aggregate observations, one JSON object per line."""
    count = 0
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        match_id = insert_match(con, row)
        for turn in row.get("turns", []):
            fields = {
                "match_id": match_id,
                "turn_no": int(turn.get("turn_no", 1)),
                "actor_type": turn.get("actor_type", "unknown"),
                "strategy_arm": turn.get("strategy_arm", row.get("strategy_arm")),
                "table_rank": integer(turn.get("table_rank")),
                "table_shape": turn.get("table_shape"),
                "hand_count_before": integer(turn.get("hand_count_before")),
                "legal_card_count": integer(turn.get("legal_card_count")),
                "chosen_rank": integer(turn.get("chosen_rank")),
                "chosen_shape": turn.get("chosen_shape"),
                "action": turn.get("action", "unknown"),
                "decision_ms": integer(turn.get("decision_ms")),
                "timeout_flag": int(bool(turn.get("timeout_flag", False))),
                "special_effect": turn.get("special_effect"),
                "visible_opponent_card_count": integer(turn.get("visible_opponent_card_count")),
                "note": turn.get("note"),
            }
            columns = ", ".join(fields)
            placeholders = ", ".join("?" for _ in fields)
            con.execute(
                f"INSERT OR IGNORE INTO turns ({columns}) VALUES ({placeholders})",
                list(fields.values()),
            )
        count += 1
    con.commit()
    return count


def legal_cards(hand: Iterable[dict[str, Any]], table_rank: int | None, table_shape: str | None) -> list[dict[str, Any]]:
    out = []
    for card in hand:
        rank = integer(card.get("rank"))
        shape = card.get("shape")
        if rank == 20 or (table_rank is not None and rank == table_rank) or (
            table_shape and shape and shape == table_shape
        ):
            out.append(card)
    return out


def recommend_action(state: dict[str, Any], strategy_arm: str | None = None) -> dict[str, Any]:
    """Return a visible-board decision; never infers hidden/deck state."""
    started = datetime.now(timezone.utc)
    hand = list(state.get("hand", []))
    table_rank = integer(state.get("table_rank"))
    table_shape = state.get("table_shape")
    opponent_cards = integer(state.get("opponent_card_count"))
    seconds = num(state.get("seconds_remaining"))
    legal = legal_cards(hand, table_rank, table_shape)
    strategy_arm = strategy_arm or state.get("strategy_arm") or "reduce_high_point_cards"
    if not legal:
        action = {"action": "draw", "reason": "no_visible_legal_card", "chosen_card": None}
    else:
        if strategy_arm == "first_legal_play":
            chosen = legal[0]
        else:
            def score(card: dict[str, Any]) -> tuple[float, int]:
                rank = integer(card.get("rank")) or 0
                special = rank in {2, 3, 5, 8, 14, 20}
                # High point removal is the default human-like arm.  Keep a
                # WHOT card for a one-card finish unless it is the only legal
                # option.
                value = float(rank)
                if special:
                    value += 2.0
                if strategy_arm == "retain_special_or_wild_cards_until_needed" and special:
                    value -= 6.0
                if rank == 20 and len(hand) > 1 and len(legal) > 1:
                    # Keep WHOT for a forced match or a one-card finish. The
                    # suit-wheel adds an interaction and is slower under a short
                    # countdown, so a visible non-wild match is safer here.
                    value -= 12.0
                if rank == 20 and seconds is not None and seconds <= 2:
                    value -= 8.0
                if len(hand) <= 2:
                    value += 3.0
                if opponent_cards is not None and opponent_cards <= 2:
                    value += 1.5
                return value, rank

            chosen = max(legal, key=score)
        action = {
            "action": "play",
            "reason": (
                "first_visible_legal"
                if strategy_arm == "first_legal_play"
                else "visible_legal_card_high_point_first"
            ),
            "chosen_card": chosen,
        }
    elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    action.update(
        {
            "policy_version": "visible-board-v1",
            "strategy_arm": strategy_arm,
            "legal_card_count": len(legal),
            "hand_count": len(hand),
            "seconds_remaining": seconds,
            "decision_ms": elapsed_ms,
            "timeout_risk": bool(seconds is not None and seconds <= 1),
        }
    )
    return action


def wilson_lower(wins: int, n: int, z: float = 1.96) -> float | None:
    if n <= 0:
        return None
    p = wins / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (centre - spread) / den


def refresh_metrics(con: sqlite3.Connection, policy_version: str = "visible-board-v1") -> list[dict[str, Any]]:
    rows = con.execute(
        """
        SELECT strategy_arm,
               COUNT(*) AS n,
               SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN result='loss' THEN 1 ELSE 0 END) AS losses,
               AVG(player_settlement_displayed_units) AS mean_settlement
        FROM matches
        WHERE player_mode='human_controlled' AND result IN ('win','loss')
        GROUP BY strategy_arm
        ORDER BY strategy_arm
        """
    ).fetchall()
    out = []
    for row in rows:
        n, wins, losses = int(row["n"]), int(row["wins"] or 0), int(row["losses"] or 0)
        turn_stats = con.execute(
            "SELECT AVG(decision_ms), AVG(timeout_flag) FROM turns WHERE strategy_arm=? AND actor_type='human'",
            (row["strategy_arm"],),
        ).fetchone()
        mean_ms = float(turn_stats[0]) if turn_stats[0] is not None else None
        timeout_rate = float(turn_stats[1]) if turn_stats[1] is not None else 0.0
        win_rate = wins / n if n else None
        lower = wilson_lower(wins, n)
        score = None if win_rate is None else (0.7 * (lower if lower is not None else win_rate) + 0.3 * win_rate - 0.1 * timeout_rate)
        item = {
            "policy_version": policy_version,
            "strategy_arm": row["strategy_arm"],
            "sample_count": n,
            "win_count": wins,
            "loss_count": losses,
            "win_rate": win_rate,
            "timeout_rate": timeout_rate,
            "mean_decision_ms": mean_ms,
            "mean_settlement": row["mean_settlement"],
            "lower_bound_95": lower,
            "score": score,
            "computed_at": utc_now(),
        }
        con.execute(
            """
            INSERT INTO strategy_metrics VALUES (:policy_version,:strategy_arm,:sample_count,
              :win_count,:loss_count,:win_rate,:timeout_rate,:mean_decision_ms,:mean_settlement,
              :lower_bound_95,:score,:computed_at)
            ON CONFLICT(policy_version,strategy_arm) DO UPDATE SET
              sample_count=excluded.sample_count, win_count=excluded.win_count,
              loss_count=excluded.loss_count, win_rate=excluded.win_rate,
              timeout_rate=excluded.timeout_rate, mean_decision_ms=excluded.mean_decision_ms,
              mean_settlement=excluded.mean_settlement, lower_bound_95=excluded.lower_bound_95,
              score=excluded.score, computed_at=excluded.computed_at
            """,
            item,
        )
        out.append(item)
    con.commit()
    return out


def select_strategy(con: sqlite3.Connection, min_samples: int = 5) -> str:
    """Select a strategy only after enough completed human games.

    Wilson lower-bound scoring prevents a lucky one- or two-game arm from
    replacing the current policy.  With insufficient evidence, keep the
    explicit high-point policy rather than silently overfitting.
    """
    metrics = refresh_metrics(con)
    eligible = [m for m in metrics if m["sample_count"] >= min_samples and m["score"] is not None]
    if not eligible:
        return "reduce_high_point_cards"
    return max(eligible, key=lambda m: (m["score"], m["lower_bound_95"] or 0.0))["strategy_arm"]


def report(con: sqlite3.Connection, db_path: Path = DEFAULT_DB) -> dict[str, Any]:
    metrics = refresh_metrics(con)
    selected = select_strategy(con)
    totals = con.execute(
        """
        SELECT COUNT(*) AS observed,
               SUM(CASE WHEN result IN ('win','loss') THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN result='loss' THEN 1 ELSE 0 END) AS losses
        FROM matches WHERE player_mode='human_controlled'
        """
    ).fetchone()
    observations = con.execute(
        "SELECT COUNT(*) FROM turns WHERE actor_type IN ('bot','auto_play')"
    ).fetchone()[0]
    return {
        "database": str(db_path),
        "scope": "test_h5 / WHOT 6001 / aggregate-only",
        "human_controlled": {
            "observed_matches": int(totals["observed"] or 0),
            "completed_matches": int(totals["completed"] or 0),
            "wins": int(totals["wins"] or 0),
            "losses": int(totals["losses"] or 0),
            "win_rate": (float(totals["wins"] or 0) / int(totals["completed"]) if totals["completed"] else None),
        },
        "bot_auto_play_observations": int(observations),
        "selected_strategy_arm": selected,
        "strategy_metrics": metrics,
        "next_policy_rule": "样本数不足时固定使用 visible-board-v1；达到每策略至少 5 局后才按 95% Wilson 下界与超时率选择策略。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("--receipts", type=Path, default=DEFAULT_RECEIPTS)
    jsonl = sub.add_parser("ingest-jsonl")
    jsonl.add_argument("path", type=Path)
    sub.add_parser("report")
    rec = sub.add_parser("recommend")
    rec.add_argument("--state-json", required=True)
    args = parser.parse_args()
    con = connect(args.db)
    if args.command == "init":
        con.commit()
        print(json.dumps({"status": "ok", "db": str(args.db)}, ensure_ascii=False, indent=2))
    elif args.command == "ingest":
        count = ingest_receipts(con, args.receipts)
        print(json.dumps({"status": "ok", "ingested_matches": count, "db": str(args.db)}, ensure_ascii=False, indent=2))
    elif args.command == "report":
        print(json.dumps(report(con, args.db), ensure_ascii=False, indent=2))
    elif args.command == "ingest-jsonl":
        count = ingest_jsonl(con, args.path)
        print(json.dumps({"status": "ok", "ingested_observations": count, "db": str(args.db)}, ensure_ascii=False, indent=2))
    elif args.command == "recommend":
        state = json.loads(args.state_json)
        selected = select_strategy(con)
        print(json.dumps(recommend_action(state, selected), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""WHOT V2 local QA sample store, rule engine, and evaluation CLI.

The implementation is intentionally local and aggregate-only. It stores no
credentials, cookies, tokens, raw opponent names, hidden cards, or network
payloads. Existing V1 receipts remain immutable inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse


SCHEMA_VERSION = "2.0"
POLICY_VERSION = "visible-board-v2"
DEFAULT_RULESET_VERSION = "observed_v1"
ALLOWED_HOST = "test-h5.wajew.com"
ALLOWED_GAME_ID = "6001"
ALLOWED_BROWSER_SURFACE = "external_chrome"
ALLOWED_SHAPES = ("circle", "square", "triangle", "star", "cross")
ALLOWED_STRATEGIES = (
    "baseline_unknown",
    "first_legal_play",
    "reduce_high_point_cards",
    "retain_special_or_wild_cards_until_needed",
)
ALLOWED_RESULTS = ("win", "loss", "draw", "unknown")
ALLOWED_PENDING_EFFECTS = (
    "none",
    "pick_two",
    "whot_shape_selection",
    "last_card_declaration",
    "last_card_catch",
    "suspension",
    "soko_la_wote",
    "auto_play",
    "unknown",
)
BANNED_FIELD_FRAGMENTS = (
    "password",
    "cookie",
    "token",
    "phone",
    "email",
    "user_id",
    "device_id",
    "session_id",
    "hidden_card",
    "raw_response",
    "request_body",
    "response_body",
)

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[2]
DEFAULT_DB = ROOT / "whot_samples_v2.sqlite3"
DEFAULT_RULESET = ROOT / "ruleset_observed_v1.json"
DEFAULT_RECEIPTS = ROOT.parent / "runs"
DEFAULT_MANUAL = ROOT.parent / "manual_observations.jsonl"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  run_started_at TEXT NOT NULL,
  run_ended_at TEXT,
  environment TEXT NOT NULL,
  host TEXT NOT NULL,
  browser_surface TEXT NOT NULL,
  game_id TEXT NOT NULL,
  ruleset_version TEXT NOT NULL,
  game_build TEXT NOT NULL,
  target_rounds INTEGER NOT NULL,
  status TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  CHECK (host = 'test-h5.wajew.com'),
  CHECK (browser_surface = 'external_chrome'),
  CHECK (game_id = '6001'),
  CHECK (target_rounds >= 0)
);

CREATE TABLE IF NOT EXISTS matches (
  match_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  round_seq INTEGER NOT NULL,
  observed_at TEXT NOT NULL,
  completed_at TEXT,
  environment TEXT NOT NULL,
  host TEXT NOT NULL,
  browser_surface TEXT NOT NULL,
  game_id TEXT NOT NULL,
  ruleset_version TEXT NOT NULL,
  game_build TEXT NOT NULL,
  strategy_arm TEXT NOT NULL,
  room_id TEXT,
  room_stake_displayed_units REAL,
  result TEXT NOT NULL,
  end_reason TEXT NOT NULL,
  player_points INTEGER,
  opponent_points INTEGER,
  player_cards_remaining INTEGER,
  opponent_cards_remaining INTEGER,
  displayed_settlement_delta REAL,
  opponent_displayed_settlement_delta REAL,
  gross_return REAL,
  fee REAL,
  net_delta REAL,
  balance_before REAL,
  balance_after REAL,
  settlement_visible INTEGER NOT NULL,
  human_turn_count INTEGER NOT NULL,
  opponent_turn_count INTEGER NOT NULL,
  auto_play_turn_count INTEGER NOT NULL,
  full_state_human_turn_count INTEGER NOT NULL,
  human_control_share REAL,
  turn_capture_coverage REAL,
  eligibility_status TEXT NOT NULL,
  quality_status TEXT NOT NULL,
  evidence_note TEXT,
  source_hash TEXT NOT NULL,
  UNIQUE (run_id, round_seq),
  CHECK (host = 'test-h5.wajew.com'),
  CHECK (browser_surface = 'external_chrome'),
  CHECK (game_id = '6001'),
  CHECK (strategy_arm IN ('baseline_unknown','first_legal_play','reduce_high_point_cards','retain_special_or_wild_cards_until_needed')),
  CHECK (result IN ('win','loss','draw','unknown')),
  CHECK (settlement_visible IN (0,1)),
  CHECK (human_turn_count >= 0),
  CHECK (opponent_turn_count >= 0),
  CHECK (auto_play_turn_count >= 0),
  CHECK (full_state_human_turn_count >= 0),
  CHECK (human_control_share IS NULL OR (human_control_share >= 0 AND human_control_share <= 1)),
  CHECK (turn_capture_coverage IS NULL OR (turn_capture_coverage >= 0 AND turn_capture_coverage <= 1))
);

CREATE TABLE IF NOT EXISTS turns (
  turn_id TEXT PRIMARY KEY,
  match_id TEXT NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
  event_seq INTEGER NOT NULL,
  observed_at TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  is_player_turn INTEGER,
  pending_effect TEXT NOT NULL,
  table_rank INTEGER,
  table_shape TEXT,
  hand_count_before INTEGER,
  legal_action_count INTEGER,
  action TEXT NOT NULL,
  chosen_rank INTEGER,
  chosen_shape TEXT,
  target_shape TEXT,
  decision_latency_ms INTEGER,
  policy_compute_ms INTEGER,
  action_accepted INTEGER,
  timeout_flag INTEGER,
  capture_confidence REAL,
  special_effect TEXT,
  opponent_visible_counts_json TEXT,
  note TEXT,
  source_hash TEXT NOT NULL,
  UNIQUE (match_id, event_seq),
  CHECK (actor_type IN ('human','bot','auto_play','unknown')),
  CHECK (is_player_turn IS NULL OR is_player_turn IN (0,1)),
  CHECK (pending_effect IN ('none','pick_two','whot_shape_selection','last_card_declaration','last_card_catch','suspension','soko_la_wote','auto_play','unknown')),
  CHECK (table_shape IS NULL OR table_shape IN ('circle','square','triangle','star','cross','wild')),
  CHECK (chosen_shape IS NULL OR chosen_shape IN ('circle','square','triangle','star','cross','wild')),
  CHECK (target_shape IS NULL OR target_shape IN ('circle','square','triangle','star','cross')),
  CHECK (action IN ('play','draw','declare_last_card','catch_last_card','select_shape','resume_control','wait','rescan','unresolved_turn','unknown')),
  CHECK (timeout_flag IS NULL OR timeout_flag IN (0,1)),
  CHECK (action_accepted IS NULL OR action_accepted IN (0,1)),
  CHECK (capture_confidence IS NULL OR (capture_confidence >= 0 AND capture_confidence <= 1))
);

CREATE TABLE IF NOT EXISTS special_events (
  event_id TEXT PRIMARY KEY,
  match_id TEXT NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
  event_seq INTEGER NOT NULL,
  observed_at TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  event_type TEXT NOT NULL,
  state TEXT NOT NULL,
  latency_ms INTEGER,
  result TEXT,
  note TEXT,
  source_hash TEXT NOT NULL,
  UNIQUE (match_id, event_seq, event_type)
);

CREATE TABLE IF NOT EXISTS policy_decisions (
  decision_id TEXT PRIMARY KEY,
  match_id TEXT REFERENCES matches(match_id) ON DELETE SET NULL,
  turn_id TEXT REFERENCES turns(turn_id) ON DELETE SET NULL,
  policy_version TEXT NOT NULL,
  ruleset_version TEXT NOT NULL,
  strategy_arm TEXT NOT NULL,
  action TEXT NOT NULL,
  chosen_rank INTEGER,
  chosen_shape TEXT,
  target_shape TEXT,
  reason_codes_json TEXT NOT NULL,
  legal_action_count INTEGER,
  capture_confidence REAL,
  policy_compute_ms INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_lineage (
  lineage_id TEXT PRIMARY KEY,
  match_id TEXT NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
  source_path TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  source_line INTEGER NOT NULL,
  source_hash TEXT NOT NULL,
  ingested_at TEXT NOT NULL,
  UNIQUE (source_path, source_line)
);

CREATE TABLE IF NOT EXISTS strategy_evaluations (
  evaluation_id TEXT PRIMARY KEY,
  computed_at TEXT NOT NULL,
  data_scope TEXT NOT NULL,
  ruleset_version TEXT NOT NULL,
  room_stake_displayed_units REAL,
  strategy_arm TEXT NOT NULL,
  sample_count INTEGER NOT NULL,
  win_count INTEGER NOT NULL,
  loss_count INTEGER NOT NULL,
  draw_count INTEGER NOT NULL,
  win_rate REAL,
  wilson_lower_95 REAL,
  wilson_upper_95 REAL,
  settlement_coverage REAL,
  turn_capture_coverage REAL,
  auto_play_rate REAL,
  decision_latency_p95_ms REAL,
  eligible_for_selection INTEGER NOT NULL,
  notes TEXT NOT NULL,
  CHECK (eligible_for_selection IN (0,1))
);

CREATE TABLE IF NOT EXISTS experiment_schedule (
  schedule_id TEXT PRIMARY KEY,
  ordinal INTEGER NOT NULL UNIQUE,
  strategy_arm TEXT NOT NULL,
  status TEXT NOT NULL,
  assigned_match_id TEXT REFERENCES matches(match_id),
  created_at TEXT NOT NULL,
  CHECK (strategy_arm IN ('first_legal_play','reduce_high_point_cards','retain_special_or_wild_cards_until_needed')),
  CHECK (status IN ('pending','completed','invalid','skipped'))
);

CREATE INDEX IF NOT EXISTS idx_matches_result ON matches(result, eligibility_status);
CREATE INDEX IF NOT EXISTS idx_matches_strategy ON matches(strategy_arm, room_stake_displayed_units);
CREATE INDEX IF NOT EXISTS idx_turns_match_seq ON turns(match_id, event_seq);
CREATE INDEX IF NOT EXISTS idx_turns_actor ON turns(actor_type, timeout_flag);
CREATE INDEX IF NOT EXISTS idx_events_type ON special_events(event_type, state);
"""


@dataclass
class IngestStats:
    read: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    rejected: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "read": self.read,
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "rejected": self.rejected,
        }

    def add(self, other: "IngestStats") -> None:
        for field in ("read", "inserted", "updated", "skipped", "rejected"):
            setattr(self, field, getattr(self, field) + getattr(other, field))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def reject_sensitive_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower()
            if any(fragment in normalized for fragment in BANNED_FIELD_FRAGMENTS):
                raise ValueError(f"sensitive_field_rejected:{path}.{key}")
            reject_sensitive_fields(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            reject_sensitive_fields(nested, f"{path}[{index}]")


def project_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.name


def parse_run_timestamp(run_id: str) -> str:
    match = re.search(r"(20\d{6}T\d{6}Z)", run_id)
    if not match:
        return utc_now()
    parsed = datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def coerce_int(value: Any) -> int | None:
    number = coerce_float(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def percentile(values: Sequence[float], proportion: float) -> float | None:
    cleaned = sorted(float(value) for value in values if value is not None)
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned[0]
    rank = (len(cleaned) - 1) * proportion
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return cleaned[lower]
    weight = rank - lower
    return cleaned[lower] * (1 - weight) + cleaned[upper] * weight


def wilson_interval(wins: int, total: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None
    rate = wins / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    half = z * math.sqrt((rate * (1 - rate) + z * z / (4 * total)) / total) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def init_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    connection.execute(
        "INSERT INTO metadata(key,value) VALUES('schema_version',?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (SCHEMA_VERSION,),
    )
    connection.execute(
        "INSERT INTO metadata(key,value) VALUES('policy_mode','frozen_controlled_experiment') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
    )
    connection.commit()
    return connection


def open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def canonical_strategy(run_id: str, receipt: dict[str, Any], row: dict[str, Any]) -> str:
    if "normal-player" in run_id or "restart-normal" in run_id:
        return "baseline_unknown"
    raw = row.get("strategy_arm") or receipt.get("strategy")
    if raw == "reduce_high_point_cards_with_5_second_turn_target":
        return "reduce_high_point_cards"
    if raw in ALLOWED_STRATEGIES:
        return str(raw)
    return "baseline_unknown"


def run_row(run_id: str, receipt: dict[str, Any], source_hash: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "run_started_at": receipt.get("run_at") or parse_run_timestamp(run_id),
        "run_ended_at": None,
        "environment": receipt.get("environment") or "test_h5",
        "host": ALLOWED_HOST,
        "browser_surface": ALLOWED_BROWSER_SURFACE,
        "game_id": ALLOWED_GAME_ID,
        "ruleset_version": DEFAULT_RULESET_VERSION,
        "game_build": "unknown",
        "target_rounds": int(receipt.get("round_target") or receipt.get("target", {}).get("requested_rounds") or 100),
        "status": str(receipt.get("status") or "unknown"),
        "source_hash": source_hash,
    }


def upsert_row(
    connection: sqlite3.Connection,
    table: str,
    key_field: str,
    row: dict[str, Any],
) -> str:
    key = row[key_field]
    existing = connection.execute(
        f"SELECT source_hash FROM {table} WHERE {key_field}=?", (key,)
    ).fetchone()
    if existing is None:
        columns = ",".join(row)
        placeholders = ",".join("?" for _ in row)
        connection.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(row.values())
        )
        return "inserted"
    if existing["source_hash"] == row["source_hash"]:
        return "skipped"
    assignments = ",".join(f"{column}=?" for column in row if column != key_field)
    values = [row[column] for column in row if column != key_field]
    connection.execute(
        f"UPDATE {table} SET {assignments} WHERE {key_field}=?", (*values, key)
    )
    return "updated"


def increment(stats: IngestStats, action: str) -> None:
    if action not in {"inserted", "updated", "skipped"}:
        raise ValueError(f"Unsupported ingest action: {action}")
    setattr(stats, action, getattr(stats, action) + 1)


def validate_match_scope(row: dict[str, Any]) -> None:
    if row["host"] != ALLOWED_HOST:
        raise ValueError("host_not_allowed")
    if row["game_id"] != ALLOWED_GAME_ID:
        raise ValueError("game_not_allowed")
    if row["browser_surface"] != ALLOWED_BROWSER_SURFACE:
        raise ValueError("browser_surface_not_allowed")
    if row["strategy_arm"] not in ALLOWED_STRATEGIES:
        raise ValueError("strategy_not_allowed")
    if row["result"] not in ALLOWED_RESULTS:
        raise ValueError("result_not_allowed")


def match_identifier(source_path: str, run_id: str, round_seq: int) -> str:
    return f"match_{stable_hash(f'{source_path}|{run_id}|{round_seq}')[:20]}"


def turn_identifier(match_id: str, event_seq: int) -> str:
    return f"turn_{stable_hash(f'{match_id}|{event_seq}')[:20]}"


def lineage_identifier(source_path: str, source_line: int) -> str:
    return f"lineage_{stable_hash(f'{source_path}|{source_line}')[:20]}"


def infer_eligibility(
    strategy_arm: str,
    result: str,
    settlement_visible: bool,
    stake: float | None,
    turns: list[dict[str, Any]],
) -> tuple[str, float | None, float | None]:
    human = [turn for turn in turns if turn.get("actor_type") == "human"]
    auto = [turn for turn in turns if turn.get("actor_type") == "auto_play"]
    denominator = len(human) + len(auto)
    human_control_share = len(human) / denominator if denominator else None
    fully_captured = [
        turn
        for turn in human
        if all(
            turn.get(field) is not None
            for field in (
                "table_rank",
                "table_shape",
                "hand_count_before",
                "legal_card_count",
                "decision_ms",
            )
        )
    ]
    coverage = len(fully_captured) / len(human) if human else 0.0
    if result not in {"win", "loss", "draw"}:
        return "incomplete", human_control_share, coverage
    if not settlement_visible:
        return "incomplete_settlement", human_control_share, coverage
    if strategy_arm == "baseline_unknown":
        return "baseline_unknown", human_control_share, coverage
    if stake is None:
        return "missing_stake", human_control_share, coverage
    if auto:
        return "mixed_auto_play", human_control_share, coverage
    if not human or coverage < 0.95:
        return "partial_turn_capture", human_control_share, coverage
    return "eligible_controlled", human_control_share, coverage


def normalize_turn(
    match_id: str,
    event_seq: int,
    turn: dict[str, Any],
    observed_at: str,
    source_hash: str,
) -> dict[str, Any]:
    actor = str(turn.get("actor_type") or "unknown")
    pending = str(turn.get("pending_effect") or "unknown")
    if pending not in ALLOWED_PENDING_EFFECTS:
        pending = "unknown"
    special = turn.get("special_effect")
    if pending == "unknown" and special in ALLOWED_PENDING_EFFECTS:
        pending = str(special)
    return {
        "turn_id": turn_identifier(match_id, event_seq),
        "match_id": match_id,
        "event_seq": event_seq,
        "observed_at": turn.get("observed_at") or observed_at,
        "actor_type": actor if actor in {"human", "bot", "auto_play", "unknown"} else "unknown",
        "is_player_turn": None if turn.get("is_player_turn") is None else int(bool(turn.get("is_player_turn"))),
        "pending_effect": pending,
        "table_rank": coerce_int(turn.get("table_rank")),
        "table_shape": turn.get("table_shape"),
        "hand_count_before": coerce_int(turn.get("hand_count_before")),
        "legal_action_count": coerce_int(turn.get("legal_card_count")),
        "action": str(turn.get("action") or "unknown"),
        "chosen_rank": coerce_int(turn.get("chosen_rank")),
        "chosen_shape": turn.get("chosen_shape"),
        "target_shape": turn.get("target_shape"),
        "decision_latency_ms": coerce_int(turn.get("decision_ms")),
        "policy_compute_ms": coerce_int(turn.get("policy_compute_ms")),
        "action_accepted": None if turn.get("action_accepted") is None else int(bool(turn.get("action_accepted"))),
        "timeout_flag": None if turn.get("timeout_flag") is None else int(bool(turn.get("timeout_flag"))),
        "capture_confidence": coerce_float(turn.get("capture_confidence")),
        "special_effect": special,
        "opponent_visible_counts_json": canonical_json(
            turn.get("opponent_visible_card_counts")
            if turn.get("opponent_visible_card_counts") is not None
            else ([turn.get("visible_opponent_card_count")] if turn.get("visible_opponent_card_count") is not None else [])
        ),
        "note": turn.get("note"),
        "source_hash": source_hash,
    }


def ingest_match(
    connection: sqlite3.Connection,
    run: dict[str, Any],
    raw_match: dict[str, Any],
    source_path: str,
    source_kind: str,
    source_line: int,
    source_hash: str,
    stats: IngestStats,
) -> None:
    stats.read += 1
    try:
        run_action = upsert_row(connection, "runs", "run_id", run)
        if run_action == "inserted":
            pass
        round_seq = int(raw_match.get("round_no") or raw_match.get("round_seq") or 0)
        match_id = match_identifier(source_path, run["run_id"], round_seq)
        observed_at = raw_match.get("observed_at") or run["run_started_at"]
        strategy = canonical_strategy(run["run_id"], raw_match.get("_receipt", {}), raw_match)
        turns_raw = list(raw_match.get("turns") or [])
        stake = coerce_float(raw_match.get("room_stake_displayed_units", raw_match.get("stake_displayed_units")))
        result = str(raw_match.get("result") or "unknown")
        settlement = raw_match.get("player_settlement_displayed_units", raw_match.get("settlement_displayed_units"))
        settlement_visible = bool(raw_match.get("settlement_visible", settlement is not None))
        eligibility, human_share, coverage = infer_eligibility(
            strategy, result, settlement_visible, stake, turns_raw
        )
        human_count = sum(turn.get("actor_type") == "human" for turn in turns_raw)
        opponent_count = sum(turn.get("actor_type") == "bot" for turn in turns_raw)
        auto_count = sum(turn.get("actor_type") == "auto_play" for turn in turns_raw)
        full_count = sum(
            turn.get("actor_type") == "human"
            and all(
                turn.get(field) is not None
                for field in ("table_rank", "table_shape", "hand_count_before", "legal_card_count", "decision_ms")
            )
            for turn in turns_raw
        )
        row = {
            "match_id": match_id,
            "run_id": run["run_id"],
            "round_seq": round_seq,
            "observed_at": observed_at,
            "completed_at": observed_at if result in {"win", "loss", "draw"} else None,
            "environment": run["environment"],
            "host": run["host"],
            "browser_surface": run["browser_surface"],
            "game_id": run["game_id"],
            "ruleset_version": run["ruleset_version"],
            "game_build": run["game_build"],
            "strategy_arm": strategy,
            "room_id": raw_match.get("room_id"),
            "room_stake_displayed_units": stake,
            "result": result,
            "end_reason": str(raw_match.get("end_reason") or "unknown"),
            "player_points": coerce_int(raw_match.get("player_points", raw_match.get("player_points_at_settlement"))),
            "opponent_points": coerce_int(raw_match.get("opponent_points", raw_match.get("opponent_points_at_settlement"))),
            "player_cards_remaining": coerce_int(raw_match.get("player_cards_remaining")),
            "opponent_cards_remaining": coerce_int(raw_match.get("opponent_cards_remaining")),
            "displayed_settlement_delta": coerce_float(settlement),
            "opponent_displayed_settlement_delta": coerce_float(
                raw_match.get("opponent_settlement_displayed_units")
            ),
            "gross_return": None,
            "fee": None,
            "net_delta": None,
            "balance_before": coerce_float(raw_match.get("balance_before_displayed_units")),
            "balance_after": coerce_float(raw_match.get("balance_after_displayed_units")),
            "settlement_visible": int(settlement_visible),
            "human_turn_count": human_count,
            "opponent_turn_count": opponent_count,
            "auto_play_turn_count": auto_count,
            "full_state_human_turn_count": full_count,
            "human_control_share": human_share,
            "turn_capture_coverage": coverage,
            "eligibility_status": eligibility,
            "quality_status": str(raw_match.get("quality_status") or "observed_only"),
            "evidence_note": raw_match.get("evidence_note", raw_match.get("evidence")),
            "source_hash": source_hash,
        }
        validate_match_scope(row)
        action = upsert_row(connection, "matches", "match_id", row)
        increment(stats, action)

        if action == "updated":
            connection.execute("DELETE FROM turns WHERE match_id=?", (match_id,))
            connection.execute("DELETE FROM special_events WHERE match_id=?", (match_id,))

        existing_turns = connection.execute(
            "SELECT COUNT(*) FROM turns WHERE match_id=?", (match_id,)
        ).fetchone()[0]
        if action != "skipped" or existing_turns == 0:
            for index, turn in enumerate(turns_raw, start=1):
                event_seq = int(turn.get("event_seq") or turn.get("turn_no") or index)
                normalized = normalize_turn(match_id, event_seq, turn, observed_at, source_hash)
                columns = ",".join(normalized)
                placeholders = ",".join("?" for _ in normalized)
                connection.execute(
                    f"INSERT OR REPLACE INTO turns ({columns}) VALUES ({placeholders})",
                    tuple(normalized.values()),
                )
                if normalized["special_effect"]:
                    event_key = f"{match_id}|{event_seq}|{normalized['special_effect']}"
                    event_id = f"event_{stable_hash(event_key)[:20]}"
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO special_events(
                          event_id,match_id,event_seq,observed_at,actor_type,event_type,state,
                          latency_ms,result,note,source_hash
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            event_id,
                            match_id,
                            event_seq,
                            normalized["observed_at"],
                            normalized["actor_type"],
                            normalized["special_effect"],
                            "observed",
                            normalized["decision_latency_ms"],
                            None,
                            normalized["note"],
                            source_hash,
                        ),
                    )

        lineage = {
            "lineage_id": lineage_identifier(source_path, source_line),
            "match_id": match_id,
            "source_path": source_path,
            "source_kind": source_kind,
            "source_line": source_line,
            "source_hash": source_hash,
            "ingested_at": utc_now(),
        }
        existing_lineage = connection.execute(
            "SELECT source_hash FROM source_lineage WHERE lineage_id=?",
            (lineage["lineage_id"],),
        ).fetchone()
        if existing_lineage is None:
            connection.execute(
                "INSERT INTO source_lineage VALUES(?,?,?,?,?,?,?)", tuple(lineage.values())
            )
        elif existing_lineage["source_hash"] != source_hash:
            connection.execute(
                """
                UPDATE source_lineage SET match_id=?,source_path=?,source_kind=?,source_line=?,
                  source_hash=?,ingested_at=? WHERE lineage_id=?
                """,
                (
                    match_id,
                    source_path,
                    source_kind,
                    source_line,
                    source_hash,
                    lineage["ingested_at"],
                    lineage["lineage_id"],
                ),
            )
    except Exception:
        stats.rejected += 1
        raise


def migrate_sources(connection: sqlite3.Connection, receipts: Path, manual: Path) -> IngestStats:
    stats = IngestStats()
    with connection:
        for receipt_path in sorted(receipts.glob("*/run_receipt.json")):
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            rounds = receipt.get("rounds")
            if not isinstance(rounds, list):
                continue
            source_path = project_relative(receipt_path)
            receipt_hash = file_hash(receipt_path)
            run_id = str(receipt.get("run_id") or receipt_path.parent.name)
            run = run_row(run_id, receipt, receipt_hash)
            for line_no, round_row in enumerate(rounds, start=1):
                if not isinstance(round_row, dict):
                    stats.read += 1
                    stats.rejected += 1
                    continue
                raw = dict(round_row)
                raw["_receipt"] = receipt
                source_hash = stable_hash(receipt_hash + canonical_json(round_row))
                try:
                    reject_sensitive_fields(round_row)
                    ingest_match(
                        connection,
                        run,
                        raw,
                        source_path,
                        "run_receipt",
                        line_no,
                        source_hash,
                        stats,
                    )
                except Exception:
                    continue

        if manual.exists():
            manual_file_hash = file_hash(manual)
            source_path = project_relative(manual)
            for line_no, line in enumerate(manual.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                try:
                    raw = json.loads(line)
                    if not isinstance(raw, dict):
                        raise ValueError("manual_observation_not_object")
                    reject_sensitive_fields(raw)
                    run_id = str(raw.get("run_id") or "manual-observation")
                    receipt = {
                        "run_id": run_id,
                        "status": "in_progress",
                        "environment": raw.get("environment") or "test_h5",
                        "round_target": 100,
                    }
                    run = run_row(run_id, receipt, manual_file_hash)
                    raw["_receipt"] = receipt
                    source_hash = stable_hash(manual_file_hash + line)
                except Exception:
                    stats.read += 1
                    stats.rejected += 1
                    continue
                try:
                    ingest_match(
                        connection,
                        run,
                        raw,
                        source_path,
                        "manual_jsonl",
                        line_no,
                        source_hash,
                        stats,
                    )
                except Exception:
                    continue
    return stats


def record_live_observation(connection: sqlite3.Connection, input_path: Path) -> IngestStats:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    reject_sensitive_fields(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get("match"), dict):
        raise ValueError("live_observation_requires_match_object")
    run_payload = payload.get("run") if isinstance(payload.get("run"), dict) else {}
    raw_match = dict(payload["match"])
    run_id = str(run_payload.get("run_id") or raw_match.get("run_id") or "")
    if not run_id:
        raise ValueError("live_observation_requires_run_id")
    run_payload = {
        **run_payload,
        "run_id": run_id,
        "status": run_payload.get("status") or "in_progress",
        "environment": run_payload.get("environment") or "test_h5",
        "round_target": run_payload.get("round_target") or 100,
    }
    source_path = project_relative(input_path)
    source_hash = file_hash(input_path)
    run = run_row(run_id, run_payload, source_hash)
    raw_match["_receipt"] = run_payload
    stats = IngestStats()
    with connection:
        ingest_match(
            connection,
            run,
            raw_match,
            source_path,
            "live_observation",
            1,
            source_hash,
            stats,
        )
    return stats


def load_ruleset(path: Path = DEFAULT_RULESET) -> dict[str, Any]:
    rules = json.loads(path.read_text(encoding="utf-8"))
    if rules.get("ruleset_version") != DEFAULT_RULESET_VERSION:
        raise ValueError("ruleset_version_mismatch")
    return rules


def validate_browser_gate(state: dict[str, Any]) -> dict[str, Any]:
    surface = str(state.get("browser_surface") or "unknown")
    current_url = str(state.get("current_url") or "")
    entry_method = str(state.get("entry_method") or "unknown")
    parsed = urlparse(current_url)
    reasons: list[str] = []
    if surface != ALLOWED_BROWSER_SURFACE:
        reasons.append("browser_surface_not_external_chrome")
    if parsed.hostname != ALLOWED_HOST:
        reasons.append("host_not_allowed")
    if entry_method not in {"site_home_card_6001", "site_search_whot", "existing_game_tab"}:
        reasons.append("entry_method_not_allowed")
    if parsed.path.startswith("/game/") and parsed.path != "/game/6001-whot":
        reasons.append("game_path_not_whot_6001")
    phase = "game" if parsed.path == "/game/6001-whot" else "lobby" if parsed.path in {"", "/"} else "unknown"
    if phase == "unknown":
        reasons.append("page_phase_not_allowed")
    return {
        "status": "passed" if not reasons else "blocked",
        "allowed": not reasons,
        "phase": phase,
        "host": parsed.hostname,
        "path": parsed.path,
        "reasons": reasons,
    }


def normalize_card(card: dict[str, Any]) -> dict[str, Any]:
    rank = coerce_int(card.get("rank"))
    shape = card.get("shape")
    if rank not in {*range(1, 15), 20}:
        raise ValueError("invalid_card_rank")
    if shape not in {*ALLOWED_SHAPES, "wild"}:
        raise ValueError("invalid_card_shape")
    return {"rank": rank, "shape": shape}


def legal_actions(hand: Sequence[dict[str, Any]], table_card: dict[str, Any]) -> list[dict[str, Any]]:
    table = normalize_card(table_card)
    actions: list[dict[str, Any]] = []
    for index, raw_card in enumerate(hand):
        card = normalize_card(raw_card)
        if card["rank"] == 20 or card["rank"] == table["rank"] or card["shape"] == table["shape"]:
            actions.append({"index": index, **card})
    return actions


def choose_target_shape(hand: Sequence[dict[str, Any]], excluded_index: int | None = None) -> str:
    counts = {shape: 0 for shape in ALLOWED_SHAPES}
    for index, raw in enumerate(hand):
        if excluded_index is not None and index == excluded_index:
            continue
        card = normalize_card(raw)
        if card["shape"] in counts:
            counts[card["shape"]] += 1
    return max(ALLOWED_SHAPES, key=lambda shape: (counts[shape], -ALLOWED_SHAPES.index(shape)))


def recommend_action(
    state: dict[str, Any],
    strategy_arm: str,
    ruleset_path: Path = DEFAULT_RULESET,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    rules = load_ruleset(ruleset_path)
    if strategy_arm not in ALLOWED_STRATEGIES or strategy_arm == "baseline_unknown":
        raise ValueError("explicit_controlled_strategy_required")
    confidence = coerce_float(state.get("capture_confidence"))
    confidence = 0.0 if confidence is None else confidence
    rescan_count = coerce_int(state.get("rescan_count")) or 0
    common = {
        "policy_version": POLICY_VERSION,
        "ruleset_version": rules["ruleset_version"],
        "strategy_arm": strategy_arm,
        "capture_confidence": confidence,
    }

    if confidence < float(rules["minimum_capture_confidence"]):
        action = "rescan" if rescan_count < 1 else "unresolved_turn"
        reason = "capture_confidence_below_threshold"
        return finalize_decision(common, action, reason, started)

    pending = str(state.get("pending_effect") or "none")
    if pending not in ALLOWED_PENDING_EFFECTS:
        pending = "unknown"
    if pending == "auto_play":
        return finalize_decision(common, "resume_control", "auto_play_overlay_visible", started)
    if pending == "pick_two":
        return finalize_decision(common, "draw", "mandatory_pick_two", started, draw_count=2)
    if pending == "whot_shape_selection":
        hand = list(state.get("visible_hand") or [])
        target = choose_target_shape(hand)
        return finalize_decision(common, "select_shape", "whot_shape_required", started, target_shape=target)
    if pending == "last_card_declaration":
        return finalize_decision(common, "declare_last_card", "last_card_declaration_required", started)
    if pending == "last_card_catch":
        return finalize_decision(common, "catch_last_card", "last_card_catch_window", started)
    if pending in {"suspension", "soko_la_wote"}:
        return finalize_decision(common, "wait", f"special_resolution_{pending}", started)
    if pending == "unknown":
        return finalize_decision(common, "unresolved_turn", "unknown_pending_effect", started)
    if state.get("is_player_turn") is not True:
        return finalize_decision(common, "wait", "not_player_turn", started)

    hand = list(state.get("visible_hand") or [])
    table_card = state.get("table_card")
    if not hand or not isinstance(table_card, dict):
        return finalize_decision(common, "unresolved_turn", "missing_visible_state", started)
    candidates = legal_actions(hand, table_card)
    if not candidates:
        return finalize_decision(common, "draw", "no_legal_visible_card", started, legal_action_count=0)

    if strategy_arm == "first_legal_play":
        chosen = candidates[0]
        reason = "first_visible_legal"
    elif strategy_arm == "reduce_high_point_cards":
        non_wild = [candidate for candidate in candidates if candidate["rank"] != 20]
        pool = non_wild or candidates
        chosen = max(pool, key=lambda candidate: (candidate["rank"], -candidate["index"]))
        reason = "highest_visible_point_reduction"
    else:
        verified_special_ranks = set(rules["verified_special_ranks"])
        ordinary = [
            candidate
            for candidate in candidates
            if candidate["rank"] not in verified_special_ranks and candidate["rank"] != 20
        ]
        pool = ordinary or [candidate for candidate in candidates if candidate["rank"] != 20] or candidates
        chosen = max(pool, key=lambda candidate: (candidate["rank"], -candidate["index"]))
        reason = "retain_verified_special_or_wild_when_alternative_exists"

    target_shape = None
    if chosen["rank"] == 20:
        target_shape = choose_target_shape(hand, chosen["index"])
    return finalize_decision(
        common,
        "play",
        reason,
        started,
        chosen_card={"index": chosen["index"], "rank": chosen["rank"], "shape": chosen["shape"]},
        target_shape=target_shape,
        legal_action_count=len(candidates),
    )


def finalize_decision(
    common: dict[str, Any],
    action: str,
    reason: str,
    started: datetime,
    **extras: Any,
) -> dict[str, Any]:
    elapsed = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    return {
        **common,
        "action": action,
        "chosen_card": None,
        "target_shape": None,
        "reason_codes": [reason],
        "legal_action_count": None,
        "policy_compute_ms": elapsed,
        "execute_before_ms": 2200,
        **extras,
    }


def quality_summary(connection: sqlite3.Connection) -> dict[str, Any]:
    totals = connection.execute(
        """
        SELECT COUNT(*) AS observed,
               SUM(result IN ('win','loss','draw')) AS completed,
               SUM(result='win') AS wins,
               SUM(result='loss') AS losses,
               SUM(result='unknown') AS incomplete,
               SUM(settlement_visible) AS settlement_visible,
               SUM(eligibility_status='eligible_controlled') AS eligible_controlled
        FROM matches
        """
    ).fetchone()
    turns = connection.execute(
        """
        SELECT COUNT(*) AS turns,
               SUM(actor_type IN ('bot','auto_play')) AS robot_or_auto,
               SUM(actor_type='human') AS human,
               SUM(actor_type='human' AND table_rank IS NOT NULL AND table_shape IS NOT NULL
                   AND hand_count_before IS NOT NULL AND legal_action_count IS NOT NULL
                   AND decision_latency_ms IS NOT NULL) AS full_human,
               SUM(actor_type='human' AND timeout_flag IS NULL) AS timeout_unknown
        FROM turns
        """
    ).fetchone()
    completed = int(totals["completed"] or 0)
    wins = int(totals["wins"] or 0)
    lower, upper = wilson_interval(wins, completed)
    duplicate_count = connection.execute(
        "SELECT COUNT(*) FROM (SELECT run_id,round_seq,COUNT(*) c FROM matches GROUP BY run_id,round_seq HAVING c>1)"
    ).fetchone()[0]
    mislabeled_baseline = connection.execute(
        """
        SELECT COUNT(*) FROM matches
        WHERE (run_id LIKE '%normal-player%' OR run_id LIKE '%restart-normal%')
          AND strategy_arm <> 'baseline_unknown'
        """
    ).fetchone()[0]
    checks = [
        {
            "id": "sqlite_integrity",
            "status": connection.execute("PRAGMA integrity_check").fetchone()[0],
            "severity": "critical",
            "evidence": "SQLite integrity_check",
        },
        {
            "id": "unique_match_key",
            "status": "passed" if duplicate_count == 0 else "failed",
            "severity": "critical",
            "evidence": {"duplicate_keys": duplicate_count},
        },
        {
            "id": "strategy_label_certification",
            "status": "passed" if mislabeled_baseline == 0 else "failed",
            "severity": "high",
            "evidence": {
                "historical_baseline_mislabeled": int(mislabeled_baseline),
                "policy": "Historical baseline is retained as baseline_unknown",
            },
        },
        {
            "id": "turn_context_coverage",
            "status": "failed" if int(turns["full_human"] or 0) == 0 else "partial",
            "severity": "high",
            "evidence": {
                "human_turns": int(turns["human"] or 0),
                "full_context_human_turns": int(turns["full_human"] or 0),
            },
        },
        {
            "id": "timeout_measurement",
            "status": "failed" if int(turns["timeout_unknown"] or 0) else "passed",
            "severity": "high",
            "evidence": {"human_turns_with_unknown_timeout": int(turns["timeout_unknown"] or 0)},
        },
        {
            "id": "rtp_definition",
            "status": "blocked",
            "severity": "high",
            "evidence": "gross_return, fee and reconciled net_delta are unavailable",
        },
    ]
    return {
        "status": "needs_revision",
        "as_of": utc_now(),
        "scope": "test-h5.wajew.com / WHOT 6001 / local exploratory evidence",
        "matches": {
            "observed": int(totals["observed"] or 0),
            "completed": completed,
            "wins": wins,
            "losses": int(totals["losses"] or 0),
            "incomplete": int(totals["incomplete"] or 0),
            "win_rate": wins / completed if completed else None,
            "wilson_95_lower": lower,
            "wilson_95_upper": upper,
            "settlement_visible": int(totals["settlement_visible"] or 0),
            "eligible_controlled": int(totals["eligible_controlled"] or 0),
        },
        "turns": {
            "total": int(turns["turns"] or 0),
            "human": int(turns["human"] or 0),
            "robot_or_auto": int(turns["robot_or_auto"] or 0),
            "full_context_human": int(turns["full_human"] or 0),
            "timeout_unknown": int(turns["timeout_unknown"] or 0),
        },
        "checks": checks,
    }


def recompute_evaluations(connection: sqlite3.Connection) -> dict[str, Any]:
    computed_at = utc_now()
    with connection:
        connection.execute("DELETE FROM strategy_evaluations")
        groups = connection.execute(
            """
            SELECT strategy_arm,room_stake_displayed_units,
                   COUNT(*) AS n,
                   SUM(result='win') AS wins,
                   SUM(result='loss') AS losses,
                   SUM(result='draw') AS draws,
                   AVG(settlement_visible) AS settlement_coverage,
                   AVG(turn_capture_coverage) AS turn_coverage,
                   AVG(CASE WHEN auto_play_turn_count>0 THEN 1.0 ELSE 0.0 END) AS auto_play_rate
            FROM matches
            WHERE result IN ('win','loss','draw')
            GROUP BY strategy_arm,room_stake_displayed_units
            ORDER BY strategy_arm,room_stake_displayed_units
            """
        ).fetchall()
        inserted = 0
        for row in groups:
            n = int(row["n"] or 0)
            wins = int(row["wins"] or 0)
            lower, upper = wilson_interval(wins, n)
            latencies = [
                result[0]
                for result in connection.execute(
                    """
                    SELECT t.decision_latency_ms FROM turns t JOIN matches m ON m.match_id=t.match_id
                    WHERE m.strategy_arm=? AND m.room_stake_displayed_units IS ?
                      AND t.actor_type='human' AND t.decision_latency_ms IS NOT NULL
                    """,
                    (row["strategy_arm"], row["room_stake_displayed_units"]),
                ).fetchall()
            ]
            latency_p95 = percentile(latencies, 0.95)
            settlement_coverage = float(row["settlement_coverage"] or 0.0)
            turn_coverage = float(row["turn_coverage"] or 0.0)
            auto_rate = float(row["auto_play_rate"] or 0.0)
            eligible = (
                row["strategy_arm"] != "baseline_unknown"
                and n >= 25
                and settlement_coverage >= 0.95
                and turn_coverage >= 0.95
                and auto_rate == 0.0
                and latency_p95 is not None
                and latency_p95 <= 2000
            )
            evaluation_id = f"eval_{stable_hash(canonical_json([computed_at, *list(row)]))[:20]}"
            notes = (
                "Eligible for controlled comparison"
                if eligible
                else "Exploratory only: one or more sample, coverage, auto-play, stake, or latency gates failed"
            )
            connection.execute(
                """
                INSERT INTO strategy_evaluations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    evaluation_id,
                    computed_at,
                    "exploratory_all_completed",
                    DEFAULT_RULESET_VERSION,
                    row["room_stake_displayed_units"],
                    row["strategy_arm"],
                    n,
                    wins,
                    int(row["losses"] or 0),
                    int(row["draws"] or 0),
                    wins / n if n else None,
                    lower,
                    upper,
                    settlement_coverage,
                    turn_coverage,
                    auto_rate,
                    latency_p95,
                    int(eligible),
                    notes,
                ),
            )
            inserted += 1
    return {"computed_at": computed_at, "evaluations": inserted}


def generate_schedule(count: int = 77) -> list[dict[str, Any]]:
    arms = [
        "first_legal_play",
        "reduce_high_point_cards",
        "retain_special_or_wild_cards_until_needed",
    ]
    schedule: list[dict[str, Any]] = []
    complete_blocks = count // 3
    for block in range(complete_blocks):
        rotation = block % 3
        block_arms = arms[rotation:] + arms[:rotation]
        for arm in block_arms:
            ordinal = len(schedule) + 1
            schedule.append(
                {
                    "schedule_id": f"schedule_{ordinal:03d}",
                    "ordinal": ordinal,
                    "strategy_arm": arm,
                    "status": "pending",
                    "assigned_match_id": None,
                }
            )
    for arm in arms[: count - len(schedule)]:
        ordinal = len(schedule) + 1
        schedule.append(
            {
                "schedule_id": f"schedule_{ordinal:03d}",
                "ordinal": ordinal,
                "strategy_arm": arm,
                "status": "pending",
                "assigned_match_id": None,
            }
        )
    return schedule


def persist_schedule(connection: sqlite3.Connection, schedule: list[dict[str, Any]]) -> None:
    with connection:
        connection.execute("DELETE FROM experiment_schedule WHERE status='pending'")
        created_at = utc_now()
        for row in schedule:
            connection.execute(
                "INSERT OR REPLACE INTO experiment_schedule VALUES(?,?,?,?,?,?)",
                (
                    row["schedule_id"],
                    row["ordinal"],
                    row["strategy_arm"],
                    row["status"],
                    row["assigned_match_id"],
                    created_at,
                ),
            )


def read_report(connection: sqlite3.Connection) -> dict[str, Any]:
    quality = quality_summary(connection)
    strategies = [dict(row) for row in connection.execute(
        """
        SELECT strategy_arm,room_stake_displayed_units AS stake,sample_count,win_count,
               loss_count,draw_count,win_rate,wilson_lower_95,wilson_upper_95,
               settlement_coverage,turn_capture_coverage,auto_play_rate,
               decision_latency_p95_ms,eligible_for_selection,notes
        FROM strategy_evaluations
        ORDER BY strategy_arm,stake
        """
    ).fetchall()]
    schedule_counts = [dict(row) for row in connection.execute(
        "SELECT strategy_arm,COUNT(*) AS planned FROM experiment_schedule GROUP BY strategy_arm ORDER BY strategy_arm"
    ).fetchall()]
    return {
        "schema_version": connection.execute(
            "SELECT value FROM metadata WHERE key='schema_version'"
        ).fetchone()[0],
        "quality": quality,
        "strategy_evaluations": strategies,
        "experiment_schedule": schedule_counts,
        "policy_selection": {
            "mode": "frozen_controlled_experiment",
            "selected_strategy": None,
            "reason": "No strategy passes the controlled-comparison gates",
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_summary_markdown(report: dict[str, Any]) -> str:
    match = report["quality"]["matches"]
    turns = report["quality"]["turns"]
    schedule = {row["strategy_arm"]: row["planned"] for row in report["experiment_schedule"]}
    return f"""# WHOT 测试与策略系统 V2 摘要

## 当前状态

- 观察局：{match['observed']}；完成局：{match['completed']}；未完成：{match['incomplete']}。
- 完成局胜负：{match['wins']} 胜、{match['losses']} 负；观察胜率 {match['win_rate']:.1%}。
- 95% Wilson 区间：{match['wilson_95_lower']:.1%}–{match['wilson_95_upper']:.1%}。
- 回合记录：{turns['total']}；机器人/托管观察：{turns['robot_or_auto']}。
- 合格受控策略样本：{match['eligible_controlled']}；当前策略自动选优保持冻结。

## 结论

现有数据可用于今日过程复盘，不足以认证最优策略、机器人智能水平或正式 RTP。历史基线已改为 `baseline_unknown`，缺失超时不再按 0 处理，不同下注档位不再混合比较。

## 后续 77 局计划

- `first_legal_play`：{schedule.get('first_legal_play', 0)} 局。
- `reduce_high_point_cards`：{schedule.get('reduce_high_point_cards', 0)} 局。
- `retain_special_or_wild_cards_until_needed`：{schedule.get('retain_special_or_wild_cards_until_needed', 0)} 局。

托管、URL 错误、结算缺失或规则不确定的局不计入受控样本，需补测。
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    migrate = sub.add_parser("migrate")
    migrate.add_argument("--receipts", type=Path, default=DEFAULT_RECEIPTS)
    migrate.add_argument("--manual", type=Path, default=DEFAULT_MANUAL)
    migrate.add_argument("--receipt-out", type=Path)
    record = sub.add_parser("record-live")
    record.add_argument("--input", type=Path, required=True)
    record.add_argument("--receipt-out", type=Path)
    sub.add_parser("recompute-metrics")
    quality = sub.add_parser("quality")
    quality.add_argument("--output", type=Path)
    report = sub.add_parser("report")
    report.add_argument("--output", type=Path)
    summary = sub.add_parser("render-summary")
    summary.add_argument("--output", type=Path, required=True)
    schedule = sub.add_parser("schedule")
    schedule.add_argument("--count", type=int, default=77)
    schedule.add_argument("--output", type=Path)
    recommend = sub.add_parser("recommend")
    recommend.add_argument("--strategy-arm", required=True, choices=ALLOWED_STRATEGIES[1:])
    recommend.add_argument("--state-json", required=True)
    recommend.add_argument("--ruleset", type=Path, default=DEFAULT_RULESET)
    gate = sub.add_parser("validate-gate")
    gate.add_argument("--state-json", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        connection = init_db(args.db)
        connection.close()
        print(canonical_json({"status": "ok", "db": str(args.db), "schema_version": SCHEMA_VERSION}))
        return 0
    if args.command == "migrate":
        connection = init_db(args.db)
        stats = migrate_sources(connection, args.receipts, args.manual)
        connection.close()
        payload = {
            "status": "ok" if stats.rejected == 0 else "quality_warning",
            "db": str(args.db),
            "schema_version": SCHEMA_VERSION,
            "inputs": {
                "receipts": project_relative(args.receipts),
                "manual": project_relative(args.manual),
            },
            "ingest": stats.as_dict(),
            "generated_at": utc_now(),
        }
        if args.receipt_out:
            write_json(args.receipt_out, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.command == "record-live":
        connection = init_db(args.db)
        stats = record_live_observation(connection, args.input)
        connection.close()
        payload = {
            "status": "ok" if stats.rejected == 0 else "quality_warning",
            "db": str(args.db),
            "input": project_relative(args.input),
            "ingest": stats.as_dict(),
            "generated_at": utc_now(),
        }
        if args.receipt_out:
            write_json(args.receipt_out, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.command == "recompute-metrics":
        connection = init_db(args.db)
        result = recompute_evaluations(connection)
        connection.close()
        print(json.dumps({"status": "ok", **result}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "schedule":
        if args.count <= 0:
            raise SystemExit("schedule count must be positive")
        schedule_rows = generate_schedule(args.count)
        connection = init_db(args.db)
        persist_schedule(connection, schedule_rows)
        connection.close()
        payload = {
            "status": "ok",
            "count": len(schedule_rows),
            "counts": {
                arm: sum(row["strategy_arm"] == arm for row in schedule_rows)
                for arm in ALLOWED_STRATEGIES[1:]
            },
            "schedule": schedule_rows,
        }
        if args.output:
            write_json(args.output, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.command == "recommend":
        state = json.loads(args.state_json)
        result = recommend_action(state, args.strategy_arm, args.ruleset)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "validate-gate":
        state = json.loads(args.state_json)
        result = validate_browser_gate(state)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["allowed"] else 2

    connection = open_readonly(args.db)
    if args.command == "quality":
        payload = quality_summary(connection)
        connection.close()
        if args.output:
            write_json(args.output, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.command == "report":
        payload = read_report(connection)
        connection.close()
        if args.output:
            write_json(args.output, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.command == "render-summary":
        payload = read_report(connection)
        connection.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_summary_markdown(payload), encoding="utf-8")
        print(canonical_json({"status": "ok", "output": str(args.output)}))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

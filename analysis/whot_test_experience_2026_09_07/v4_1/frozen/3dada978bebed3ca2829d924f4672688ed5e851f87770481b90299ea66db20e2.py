"""WHOT 6001 V3.2 controlled-test store and deterministic policy engine.

The module is deliberately browser-agnostic.  A Chrome/CUA adapter supplies
sanitised visible state; this file validates it, chooses a fixed policy action,
persists an append-only audit trail, and produces aggregate-only summaries.
It never accesses hidden cards, network responses, credentials, or account
operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sqlite3
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

GAME = "6001"
ORIGIN = "https://test-h5.wajetan.com"
ROUTE = "/game/6001-whot"
POLICY_VERSION = "legacy6001-policy-v4"
RULESET_VERSION = "6001-observed-v4"
ARMS = (
    "first_legal_play",
    "reduce_high_point_cards",
    "retain_special_or_wild_cards_until_needed",
)
BET_COUNTS = ((1, 20), (100, 20), (200, 20), (1000, 25), (5000, 15))
PLAYER_COUNTS = ((2, 60), (3, 20), (4, 20))
SENSITIVE_KEYS = {
    "password", "cookie", "token", "access_token", "device_id", "userid",
    "user_id", "email", "phone", "opponent_name", "hidden_cards",
    "deck_order", "network_response", "request_body", "response_body",
    "order_id", "payment_id", "kyc", "stack_trace", "url_query",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def reject_sensitive(value: object, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = str(key).lower().replace("-", "_")
            if key_l in SENSITIVE_KEYS or "access_token" in key_l:
                raise ValueError(f"forbidden_field:{path}.{key}")
            reject_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            reject_sensitive(child, f"{path}[{i}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"nonfinite_number:{path}")


def safe_route(url: str) -> bool:
    """Accept only the configured route and reject query-bearing URLs."""
    parts = urlsplit(url)
    return (parts.scheme == "https" and parts.netloc == "test-h5.wajetan.com"
            and parts.path == ROUTE and not parts.query and not parts.fragment)


def _schema() -> str:
    return """
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS runs(
      run_id TEXT PRIMARY KEY, game_id TEXT NOT NULL CHECK(game_id='6001'),
      origin TEXT NOT NULL, route TEXT NOT NULL, browser_surface TEXT NOT NULL,
      ruleset_version TEXT NOT NULL, controller_version TEXT NOT NULL,
      vision_profile_version TEXT NOT NULL, schedule_seed INTEGER NOT NULL,
      target_matches INTEGER NOT NULL, started_at TEXT NOT NULL,
      finished_at TEXT, status TEXT NOT NULL, source_hash TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS match_attempts(
      attempt_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
      requested_players INTEGER NOT NULL CHECK(requested_players IN (2,3,4)),
      bet_display REAL NOT NULL CHECK(bet_display>0), room_label TEXT,
      requested_at TEXT NOT NULL, ended_at TEXT, wait_ms REAL,
      actual_players INTEGER, human_count INTEGER, robot_count INTEGER,
      opponent_mix TEXT, terminal_reason TEXT, fallback_from_attempt_id TEXT,
      source_hash TEXT NOT NULL UNIQUE, quality_status TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS matches(
      match_id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL REFERENCES match_attempts(attempt_id),
      strategy_arm TEXT NOT NULL CHECK(strategy_arm IN ('first_legal_play','reduce_high_point_cards','retain_special_or_wild_cards_until_needed')),
      policy_version TEXT NOT NULL, control_source TEXT NOT NULL DEFAULT 'unknown',
      game_build TEXT, started_at TEXT NOT NULL,
      finished_at TEXT, result TEXT, end_reason TEXT, player_points INTEGER,
      opponent_points INTEGER, player_cards INTEGER, opponent_cards INTEGER,
      autoplay_observed INTEGER, manual_intervention INTEGER, qualified INTEGER,
      exclusion_reason TEXT, source_hash TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS turns(
      turn_id TEXT PRIMARY KEY, match_id TEXT NOT NULL REFERENCES matches(match_id),
      seq INTEGER NOT NULL, state_seq TEXT NOT NULL, phase TEXT NOT NULL,
      action_owner TEXT, table_rank INTEGER, table_shape TEXT,
      own_hand_count INTEGER, legal_action_count INTEGER, action TEXT,
      chosen_rank INTEGER, chosen_shape TEXT, target_shape TEXT,
      captured_at TEXT NOT NULL, submitted_at TEXT, confirmed_at TEXT,
      decision_ms REAL, click_latency_ms REAL, confirmation_ms REAL,
      accepted INTEGER, timeout INTEGER, capture_confidence REAL,
      source_hash TEXT NOT NULL UNIQUE, UNIQUE(match_id,seq)
    );
    CREATE TABLE IF NOT EXISTS special_events(
      event_id TEXT PRIMARY KEY, match_id TEXT NOT NULL REFERENCES matches(match_id),
      turn_id TEXT, kind TEXT NOT NULL, actor TEXT, status TEXT,
      observed_at TEXT NOT NULL, source_hash TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS settlements(
      settlement_id TEXT PRIMARY KEY, match_id TEXT NOT NULL UNIQUE REFERENCES matches(match_id),
      page_stake REAL, page_return REAL, page_net_change REAL,
      balance_before REAL, balance_after_debit REAL, balance_after REAL,
      fee REAL, bonus REAL, ledger_semantics_status TEXT NOT NULL,
      return_assumption TEXT NOT NULL, observed_at TEXT NOT NULL,
      source_hash TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS source_lineage(
      lineage_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
      source_path TEXT NOT NULL, source_line_no INTEGER, content_hash TEXT NOT NULL,
      created_at TEXT NOT NULL, UNIQUE(entity_type,entity_id,source_path,source_line_no)
    );
    CREATE TABLE IF NOT EXISTS strategy_evaluations(
      evaluation_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
      strategy_arm TEXT NOT NULL, bet_display REAL, actual_players INTEGER,
      attempts INTEGER NOT NULL, completed INTEGER NOT NULL, qualified INTEGER NOT NULL,
      wins INTEGER NOT NULL, losses INTEGER NOT NULL, win_rate REAL,
      wilson_low REAL, wilson_high REAL, provisional_rtp REAL,
      rtp_status TEXT NOT NULL, created_at TEXT NOT NULL,
      source_hash TEXT NOT NULL UNIQUE
    );
    CREATE INDEX IF NOT EXISTS idx_attempts_run ON match_attempts(run_id);
    CREATE INDEX IF NOT EXISTS idx_attempts_matrix ON match_attempts(bet_display,requested_players,terminal_reason);
    CREATE INDEX IF NOT EXISTS idx_matches_strategy ON matches(strategy_arm,result,qualified);
    CREATE INDEX IF NOT EXISTS idx_turns_match ON turns(match_id,seq);
    """


class Store:
    def __init__(self, path: Path, readonly: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        uri = f"file:{self.path}?mode=ro" if readonly else str(self.path)
        self.conn = sqlite3.connect(uri, uri=readonly)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        if not readonly:
            self.conn.executescript(_schema())
            self._migrate_schema()
            self.conn.commit()

    def _migrate_schema(self) -> None:
        """Apply additive migrations to databases created by V3.2 before control_source."""
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(matches)")}
        if "control_source" not in columns:
            self.conn.execute("ALTER TABLE matches ADD COLUMN control_source TEXT NOT NULL DEFAULT 'unknown'")
            # Backfill only from already persisted flags; never infer a strategy.
            self.conn.execute("""UPDATE matches
                SET control_source=CASE
                  WHEN autoplay_observed=1 AND manual_intervention=1 THEN 'mixed_auto_play'
                  WHEN autoplay_observed=1 THEN 'autoplay'
                  WHEN manual_intervention=1 THEN 'manual'
                  ELSE 'unknown' END
                WHERE control_source='unknown'""")

    def close(self) -> None:
        self.conn.close()

    def _insert_idempotent(self, table: str, fields: dict[str, object], unique_key: str = "source_hash") -> str:
        reject_sensitive(fields)
        source = str(fields[unique_key])
        row = self.conn.execute(f"SELECT * FROM {table} WHERE {unique_key}=?", (source,)).fetchone()
        if row:
            return str(row[0])
        cols = ",".join(fields)
        placeholders = ",".join("?" for _ in fields)
        self.conn.execute(f"INSERT INTO {table}({cols}) VALUES({placeholders})", tuple(fields.values()))
        self.conn.commit()
        return str(fields[next(iter(fields))])

    def create_run(self, *, seed: int = 6001, controller_version: str = POLICY_VERSION,
                   vision_profile_version: str = "6001-uncalibrated-v4",
                   target: int = 100, source: str = "run-start") -> str:
        run_id = str(uuid.uuid4())
        fields = dict(run_id=run_id, game_id=GAME, origin=ORIGIN, route=ROUTE,
                      browser_surface="ordinary_chrome", ruleset_version=RULESET_VERSION,
                      controller_version=controller_version,
                      vision_profile_version=vision_profile_version, schedule_seed=seed,
                      target_matches=target, started_at=utc_now(), status="prepared",
                      source_hash=digest([run_id, source, seed, target]))
        self._insert_idempotent("runs", fields)
        return run_id

    def add_attempt(self, run_id: str, *, requested_players: int, bet: float,
                    room_label: str = "", source: str = "", requested_at: str | None = None,
                    **extra: object) -> str:
        if requested_players not in (2, 3, 4) or bet <= 0:
            raise ValueError("invalid_attempt_matrix")
        reject_sensitive(extra)
        attempt_id = str(uuid.uuid4())
        fields = dict(attempt_id=attempt_id, run_id=run_id,
                      requested_players=requested_players, bet_display=bet,
                      room_label=room_label, requested_at=requested_at or utc_now(),
                      ended_at=extra.get("ended_at"), wait_ms=extra.get("wait_ms"),
                      actual_players=extra.get("actual_players"), human_count=extra.get("human_count"),
                      robot_count=extra.get("robot_count"), opponent_mix=extra.get("opponent_mix"),
                      terminal_reason=extra.get("terminal_reason"),
                      fallback_from_attempt_id=extra.get("fallback_from_attempt_id"),
                      source_hash=digest([source or attempt_id, run_id, requested_players, bet]),
                      quality_status=extra.get("quality_status", "observed"))
        return self._insert_idempotent("match_attempts", fields)

    def add_match(self, attempt_id: str, *, strategy_arm: str, game_build: str | None = None,
                  source: str = "", started_at: str | None = None,
                  control_source: str = "unknown") -> str:
        if strategy_arm not in ARMS:
            raise ValueError("invalid_strategy_arm")
        if control_source not in {"unknown", "manual", "autoplay", "mixed_auto_play", "uncontrolled_observation"}:
            raise ValueError("invalid_control_source")
        match_id = str(uuid.uuid4())
        fields = dict(match_id=match_id, attempt_id=attempt_id, strategy_arm=strategy_arm,
                      policy_version=POLICY_VERSION, control_source=control_source, game_build=game_build,
                      started_at=started_at or utc_now(), source_hash=digest([source or match_id, attempt_id, strategy_arm]))
        return self._insert_idempotent("matches", fields)

    def add_turn(self, match_id: str, state: dict[str, object], decision: dict[str, object] | None,
                 ack: dict[str, object] | None, *, seq: int, source: str = "") -> str:
        if seq < 1:
            raise ValueError("invalid_turn_seq")
        state = dict(state)
        decision = decision or {}
        ack = ack or {}
        hand = state.get("visible_hand")
        fields = dict(
            turn_id=str(uuid.uuid4()), match_id=match_id, seq=seq,
            state_seq=str(state.get("state_seq", "unknown")), phase=str(state.get("phase", "unknown")),
            action_owner=state.get("action_owner"), table_rank=(state.get("table_card") or {}).get("rank") if isinstance(state.get("table_card"), dict) else None,
            table_shape=(state.get("table_card") or {}).get("shape") if isinstance(state.get("table_card"), dict) else None,
            own_hand_count=len(hand) if isinstance(hand, list) else state.get("own_hand_count"),
            legal_action_count=len(decision.get("candidates", [])) if isinstance(decision.get("candidates"), list) else state.get("legal_action_count"),
            action=decision.get("action"), chosen_rank=(decision.get("chosen_card") or {}).get("rank") if isinstance(decision.get("chosen_card"), dict) else None,
            chosen_shape=(decision.get("chosen_card") or {}).get("shape") if isinstance(decision.get("chosen_card"), dict) else None,
            target_shape=decision.get("target_shape"), captured_at=str(state.get("captured_at") or utc_now()),
            submitted_at=ack.get("submitted_at"), confirmed_at=ack.get("confirmed_at"),
            decision_ms=decision.get("policy_compute_ms"), click_latency_ms=ack.get("click_latency_ms"),
            confirmation_ms=ack.get("confirmation_ms"), accepted=ack.get("accepted"),
            timeout=ack.get("timeout"), capture_confidence=state.get("capture_confidence"),
            source_hash=digest([source or match_id, seq, state, decision, ack]),
        )
        return self._insert_idempotent("turns", fields)

    def add_special(self, match_id: str, *, kind: str, actor: str | None = None,
                    status: str | None = None, turn_id: str | None = None, source: str = "") -> str:
        event_id = str(uuid.uuid4())
        fields = dict(event_id=event_id, match_id=match_id, turn_id=turn_id, kind=kind,
                      actor=actor, status=status, observed_at=utc_now(),
                      source_hash=digest([source or event_id, match_id, kind, status]))
        return self._insert_idempotent("special_events", fields)

    def settle(self, match_id: str, *, result: str, end_reason: str | None,
               player_points: int | None, opponent_points: int | None,
               player_cards: int | None, opponent_cards: int | None,
               autoplay_observed: bool, manual_intervention: bool = False,
               page_stake: float | None = None, page_return: float | None = None,
               page_net_change: float | None = None, balance_before: float | None = None,
               balance_after_debit: float | None = None, balance_after: float | None = None,
               fee: float | None = None, bonus: float | None = None,
               control_source: str | None = None,
               ledger_semantics_status: str = "unverified",
               return_assumption: str = "page_value_unverified", source: str = "",
               coverage_verified: bool = False, turn_opportunities: int | None = None) -> dict[str, object]:
        if result not in ("win", "loss", "draw", "unknown"):
            raise ValueError("invalid_result")
        settlement_id = str(uuid.uuid4())
        fields = dict(settlement_id=settlement_id, match_id=match_id, page_stake=page_stake,
                      page_return=page_return, page_net_change=page_net_change,
                      balance_before=balance_before, balance_after_debit=balance_after_debit,
                      balance_after=balance_after, fee=fee, bonus=bonus,
                      ledger_semantics_status=ledger_semantics_status,
                      return_assumption=return_assumption, observed_at=utc_now(),
                      source_hash=digest([source or settlement_id, match_id, result, page_stake, page_return]))
        self._insert_idempotent("settlements", fields)
        bad = []
        if result not in ("win", "loss", "draw"):
            bad.append("result_unknown")
        if control_source is not None and control_source not in {
            "unknown", "manual", "autoplay", "mixed_auto_play", "uncontrolled_observation"
        }:
            raise ValueError("invalid_control_source")
        if not end_reason:
            bad.append("end_reason_unknown")
        if autoplay_observed:
            bad.append("autoplay")
        if manual_intervention:
            bad.append("manual_intervention")
        if page_stake is None or page_return is None:
            bad.append("page_amount_missing")
        turns = self.conn.execute(
            "SELECT accepted,timeout,click_latency_ms FROM turns WHERE match_id=? ORDER BY seq",
            (match_id,),
        ).fetchall()
        if not turns:
            bad.append("turn_evidence_missing")
        elif any(t["accepted"] != 1 or t["timeout"] == 1 for t in turns):
            bad.append("turn_ack_unknown_or_timeout")
        elif not coverage_verified or turn_opportunities is None or turn_opportunities != len(turns):
            bad.append("turn_coverage_unverified")
        elif len(turns) / turn_opportunities < .95:
            bad.append("turn_coverage_below_95pct")
        latencies = [t["click_latency_ms"] for t in turns if isinstance(t["click_latency_ms"], (int, float))]
        if not latencies or max(latencies) > 2000:
            bad.append("click_latency_gate")
        qualified = not bad
        exclusion = ",".join(bad) or None
        self.conn.execute("""UPDATE matches SET finished_at=?,result=?,end_reason=?,player_points=?,
          opponent_points=?,player_cards=?,opponent_cards=?,autoplay_observed=?,manual_intervention=?,
          control_source=?,qualified=?,exclusion_reason=? WHERE match_id=?""",
                         (utc_now(), result, end_reason, player_points, opponent_points,
                          player_cards, opponent_cards, int(autoplay_observed), int(manual_intervention),
                          (control_source or
                           ("mixed_auto_play" if autoplay_observed and manual_intervention else
                            "autoplay" if autoplay_observed else
                            "manual" if manual_intervention else "unknown")),
                          int(qualified), exclusion, match_id))
        self.conn.commit()
        return {"qualified": qualified, "exclusion_reason": exclusion}

    def status(self) -> dict[str, object]:
        def count(q: str, args: tuple[object, ...] = ()) -> int:
            return int(self.conn.execute(q, args).fetchone()[0])
        by_game = self.conn.execute("SELECT strategy_arm,result,COUNT(*) n FROM matches GROUP BY 1,2").fetchall()
        attempts = self.conn.execute("SELECT requested_players,bet_display,COUNT(*) n FROM match_attempts GROUP BY 1,2 ORDER BY 1,2").fetchall()
        return {"runs": count("SELECT COUNT(*) FROM runs"), "attempts": count("SELECT COUNT(*) FROM match_attempts"),
                "matches": count("SELECT COUNT(*) FROM matches"), "finished": count("SELECT COUNT(*) FROM matches WHERE finished_at IS NOT NULL"),
                "qualified": count("SELECT COUNT(*) FROM matches WHERE qualified=1"),
                "strategy_results": [dict(x) for x in by_game], "matrix": [dict(x) for x in attempts]}


def wilson(wins: int, n: int) -> tuple[float | None, float | None]:
    if not n:
        return None, None
    z = 1.96
    p = wins / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return mid - half, mid + half


def build_schedule(seed: int = 6001) -> list[dict[str, object]]:
    """Create a reproducible 100-slot matrix with 34/33/33 policy arms."""
    cells: list[tuple[float, int]] = []
    for bet, n in BET_COUNTS:
        for players, target in PLAYER_COUNTS:
            # Proportionally allocate the requested player mix inside each bet block.
            # The explicit cell totals below keep the published matrix exact.
            if bet == 1:
                cell = {2: 12, 3: 4, 4: 4}[players]
            elif bet in (100, 200):
                cell = {2: 12, 3: 4, 4: 4}[players]
            elif bet == 1000:
                cell = {2: 15, 3: 5, 4: 5}[players]
            else:
                cell = {2: 9, 3: 3, 4: 3}[players]
            cells.extend((bet, players) for _ in range(cell))
    if len(cells) != 100:
        raise AssertionError("matrix_total")
    arms = [ARMS[0]] * 34 + [ARMS[1]] * 33 + [ARMS[2]] * 33
    rnd = random.Random(seed)
    rnd.shuffle(arms)
    slots = [dict(ordinal=i + 1, bet_display=bet, requested_players=players,
                  strategy_arm=arms[i], seed=seed) for i, (bet, players) in enumerate(cells)]
    return slots


def choose_decision(state: dict[str, object], strategy_arm: str, rules: dict[str, object]) -> dict[str, object]:
    """Pure, deterministic decision over visible state only; never clicks."""
    started = time.perf_counter_ns()
    out: dict[str, object] = {"action": "wait", "candidates": [], "chosen_card": None,
                              "target_shape": None, "reason_codes": [],
                              "policy_version": POLICY_VERSION, "strategy_arm": strategy_arm}
    if strategy_arm not in ARMS:
        out.update(action="stop", reason_codes=["unknown_strategy"])
    elif state.get("client_game_id", GAME) != GAME or state.get("route") not in (None, ROUTE):
        out.update(action="stop", reason_codes=["route_or_game_mismatch"])
    elif state.get("autoplay") is not False:
        out.update(action="stop", reason_codes=["control_mode_unknown_or_autoplay"])
    elif state.get("action_owner") not in ("self", "player"):
        out.update(action="wait", reason_codes=["not_player_turn"])
    elif state.get("phase") not in ("player_turn", "special_resolution"):
        out.update(action="wait", reason_codes=["not_actionable"])
    else:
        pending = state.get("pending_effect", "none")
        hand = state.get("visible_hand") or []
        if pending == "whot_shape_selection":
            shapes = rules.get("shapes", ["circle", "square", "triangle", "star", "cross"])
            counts = Counter(c.get("shape") for c in hand if isinstance(c, dict))
            target = max(shapes, key=lambda x: (counts.get(x, 0), -shapes.index(x)))
            out.update(action="select_shape", target_shape=target, reason_codes=["visible_hand_majority"])
        elif pending not in (None, "none"):
            out.update(action=str(pending), reason_codes=["verified_special_window"])
        else:
            table = state.get("table_card") or {}
            active_shape = state.get("effective_shape") or table.get("shape")
            candidates = [c for c in hand if isinstance(c, dict) and
                          (c.get("rank") == 20 or c.get("rank") == table.get("rank") or c.get("shape") == active_shape)]
            out["candidates"] = candidates
            if not candidates:
                out.update(action="draw", reason_codes=["no_legal_card"])
            else:
                if strategy_arm == ARMS[0]:
                    chosen = candidates[0]
                elif strategy_arm == ARMS[1]:
                    points = rules.get("points", {})
                    chosen = max(candidates, key=lambda c: (points.get(str(c.get("rank")), c.get("rank", 0)), -hand.index(c)))
                else:
                    normal = [c for c in candidates if c.get("rank") != 20]
                    chosen = normal[0] if normal else candidates[0]
                out.update(action="play", chosen_card=chosen, reason_codes=["fixed_policy"])
    out["policy_compute_ms"] = (time.perf_counter_ns() - started) / 1e6
    out["expires_at_ms"] = state.get("deadline_ms")
    return out


def confirm_action(before: dict[str, object], after: dict[str, object], decision: dict[str, object]) -> dict[str, object]:
    """Determine acceptance from a new visible state; animation alone is not acceptance."""
    if before.get("state_seq") == after.get("state_seq"):
        return {"accepted": None, "reason": "same_state_or_animation", "timeout": None}
    if after.get("autoplay") is not False:
        return {"accepted": None, "reason": "control_mode_unknown_or_autoplay", "timeout": None}
    action = decision.get("action")
    if action == "play":
        old = list(before.get("visible_hand") or [])
        new = list(after.get("visible_hand") or [])
        chosen = decision.get("chosen_card") or {}
        if len(new) != max(0, len(old) - 1):
            return {"accepted": False, "reason": "hand_count_not_decreased", "timeout": False}
        table = after.get("table_card") or {}
        ok = table.get("rank") == chosen.get("rank") and table.get("shape") == chosen.get("shape")
        return {"accepted": True if ok else False, "reason": "table_and_hand_changed", "timeout": False}
    if action == "draw":
        old_n, new_n = len(before.get("visible_hand") or []), len(after.get("visible_hand") or [])
        return {"accepted": True if new_n == old_n + 1 else False, "reason": "draw_count_changed", "timeout": False}
    if action == "select_shape":
        ok = after.get("effective_shape") == decision.get("target_shape") and after.get("pending_effect") in (None, "none")
        return {"accepted": True if ok else False, "reason": "shape_window_resolved", "timeout": False}
    return {"accepted": after.get("state_seq") != before.get("state_seq"), "reason": "special_state_changed", "timeout": False}


def report(path: Path, *, run_id: str | None = None, assume_gross: bool = False) -> dict[str, object]:
    store = Store(path, readonly=True)
    where, args = ("", ()) if run_id is None else (" WHERE a.run_id=?", (run_id,))
    rows = store.conn.execute(f"""SELECT a.bet_display,a.requested_players,a.actual_players,
      m.strategy_arm,m.control_source,m.result,m.qualified,m.autoplay_observed,s.page_stake,s.page_return
      FROM matches m JOIN match_attempts a ON a.attempt_id=m.attempt_id
      LEFT JOIN settlements s ON s.match_id=m.match_id{where}""", args).fetchall()
    groups: dict[tuple[object, object, object], list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        groups[(row["strategy_arm"], row["bet_display"], row["actual_players"] or row["requested_players"])].append(row)
    out = {"as_of": utc_now(), "status": "provisional", "run_id": run_id,
           "formal_rtp_status": "unverified", "groups": []}
    for (arm, bet, players), cohort in sorted(groups.items(), key=lambda x: str(x[0])):
        completed = [r for r in cohort if r["result"] in ("win", "loss", "draw")]
        qualified = [r for r in completed if r["qualified"] == 1]
        wins = sum(r["result"] == "win" for r in qualified)
        lo, hi = wilson(wins, len(qualified))
        rtp = None
        rtp_status = "not_computed"
        if assume_gross:
            vals = [(r["page_stake"], r["page_return"]) for r in qualified
                    if r["page_stake"] is not None and r["page_return"] is not None]
            if vals and sum(v[0] for v in vals) > 0:
                rtp = sum(v[1] for v in vals) / sum(v[0] for v in vals)
                rtp_status = "provisional_page_rtp_assuming_gross_return"
        out["groups"].append({"strategy_arm": arm, "bet_display": bet, "actual_players": players,
                              "attempts": len(cohort), "completed": len(completed), "qualified": len(qualified),
                              "wins": wins, "losses": sum(r["result"] == "loss" for r in qualified),
                              "win_rate": wins / len(qualified) if qualified else None,
                              "wilson95": [lo, hi], "provisional_rtp": rtp, "rtp_status": rtp_status,
                              "control_source_counts": dict(Counter(
                                  (r["control_source"] or "unknown") for r in cohort
                              ))})
    store.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="WHOT 6001 V3.2 local controlled-test store")
    parser.add_argument("--db", type=Path, default=Path(__file__).with_name("legacy6001_v3_2.sqlite3"))
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    s = sub.add_parser("schedule"); s.add_argument("--seed", type=int, default=6001)
    s = sub.add_parser("start-run"); s.add_argument("--seed", type=int, default=6001); s.add_argument("--target", type=int, default=100)
    s = sub.add_parser("report"); s.add_argument("--run-id"); s.add_argument("--assume-gross", action="store_true")
    args = parser.parse_args()
    if args.cmd == "init":
        s = Store(args.db); s.close(); print(json.dumps({"status": "initialized", "db": str(args.db)}))
    elif args.cmd == "status":
        s = Store(args.db, readonly=True); print(json.dumps(s.status(), ensure_ascii=False)); s.close()
    elif args.cmd == "schedule":
        slots = build_schedule(args.seed); print(json.dumps({"seed": args.seed, "count": len(slots), "strategy_counts": dict(Counter(x["strategy_arm"] for x in slots)), "bet_counts": dict(Counter(x["bet_display"] for x in slots)), "player_counts": dict(Counter(x["requested_players"] for x in slots))}, ensure_ascii=False))
    elif args.cmd == "start-run":
        s = Store(args.db); rid = s.create_run(seed=args.seed, target=args.target); print(json.dumps({"run_id": rid, "schedule": build_schedule(args.seed)} , ensure_ascii=False)); s.close()
    else:
        print(json.dumps(report(args.db, run_id=args.run_id, assume_gross=args.assume_gross), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

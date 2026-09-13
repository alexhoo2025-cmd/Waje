"""Version-specific WHOT flows and visible-state policy programs.

6001 and 9006 intentionally have different state and input contracts.  The
functions here are pure: the browser adapter performs the returned action and
persists the acknowledgement separately.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

ARMS = (
    "first_legal_play",
    "reduce_high_point_cards",
    "retain_special_or_wild_cards_until_needed",
)


@dataclass(frozen=True)
class VersionSpec:
    game_id: str
    route: str
    interaction_mode: str
    state_source: str
    player_mode: str
    observed_bets: tuple[int, ...]
    matching_timeout_seconds: int


LEGACY_6001 = VersionSpec(
    game_id="6001", route="/game/6001-whot",
    interaction_mode="legacy_canvas_single_click",
    state_source="masked_screen_ocr_and_shape_geometry",
    player_mode="server_selected_observed",
    observed_bets=(1, 100, 200, 500, 1000, 2000),
    matching_timeout_seconds=15,
)

NEW_9006 = VersionSpec(
    game_id="9006", route="/game/9006-wajewhot",
    interaction_mode="ax_select_then_play",
    state_source="full_accessibility_tree",
    player_mode="explicit_2_or_4",
    observed_bets=(1, 50, 100, 200, 1000, 5000, 50000),
    matching_timeout_seconds=45,
)

SPECS = {"6001": LEGACY_6001, "9006": NEW_9006}


def _majority_shape(hand: list[dict[str, Any]]) -> str:
    shapes = ("circle", "square", "triangle", "star", "cross")
    counts = Counter(c.get("shape") for c in hand)
    return max(shapes, key=lambda s: (counts.get(s, 0), -shapes.index(s)))


def _legal(hand: list[dict[str, Any]], table: dict[str, Any], effective_shape: str | None) -> list[dict[str, Any]]:
    rank, shape = table.get("rank"), effective_shape or table.get("shape")
    return [c for c in hand if c.get("rank") == 20 or c.get("rank") == rank or c.get("shape") == shape]


def _legacy_decide(state: dict[str, Any], arm: str) -> dict[str, Any]:
    """6001: single-click Canvas protocol; no AX enabled/selected state."""
    hand = state.get("visible_hand") or []
    pending = state.get("pending_effect", "none")
    if state.get("phase") == "settlement":
        return {"action": "wait", "reason": "settlement", "input_steps": 0}
    if state.get("autoplay") is True:
        return {"action": "stop", "reason": "legacy_autoplay", "input_steps": 0}
    if state.get("action_owner") not in ("self", "player") or not state.get("is_player_turn", False):
        return {"action": "wait", "reason": "not_player_turn", "input_steps": 0}
    if state.get("capture_confidence", 0) < .98:
        return {"action": "rescan", "reason": "legacy_ocr_confidence", "input_steps": 0}
    if pending == "whot_shape_selection":
        return {"action": "select_shape", "target_shape": _majority_shape(hand),
                "reason": "legacy_visible_hand_majority", "input_steps": 1}
    if pending not in (None, "none"):
        return {"action": "stop", "reason": "legacy_special_rule_unverified", "input_steps": 0}
    table = state.get("table_card") or {}
    if table.get("rank") in (2, 14) and not state.get("special_rule_verified", False):
        return {"action": "stop", "reason": "legacy_special_rule_unverified", "input_steps": 0}
    candidates = _legal(hand, table, state.get("effective_shape"))
    if not candidates:
        return {"action": "draw", "reason": "legacy_no_legal_card", "input_steps": 1,
                "confirm_rule": "hand_count_increases_or_turn_changes"}
    if arm == ARMS[0]:
        chosen = candidates[0]
    elif arm == ARMS[1]:
        chosen = max(candidates, key=lambda c: (c.get("rank", 0), -hand.index(c)))
    else:
        normal = [c for c in candidates if c.get("rank") != 20]
        chosen = normal[0] if normal else candidates[0]
    return {"action": "play", "chosen_card": chosen, "reason": "legacy_fixed_policy",
            "input_steps": 1, "confirm_rule": "card_leaves_hand_and_table_changes"}


def _new_decide(state: dict[str, Any], arm: str) -> dict[str, Any]:
    """9006: full AX protocol; a normal card is selected then played."""
    if state.get("phase") == "settlement":
        return {"action": "wait", "reason": "settlement", "input_steps": 0}
    if state.get("autoplay") is not False:
        return {"action": "stop", "reason": "new_autoplay_or_unknown", "input_steps": 0}
    if state.get("action_owner") not in ("self", "player") or not state.get("is_player_turn", False):
        return {"action": "wait", "reason": "not_player_turn", "input_steps": 0}
    if state.get("pending_effect") == "whot_shape_selection":
        return {"action": "select_shape", "target_shape": _majority_shape(state.get("visible_hand") or []),
                "reason": "new_ax_shape_window", "input_steps": 1}
    if state.get("pending_effect") not in (None, "none"):
        return {"action": str(state["pending_effect"]), "reason": "new_verified_special_window", "input_steps": 1}
    hand = state.get("visible_hand") or []
    table = state.get("table_card") or {}
    candidates = [c for c in hand if c.get("enabled") is not False and
                  (c.get("rank") == 20 or c.get("rank") == table.get("rank") or c.get("shape") == state.get("effective_shape", table.get("shape")))]
    if not candidates:
        return {"action": "draw", "reason": "new_no_enabled_legal_card", "input_steps": 1,
                "confirm_rule": "hand_count_increases"}
    if arm == ARMS[0]:
        chosen = candidates[0]
    elif arm == ARMS[1]:
        chosen = max(candidates, key=lambda c: (c.get("rank", 0), -hand.index(c)))
    else:
        normal = [c for c in candidates if c.get("rank") != 20]
        chosen = normal[0] if normal else candidates[0]
    if chosen.get("selected") is True:
        return {"action": "play_selected", "chosen_card": chosen,
                "reason": "new_selected_card_second_step", "input_steps": 1,
                "confirm_rule": "selected_card_leaves_hand_and_table_changes"}
    return {"action": "select_card", "chosen_card": chosen,
            "reason": "new_ax_first_step", "input_steps": 1,
            "confirm_rule": "card_selected_before_play"}


def decide(version: str, state: dict[str, Any], arm: str) -> dict[str, Any]:
    if version not in SPECS:
        return {"action": "stop", "reason": "unknown_version", "input_steps": 0}
    if arm not in ARMS:
        return {"action": "stop", "reason": "unknown_strategy", "input_steps": 0}
    state = dict(state)
    state.setdefault("client_game_id", version)
    if state.get("client_game_id") != version or state.get("route") not in (None, SPECS[version].route):
        return {"action": "stop", "reason": "version_route_mismatch", "input_steps": 0}
    result = _legacy_decide(state, arm) if version == "6001" else _new_decide(state, arm)
    result.update(version=version, strategy_arm=arm, policy_version=f"{version}-policy-v4")
    return result


def confirm(version: str, before: dict[str, Any], after: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    if version not in SPECS:
        return {"accepted": None, "reason": "unknown_version"}
    if before.get("state_seq") == after.get("state_seq"):
        return {"accepted": None, "reason": "same_frame_or_animation"}
    if after.get("autoplay") is not False:
        return {"accepted": None, "reason": "autoplay_or_unknown_control"}
    action = decision.get("action")
    if action in ("play", "play_selected", "select_card"):
        old_n = len(before.get("visible_hand") or [])
        new_n = len(after.get("visible_hand") or [])
        if action == "select_card":
            selected = after.get("selected_card") or {}
            return {"accepted": True if selected else False, "reason": "selection_state_changed"}
        chosen = decision.get("chosen_card") or {}
        table = after.get("table_card") or {}
        ok = (new_n == max(0, old_n - 1)
              and table.get("rank") == chosen.get("rank")
              and table.get("shape") == chosen.get("shape"))
        return {"accepted": bool(ok), "reason": "hand_and_table_changed"}
    if action == "draw":
        return {"accepted": len(after.get("visible_hand") or []) == len(before.get("visible_hand") or []) + 1,
                "reason": "draw_count_changed"}
    if action == "select_shape":
        return {"accepted": after.get("effective_shape") == decision.get("target_shape") and
                after.get("pending_effect") in (None, "none"), "reason": "shape_window_resolved"}
    return {"accepted": after.get("state_seq") != before.get("state_seq"), "reason": "special_state_changed"}


def flow(version: str) -> list[str]:
    if version == "6001":
        return ["HOME", "WHOT_CARD", "LEGACY_BET_LOBBY", "MATCHING", "DEALING",
                "PLAYER_TURN_OCR", "SINGLE_CLICK", "CONFIRM_CANVAS_CHANGE", "SETTLEMENT", "EXIT"]
    if version == "9006":
        return ["HOME", "WAJEWHOT_CARD", "NEW_PLAYER_MODE", "NEW_BET_LOBBY", "MATCHING",
                "DEALING", "PLAYER_TURN_AX", "SELECT_CARD", "PLAY_SELECTED",
                "SPECIAL_RESOLUTION", "SETTLEMENT", "PLAY_AGAIN_OR_CHANGE_ROOM"]
    raise ValueError("unknown_version")

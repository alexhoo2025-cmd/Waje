"""Stream sanitised visible state for the 6001 Canvas.

The process is read-only. It deliberately emits no names, URLs, account
values, cookies, tokens or raw OCR; the coordinator uses the normalized card
points to decide a CUA click and records the acknowledgement separately.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone


REGIONS = {
    "turn": [.30, .50, .45, .25],
    "autoplay": [.25, .35, .50, .30],
    "hand": [.20, .68, .65, .32],
    "table": [.50, .25, .25, .35],
    "stake": [.35, .35, .30, .20],
    "title": [.25, .00, .50, .25],
    "rewards": [.25, .25, .25, .35],
    "points": [.45, .25, .25, .35],
}


def request(proc: subprocess.Popen[str], payload: dict[str, object]) -> dict[str, object]:
    proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("native_worker_closed")
    return json.loads(line)


def text_values(region: dict[str, object]) -> list[str]:
    return [str(x.get("value", "")) for x in region.get("text", []) if isinstance(x, dict)]


def compact(frame: dict[str, object], inspected: dict[str, object]) -> dict[str, object]:
    regions = frame.get("regions", {})
    if not isinstance(regions, dict):
        regions = {}

    def reg(name: str) -> dict[str, object]:
        value = regions.get(name, {})
        return value if isinstance(value, dict) else {}

    def cards(name: str) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for raw in reg(name).get("cards", []):
            if not isinstance(raw, dict):
                continue
            point = raw.get("point")
            if not isinstance(point, list) or len(point) != 2:
                continue
            shape = raw.get("shape")
            out.append({
                "rank": raw.get("rank"),
                "shape": shape if shape in {"circle", "square", "triangle", "star", "cross", "wild"} else "unknown",
                "point": [round(float(point[0]), 5), round(float(point[1]), 5)],
            })
        return out

    all_turn = " ".join(text_values(reg("turn"))).upper()
    all_auto = " ".join(text_values(reg("autoplay"))).upper()
    title = " ".join(text_values(reg("title"))).upper()
    reward_text = " ".join(text_values(reg("rewards"))).upper()
    point_text = " ".join(text_values(reg("points"))).upper()
    turn_signal = ("YOUR TURN" in all_turn or "ZAMU YAKO" in all_turn)
    # OCR can pick up unrelated lobby copy (for example BET/bonus text).  A
    # non-empty OCR region is therefore not evidence of auto-play.  Require
    # one of the actual client prompt phrases before stopping the controller.
    auto_signal = any(phrase in (all_auto + " " + all_turn) for phrase in (
        "PLAY CARDS AUTOMATICALLY", "KIOTOMATIKI", "AUTOMATIC PLAY",
    ))
    settlement_signal = any(x in title for x in ("VICTORY", "DEFEAT", "WIN", "LOSE"))
    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "route": inspected.get("path"),
        "capture_ms": round(float(frame.get("native_ms", 0)), 2),
        "frame_age_ms": round(float(frame.get("frame_age_ms", 0)), 2),
        "turn": turn_signal,
        "auto": auto_signal,
        "auto_text_present": auto_signal,
        "hand": cards("hand"),
        "table": cards("table"),
        "turn_text_present": turn_signal,
        "settlement_visible": settlement_signal,
        "reward_sign": "+" if "+" in reward_text else ("-" if "-" in reward_text else None),
        "point_text_present": bool(point_text),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--pid", type=int, default=None)
    parser.add_argument("--window-id", type=int, default=None)
    parser.add_argument("--worker", default="/tmp/whot-native-v4")
    args = parser.parse_args()
    proc = subprocess.Popen([args.worker], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    try:
        status = request(proc, {"op": "status", "request_id": "status"})
        windows = [w for w in status.get("windows", []) if isinstance(w, dict) and w.get("bounds", {}).get("Height", 0) > 300]
        if not windows:
            raise RuntimeError("chrome_window_not_found")
        w = next((x for x in windows if args.window_id is not None and x.get("id") == args.window_id), windows[0])
        pid = args.pid or int(w["pid"])
        inspected = request(proc, {"op": "inspect", "pid": pid, "request_id": "inspect"})
        if inspected.get("origin") != "https://test-h5.wajetan.com" or inspected.get("path") != "/game/6001-whot":
            raise RuntimeError("wrong_game_route")
        window_id = int(args.window_id or w["id"])
        bounds = w["bounds"]
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            inspected = request(proc, {"op": "inspect", "pid": pid, "request_id": "inspect"})
            if inspected.get("origin") != "https://test-h5.wajetan.com" or inspected.get("path") != "/game/6001-whot":
                print(json.dumps({"status": "stop", "reason": "wrong_game_route"}), flush=True)
                return
            frame = request(proc, {
                "op": "capture", "window_id": window_id, "bounds": bounds,
                "screen_rect": inspected.get("content_bounds"), "crop": [0, 0, 1, 1],
                "regions": REGIONS, "allow_background_capture": True,
                "request_id": "capture",
            })
            if frame.get("status") != "ok":
                print(json.dumps({"status": "stop", "reason": frame.get("reason", "capture_failed")}), flush=True)
                return
            print(json.dumps(compact(frame, inspected), ensure_ascii=False), flush=True)
            time.sleep(.10)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Local-only visible-board brightness service for WHOT QA.

It accepts a screenshot over loopback and returns dimensions plus coarse
brightness samples. It never receives credentials, cookies, game state, or
network payloads, and it does not click the browser.
"""

from __future__ import annotations

import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ANALYZER = Path("/tmp/waje_whot_visible_board_analyzer")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/analyze":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 8_000_000:
                raise ValueError("invalid_image_length")
            body = self.rfile.read(length)
            completed = subprocess.run(
                [str(ANALYZER)],
                input=body,
                capture_output=True,
                check=False,
                timeout=2,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.decode("utf-8", "replace")[:200])
            payload = json.loads(completed.stdout.decode("utf-8"))
        except Exception as exc:  # pragma: no cover - operational guard
            payload = {"status": "error", "reason": str(exc)}
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *_args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()

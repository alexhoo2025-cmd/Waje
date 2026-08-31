#!/usr/bin/env python3
"""Entry point for on-demand enterprise Gemini Waje analysis."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from gemini_bridge import cli_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(cli_main())

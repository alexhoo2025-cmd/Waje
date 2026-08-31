#!/usr/bin/env python3
"""Apply a minimal viewport-overflow repair to a generated portable report.

The repair keeps the canonical report runtime and artifact payload intact.  It
only corrects the reader header's `100vw` viewport width, which creates a
horizontal scrollbar in desktop verification when a vertical scrollbar exists.
"""

from __future__ import annotations

import argparse
from pathlib import Path


MARKER = 'data-waje-portable-overflow-repair="true"'
STYLE = '''<style data-waje-portable-overflow-repair="true">
html,body{overflow-x:hidden!important}
.portable-page-header{width:100%!important;margin-right:0!important;margin-left:0!important}
</style>\n'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    content = args.html.read_text(encoding="utf-8")
    if MARKER not in content:
        if "</head>" not in content:
            raise ValueError("portable report does not contain a head closing tag")
        content = content.replace("</head>", f"{STYLE}</head>", 1)
        args.html.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()

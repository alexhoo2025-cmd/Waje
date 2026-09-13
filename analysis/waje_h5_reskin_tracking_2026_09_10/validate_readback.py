from __future__ import annotations

import json
import re
import sys


payload = json.load(sys.stdin)
document = payload["data"]["document"]
content = document["content"]

checks = {
    "revision": document["revision_id"],
    "characters": len(content),
    "h1_sections": len(re.findall(r"<h1(?: |>)", content)),
    "tables": content.count("<table"),
    "callouts": content.count("<callout"),
    "title_ok": "WAJE H5换皮数据指标与埋点设计 V1" in content,
    "for_you_chain_ok": all(
        marker in content
        for marker in (
            "FOR_YOU_REQUEST",
            "FOR_YOU_RESPONSE",
            "FOR_YOU_EXPOSURE",
            "FOR_YOU_CLICK",
            "FOR_YOU_GAME_OPEN",
            "GAMESTART",
        )
    ),
    "page_id_candidates_ok": all(
        marker in content
        for marker in ("n9pixal64m", "x8asb2sqh7", "ijkbaricdx", "vue16bnq1d")
    ),
    "quality_gates_ok": all(marker in content for marker in ("99.5%", "99%", "98%")),
    "privacy_rules_ok": all(
        marker in content for marker in ("手机号", "完整搜索词", "原始错误堆栈")
    ),
    "no_undefined": "undefined" not in content.lower(),
    "no_placeholder_tag": "<placeholder" not in content.lower(),
}

print(json.dumps(checks, ensure_ascii=False, indent=2))

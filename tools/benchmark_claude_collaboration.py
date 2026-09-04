#!/usr/bin/env python3
"""Small controlled serial-Sonnet comparator, not a Codex productivity claim."""
import argparse
import copy
import json
from pathlib import Path
import time
try:
    from .claude_bridge import Bridge, ROOT, READY, read, write, now
except ImportError:
    from claude_bridge import Bridge, ROOT, READY, read, write, now


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    b=Bridge(a.output/"serial-baseline")
    records=[]; started=time.monotonic()
    for name in ("report-task.json","code-task.json","diagnosis-task.json"):
        t=copy.deepcopy(read(ROOT/"analysis/agent_collaboration_validation_2026_09_04"/name))
        t.update({"role":"analyst","complexity":"normal","risk":"normal","parent_task_id":"serial-sonnet-baseline"})
        tid=b.submit(t)
        while b.status(tid)["status"] not in READY:time.sleep(.5)
        r=b.collect(tid)
        records.append({"fixture":name,"task_id":tid,"status":r["status"],"receipt":r["receipt"]})
        write(a.output/"baseline-progress.json",{"started_mode":"serial_sonnet","runs":records})
    write(a.output/"baseline.json",{"status":"completed","finished_at":now(),"mode":"serial_sonnet","elapsed_seconds":round(time.monotonic()-started,3),"runs":records,"limitation":"single small sample; no Codex-only baseline, no production speedup claim; outputs require coordinator rubric review"})
    print(json.dumps({"status":"completed","runs":len(records)}))


if __name__=="__main__":main()
